"""Rich-based terminal dashboard for meeting-entropy.

Affiche le score d'entropie en temps réel. Kevin approuve ce niveau de transparence.
"""

from __future__ import annotations

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from meeting_entropy.detector.buzzword_evangelist_detector import MeetingState
from meeting_entropy.detector.entropy_oracle import get_threshold_label


def _format_duration(seconds: float) -> str:
    """Format seconds into HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _build_score_bar(label: str, value: float, color: str) -> Panel:
    """Build a labeled progress bar panel for a score (0-100)."""
    clamped = _clamp(value)
    bar = ProgressBar(total=100.0, completed=clamped)
    text = Text.assemble(
        (f" {label}: ", "bold"),
        (f"{clamped:.1f}%", f"bold {color}"),
    )
    content = Text()
    content.append_text(text)
    # We build a simple renderable group
    from rich.console import Group

    group = Group(text, bar)
    return Panel(group, border_style=color)


def _build_header(state: MeetingState) -> Panel:
    """Build the header panel with meeting metadata."""
    duration = _format_duration(state.duration)
    voices = getattr(state, "voices_detected", 0)
    language = getattr(state, "language", "fr")

    header_text = Text.assemble(
        ("MEETING ENTROPY v1.0 — kevin-sigmoid-org", "bold magenta"),
        "\n",
        (f"Duration: {duration}", "cyan"),
        ("  |  ", "dim"),
        (f"Voices detected: {voices}", "cyan"),
        ("  |  ", "dim"),
        (f"Language: {language}", "cyan"),
    )
    return Panel(header_text, border_style="magenta")


def _build_transcript_panel(state: MeetingState) -> Panel:
    """Build the last transcript panel."""
    transcripts = getattr(state, "transcripts", [])
    if transcripts:
        last = transcripts[-1] if isinstance(transcripts[-1], str) else str(transcripts[-1])
    else:
        last = "(silence — the only productive moment so far)"
    return Panel(
        Text(last, style="italic"),
        title="Last Transcript",
        border_style="blue",
    )


def _build_offenders_table(state: MeetingState) -> Panel:
    """Build the top offenders table sorted by total points."""
    table = Table(title="Top Offenders", expand=True)
    table.add_column("Word", style="bold red")
    table.add_column("Category", style="yellow")
    table.add_column("Weight", justify="right", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Total", justify="right", style="bold magenta")

    hits = getattr(state, "hits", [])
    # Aggregate hits by word
    aggregated: dict[str, dict] = {}
    for hit in hits:
        word = getattr(hit, "word", str(hit))
        category = getattr(hit, "category", "unknown")
        weight = getattr(hit, "weight", 1.0)
        if word not in aggregated:
            aggregated[word] = {
                "category": category,
                "weight": weight,
                "count": 0,
                "total": 0.0,
            }
        aggregated[word]["count"] += 1
        aggregated[word]["total"] += weight

    # Sort by total points descending
    sorted_offenders = sorted(aggregated.items(), key=lambda x: x[1]["total"], reverse=True)

    for word, info in sorted_offenders[:10]:
        table.add_row(
            word,
            info["category"],
            f"{info['weight']:.1f}",
            str(info["count"]),
            f"{info['total']:.1f}",
        )

    return Panel(table, border_style="red")


def _build_recommendation(state: MeetingState) -> Panel:
    """Build the recommendation line based on threshold."""
    entropy = getattr(state, "entropy_score", 0.0)
    label = get_threshold_label(entropy)
    if entropy < 30:
        style = "bold green"
    elif entropy < 60:
        style = "bold yellow"
    else:
        style = "bold red"

    text = Text.assemble(
        ("Recommendation: ", "bold"),
        (label, style),
    )
    return Panel(text, border_style="green")


def _build_footer() -> Panel:
    """Build the footer with keyboard shortcuts."""
    footer = Text.assemble(
        ("[Q] ", "bold cyan"),
        ("Quit  ", "dim"),
        ("[E] ", "bold cyan"),
        ("Export  ", "dim"),
        ("[R] ", "bold cyan"),
        ("Reset  ", "dim"),
        ("[P] ", "bold cyan"),
        ("Pause  ", "dim"),
        ("[?] ", "bold cyan"),
        ("Help", "dim"),
    )
    return Panel(footer, border_style="dim")


def _build_dashboard(state: MeetingState) -> Layout:
    """Assemble the full dashboard layout from a MeetingState."""
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="scores", size=5),
        Layout(name="transcript", size=5),
        Layout(name="offenders"),
        Layout(name="recommendation", size=4),
        Layout(name="footer", size=3),
    )

    # Header
    layout["header"].update(_build_header(state))

    # Score bars
    entropy_score = getattr(state, "entropy_score", 0.0)
    signal_noise = getattr(state, "signal_noise", 0.0)
    email_score = getattr(state, "email_score", 0.0)

    scores_layout = Layout()
    scores_layout.split_row(
        Layout(_build_score_bar("Entropy", entropy_score, "red")),
        Layout(_build_score_bar("Signal/Noise", signal_noise, "yellow")),
        Layout(_build_score_bar("Email Score", email_score, "blue")),
    )
    layout["scores"].update(scores_layout)

    # Transcript
    layout["transcript"].update(_build_transcript_panel(state))

    # Top offenders
    layout["offenders"].update(_build_offenders_table(state))

    # Recommendation
    layout["recommendation"].update(_build_recommendation(state))

    # Footer
    layout["footer"].update(_build_footer())

    return layout


def render_the_wall_of_shame(state: MeetingState) -> None:
    """Actualise le dashboard Rich. Ne juge pas. Enfin, si."""
    console = Console()
    dashboard = _build_dashboard(state)
    console.print(dashboard)


class TerminalOfDoom:
    """Rich Live-based real-time terminal dashboard for meeting entropy.

    Uses rich.live.Live to continuously update the terminal with the
    current meeting state, including entropy scores, transcript, and
    the wall of shame for top offenders.
    """

    def __init__(self) -> None:
        self._console = Console()
        self._live: Live | None = None
        self._current_state: MeetingState | None = None

    def start(self) -> None:
        """Start the live dashboard rendering."""
        self._live = Live(
            console=self._console,
            refresh_per_second=4,
            screen=True,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live dashboard rendering and restore the terminal."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def update(self, state: MeetingState) -> None:
        """Update the dashboard with a new MeetingState snapshot.

        Args:
            state: The current meeting state to render.
        """
        self._current_state = state
        if self._live is not None:
            dashboard = _build_dashboard(state)
            self._live.update(dashboard)

    def __enter__(self) -> TerminalOfDoom:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.stop()


def handle_the_nuclear_option(state: MeetingState) -> None:
    """Mode --display-public. Kevin décline toute responsabilité."""
    console = Console()
    entropy = getattr(state, "entropy_score", 0.0)

    if entropy >= 80:
        color = "bold red"
        verdict = "CORPORATE NOISE OVERLOAD"
    elif entropy >= 50:
        color = "bold yellow"
        verdict = "ENTROPY RISING"
    else:
        color = "bold green"
        verdict = "SURPRISINGLY USEFUL"

    # Giant text for public display
    big_text = Text()
    big_text.append("\n\n")
    big_text.append(f"  {verdict}  ", style=f"{color} reverse")
    big_text.append("\n\n")
    big_text.append(f"  ENTROPY: {entropy:.1f}%  ", style=f"{color}")
    big_text.append("\n\n")

    label = get_threshold_label(entropy)
    big_text.append(f"  {label}  ", style="italic")
    big_text.append("\n\n")

    panel = Panel(
        big_text,
        title="[bold red]MEETING ENTROPY — PUBLIC MODE[/bold red]",
        subtitle="[dim]Kevin décline toute responsabilité[/dim]",
        border_style="red",
        expand=True,
        padding=(2, 4),
    )

    console.print(panel)
