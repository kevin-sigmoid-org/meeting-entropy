"""
Click-based CLI for meeting-entropy.

Because typing commands is still more productive than most meetings.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import click
import yaml

from meeting_entropy import __version__
from meeting_entropy.consent import (
    CONSENT_DIR,
    ask_for_consent_like_a_civilized_tool,
    check_consent,
    revoke_consent,
)
from meeting_entropy.detector.buzzword_evangelist_detector import (
    Corpus,
    MeetingState,
    detect_synergy_contamination,
    load_the_buzzword_bible,
)

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
EXPORT_DIR = CONSENT_DIR / "logs"


def _ensure_consent() -> None:
    """Check for valid consent. Ask if missing. Exit if refused."""
    if not check_consent():
        granted = ask_for_consent_like_a_civilized_tool()
        if not granted:
            raise SystemExit(0)


def _load_corpora(languages: tuple[str, ...]) -> list[Corpus]:
    """Load corpus files for each requested language, plus universal."""
    corpora: list[Corpus] = []

    # Always load universal if it exists
    universal_path = CORPUS_DIR / "universal.yaml"
    if universal_path.exists():
        corpora.append(load_the_buzzword_bible("universal"))

    for lang in languages:
        try:
            corpora.append(load_the_buzzword_bible(lang))
        except FileNotFoundError:
            click.echo(
                click.style(f"Warning: corpus for '{lang}' not found. Skipping.", fg="yellow")
            )

    if not corpora:
        click.echo(click.style("No corpora loaded. Nothing to detect. Exiting.", fg="red"))
        raise SystemExit(1)

    return corpora


def _compute_entropy_score(state: MeetingState) -> float:
    """Compute the entropy score from accumulated hits.

    Score is total weighted hits divided by elapsed minutes, capped at 100.
    A higher score means the meeting is dissolving into pure corporate noise.
    """
    elapsed_minutes = max(state.duration / 60.0, 0.5)  # avoid division by zero
    weighted_sum = sum(hit.weight for hit in state.hits)
    raw = (weighted_sum / elapsed_minutes) * 10.0
    return min(raw, 100.0)


def _compute_email_score(state: MeetingState) -> float:
    """Estimate the probability this meeting could have been an email.

    Based on: high entropy + low voice count + short duration = email territory.
    """
    entropy_factor = state.entropy_score / 100.0
    voice_factor = max(0.0, 1.0 - (state.voices_detected - 1) * 0.2) if state.voices_detected else 1.0
    duration_factor = max(0.0, 1.0 - state.duration / 3600.0)
    return min((entropy_factor * 0.5 + voice_factor * 0.25 + duration_factor * 0.25) * 100.0, 100.0)


def _render_dashboard(state: MeetingState, font_size: int, display_public: bool) -> None:
    """Render the terminal dashboard using Rich."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = Console()
    console.clear()

    # Header
    header = Text("meeting-entropy", style="bold magenta")
    header.append(f" v{__version__}", style="dim")
    elapsed = time.strftime("%H:%M:%S", time.gmtime(state.duration))
    header.append(f"  |  elapsed: {elapsed}", style="dim cyan")

    # Entropy gauge
    entropy_color = "green" if state.entropy_score < 30 else "yellow" if state.entropy_score < 60 else "red"
    bar_filled = int(state.entropy_score / 2)
    bar = "\u2588" * bar_filled + "\u2591" * (50 - bar_filled)
    entropy_display = Text(f"Entropy: {state.entropy_score:5.1f}% [{bar}]", style=entropy_color)

    # Email score
    email_color = "green" if state.email_score < 40 else "yellow" if state.email_score < 70 else "red bold"
    email_display = Text(
        f'"Could have been an email" score: {state.email_score:5.1f}%', style=email_color
    )

    # Recent hits table
    hit_table = Table(title="Recent Detections", show_lines=False, expand=True)
    hit_table.add_column("Word/Phrase", style="bold")
    hit_table.add_column("Category", style="dim")
    hit_table.add_column("Weight", justify="right")
    hit_table.add_column("Sarcasm", style="italic")

    recent_hits = state.hits[-10:] if state.hits else []
    for hit in reversed(recent_hits):
        hit_table.add_row(hit.word, hit.category, str(hit.weight), hit.sarcasm_level)

    # Last transcript (only shown if not in public/private mode that restricts it)
    transcript_text = ""
    if not display_public and state.last_transcript:
        transcript_text = f"\nLast transcript: {state.last_transcript[:120]}..."

    body = Text()
    body.append_text(entropy_display)
    body.append("\n")
    body.append_text(email_display)
    body.append(f"\nTotal hits: {len(state.hits)}  |  Languages loaded: {', '.join(state.languages)}")
    if transcript_text:
        body.append(transcript_text, style="dim")

    console.print(Panel(header, border_style="magenta"))
    console.print(Panel(body, title="Scores", border_style="blue"))
    console.print(hit_table)
    console.print(
        "\n[dim]Press Ctrl+C to stop. Kevin believes in you.[/dim]",
        highlight=False,
    )


