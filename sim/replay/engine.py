"""
Replay engine — takes a mission log and replays it step by step.

For MVP, we use MuJoCo for physics validation. Later can swap in Isaac Sim
for photorealistic rendering when a customer needs it.

Log format expected (JSON):
{
  "robot_type": "AMR",
  "timestep_s": 0.05,
  "frames": [
    {"t": 0.0, "x": 0.0, "y": 0.0, "theta": 0.0, "velocity": 0.0},
    ...
  ],
  "waypoints": [{"x": 1.0, "y": 0.0}, ...],
  "obstacles": [{"x": 2.0, "y": 1.0, "radius": 0.3}, ...]
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Frame:
    t: float
    x: float
    y: float
    theta: float
    velocity: float


@dataclass
class ReplayResult:
    frames: list[Frame]
    waypoints: list[dict[str, float]]
    obstacles: list[dict[str, Any]]
    collisions: list[dict[str, Any]] = field(default_factory=list)
    deviations: list[float] = field(default_factory=list)
    completed: bool = False
    duration_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "frame_count": len(self.frames),
            "collision_count": len(self.collisions),
            "max_deviation_m": max(self.deviations, default=0.0),
            "completion_rate": len(
                [wp for wp in self.waypoints if any(
                    ((fr.x - wp["x"]) ** 2 + (fr.y - wp["y"]) ** 2) ** 0.5 < 0.4
                    for fr in self.frames
                )]
            ) / max(len(self.waypoints), 1),
            "duration_s": self.duration_s,
            "collisions": self.collisions,
            "deviations": self.deviations,
        }


def load_log(log_path: Path) -> dict:
    with open(log_path) as f:
        return json.load(f)


def replay(log: dict) -> ReplayResult:
    """
    Replay a mission log and compute basic metrics.
    Does not require MuJoCo installed for MVP — runs pure geometry checks.
    Swap the collision check for mujoco.MjModel/MjData later for physics fidelity.
    """
    frames = [Frame(**fr) for fr in log["frames"]]
    waypoints = log.get("waypoints", [])
    obstacles = log.get("obstacles", [])

    collisions = []
    deviations = []
    WAYPOINT_REACH_RADIUS = 0.4  # meters

    for frame in frames:
        # Collision check: is robot within obstacle radius?
        for obs in obstacles:
            dist = ((frame.x - obs["x"]) ** 2 + (frame.y - obs["y"]) ** 2) ** 0.5
            if dist < obs.get("radius", 0.3):
                collisions.append({"t": frame.t, "obstacle": obs, "dist": dist})

        # Deviation: distance from nearest waypoint
        if waypoints:
            nearest = min(
                ((frame.x - wp["x"]) ** 2 + (frame.y - wp["y"]) ** 2) ** 0.5
                for wp in waypoints
            )
            deviations.append(nearest)

    # Completion rate: fraction of waypoints reached (within WAYPOINT_REACH_RADIUS)
    reached = 0
    for wp in waypoints:
        if any(
            ((fr.x - wp["x"]) ** 2 + (fr.y - wp["y"]) ** 2) ** 0.5 < WAYPOINT_REACH_RADIUS
            for fr in frames
        ):
            reached += 1
    completion_rate = reached / len(waypoints) if waypoints else 1.0

    duration_s = frames[-1].t if frames else 0.0
    completed = len(collisions) == 0 and completion_rate >= 1.0

    return ReplayResult(
        frames=frames,
        waypoints=waypoints,
        obstacles=obstacles,
        collisions=collisions,
        deviations=deviations,
        completed=completed,
        duration_s=duration_s,
    )
