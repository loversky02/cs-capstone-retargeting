"""Predict grasp failure before acting, and ask a (simulated) human only when risk is high.

Each episode samples a cube and a perception-noise level. The robot sees K noisy detections,
grasps at their mean, and may ask for help first. Pre-grasp features use only what the robot
can observe: the believed pose, the believed size and the spread between detections. Friction is
hidden, so some failures stay unpredictable by design.

The "human" is an oracle that knows the true pose. It is a stand-in for measuring the value of
asking, not evidence about real operators.
"""

import argparse
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from sim.grasp import run_grasp
from sim.scene import Cube, Recorder, panda_scene, write_video

DETECTIONS = 5
FEATURES = ["belief_x", "belief_y", "belief_yaw", "belief_half", "spread_xy_mm", "spread_yaw_deg"]


def sample_episode(seed):
    rng = np.random.default_rng(seed)
    cube = Cube(x=rng.uniform(0.42, 0.65), y=rng.uniform(-0.2, 0.2), yaw=rng.uniform(-0.6, 0.6),
                half=rng.uniform(0.017, 0.03), friction=rng.uniform(0.08, 1.2))
    sigma = rng.choice([0.002, 0.006, 0.012, 0.02])  # lighting/occlusion levels, unknown to robot
    shots = np.array([cube.x, cube.y, cube.yaw]) + rng.normal(0, [sigma, sigma, sigma * 8], (DETECTIONS, 3))
    belief = shots.mean(axis=0)
    half_seen = cube.half + rng.normal(0, 0.0015)
    spread_xy = float(np.mean(np.linalg.norm(shots[:, :2] - belief[:2], axis=1)) * 1000)
    spread_yaw = float(np.degrees(np.std(shots[:, 2])))
    return cube, tuple(belief), [belief[0], belief[1], belief[2], half_seen, spread_xy, spread_yaw]


def rollout(seed):
    cube, belief, features = sample_episode(seed)
    auto = run_grasp(cube, belief)["success"]
    human = run_grasp(cube, (cube.x, cube.y, cube.yaw))["success"]
    return {"seed": seed, "features": features, "auto_success": auto, "human_success": human}


class RiskNet:
    """One-hidden-layer MLP trained with Adam on binary cross-entropy (numpy only)."""

    def __init__(self, inputs, hidden=16, seed=0):
        rng = np.random.default_rng(seed)
        self.p = {"w1": rng.normal(0, 0.5, (inputs, hidden)), "b1": np.zeros(hidden),
                  "w2": rng.normal(0, 0.5, hidden), "b2": np.zeros(1)}

    def _forward(self, x):
        h = np.tanh(x @ self.p["w1"] + self.p["b1"])
        return h, 1 / (1 + np.exp(-(h @ self.p["w2"] + self.p["b2"])))

    def predict(self, x):
        return self._forward((x - self.mu) / self.sd)[1]

    def fit(self, x, y, epochs=1500, lr=0.01, l2=1e-3):
        self.mu, self.sd = x.mean(0), x.std(0) + 1e-9
        x = (x - self.mu) / self.sd
        m = {k: 0 for k in self.p}
        v = {k: 0 for k in self.p}
        for t in range(1, epochs + 1):
            h, out = self._forward(x)
            d = (out - y) / len(y)
            dh = np.outer(d, self.p["w2"]) * (1 - h ** 2)
            grads = {"w2": h.T @ d + l2 * self.p["w2"], "b2": np.array([d.sum()]),
                     "w1": x.T @ dh + l2 * self.p["w1"], "b1": dh.sum(0)}
            for k, g in grads.items():
                m[k] = 0.9 * m[k] + 0.1 * g
                v[k] = 0.999 * v[k] + 0.001 * g ** 2
                self.p[k] -= lr * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8)
        return self


