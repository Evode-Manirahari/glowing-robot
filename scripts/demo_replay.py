#!/usr/bin/env python3
"""
demo_replay.py — run a mission replay end-to-end from the CLI.

Usage:
    python scripts/demo_replay.py sim/scenarios/warehouse_basic.json
    python scripts/demo_replay.py sim/scenarios/warehouse_collision.json
    python scripts/demo_replay.py mylog.csv --robot-type AMR

This is the canonical demo script. Every significant feature must have a
runnable demo script in scripts/ before it is considered done.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_api.parsers import parse_log
from sim.replay.engine import replay
from evals.metrics.compute import compute
from evals.reports.generator import generate, save, print_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="glowing-robot: replay a mission log")
    parser.add_argument("log", help="Path to .json or .csv log file")
    parser.add_argument("--robot-type", default="AMR", help="Robot type (default: AMR)")
    parser.add_argument("--no-report", action="store_true", help="Skip saving report to disk")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"Error: {log_path} not found", file=sys.stderr)
        return 1

    print(f"\n--- glowing-robot: Mission Replay ---")
    print(f"Log: {log_path}\n")

    log = parse_log(log_path, robot_type=args.robot_type)
    result = replay(log)
    metrics = compute(result)
    report = generate(metrics, mission_name=log.get("name", log_path.stem))

    print_summary(report)

    if not args.no_report:
        out = Path("runs") / f"{log_path.stem}_report.json"
        save(report, out)
        print(f"\n  Report saved: {out}\n")

    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