def _export_session(state: MeetingState, export_path: Path) -> None:
    """Export the session data to a JSON file."""
    export_path.parent.mkdir(parents=True, exist_ok=True)

    session_data = {
        "version": __version__,
        "start_time": state.start_time,
        "duration_seconds": state.duration,
        "entropy_score": round(state.entropy_score, 2),
        "email_score": round(state.email_score, 2),
        "total_hits": len(state.hits),
        "languages": state.languages,
        "hits": [
            {
                "word": h.word,
                "category": h.category,
                "weight": h.weight,
                "timestamp": h.timestamp,
                "sarcasm_level": h.sarcasm_level,
            }
            for h in state.hits
        ],
        "transcripts": state.transcripts,
    }

    export_path.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")
    click.echo(click.style(f"\nSession exported to {export_path}", fg="green"))


def _audio_capture_loop(
    state: MeetingState,
    corpora: list[Corpus],
    model_name: str,
    language: str | None,
    stop_event: threading.Event,
    sound_alert: bool,
) -> None:
    """Background thread: capture audio, transcribe, detect, update state."""
    from meeting_entropy.audio.microphone_whisperer import MicrophoneWhisperer
    from meeting_entropy.audio.the_uncomfortable_listener import TheUncomfortableListener

    whisper = MicrophoneWhisperer(model_name=model_name, language=language)
    listener = TheUncomfortableListener()

    # We accumulate chunks into ~3-second windows for transcription
    target_chunks = int(3.0 * listener.sample_rate / listener.chunk_size)

    try:
        listener.start()
        import numpy as np

        while not stop_event.is_set():
            chunks = []
            for _ in range(target_chunks):
                if stop_event.is_set():
                    break
                chunk = listener.read_chunk()
                chunks.append(chunk)

            if not chunks or stop_event.is_set():
                break

            # Combine chunks into one AudioChunk for transcription
            from meeting_entropy.audio.the_uncomfortable_listener import AudioChunk

            combined_data = np.concatenate([c.data for c in chunks])
            combined = AudioChunk(
                data=combined_data,
                sample_rate=chunks[0].sample_rate,
                timestamp=chunks[0].timestamp,
                duration_ms=sum(c.duration_ms for c in chunks),
            )

            text = whisper.transcribe_the_meaningless_words(combined)
            if not text or not text.strip():
                continue

            state.last_transcript = text.strip()
            state.transcripts.append(state.last_transcript)

            # Detect across all loaded corpora
            for corpus in corpora:
                hits = detect_synergy_contamination(text, corpus)
                state.hits.extend(hits)

                if sound_alert and hits:
                    # Terminal bell for each detection batch
                    sys.stdout.write("\a")
                    sys.stdout.flush()

    finally:
        listener.stop()


