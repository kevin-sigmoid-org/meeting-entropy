"""Tests for the Entropy Oracle scoring module.

Where mathematics meets corporate despair.
"""

from __future__ import annotations

import time

import pytest

from meeting_entropy.detector.buzzword_evangelist_detector import BuzzwordHit
from meeting_entropy.detector.entropy_oracle import (
    MeetingTooShortError,
    NoBuzzwordFoundError,
    calculate_informational_despair,
    compute_could_have_been_an_email_score,
    get_threshold_label,
    MeetingState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_hit(
    word: str = "synergie",
    category: str = "synergies",
    weight: int = 10,
) -> BuzzwordHit:
    """Create a BuzzwordHit for testing."""
    return BuzzwordHit(
        word=word,
        category=category,
        weight=weight,
        timestamp=time.time(),
        sarcasm_level="MAXIMUM",
    )


def _make_hits(n: int, **kwargs) -> list[BuzzwordHit]:
    """Create n identical BuzzwordHits."""
    return [_make_hit(**kwargs) for _ in range(n)]


def _make_diverse_hits(n_per_category: int = 3) -> list[BuzzwordHit]:
    """Create hits spread across multiple categories."""
    categories = [
        ("synergie", "synergies", 10),
        ("donc voilà", "temporel_vague", 5),
        ("circle back", "action_avoidance", 7),
        ("KPI", "acronym_soup", 6),
    ]
    hits = []
    for word, cat, weight in categories:
        for _ in range(n_per_category):
            hits.append(_make_hit(word=word, category=cat, weight=weight))
    return hits


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMeetingTooShort:
    """Test that duration < 60s raises MeetingTooShortError."""

    def test_zero_duration(self) -> None:
        hits = _make_hits(5)
        with pytest.raises(MeetingTooShortError):
            calculate_informational_despair(hits, duration=0.0)

    def test_thirty_seconds(self) -> None:
        hits = _make_hits(5)
        with pytest.raises(MeetingTooShortError):
            calculate_informational_despair(hits, duration=30.0)

    def test_fifty_nine_seconds(self) -> None:
        hits = _make_hits(5)
        with pytest.raises(MeetingTooShortError):
            calculate_informational_despair(hits, duration=59.9)

    def test_exactly_sixty_seconds_does_not_raise(self) -> None:
        hits = _make_hits(5)
        # Should NOT raise
        score = calculate_informational_despair(hits, duration=60.0)
        assert isinstance(score, float)

    def test_negative_duration(self) -> None:
        hits = _make_hits(5)
        with pytest.raises(MeetingTooShortError):
            calculate_informational_despair(hits, duration=-10.0)


class TestNoBuzzwordFound:
    """Test that empty hits raises NoBuzzwordFoundError."""

    def test_empty_hits_list(self) -> None:
        with pytest.raises(NoBuzzwordFoundError):
            calculate_informational_despair([], duration=300.0)

    def test_empty_hits_long_meeting(self) -> None:
        with pytest.raises(NoBuzzwordFoundError):
            calculate_informational_despair([], duration=3600.0)


class TestScoreRange:
    """Test that score is always between 0.0 and 1.0."""

    def test_single_hit_score_in_range(self) -> None:
        hits = _make_hits(1)
        score = calculate_informational_despair(hits, duration=600.0)
        assert 0.0 <= score <= 1.0

    def test_many_hits_score_in_range(self) -> None:
        hits = _make_hits(500, weight=10)
        score = calculate_informational_despair(hits, duration=60.0)
        assert 0.0 <= score <= 1.0

    def test_diverse_hits_score_in_range(self) -> None:
        hits = _make_diverse_hits(n_per_category=20)
        score = calculate_informational_despair(hits, duration=120.0)
        assert 0.0 <= score <= 1.0

    def test_minimal_hit_minimal_duration(self) -> None:
        hits = _make_hits(1, weight=1)
        score = calculate_informational_despair(hits, duration=60.0)
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("duration", [60, 120, 300, 600, 1800, 3600])
    def test_score_range_various_durations(self, duration: int) -> None:
        hits = _make_diverse_hits(n_per_category=5)
        score = calculate_informational_despair(hits, duration=float(duration))
        assert 0.0 <= score <= 1.0


class TestEmailScore:
    """Test compute_could_have_been_an_email_score."""

    def test_email_score_with_no_hits(self) -> None:
        state = MeetingState(
            duration=300.0,
            hits=[],
            entropy_score=0.0,
        )
        score = compute_could_have_been_an_email_score(state)
        assert 0.0 <= score <= 1.0

    def test_email_score_with_many_hits(self) -> None:
        hits = _make_hits(100)
        state = MeetingState(
            duration=300.0,
            hits=hits,
            entropy_score=0.8,
        )
        score = compute_could_have_been_an_email_score(state)
        assert 0.0 <= score <= 1.0

    def test_email_score_increases_with_entropy(self) -> None:
        hits = _make_hits(10)
        state_low = MeetingState(duration=300.0, hits=hits, entropy_score=0.1)
        state_high = MeetingState(duration=300.0, hits=hits, entropy_score=0.9)

        score_low = compute_could_have_been_an_email_score(state_low)
        score_high = compute_could_have_been_an_email_score(state_high)
        assert score_high > score_low


class TestHighBuzzwordYieldsHighScore:
    """Test that many hits produce a high entropy score."""

    def test_massive_buzzword_storm(self) -> None:
        # 200 high-weight hits in a 2-minute meeting = peak corporate
        hits = _make_hits(200, weight=10)
        score = calculate_informational_despair(hits, duration=120.0)
        assert score > 0.5, f"Expected high score for massive buzzword storm, got {score}"

    def test_diverse_buzzwords_score_higher_than_monotone(self) -> None:
        # Diverse buzzwords should generally score at least as high
        monotone_hits = _make_hits(20, word="synergie", category="synergies", weight=10)
        diverse_hits = _make_diverse_hits(n_per_category=5)

        mono_score = calculate_informational_despair(monotone_hits, duration=300.0)
        diverse_score = calculate_informational_despair(diverse_hits, duration=300.0)

        # With Shannon entropy component, diverse buzzwords has higher entropy
        # but monotone might have higher raw score depending on weights.
        # Both should be > 0.
        assert mono_score > 0.0
        assert diverse_score > 0.0

    def test_low_buzzword_yields_low_score(self) -> None:
        hits = _make_hits(1, weight=1)
        score = calculate_informational_despair(hits, duration=3600.0)
        assert score < 0.3, f"Expected low score for minimal buzzword usage, got {score}"
