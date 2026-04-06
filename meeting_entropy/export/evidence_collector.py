"""Export module for meeting-entropy sessions.

Collecte les preuves pour la postérité (ou pour les RH).
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from meeting_entropy.detector.buzzword_evangelist_detector import (
    BuzzwordHit,
    MeetingState,
)


def _state_to_dict(state: MeetingState) -> dict:
    """Convert a MeetingState to a serialisable dictionary."""
    hits = getattr(state, "hits", [])
    serialised_hits = []
    for hit in hits:
        serialised_hits.append({
            "word": getattr(hit, "word", str(hit)),
            "category": getattr(hit, "category", "unknown"),
            "weight": getattr(hit, "weight", 1.0),
            "timestamp": getattr(hit, "timestamp", 0.0),
        })

    silence_events = getattr(state, "silence_events", [])
    serialised_silence = []
    for evt in silence_events:
        if isinstance(evt, dict):
            serialised_silence.append(evt)
        else:
            serialised_silence.append({
                "start": getattr(evt, "start", 0.0),
                "duration": getattr(evt, "duration", 0.0),
            })

    transcripts = getattr(state, "transcripts", [])
    serialised_transcripts = [
        t if isinstance(t, str) else str(t) for t in transcripts
    ]

    return {
        "start_time": getattr(state, "start_time", 0.0),
        "duration": getattr(state, "duration", 0.0),
        "entropy_score": getattr(state, "entropy_score", 0.0),
        "email_score": getattr(state, "email_score", 0.0),
        "hits": serialised_hits,
        "silence_events": serialised_silence,
        "transcripts": serialised_transcripts,
    }


def _export_json(data: dict, path: Path) -> None:
    """Write session data as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _export_csv(data: dict, path: Path) -> None:
    """Write session hits as CSV (one row per hit, with session metadata)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "start_time",
        "duration",
        "entropy_score",
        "email_score",
        "word",
        "category",
        "weight",
        "timestamp",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        hits = data.get("hits", [])
        if not hits:
            # Write a single summary row even if there are no hits
            writer.writerow({
                "start_time": data.get("start_time", ""),
                "duration": data.get("duration", ""),
                "entropy_score": data.get("entropy_score", ""),
                "email_score": data.get("email_score", ""),
                "word": "",
                "category": "",
                "weight": "",
                "timestamp": "",
            })
        else:
            for hit in hits:
                writer.writerow({
                    "start_time": data.get("start_time", ""),
                    "duration": data.get("duration", ""),
                    "entropy_score": data.get("entropy_score", ""),
                    "email_score": data.get("email_score", ""),
                    "word": hit.get("word", ""),
                    "category": hit.get("category", ""),
                    "weight": hit.get("weight", ""),
                    "timestamp": hit.get("timestamp", ""),
                })


def save_evidence_for_posterity(state: MeetingState, path: Path) -> None:
    """Exporte les preuves si l'utilisateur veut faire un rapport RH."""
    data = _state_to_dict(state)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        _export_csv(data, path)
    else:
        # Default to JSON for .json or any other extension
        if not suffix:
            path = path.with_suffix(".json")
        _export_json(data, path)


def load_evidence(path: Path) -> dict:
    """Load a previously exported session.

    Args:
        path: Path to a JSON export file.

    Returns:
        The session data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def format_stats(sessions: list[dict]) -> str:
    """Format stats across multiple sessions for the ``meeting-entropy stats`` command.

    Computes aggregate statistics over a list of session dictionaries
    (as returned by :func:`load_evidence`).

    Args:
        sessions: A list of session dicts, each containing at least
                  ``entropy_score``, ``email_score``, ``duration``, and ``hits``.

    Returns:
        A human-readable multi-line string with aggregate statistics.
    """
    if not sessions:
        return "No sessions found. Either you never had a meeting, or you're very lucky."

    total_sessions = len(sessions)
    total_duration = sum(s.get("duration", 0.0) for s in sessions)
    entropy_scores = [s.get("entropy_score", 0.0) for s in sessions]
    email_scores = [s.get("email_score", 0.0) for s in sessions]
    total_hits = sum(len(s.get("hits", [])) for s in sessions)

    avg_entropy = sum(entropy_scores) / total_sessions
    max_entropy = max(entropy_scores)
    min_entropy = min(entropy_scores)

    avg_email = sum(email_scores) / total_sessions

    # Top offending words across all sessions
    word_counts: dict[str, int] = {}
    for session in sessions:
        for hit in session.get("hits", []):
            word = hit.get("word", "???")
            word_counts[word] = word_counts.get(word, 0) + 1

    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Format duration
    hours = int(total_duration // 3600)
    minutes = int((total_duration % 3600) // 60)

    lines = [
        "=" * 50,
        "  MEETING ENTROPY — Aggregate Stats",
        "=" * 50,
        "",
        f"  Sessions analysed:   {total_sessions}",
        f"  Total time wasted:   {hours}h {minutes}m",
        "",
        f"  Avg entropy score:   {avg_entropy:.1f}%",
        f"  Max entropy score:   {max_entropy:.1f}%",
        f"  Min entropy score:   {min_entropy:.1f}%",
        f"  Avg email score:     {avg_email:.1f}%",
        "",
        f"  Total buzzword hits: {total_hits}",
        "",
        "  Top offending words:",
    ]

    if top_words:
        for word, count in top_words:
            lines.append(f"    - {word!r}: {count} occurrences")
    else:
        lines.append("    (none — suspicious)")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)