@click.group(invoke_without_command=True)
@click.option(
    "--revoke-consent",
    "revoke_consent_flag",
    is_flag=True,
    default=False,
    help="Revoke GDPR consent and delete all local data.",
)
@click.version_option(version=__version__, prog_name="meeting-entropy")
@click.pass_context
def cli(ctx: click.Context, revoke_consent_flag: bool = False) -> None:
    """meeting-entropy -- Real-time corporate noise detection for meetings.

    Because someone had to build this.
    """
    if revoke_consent_flag:
        revoke_consent()
        raise SystemExit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--lang",
    "languages",
    multiple=True,
    default=("en",),
    help="Language corpus to load. Can be specified multiple times.",
)
@click.option(
    "--model",
    "model_name",
    default="small",
    show_default=True,
    help="Whisper model size (tiny, base, small, medium, large).",
)
@click.option(
    "--private",
    "private_mode",
    is_flag=True,
    default=False,
    help="Private mode: do not store transcripts in exports.",
)
@click.option(
    "--display-public",
    is_flag=True,
    default=False,
    help="Public display mode: hide transcript text on dashboard.",
)
@click.option(
    "--font-size",
    type=int,
    default=48,
    show_default=True,
    help="Suggested font size for dashboard rendering (terminal-dependent).",
)
@click.option(
    "--export",
    "export_path",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Path to export session data as JSON on exit.",
)
@click.option(
    "--sound-alert",
    is_flag=True,
    default=False,
    help="Play a terminal bell when buzzwords are detected.",
)
def start(
    languages: tuple[str, ...],
    model_name: str,
    private_mode: bool,
    display_public: bool,
    font_size: int,
    export_path: Path | None,
    sound_alert: bool,
) -> None:
    """Start a live meeting-entropy session.

    Captures audio from your microphone, transcribes it with Whisper,
    detects corporate noise in real-time, and displays an entropy
    dashboard in your terminal.

    Kevin Sigmoid approves of your decision to quantify the void.
    """
    _ensure_consent()

    click.echo(click.style("Loading corpora...", fg="cyan"))
    corpora = _load_corpora(languages)
    loaded_langs = [c.language for c in corpora]
    click.echo(click.style(f"Loaded: {', '.join(loaded_langs)}", fg="green"))

    click.echo(click.style(f"Initializing Whisper model '{model_name}'...", fg="cyan"))
    click.echo(click.style("Model ready. Starting audio capture...\n", fg="green"))

    # Determine language hint for Whisper (use first non-universal language)
    whisper_lang = None
    for lang in languages:
        if lang != "universal":
            whisper_lang = lang
            break

    state = MeetingState(
        start_time=time.time(),
        is_running=True,
        languages=loaded_langs,
    )

    stop_event = threading.Event()

    capture_thread = threading.Thread(
        target=_audio_capture_loop,
        args=(state, corpora, model_name, whisper_lang, stop_event, sound_alert),
        daemon=True,
    )
    capture_thread.start()

    try:
        while True:
            state.duration = time.time() - state.start_time
            state.entropy_score = _compute_entropy_score(state)
            state.email_score = _compute_email_score(state)
            _render_dashboard(state, font_size, display_public)
            time.sleep(1.0)
    except KeyboardInterrupt:
        click.echo(click.style("\n\nStopping capture...", fg="yellow"))
        stop_event.set()
        capture_thread.join(timeout=5.0)
        state.is_running = False
        state.duration = time.time() - state.start_time
        state.entropy_score = _compute_entropy_score(state)
        state.email_score = _compute_email_score(state)

        # Final summary
        click.echo(click.style("\n--- Session Summary ---", fg="magenta", bold=True))
        elapsed = time.strftime("%H:%M:%S", time.gmtime(state.duration))
        click.echo(f"Duration:      {elapsed}")
        click.echo(f"Entropy score: {state.entropy_score:.1f}%")
        click.echo(f"Email score:   {state.email_score:.1f}%")
        click.echo(f"Total hits:    {len(state.hits)}")
        click.echo(f"Languages:     {', '.join(state.languages)}")

        # Export
        if export_path is not None:
            if private_mode:
                state.transcripts = []  # strip transcripts in private mode
            _export_session(state, export_path)
        else:
            # Offer to export to default location
            if click.confirm("\nExport session?", default=False):
                default_path = EXPORT_DIR / f"session_{int(state.start_time)}.json"
                if private_mode:
                    state.transcripts = []
                _export_session(state, default_path)

        click.echo(
            click.style(
                "\nSession ended. Go touch grass. -- Kevin",
                fg="green",
                bold=True,
            )
        )


@cli.group()
def corpus() -> None:
    """Manage buzzword corpora."""


