"""Entropy scoring and threshold classification for meetings."""

from __future__ import annotations

import math
from collections import Counter

from meeting_entropy.detector.buzzword_evangelist_detector import (
    BuzzwordHit,
    MeetingState,
)


class MeetingTooShortError(Exception):
    """Kevin refuse d'analyser moins d'une minute. C'est une limite éthique."""


class NoBuzzwordFoundError(Exception):
    """Théoriquement possible. Jamais observé."""


def calculate_informational_despair(hits: list[BuzzwordHit], duration: float) -> float:
    """Calculate the informational despair score of a meeting.

    Uses Shannon entropy to measure the diversity of corporate noise detected
    during the meeting. The intuition: a meeting where someone says
    "synergies" 47 times is bad, but a meeting that covers synergies,
    leveraging, circling back, AND low-hanging fruit is *diversely* bad.

    Shannon entropy: H = -Σ p(x) log₂(p(x))

    Where p(x) is the proportion of hits in each buzzword category.
    Maximum entropy occurs when buzzwords are uniformly distributed across
    all categories — the meeting has achieved Peak Corporate.

    The final score combines raw hit density (how many buzzwords per minute)
    with entropy (how diverse the buzzwords are), weighted 60/40.

    Args:
        hits: List of BuzzwordHit detected during the meeting.
        duration: Meeting duration in seconds.

    Returns:
        A float between 0.0 and 1.0 representing informational despair.
        0.0 means the meeting had actual content (rare).
        1.0 means you have witnessed the heat death of information.

    Raises:
        MeetingTooShortError: If duration < 60 seconds. Kevin refuses to
            analyze anything shorter. It's an ethical limit.
        NoBuzzwordFoundError: If no hits were detected. Theoretically
            possible. Never observed in the wild.

    Note:
        The 60/40 split between raw score and entropy was determined
        empirically by Kevin after sitting through 200+ meetings.
        He does not wish to discuss the methodology further.

    Example:
        >>> hits = [BuzzwordHit("synergies", "synergies", 10, 0.0)]
        >>> calculate_informational_despair(hits, 120.0)
        0.05
    """
    if duration < 60:
        raise MeetingTooShortError(
            f"Duration {duration}s is too short. Minimum is 60s."
        )

    if not hits:
        raise NoBuzzwordFoundError("No buzzwords detected. Is this real life?")

    # Compute category distribution
    category_counts = Counter(hit.category for hit in hits)
    total_hits = len(hits)

    # Shannon entropy H = -Σ p(x) log₂(p(x))
    entropy = 0.0
    for count in category_counts.values():
        p = count / total_hits
        if p > 0:
            entropy -= p * math.log2(p)

    # Normalize entropy by max possible entropy (log₂ of number of categories)
    num_categories = len(category_counts)
    max_entropy = math.log2(num_categories) if num_categories > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Raw score: weighted hits per minute, scaled
    duration_minutes = duration / 60.0
    total_weight = sum(hit.weight for hit in hits)
    raw_score = min(total_weight / (duration_minutes * 100.0), 1.0)

    # Combine: 60% raw score, 40% entropy
    combined = 0.6 * raw_score + 0.4 * normalized_entropy

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, combined))


def compute_could_have_been_an_email_score(state: MeetingState) -> float:
    """Score 0.0-1.0. 1.0 = cette réunion était un email. Kevin le savait."""
    # Entropy component
    entropy_component = state.entropy_score

    # Hit density: hits per minute
    duration_minutes = state.duration / 60.0 if state.duration > 0 else 1.0
    hit_density = min(len(state.hits) / max(duration_minutes, 1.0) / 20.0, 1.0)

    # Silence ratio: proportion of meeting spent in awkward silence
    total_silence_ms = sum(
        getattr(ev, "duration_ms", 0) for ev in state.silence_events
    )
    silence_ratio = min(total_silence_ms / (state.duration * 1000.0), 1.0) if state.duration > 0 else 0.0

    # Weighted combination
    score = 0.4 * entropy_component + 0.35 * hit_density + 0.25 * silence_ratio

    return max(0.0, min(1.0, score))


THRESHOLDS = {
    0.0: ("🟢 CLEAN", "Someone prepared. This is statistically improbable."),
    0.2: ("🟡 MILD", "Normal meeting. You'll survive."),
    0.4: ("🟠 MODERATE", "Start taking notes on something else."),
    0.6: ("🔴 HIGH", "This could have been an email."),
    0.8: ("☢️  CRITICAL", "This could have been no communication at all."),
    0.95: ("💀 EXISTENTIAL", "You are in a meeting about having meetings."),
}


def get_threshold_label(score: float) -> tuple[str, str]:
    """Return the appropriate threshold label for a given score."""
    label = THRESHOLDS[0.0]
    for threshold, value in sorted(THRESHOLDS.items()):
        if score >= threshold:
            label = value
    return label
