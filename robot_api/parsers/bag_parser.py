"""
Parse ROS1 .bag and ROS2 .mcap / .db3 files into the glowing-robot trajectory format.

Requires: rosbags>=0.9.0 — pure Python, no ROS installation needed.
    pip install rosbags

Tries common navigation topics automatically.
Override with topic_config if your robot uses non-standard names:
    parse(path, topic_config={"odom_topics": ["/my_robot/odom"]})
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

from robot_api.schemas.trajectory import Trajectory, TrajectoryFrame, Waypoint

# Ordered by how common they are in warehouse AMR deployments
ODOM_TOPICS = [
    "/odom",
    "/robot_pose",
    "/amcl_pose",
    "/base_pose_ground_truth",
    "/localization_pose",
    "/ekf_pose",
]

PATH_TOPICS = [
    "/move_base/GlobalPlanner/plan",
    "/move_base/NavfnROS/plan",
    "/move_base/TebLocalPlannerROS/global_plan",
    "/move_base_flex/exe_path/goal",
    "/global_plan",
    "/planned_path",
    "/nav/path",
]

MAX_FRAMES = 2000  # downsample to this for viewer performance


def parse(
    path: str | Path,
    robot_type: str = "AMR",
    topic_config: Optional[dict] = None,
) -> dict:
    """Auto-detect ROS1/ROS2 format and parse. Returns an engine-ready dict."""
    p = Path(path)
    cfg = topic_config or {}
    odom_topics = cfg.get("odom_topics", ODOM_TOPICS)
    path_topics = cfg.get("path_topics", PATH_TOPICS)

    if p.suffix == ".bag":
        return _parse_ros1(p, robot_type, odom_topics, path_topics)
    elif p.suffix in (".mcap", ".db3"):
        return _parse_ros2(p, robot_type, odom_topics, path_topics)
    else:
        raise ValueError(f"Unsupported bag format: {p.suffix!r}")


def _quat_to_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def _extract_pose_vel(msg) -> tuple[float, float, float, float] | None:
    """Returns (x, y, theta, velocity) or None if structure is unrecognised."""
    # nav_msgs/Odometry
    if hasattr(msg, "pose") and hasattr(msg.pose, "pose"):
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        vel = float(msg.twist.twist.linear.x) if hasattr(msg, "twist") else 0.0
        return (
            float(pos.x), float(pos.y),
            _quat_to_yaw(float(ori.x), float(ori.y), float(ori.z), float(ori.w)),
            vel,
        )
    # geometry_msgs/PoseWithCovarianceStamped
    if hasattr(msg, "pose") and hasattr(msg.pose, "position"):
        pos = msg.pose.position
        ori = msg.pose.orientation
        return (
            float(pos.x), float(pos.y),
            _quat_to_yaw(float(ori.x), float(ori.y), float(ori.z), float(ori.w)),
            0.0,
        )
    return None


def _downsample(frames: list[TrajectoryFrame]) -> list[TrajectoryFrame]:
    if len(frames) <= MAX_FRAMES:
        return frames
    step = len(frames) // MAX_FRAMES
    return frames[::step]


def _build_trajectory(
    frames: list[TrajectoryFrame],
    waypoints: list[Waypoint],
    robot_type: str,
    name: str,
) -> dict:
    if not frames:
        raise ValueError("No pose data found — check topic names with scripts/bag_info.py")
    frames = _downsample(frames)
    traj = Trajectory(robot_type=robot_type, frames=frames, waypoints=waypoints, name=name)
    return traj.to_engine_dict()


def _parse_ros1(
    path: Path,
    robot_type: str,
    odom_topics: list[str],
    path_topics: list[str],
) -> dict:
    try:
        from rosbags.rosbag1 import Reader
        from rosbags.typesys import Stores, get_typestore
    except ImportError:
        raise ImportError(
            "rosbags is required to parse .bag files.\n"
            "Install it with: pip install rosbags"
        )

    typestore = get_typestore(Stores.ROS1_NOETIC)
    frames: list[TrajectoryFrame] = []
    waypoints: list[Waypoint] = []
    t0: Optional[float] = None

    with Reader(str(path)) as reader:
        available = {c.topic for c in reader.connections}
        odom_topic = next((t for t in odom_topics if t in available), None)

        if not odom_topic:
            raise ValueError(
                f"No odometry topic found.\n"
                f"  Available: {sorted(available)}\n"
                f"  Tried: {odom_topics}\n"
                f"  Use topic_config={{'odom_topics': ['/your/topic']}} to override."
            )

        odom_conns = [c for c in reader.connections if c.topic == odom_topic]
        for _, timestamp, rawdata in reader.messages(connections=odom_conns):
            t_s = timestamp / 1e9
            if t0 is None:
                t0 = t_s
            msg = typestore.deserialize_ros1(rawdata, odom_conns[0].msgtype)
            pose = _extract_pose_vel(msg)
            if pose:
                x, y, theta, vel = pose
                frames.append(TrajectoryFrame(t=round(t_s - t0, 4), x=x, y=y, theta=theta, velocity=vel))

        # Waypoints from first matching path topic
        for topic in path_topics:
            if topic not in available:
                continue
            path_conns = [c for c in reader.connections if c.topic == topic]
            for _, _, rawdata in reader.messages(connections=path_conns):
                msg = typestore.deserialize_ros1(rawdata, path_conns[0].msgtype)
                if hasattr(msg, "poses"):
                    for ps in msg.poses:
                        p_pos = ps.pose.position
                        waypoints.append(Waypoint(x=float(p_pos.x), y=float(p_pos.y)))
                break
            if waypoints:
                break

    return _build_trajectory(frames, waypoints, robot_type, path.stem)


def _parse_ros2(
    path: Path,
    robot_type: str,
    odom_topics: list[str],
    path_topics: list[str],
) -> dict:
    try:
        from rosbags.rosbag2 import Reader
        from rosbags.typesys import Stores, get_typestore
    except ImportError:
        raise ImportError(
            "rosbags is required to parse .mcap/.db3 files.\n"
            "Install it with: pip install rosbags"
        )

    typestore = get_typestore(Stores.ROS2_HUMBLE)
    frames: list[TrajectoryFrame] = []
    waypoints: list[Waypoint] = []
    t0: Optional[float] = None

    with Reader(str(path)) as reader:
        available = {c.topic for c in reader.connections}
        odom_topic = next((t for t in odom_topics if t in available), None)

        if not odom_topic:
            raise ValueError(
                f"No odometry topic found.\n"
                f"  Available: {sorted(available)}\n"
                f"  Tried: {odom_topics}"
            )

        odom_conns = [c for c in reader.connections if c.topic == odom_topic]
        for _, timestamp, rawdata in reader.messages(connections=odom_conns):
            t_s = timestamp / 1e9
            if t0 is None:
                t0 = t_s
            msg = typestore.deserialize_cdr(rawdata, odom_conns[0].msgtype)
            pose = _extract_pose_vel(msg)
            if pose:
                x, y, theta, vel = pose
                frames.append(TrajectoryFrame(t=round(t_s - t0, 4), x=x, y=y, theta=theta, velocity=vel))

        for topic in path_topics:
            if topic not in available:
                continue
            path_conns = [c for c in reader.connections if c.topic == topic]
            for _, _, rawdata in reader.messages(connections=path_conns):
                msg = typestore.deserialize_cdr(rawdata, path_conns[0].msgtype)
                if hasattr(msg, "poses"):
                    for ps in msg.poses:
                        p_pos = ps.pose.position
                        waypoints.append(Waypoint(x=float(p_pos.x), y=float(p_pos.y)))
                break
            if waypoints:
                break

    return _build_trajectory(frames, waypoints, robot_type, path.stem)
