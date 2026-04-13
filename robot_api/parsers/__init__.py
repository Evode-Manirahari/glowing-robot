from pathlib import Path
from robot_api.parsers import json_parser, csv_parser


def parse_log(path: str | Path, robot_type: str = "AMR") -> dict:
    """Auto-detect format and parse a log file into an engine-ready dict."""
    p = Path(path)
    if p.suffix == ".csv":
        return csv_parser.parse(p, robot_type=robot_type)
    elif p.suffix == ".json":
        return json_parser.parse(p)
    else:
        raise ValueError(f"Unsupported log format: {p.suffix}. Use .json or .csv")
