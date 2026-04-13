#!/usr/bin/env python3
"""
demo_compare.py — compare two mission logs side by side from the CLI.

Usage:
    python scripts/demo_compare.py sim/scenarios/warehouse_basic.json sim/scenarios/warehouse_collision.json

Outputs a side-by-side metric table and a delta summary.
Does not call the AI — use the web UI for AI-powered comparison summaries.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_api.parsers import parse_log
from sim.replay.engine import replay
from evals.metrics.compute import compute


def fmt_verdict(v: str) -> str:
    colors = {"pass": "\033[92m", "fail": "\033[91m", "warning": "\033[93m"}
    reset = "\033[0m"
    return f"{colors.get(v, '')}{v.upper()}{reset}"


def compare(log_a: Path, log_b: Path) -> None:
    print(f"\n--- glowing-robot: Policy Comparison ---\n")

    metrics_list = []
    for path in [log_a, log_b]:
        log = parse_log(path)
        result = replay(log)
        metrics_list.append(compute(result))

    r_a, r_b = metrics_list

    col = 28
    sep = "-" * (col * 2 + 7)

    print(f"{'Metric':<20}  {'A: ' + log_a.stem:<{col}}  {'B: ' + log_b.stem:<{col}}  Delta")
    print(sep)

    def row(label: str, a, b, fmt=str, lower_better=True):
        delta = b - a if isinstance(a, (int, float)) else None
        if delta is not None:
            if delta == 0:
                delta_str = "  —"
            elif (lower_better and delta < 0) or (not lower_better and delta > 0):
                delta_str = f"\033[92m{delta:+.3g}\033[0m"
            else:
                delta_str = f"\033[91m{delta:+.3g}\033[0m"
        else:
            delta_str = ""
        print(f"{label:<20}  {fmt(a):<{col}}  {fmt(b):<{col}}  {delta_str}")

    row("Verdict", r_a["verdict"], r_b["verdict"], fmt=fmt_verdict, lower_better=False)
    row("Collisions", r_a["collision_count"], r_b["collision_count"], fmt=str)
    row("Max deviation (m)", r_a["max_deviation_m"], r_b["max_deviation_m"], fmt=lambda v: f"{v:.3f}")
    row("Completion (%)", r_a["completion_rate"] * 100, r_b["completion_rate"] * 100, fmt=lambda v: f"{v:.0f}%", lower_better=False)
    row("Duration (s)", r_a["duration_s"], r_b["duration_s"], fmt=lambda v: f"{v:.1f}")
    print(sep)

    verdict_a, verdict_b = r_a["verdict"], r_b["verdict"]
    if verdict_a == verdict_b == "pass":
        print("\nBoth runs passed. No regression detected.")
    elif verdict_b == "fail" and verdict_a != "fail":
        print(f"\n\033[91mREGRESSION: Mission B failed where A passed.\033[0m")
    elif verdict_b == "pass" and verdict_a != "pass":
        print(f"\n\033[92mIMPROVEMENT: Mission B passed where A did not.\033[0m")
    else:
        print(f"\nVerdict unchanged: {fmt_verdict(verdict_b)}")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two mission logs side by side")
    parser.add_argument("log_a", help="Path to mission A log (.json or .csv)")
    parser.add_argument("log_b", help="Path to mission B log (.json or .csv)")
    args = parser.parse_args()

    path_a, path_b = Path(args.log_a), Path(args.log_b)
    for p in [path_a, path_b]:
        if not p.exists():
            print(f"Error: {p} not found", file=sys.stderr)
            return 1

    compare(path_a, path_b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
