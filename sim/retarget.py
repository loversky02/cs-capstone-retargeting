"""Kinematic cross-embodiment retargeting: replay a Panda pick on a UR5e and measure what breaks.

The Panda runs the scripted grasp; its tool-centre trajectory (position + orientation) is the
source demo. Each frame is retargeted to the UR5e by damped least-squares IK, warm-started from
the previous frame. We report tool-position error, frames that hit joint limits and the joint-space
jerk, and render both arms side by side.

This is the "kinematic retarget" first stage of DemoDiffusion-style pipelines. It says nothing
about whether the UR5e would physically grasp the cube; that needs a gripper and dynamics.
"""

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from sim.grasp import run_grasp
from sim.scene import UR5E_JOINTS, Cube, Recorder, caption_frame, solve_ik, ur5e_scene, write_video


class TcpLog:
    """Recorder stand-in that stores the Panda tool pose and the rendered frame."""

    def __init__(self, model):
        self.inner = Recorder(model, 480, 400)
        self.frames, self.poses = [], []
        self.site = model.site("tcp").id

    def snap(self, data, caption="", color=(255, 255, 255)):
        quat = np.zeros(4)
        mujoco.mju_mat2Quat(quat, data.site_xmat[self.site])
        self.poses.append((data.site_xpos[self.site].copy(), quat))
        self.inner.snap(data)
        self.frames.append(self.inner.frames[-1])


def retarget(poses, use_orientation=True, restarts=0, seed=0, cube=None):
    model, data = ur5e_scene(cube)
    qadr = [model.joint(j).qposadr[0] for j in UR5E_JOINTS]
    ranges = np.array([model.joint(j).range for j in UR5E_JOINTS])
    rows = []
    for pos, quat in poses:
        target = quat if use_orientation else None
        q, err = solve_ik(model, data, UR5E_JOINTS, pos, target, iters=100)
        rng = np.random.default_rng(seed)
        for _ in range(restarts if err > 0.005 else 0):  # escape local minima from random seeds
            data.qpos[qadr] = rng.uniform(-np.pi, np.pi, len(qadr))
            q2, e2 = solve_ik(model, data, UR5E_JOINTS, pos, target, iters=200)
            if e2 < err:
                q, err = q2, e2
            if err < 0.005:
                break
        data.qpos[qadr] = q
        mujoco.mj_forward(model, data)
        at_limit = bool(np.any(np.isclose(q, ranges[:, 0], atol=1e-3) | np.isclose(q, ranges[:, 1], atol=1e-3)))
        rows.append({"q": q.tolist(), "err_mm": err * 1000, "at_limit": at_limit})
    return model, rows


def metrics(rows, fps=30):
    q = np.array([r["q"] for r in rows])
    err = np.array([r["err_mm"] for r in rows])
    jerk = np.diff(q, 3, axis=0) * fps ** 3 if len(q) > 3 else np.zeros((1, q.shape[1]))
    return {"frames": len(rows), "tcp_err_mean_mm": float(err.mean()), "tcp_err_max_mm": float(err.max()),
            "frames_over_5mm": int((err > 5).sum()), "frames_at_joint_limit": int(sum(r["at_limit"] for r in rows)),
            "joint_jerk_rms_rad_s3": float(np.sqrt((jerk ** 2).mean()))}


def render_ur5e(model, rows, width=480, height=400):
    data = mujoco.MjData(model)
    rec = Recorder(model, width, height)
    qadr = [model.joint(j).qposadr[0] for j in UR5E_JOINTS]
    for r in rows:
        data.qpos[qadr] = r["q"]
        mujoco.mj_forward(model, data)
        rec.snap(data)
    return rec.frames


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("outputs/retarget"))
    args = parser.parse_args()
    from sim.scene import panda_scene
    cube = Cube(x=0.5, y=0.12, yaw=0.3)
    log = TcpLog(panda_scene(cube, ghost=False)[0])
    src = run_grasp(cube, (cube.x, cube.y, cube.yaw), log)
    report = {"source_panda_grasp_success": bool(src["success"]), "variants": {}}
    videos = {}
    for name, orient in (("position_and_orientation", True), ("position_only", False)):
        model, rows = retarget(log.poses, orient, cube=cube)
        report["variants"][name] = metrics(rows)
        videos[name] = (model, rows)
    model, rows = videos["position_and_orientation"]
    right = render_ur5e(model, rows)
    frames = []
    for i, (a, b) in enumerate(zip(log.frames, right)):
        e = rows[i]["err_mm"]
        frames.append(np.hstack([caption_frame(a, "SOURCE: Panda (7-DoF) scripted pick", (34, 197, 94)),
                                 caption_frame(b, f"RETARGET: UR5e (6-DoF) IK  err={e:5.1f} mm",
                                               (251, 191, 36) if e > 5 else (56, 189, 248))]))
    report["reach_sweep"] = reach_sweep()
    args.out.mkdir(parents=True, exist_ok=True)
    write_video(frames, args.out / "panda_to_ur5e.mp4")
    (args.out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def reach_sweep(xs=None, ys=None):
    """Max UR5e tool error when retargeting the pre-grasp/grasp poses for cubes across the table."""
    from sim.scene import down_quat
    xs = np.linspace(0.3, 0.9, 7) if xs is None else xs
    ys = np.linspace(-0.6, 0.6, 7) if ys is None else ys
    grid = []
    for x in xs:
        row = []
        for y in ys:
            poses = [(np.array([x, y, z]), down_quat(np.pi / 4)) for z in (0.14, 0.024, 0.22)]
            row.append(max(r["err_mm"] for r in retarget(poses, restarts=8)[1]))
        grid.append(row)
    return {"xs": xs.tolist(), "ys": ys.tolist(), "max_err_mm": grid}


if __name__ == "__main__":
    main()
