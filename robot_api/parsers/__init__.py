from pathlib import Path
from robot_api.parsers import json_parser, csv_parser

SUPPORTED_FORMATS = {".json", ".csv", ".bag", ".mcap", ".db3"}


def parse_log(path: str | Path, robot_type: str = "AMR", topic_config: dict | None = None) -> dict:
    """Auto-detect format and parse a log file into an engine-ready dict."""
    p = Path(path)
    if p.suffix == ".csv":
        return csv_parser.parse(p, robot_type=robot_type)
    elif p.suffix == ".json":
        return json_parser.parse(p)
    elif p.suffix in (".bag", ".mcap", ".db3"):
        from robot_api.parsers import bag_parser
        return bag_parser.parse(p, robot_type=robot_type, topic_config=topic_config)
    else:
        raise ValueError(
            f"Unsupported log format: {p.suffix!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )
