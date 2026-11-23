"""Deterministic planar retargeting with a synthetic segment-correction oracle."""

import argparse
import hashlib
import json
import math
from pathlib import Path

LINKS = (0.4, 0.3)
LIMITS = ((-1.2, 1.2), (0.0, 1.8))
SEGMENTS = ((4, 8, 0.18), (13, 17, -0.10), (22, 26, -0.27))


def forward(q1, q2):
    a, b = LINKS
    return (a * math.cos(q1) + b * math.cos(q1 + q2),
            a * math.sin(q1) + b * math.sin(q1 + q2))


def inverse(x, y):
    a, b = LINKS
    cosine = (x*x + y*y - a*a - b*b) / (2*a*b)
    outside = abs(cosine) > 1.0 + 1e-12
    q2 = math.acos(max(-1.0, min(1.0, cosine)))
    q1 = math.atan2(y, x) - math.atan2(b * math.sin(q2), a + b * math.cos(q2))
    return (q1, q2), outside


def run(budget):
    return simulate(budget)["result"]


def simulate(budget):
    """Return the metrics record plus per-frame trajectories for visualisation."""
    if budget not in range(len(SEGMENTS) + 1):
        raise ValueError("budget must be between 0 and 3")
    reference = [forward(0.2 * math.sin(i / 5), 1.25) for i in range(30)]
    observed = reference.copy()
    for start, stop, bias in SEGMENTS:
        for i in range(start, stop):
            x, y = reference[i]
            observed[i] = (x + bias, y)
    # The injected bias is known to the oracle. Real videos lack this information.
    selected = sorted(SEGMENTS, key=lambda segment: -abs(segment[2]))[:budget]
    for start, stop, _ in selected:
        observed[start:stop] = reference[start:stop]

    violations = outside_count = 0
    squared_errors = []
    frames = []
    for target, truth in zip(observed, reference):
        raw, outside = inverse(*target)
        outside_count += int(outside)
        violations += int(any(not low <= q <= high
                              for q, (low, high) in zip(raw, LIMITS)))
        bounded = [max(low, min(high, q)) for q, (low, high) in zip(raw, LIMITS)]
        achieved = forward(*bounded)
        squared_errors.append(math.dist(achieved, truth) ** 2)
        frames.append({"reference": truth, "target": target, "joints": bounded,
                       "achieved": achieved, "outside": outside})
    result = {
        "scenario": "synthetic-planar-2r-v1",
        "frames": len(reference),
        "budget_segments": budget,
        "used_segments": len(selected),
        "corrected_frame_ranges_half_open": [[s, e] for s, e, _ in selected],
        "position_rmse_m": round(math.sqrt(math.fsum(squared_errors) / len(reference)), 9),
        "joint_limit_violation_frames": violations,
        "geometrically_unreachable_target_frames": outside_count,
    }
    return {"result": result, "frames": frames}


def journal():
    return {
        "method": "SIM-inspired experiment record",
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "baseline": run(0),
        "change": "Replace corrupted target observations with synthetic ground truth, highest injected bias first.",
        "rationale": "Estimate the effect of segment correction under a fixed offline budget.",
        "prediction": "Oracle correction should reduce position RMSE as the budget increases.",
        "observed": [run(budget) for budget in range(1, len(SEGMENTS) + 1)],
        "decision": "Keep as a teaching reference for this synthetic case.",
        "limitations": "No orientation, collision, human corrections, video, or physical trials.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--budget", type=int, choices=range(len(SEGMENTS) + 1), default=0)
    options.add_argument("--journal", action="store_true")
    args = parser.parse_args()
    print(json.dumps(journal() if args.journal else run(args.budget), indent=2))


if __name__ == "__main__":
    main()
