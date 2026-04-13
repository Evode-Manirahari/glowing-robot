#!/usr/bin/env python3
"""
test_parsers.py — verify JSON and CSV parsers produce valid engine dicts.
Run: python scripts/test_parsers.py
"""
import sys
import csv
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_api.parsers import parse_log
from sim.replay.engine import replay
from evals.metrics.compute import compute

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
errors = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global errors
    if condition:
        print(f"  [{PASS}] {name}")
    else:
        print(f"  [{FAIL}] {name}" + (f" — {detail}" if detail else ""))
        errors += 1


print("\n=== Parser tests ===\n")

# 1. JSON native format
with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
    json.dump({
        "robot_type": "AMR",
        "timestep_s": 0.1,
        "name": "test_native",
        "frames": [
            {"t": 0.0, "x": 0.0, "y": 0.0},
            {"t": 0.1, "x": 0.2, "y": 0.0},
            {"t": 0.2, "x": 0.5, "y": 0.0},
        ],
        "waypoints": [{"x": 0.0, "y": 0.0}, {"x": 0.25, "y": 0.0}, {"x": 0.5, "y": 0.0}],
        "obstacles": [],
    }, f)
    json_path = f.name

log = parse_log(json_path)
result = replay(log)
metrics = compute(result)
check("JSON native: parses without error", True)
check("JSON native: has frames", len(log["frames"]) == 3)
check("JSON native: verdict is pass", metrics["verdict"] == "pass")

# 2. CSV format
with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", newline="", delete=False) as f:
    writer = csv.writer(f)
    writer.writerow(["t", "x", "y", "theta", "velocity"])
    writer.writerows([[0.0, 0.0, 0.0, 0.0, 0.0], [0.1, 0.5, 0.0, 0.0, 1.0], [0.2, 1.0, 0.0, 0.0, 0.5]])
    csv_path = f.name

log2 = parse_log(csv_path)
result2 = replay(log2)
check("CSV: parses without error", True)
check("CSV: has 3 frames", len(log2["frames"]) == 3)
check("CSV: x values preserved", log2["frames"][2]["x"] == 1.0)

# 3. ROS-bag-derived JSON
with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
    json.dump({
        "robot_type": "AMR",
        "poses": [
            {"secs": 10.0, "x": 0.0, "y": 0.0},
            {"secs": 10.1, "x": 0.3, "y": 0.0},
            {"secs": 10.2, "x": 0.6, "y": 0.0},
        ],
    }, f)
    ros_path = f.name

log3 = parse_log(ros_path)
result3 = replay(log3)
check("ROS poses JSON: parses without error", True)
check("ROS poses JSON: t starts at 0.0", log3["frames"][0]["t"] == 0.0, f"got {log3['frames'][0]['t']}")

# 4. Scenarios
for scenario in ["sim/scenarios/warehouse_basic.json", "sim/scenarios/warehouse_collision.json"]:
    path = Path(scenario)
    if path.exists():
        log4 = parse_log(path)
        result4 = replay(log4)
        metrics4 = compute(result4)
        expected = "pass" if "basic" in scenario else "fail"
        check(f"Scenario {path.name}: verdict={expected}", metrics4["verdict"] == expected)

print(f"\n{'All tests passed.' if errors == 0 else f'{errors} test(s) failed.'}\n")
sys.exit(0 if errors == 0 else 1)