@corpus.command("add")
@click.option(
    "--lang",
    required=True,
    help="Language code for the corpus (e.g., fr, en, de).",
)
@click.argument("words")
def corpus_add(lang: str, words: str) -> None:
    """Add words to a language corpus.

    WORDS is a comma-separated list of words or phrases to add.

    Example:
        meeting-entropy corpus add --lang fr "paradigme,ecosysteme,roadmap"
    """
    corpus_path = CORPUS_DIR / f"{lang}.yaml"

    if not corpus_path.exists():
        click.echo(click.style(f"Corpus file for '{lang}' not found at {corpus_path}.", fg="red"))
        click.echo("Creating a new corpus file...")
        data = {
            "metadata": {
                "language": lang,
                "version": "1.0",
                "curator": "community",
                "note": f"Community-contributed {lang} corpus.",
            },
            "categories": {
                "custom": {
                    "weight": 5,
                    "words": [],
                    "sarcasm_level": "MODERATE",
                },
            },
        }
    else:
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    # Parse comma-separated words
    new_words = [w.strip() for w in words.split(",") if w.strip()]
    if not new_words:
        click.echo(click.style("No words provided.", fg="yellow"))
        return

    # Add to a 'custom' category (create if needed)
    categories = data.setdefault("categories", {})
    custom = categories.setdefault("custom", {"weight": 5, "words": [], "sarcasm_level": "MODERATE"})
    existing = set(custom.get("words", []))
    added = []
    for word in new_words:
        if word not in existing:
            custom.setdefault("words", []).append(word)
            existing.add(word)
            added.append(word)

    if not added:
        click.echo(click.style("All words already exist in corpus. Nothing added.", fg="yellow"))
        return

    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(corpus_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    click.echo(click.style(f"Added {len(added)} word(s) to {lang} corpus:", fg="green"))
    for w in added:
        click.echo(f"  + {w}")


@cli.command()
def stats() -> None:
    """Show aggregated statistics from exported sessions.

    Reads all session JSON files from ~/.meeting-entropy/logs/ and
    displays a summary. Because data-driven self-awareness is a virtue.
    """
    if not EXPORT_DIR.exists():
        click.echo(click.style("No exported sessions found.", fg="yellow"))
        click.echo(f"Export directory: {EXPORT_DIR}")
        return

    session_files = sorted(EXPORT_DIR.glob("session_*.json"))
    if not session_files:
        click.echo(click.style("No exported sessions found.", fg="yellow"))
        return

    total_sessions = 0
    total_duration = 0.0
    total_hits = 0
    entropy_scores: list[float] = []
    email_scores: list[float] = []
    word_freq: dict[str, int] = {}
    category_freq: dict[str, int] = {}

    for f in session_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        total_sessions += 1
        total_duration += data.get("duration_seconds", 0.0)
        total_hits += data.get("total_hits", 0)
        entropy_scores.append(data.get("entropy_score", 0.0))
        email_scores.append(data.get("email_score", 0.0))

        for hit in data.get("hits", []):
            word = hit.get("word", "")
            cat = hit.get("category", "")
            if word:
                word_freq[word] = word_freq.get(word, 0) + 1
            if cat:
                category_freq[cat] = category_freq.get(cat, 0) + 1

    if total_sessions == 0:
        click.echo(click.style("No valid sessions found.", fg="yellow"))
        return

    # Display stats
    click.echo(click.style("\n=== meeting-entropy Statistics ===\n", fg="magenta", bold=True))
    click.echo(f"Sessions analyzed:    {total_sessions}")
    total_h = time.strftime("%H:%M:%S", time.gmtime(total_duration))
    click.echo(f"Total meeting time:   {total_h}")
    click.echo(f"Total BS detections:  {total_hits}")
    avg_entropy = sum(entropy_scores) / len(entropy_scores)
    avg_email = sum(email_scores) / len(email_scores)
    click.echo(f"Avg entropy score:    {avg_entropy:.1f}%")
    click.echo(f"Avg email score:      {avg_email:.1f}%")

    if word_freq:
        click.echo(click.style("\nTop 10 buzzwords:", fg="cyan"))
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (word, count) in enumerate(sorted_words, 1):
            click.echo(f"  {i:2}. {word:<30} ({count}x)")

    if category_freq:
        click.echo(click.style("\nTop categories:", fg="cyan"))
        sorted_cats = sorted(category_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in sorted_cats:
            click.echo(f"  - {cat}: {count} hits")

    click.echo(
        click.style(
            "\nRemember: awareness is the first step. The second step is leaving the meeting.",
            fg="green",
        )
    )


if __name__ == "__main__":
    cli()