def auroc(score, positive):
    order = np.argsort(score)
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    n_pos, n_neg = positive.sum(), (~positive).sum()
    return float((ranks[positive].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def ask_curve(risk, auto, human, rates):
    """Success rate when the robot asks on the top `rate` fraction of episodes by risk."""
    order = np.argsort(-risk)
    out = []
    for rate in rates:
        ask = np.zeros(len(risk), dtype=bool)
        ask[order[:int(round(rate * len(risk)))]] = True
        out.append(float(np.where(ask, human, auto).mean()))
    return out


def evaluate(rows, seed=0):
    x = np.array([r["features"] for r in rows])
    auto = np.array([r["auto_success"] for r in rows])
    human = np.array([r["human_success"] for r in rows])
    split = len(rows) * 2 // 3
    y = (~auto).astype(float)
    inner = split * 3 // 4  # choose L2 strength on a validation slice of the training data only
    l2 = max((1e-3, 1e-2, 3e-2, 1e-1), key=lambda reg: auroc(
        RiskNet(x.shape[1], seed=seed).fit(x[:inner], y[:inner], l2=reg).predict(x[inner:split]),
        ~auto[inner:split]))
    net = RiskNet(x.shape[1], seed=seed).fit(x[:split], y[:split], l2=l2)
    test = slice(split, None)
    rng = np.random.default_rng(seed)
    scores = {
        "random": rng.random(len(rows) - split),
        "heuristic_spread": x[test, 4],  # hand-tuned rule: ask when detections disagree
        "risk_net": net.predict(x[test]),
        "oracle_hindsight": (~auto[test]).astype(float) + 1e-3 * rng.random(len(rows) - split),
    }
    rates = [round(r, 2) for r in np.linspace(0, 1, 21)]
    fail = ~auto[test]
    return net, {
        "risk_net_l2": l2,
        "episodes_total": len(rows), "train": split, "test": len(rows) - split,
        "auto_success_rate_test": float(auto[test].mean()),
        "human_success_rate_test": float(human[test].mean()),
        "ask_rates": rates,
        "curves": {k: ask_curve(s, auto[test], human[test], rates) for k, s in scores.items()},
        "failure_auroc": {k: auroc(s, fail) for k, s in scores.items() if k != "oracle_hindsight"},
        "features": FEATURES,
        "human_model": "oracle with the true cube pose (simulated, not a real operator)",
    }


def highlight_video(rows, net, path, threshold):
    """Render three test episodes: confident success, asked-and-fixed, and a missed failure."""
    test = rows[len(rows) * 2 // 3:]
    risk = net.predict(np.array([r["features"] for r in test]))
    picks = []
    wants = [lambda r, p: r["auto_success"] and p < threshold,
             lambda r, p: not r["auto_success"] and r["human_success"] and p >= threshold,
             lambda r, p: not r["auto_success"] and p < threshold]
    for want in wants:
        found = next(((r, p) for r, p in zip(test, risk) if want(r, p)), None)
        if found:
            picks.append(found)
    frames = []
    for row, p in picks:
        cube, belief, _ = sample_episode(row["seed"])
        rec = Recorder(panda_scene(cube)[0])
        if p >= threshold:  # show the start of the approach, then pause and hand over
            run_grasp(cube, belief, rec, f"P(fail)={p:.2f} >= {threshold}: PAUSE, ASK HUMAN", (251, 191, 36))
            rec.frames = rec.frames[:20] + [rec.frames[19]] * 45  # hold the pause so it can be read
            run_grasp(cube, (cube.x, cube.y, cube.yaw), rec,
                      "HUMAN TAKEOVER (simulated oracle) -> re-perceive, regrasp", (56, 189, 248))
        else:
            ok = row["auto_success"]
            run_grasp(cube, belief, rec, f"P(fail)={p:.2f}: robot acts alone -> "
                      + ("SUCCESS" if ok else "FAILED, risk was missed"),
                      (34, 197, 94) if ok else (244, 63, 94))
        frames += rec.frames
    write_video(frames, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--episodes", type=int, default=1200)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--out", type=Path, default=Path("outputs/teleguide"))
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()
    with Pool() as pool:
        rows = pool.map(rollout, range(args.episodes))
    net, report = evaluate(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "episodes.json").write_text(json.dumps(rows))
    (args.out / "report.json").write_text(json.dumps(report, indent=2))
    if not args.no_video:
        highlight_video(rows, net, args.out / "highlights.mp4", args.threshold)
    print(json.dumps({k: report[k] for k in ("auto_success_rate_test", "human_success_rate_test",
                                             "failure_auroc")}, indent=2))


if __name__ == "__main__":
    main()
