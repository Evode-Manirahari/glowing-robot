"""
Eval service — runs replay, computes metrics, optionally calls Claude for AI summary.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Make sim/ importable from backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sim.replay.engine import load_log, replay, ReplayResult
from app.config import get_settings

settings = get_settings()

COLLISION_THRESHOLD = 0
DEVIATION_THRESHOLD_M = 0.5
COMPLETION_THRESHOLD = 0.95


def run_replay(log_path: str) -> dict:
    """Load a log file and run the replay engine. Returns a metrics dict."""
    log = load_log(log_path)
    result = replay(log)
    return _build_metrics(result, log)


def _build_metrics(result: ReplayResult, log: dict) -> dict:
    metrics = result.to_dict()
    anomalies: list[str] = []

    if metrics["collision_count"] > COLLISION_THRESHOLD:
        anomalies.append(f"{metrics['collision_count']} collision(s) detected")
    if metrics["max_deviation_m"] > DEVIATION_THRESHOLD_M:
        anomalies.append(f"Max deviation {metrics['max_deviation_m']:.2f}m exceeds {DEVIATION_THRESHOLD_M}m threshold")
    if metrics["completion_rate"] < COMPLETION_THRESHOLD:
        anomalies.append(f"Only {metrics['completion_rate']*100:.0f}% of waypoints reached")

    verdict = (
        "fail" if metrics["collision_count"] > 0 or metrics["completion_rate"] < COMPLETION_THRESHOLD
        else "warning" if metrics["max_deviation_m"] > DEVIATION_THRESHOLD_M
        else "pass"
    )

    frames_for_viewer = [
        {"t": fr.t, "x": fr.x, "y": fr.y, "theta": fr.theta, "velocity": fr.velocity}
        for fr in result.frames
    ]
    collision_times = [c["t"] for c in metrics["collisions"]]

    return {
        "verdict": verdict,
        "collision_count": metrics["collision_count"],
        "max_deviation_m": metrics["max_deviation_m"],
        "completion_rate": metrics["completion_rate"],
        "duration_s": metrics["duration_s"],
        "frame_count": metrics["frame_count"],
        "anomalies": anomalies,
        "replay_frames": frames_for_viewer,
        "waypoints": result.waypoints,
        "obstacles": result.obstacles,
        "collisions": metrics["collisions"],
        "collision_times": collision_times,
    }


async def generate_comparison_summary(report_a: dict, name_a: str, report_b: dict, name_b: str) -> str:
    """Call Claude to compare two mission reports and produce a natural-language analysis."""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        def fmt(r: dict, name: str) -> str:
            anomalies = "\n".join(f"  - {a}" for a in r.get("anomalies", [])) or "  None"
            return (
                f"Mission: {name}\n"
                f"  Verdict: {r['verdict'].upper()}\n"
                f"  Collisions: {r['collision_count']}\n"
                f"  Max deviation: {r['max_deviation_m']:.3f}m\n"
                f"  Completion: {r['completion_rate']*100:.0f}%\n"
                f"  Duration: {r['duration_s']:.1f}s\n"
                f"  Anomalies:\n{anomalies}"
            )

        prompt = f"""You are a robot QA engineer comparing two mission runs for the same robot.

{fmt(report_a, name_a)}

{fmt(report_b, name_b)}

Write a concise 2-3 sentence comparison. State clearly what changed between the two runs (improved or degraded), identify the most significant difference, and recommend what the operator should investigate or fix. Be specific and practical. Do not use bullet points."""

        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"Comparison summary unavailable: {e}"


async def generate_ai_summary(metrics: dict) -> str:
    """Call Claude to produce a natural-language failure analysis."""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        verdict = metrics["verdict"].upper()
        anomalies_text = "\n".join(f"- {a}" for a in metrics["anomalies"]) or "None"

        prompt = f"""You are a robot QA engineer reviewing a mission replay report.

Mission verdict: {verdict}
Duration: {metrics['duration_s']:.1f}s
Frames: {metrics['frame_count']}
Collisions: {metrics['collision_count']}
Max deviation: {metrics['max_deviation_m']:.3f}m
Completion rate: {metrics['completion_rate']*100:.0f}%
Anomalies:
{anomalies_text}

Write a concise 2-3 sentence analysis of what happened, what likely caused it, and what the operator should investigate next. Be specific and practical. Do not use bullet points."""

        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"AI summary unavailable: {e}"
