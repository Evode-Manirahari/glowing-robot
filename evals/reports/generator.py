"""
Report generator — takes metrics dict and produces a structured report.
Used both by the backend service and the CLI demo script.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


def generate(metrics: dict, mission_name: str = "mission", ai_summary: str | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mission_name": mission_name,
        "verdict": metrics["verdict"],
        "summary": {
            "collisions": metrics["collision_count"],
            "max_deviation_m": round(metrics["max_deviation_m"], 4),
            "completion_pct": round(metrics["completion_rate"] * 100, 1),
            "duration_s": round(metrics["duration_s"], 2),
            "frame_count": metrics["frame_count"],
        },
        "anomalies": metrics["anomalies"],
        "ai_analysis": ai_summary,
        "raw_metrics": {
            "collision_events": metrics.get("collisions", []),
        },
    }


def save(report: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def print_summary(report: dict) -> None:
    verdict_label = {"pass": "PASS", "fail": "FAIL", "warning": "WARN"}.get(report["verdict"], "???")
    s = report["summary"]
    print(f"\n[{verdict_label}] {report['mission_name']}")
    print(f"  Collisions:    {s['collisions']}")
    print(f"  Max deviation: {s['max_deviation_m']}m")
    print(f"  Completion:    {s['completion_pct']}%")
    print(f"  Duration:      {s['duration_s']}s  ({s['frame_count']} frames)")
    if report["anomalies"]:
        print("  Anomalies:")
        for a in report["anomalies"]:
            print(f"    - {a}")
    if report.get("ai_analysis"):
        print(f"\n  AI Analysis:\n  {report['ai_analysis']}")
