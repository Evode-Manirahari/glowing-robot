"""
Standalone metrics computation — can be used outside the backend too.
All logic is pure Python; no database or API dependencies.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sim.replay.engine import ReplayResult

COLLISION_THRESHOLD = 0
DEVIATION_WARN_M = 0.5
COMPLETION_THRESHOLD = 0.95


def compute(result: ReplayResult) -> dict:
    raw = result.to_dict()
    anomalies: list[str] = []

    if raw["collision_count"] > COLLISION_THRESHOLD:
        anomalies.append(f"{raw['collision_count']} collision(s) detected")
    if raw["max_deviation_m"] > DEVIATION_WARN_M:
        anomalies.append(f"Max deviation {raw['max_deviation_m']:.2f}m exceeds {DEVIATION_WARN_M}m threshold")
    if raw["completion_rate"] < COMPLETION_THRESHOLD:
        anomalies.append(f"Only {raw['completion_rate']*100:.0f}% of waypoints reached")

    verdict = (
        "fail"
        if raw["collision_count"] > 0 or raw["completion_rate"] < COMPLETION_THRESHOLD
        else "warning"
        if raw["max_deviation_m"] > DEVIATION_WARN_M
        else "pass"
    )

    return {
        "verdict": verdict,
        "collision_count": raw["collision_count"],
        "max_deviation_m": raw["max_deviation_m"],
        "completion_rate": raw["completion_rate"],
        "duration_s": raw["duration_s"],
        "frame_count": raw["frame_count"],
        "anomalies": anomalies,
        "collisions": raw["collisions"],
        "deviations": raw["deviations"],
    }
