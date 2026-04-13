"""
Parse robot trajectory logs in CSV format.

Expected columns (any order): t, x, y, [theta], [velocity]
Optional header row. If no header, assumes columns in that order.
"""
import csv
from pathlib import Path
from robot_api.schemas.trajectory import Trajectory, TrajectoryFrame


REQUIRED_COLS = {"t", "x", "y"}
OPTIONAL_COLS = {"theta", "velocity"}


def parse(path: str | Path, robot_type: str = "AMR") -> dict:
    """Return an engine-ready dict from a CSV log file."""
    with open(path, newline="") as f:
        sample = f.read(1024)
        f.seek(0)
        has_header = csv.Sniffer().has_header(sample)
        reader = csv.DictReader(f) if has_header else None

        if reader is None:
            f.seek(0)
            rows = list(csv.reader(f))
            col_names = ["t", "x", "y", "theta", "velocity"]
            frames = []
            for row in rows:
                if not row or row[0].startswith("#"):
                    continue
                vals = dict(zip(col_names, [float(v) for v in row]))
                frames.append(TrajectoryFrame(**vals))
        else:
            frames = []
            for row in reader:
                lower = {k.strip().lower(): v for k, v in row.items()}
                if not REQUIRED_COLS.issubset(lower.keys()):
                    raise ValueError(f"CSV missing required columns. Need: {REQUIRED_COLS}. Got: {set(lower.keys())}")
                frames.append(TrajectoryFrame(
                    t=float(lower["t"]),
                    x=float(lower["x"]),
                    y=float(lower["y"]),
                    theta=float(lower.get("theta", 0.0)),
                    velocity=float(lower.get("velocity", 0.0)),
                ))

    traj = Trajectory(robot_type=robot_type, frames=frames)
    return traj.to_engine_dict()
