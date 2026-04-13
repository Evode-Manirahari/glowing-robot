#!/usr/bin/env python3
"""
demo_replay.py — run a mission replay end-to-end from the CLI.

Usage:
    python scripts/demo_replay.py sim/scenarios/warehouse_basic.json
    python scripts/demo_replay.py sim/scenarios/warehouse_collision.json

This is the canonical demo script. Every significant feature must have a
runnable demo script in scripts/ before it is considered done.
"""
import json
import sys
from pathlib import Path

# Add project root to path so we can import sim/
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.replay.engine import load_log, replay


def eval_report(result, log: dict) -> dict:
    metrics = result.to_dict()
    verdict = "fail" if metrics["collision_count"] > 0 else (
        "warning" if metrics["max_deviation_m"] > 0.5 else "pass"
    )
    anomalies = []
    if metrics["collision_count"] > 0:
        anomalies.append(f"{metrics['collision_count']} collision(s) detected")
    if metrics["max_deviation_m"] > 0.5:
        anomalies.append(f"Max deviation {metrics['max_deviation_m']:.2f}m exceeds 0.5m threshold")

    return {
        "mission_name": log.get("name", "unknown"),
        "robot_type": log.get("robot_type", "unknown"),
        "verdict": verdict,
        **metrics,
        "anomalies": anomalies,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/demo_replay.py <log.json>")
        sys.exit(1)

    log_path = Path(sys.argv[1])
    if not log_path.exists():
        print(f"Error: {log_path} not found")
        sys.exit(1)

    print(f"\n--- glowing-robot: Mission Replay ---")
    print(f"Log: {log_path}\n")

    log = load_log(log_path)
    result = replay(log)
    report = eval_report(result, log)

    verdict_icon = {"pass": "PASS", "fail": "FAIL", "warning": "WARN"}[report["verdict"]]

    print(f"[{verdict_icon}] {report['mission_name']}")
    print(f"      Robot:         {report['robot_type']}")
    print(f"      Frames:        {report['frame_count']}")
    print(f"      Duration:      {report['duration_s']:.1f}s")
    print(f"      Collisions:    {report['collision_count']}")
    print(f"      Max deviation: {report['max_deviation_m']:.3f}m")
    print(f"      Completion:    {report['completion_rate'] * 100:.0f}%")

    if report["anomalies"]:
        print("\n  Anomalies:")
        for a in report["anomalies"]:
            print(f"    - {a}")

    output_path = Path("runs") / f"{log_path.stem}_report.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  Report saved: {output_path}\n")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
