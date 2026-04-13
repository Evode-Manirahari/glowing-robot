"""
Canonical trajectory schema. All log parsers must output this shape.
The sim replay engine consumes this directly.
"""
from pydantic import BaseModel, Field
from typing import Optional


class TrajectoryFrame(BaseModel):
    t: float = Field(description="Time in seconds from mission start")
    x: float = Field(description="X position in metres")
    y: float = Field(description="Y position in metres")
    theta: float = Field(default=0.0, description="Heading in radians")
    velocity: float = Field(default=0.0, description="Speed in m/s")


class Waypoint(BaseModel):
    x: float
    y: float
    label: Optional[str] = None


class Obstacle(BaseModel):
    x: float
    y: float
    radius: float = 0.3
    label: Optional[str] = None


class Trajectory(BaseModel):
    robot_type: str = "AMR"
    timestep_s: float = 0.1
    frames: list[TrajectoryFrame]
    waypoints: list[Waypoint] = Field(default_factory=list)
    obstacles: list[Obstacle] = Field(default_factory=list)
    name: Optional[str] = None

    def to_engine_dict(self) -> dict:
        """Convert to the dict format expected by sim.replay.engine."""
        return {
            "robot_type": self.robot_type,
            "timestep_s": self.timestep_s,
            "name": self.name or "mission",
            "frames": [f.model_dump() for f in self.frames],
            "waypoints": [{"x": w.x, "y": w.y} for w in self.waypoints],
            "obstacles": [{"x": o.x, "y": o.y, "radius": o.radius, "label": o.label} for o in self.obstacles],
        }
