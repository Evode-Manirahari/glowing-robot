"""
Parse robot trajectory logs in JSON format.

Supports two layouts:
1. Native format — already matches the Trajectory schema.
2. ROS-bag-derived format — flat list of stamped poses.
"""
import json
from pathlib import Path
from robot_api.schemas.trajectory import Trajectory, TrajectoryFrame, Waypoint, Obstacle


def parse(path: str | Path) -> dict:
    """Return an engine-ready dict from a JSON log file."""
    with open(path) as f:
        data = json.load(f)

    if "frames" in data:
        return _parse_native(data)
    elif "poses" in data:
        return _parse_ros_poses(data)
    else:
        raise ValueError(f"Unrecognised JSON log format in {path}. Expected 'frames' or 'poses' key.")


def _parse_native(data: dict) -> dict:
    traj = Trajectory.model_validate(data)
    return traj.to_engine_dict()


def _parse_ros_poses(data: dict) -> dict:
    """
    Minimal ROS-bag-derived format:
    {"poses": [{"secs": 0.0, "x": 0.0, "y": 0.0, "yaw": 0.0, "v": 0.0}, ...]}
    """
    frames = []
    t0 = None
    for p in data["poses"]:
        t = p.get("secs", p.get("t", 0.0))
        if t0 is None:
            t0 = t
        frames.append(TrajectoryFrame(
            t=round(t - t0, 4),
            x=p.get("x", 0.0),
            y=p.get("y", 0.0),
            theta=p.get("yaw", p.get("theta", 0.0)),
            velocity=p.get("v", p.get("velocity", 0.0)),
        ))

    waypoints = [Waypoint(**w) for w in data.get("waypoints", [])]
    obstacles = [Obstacle(**o) for o in data.get("obstacles", [])]

    traj = Trajectory(
        robot_type=data.get("robot_type", "AMR"),
        timestep_s=data.get("timestep_s", 0.1),
        frames=frames,
        waypoints=waypoints,
        obstacles=obstacles,
        name=data.get("name"),
    )
    return traj.to_engine_dict()
