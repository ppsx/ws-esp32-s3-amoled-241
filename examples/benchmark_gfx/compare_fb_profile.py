#!/usr/bin/env python3
"""
Compare FRAMEBUFFER profile CSV against baseline thresholds.

Usage:
    python compare_fb_profile.py --csv fb_profile.csv

Exit codes:
    0 - PASS
    1 - FAIL (missing scenario or threshold regression)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys


# Frozen baseline/thresholds for the canonical fb_profile benchmark (2026-03-06).
TARGETS = [
    {
        "mode": "fb_single_rebuild",
        "scenario": "primitive_stress",
        "baseline_fps": 35.511,
        "min_fps": 33.0,
        "max_avg_ms": 41.0,
    },
    {
        "mode": "fb_double_rebuild",
        "scenario": "full_redraw_control",
        "baseline_fps": 25.107,
        "min_fps": 24.0,
        "max_avg_ms": 42.0,
    },
    {
        "mode": "fb_double_retained",
        "scenario": "retained_blit_transparent",
        "baseline_fps": 573.963,
        "min_fps": 520.0,
        "max_avg_ms": 1.90,
        "max_p95_ms": 2.10,
    },
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare fb_profile.csv against baseline thresholds")
    p.add_argument("--csv", default="fb_profile.csv", help="Path to fb_profile.csv")
    return p.parse_args()


def load_metrics(csv_path: Path):
    scenario_end = {}
    last_sample = {}

    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 20:
                continue

            mode = row[0].strip()
            scenario = row[3].strip()
            key = (mode, scenario)
            event = row[19].strip()

            try:
                metrics = {
                    "fps": float(row[7]),
                    "avg_ms": float(row[8]),
                    "p95_ms": float(row[9]),
                    "max_ms": float(row[10]),
                    "draw_ms": float(row[11]),
                    "swap_ms": float(row[12]),
                    "window_frames": int(row[6]),
                }
            except (ValueError, IndexError):
                continue

            if event == "sample":
                last_sample[key] = metrics
            elif event == "scenario_end":
                scenario_end[key] = metrics

    resolved = {}
    for key, end_metrics in scenario_end.items():
        if end_metrics["window_frames"] > 0 and end_metrics["fps"] > 0:
            resolved[key] = ("scenario_end", end_metrics)
        elif key in last_sample:
            resolved[key] = ("fallback_sample", last_sample[key])
        else:
            resolved[key] = ("invalid", end_metrics)

    for key, sample_metrics in last_sample.items():
        if key not in resolved:
            resolved[key] = ("sample_only", sample_metrics)

    return resolved


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"FAIL: CSV not found: {csv_path}")
        return 1

    data = load_metrics(csv_path)

    print("FB_PROFILE_COMPARE_START")
    print("mode,scenario,source,fps,avg_ms,p95_ms,baseline_fps,min_fps,max_avg_ms,status,reason")

    failed = False

    for target in TARGETS:
        key = (target["mode"], target["scenario"])
        if key not in data:
            failed = True
            print(
                f"{target['mode']},{target['scenario']},missing,0,0,0,"
                f"{target['baseline_fps']:.3f},{target['min_fps']:.3f},{target['max_avg_ms']:.3f},FAIL,missing_scenario"
            )
            continue

        source, m = data[key]

        reasons = []
        if m["fps"] < target["min_fps"]:
            reasons.append("fps_below_threshold")
        if m["avg_ms"] > target["max_avg_ms"]:
            reasons.append("avg_ms_above_threshold")

        max_p95 = target.get("max_p95_ms")
        if max_p95 is not None and m["p95_ms"] > max_p95:
            reasons.append("p95_ms_above_threshold")

        status = "PASS" if not reasons else "FAIL"
        if status == "FAIL":
            failed = True

        reason = "ok" if not reasons else "+".join(reasons)
        print(
            f"{target['mode']},{target['scenario']},{source},"
            f"{m['fps']:.3f},{m['avg_ms']:.3f},{m['p95_ms']:.3f},"
            f"{target['baseline_fps']:.3f},{target['min_fps']:.3f},{target['max_avg_ms']:.3f},"
            f"{status},{reason}"
        )

    print("FB_PROFILE_COMPARE_END")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
