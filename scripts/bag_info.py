#!/usr/bin/env python3
"""
bag_info.py — inspect a ROS bag file and list its topics.

Use this to find the right topic names before uploading to glowing-robot.

Usage:
    python scripts/bag_info.py path/to/mission.bag
    python scripts/bag_info.py path/to/mission.mcap
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def inspect_bag(path: Path) -> None:
    if path.suffix == ".bag":
        _inspect_ros1(path)
    elif path.suffix in (".mcap", ".db3"):
        _inspect_ros2(path)
    else:
        print(f"Unsupported format: {path.suffix}")
        sys.exit(1)


def _inspect_ros1(path: Path) -> None:
    try:
        from rosbags.rosbag1 import Reader
    except ImportError:
        print("Install rosbags: pip install rosbags")
        sys.exit(1)

    print(f"\n--- ROS1 bag: {path.name} ---\n")
    with Reader(str(path)) as reader:
        topics = {}
        for conn in reader.connections:
            if conn.topic not in topics:
                topics[conn.topic] = {"type": conn.msgtype, "count": 0}
        for _, _, _ in reader.messages():
            pass  # count messages
        # Re-read with counts
        for conn, _, _ in reader.messages():
            topics[conn.topic]["count"] += 1

    print(f"{'Topic':<50}  {'Type':<45}  {'Messages':>8}")
    print("-" * 110)

    from robot_api.parsers.bag_parser import ODOM_TOPICS, PATH_TOPICS
    for topic, info in sorted(topics.items()):
        marker = ""
        if topic in ODOM_TOPICS:
            marker = "  ← odom candidate"
        elif topic in PATH_TOPICS:
            marker = "  ← path candidate"
        print(f"{topic:<50}  {info['type']:<45}  {info['count']:>8}{marker}")

    print()
    _suggest(topics)


def _inspect_ros2(path: Path) -> None:
    try:
        from rosbags.rosbag2 import Reader
    except ImportError:
        print("Install rosbags: pip install rosbags")
        sys.exit(1)

    print(f"\n--- ROS2 bag: {path.name} ---\n")
    with Reader(str(path)) as reader:
        topics = {c.topic: {"type": c.msgtype, "count": 0} for c in reader.connections}
        for conn, _, _ in reader.messages():
            topics[conn.topic]["count"] += 1

    print(f"{'Topic':<50}  {'Type':<45}  {'Messages':>8}")
    print("-" * 110)

    from robot_api.parsers.bag_parser import ODOM_TOPICS, PATH_TOPICS
    for topic, info in sorted(topics.items()):
        marker = ""
        if topic in ODOM_TOPICS:
            marker = "  ← odom candidate"
        elif topic in PATH_TOPICS:
            marker = "  ← path candidate"
        print(f"{topic:<50}  {info['type']:<45}  {info['count']:>8}{marker}")

    print()
    _suggest(topics)


def _suggest(topics: dict) -> None:
    from robot_api.parsers.bag_parser import ODOM_TOPICS, PATH_TOPICS

    found_odom = [t for t in ODOM_TOPICS if t in topics]
    found_path = [t for t in PATH_TOPICS if t in topics]

    if found_odom:
        print(f"✓ Odom topic detected: {found_odom[0]}")
        print("  glowing-robot will use this automatically.")
    else:
        print("✗ No standard odom topic found.")
        odom_like = [t for t in topics if "odom" in t.lower() or "pose" in t.lower() or "locali" in t.lower()]
        if odom_like:
            print(f"  Possible matches: {odom_like[:3]}")
            print(f"  Upload with: topic_config={{\"odom_topics\": [\"{odom_like[0]}\"]}} (API only)")

    if found_path:
        print(f"✓ Path topic detected: {found_path[0]}")
    else:
        print("  No path/waypoint topic found — waypoints will be empty.")

    print()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: {path} not found")
        return 1
    inspect_bag(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
