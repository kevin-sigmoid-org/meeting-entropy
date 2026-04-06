"""Tests for the buzzword detection engine.

Kevin Sigmoid approved. Every test here was inspired by a real meeting.
"""

from __future__ import annotations

import time

import pytest

from meeting_entropy.detector.buzzword_evangelist_detector import (
    BuzzwordHit,
    Corpus,
    detect_synergy_contamination,
    load_the_buzzword_bible,
)
from meeting_entropy.detector.entropy_oracle import (
    NoBuzzwordFoundError,
    calculate_informational_despair,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fr_corpus() -> Corpus:
    """Load the French buzzword corpus."""
    return load_the_buzzword_bible("fr")


@pytest.fixture()
def en_corpus() -> Corpus:
    """Load the English buzzword corpus."""
    return load_the_buzzword_bible("en")


@pytest.fixture()
def universal_corpus() -> Corpus:
    """Load the universal buzzword corpus."""
    return load_the_buzzword_bible("universal")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDetectClassicSynergy:
    """Teste que 'synergie' est bien détecté. Si ce test échoue, Kevin a un problème."""

    def test_detect_classic_synergy(self, fr_corpus: Corpus) -> None:
        text = "Il faut créer une synergie entre les équipes."
        hits = detect_synergy_contamination(text, fr_corpus)
        synergy_hits = [h for h in hits if h.word.lower() == "synergie"]
        assert len(synergy_hits) >= 1
        assert synergy_hits[0].category == "synergies"
        assert synergy_hits[0].weight == 10
        assert synergy_hits[0].sarcasm_level == "MAXIMUM"

    def test_detect_english_synergy(self, en_corpus: Corpus) -> None:
        text = "We need to leverage the synergy between departments."
        hits = detect_synergy_contamination(text, en_corpus)
        synergy_hits = [h for h in hits if h.word.lower() == "synergy"]
        assert len(synergy_hits) >= 1


class TestDoncVoilaRate:
    """Teste le taux de détection de 'donc voilà'.

    Ce mot a été entendu 847 fois lors de la phase de test. Kevin a compté.
    """

    def test_donc_voila_detected_at_start(self, fr_corpus: Corpus) -> None:
        text = "Donc voilà, on va commencer la réunion."
        hits = detect_synergy_contamination(text, fr_corpus)
        dv_hits = [h for h in hits if h.word == "donc voilà"]
        assert len(dv_hits) == 1

    def test_donc_voila_detected_mid_sentence(self, fr_corpus: Corpus) -> None:
        text = "On a travaillé sur le projet et donc voilà c'est fini."
        hits = detect_synergy_contamination(text, fr_corpus)
        dv_hits = [h for h in hits if h.word == "donc voilà"]
        assert len(dv_hits) == 1

    def test_donc_voila_detected_at_end(self, fr_corpus: Corpus) -> None:
        text = "Le budget est validé, donc voilà."
        hits = detect_synergy_contamination(text, fr_corpus)
        dv_hits = [h for h in hits if h.word == "donc voilà"]
        assert len(dv_hits) == 1

    def test_donc_voila_category_is_temporel_vague(self, fr_corpus: Corpus) -> None:
        text = "Donc voilà, on avance."
        hits = detect_synergy_contamination(text, fr_corpus)
        dv_hits = [h for h in hits if h.word == "donc voilà"]
        assert dv_hits[0].category == "temporel_vague"


class TestEntropyOfPureSignal:
    """Une réunion sans aucun buzzword devrait avoir une entropie de 0.

    Ce test ne passera jamais en conditions réelles. Il existe pour documenter l'idéal.
    """

    def test_no_hits_raises_no_buzzword_found_error(self) -> None:
        with pytest.raises(NoBuzzwordFoundError):
            calculate_informational_despair([], duration=300.0)

    def test_pure_signal_text_has_no_hits(self, fr_corpus: Corpus) -> None:
        text = "Le chiffre d'affaires du trimestre est de 2,4 millions d'euros."
        hits = detect_synergy_contamination(text, fr_corpus)
        assert len(hits) == 0


class TestMultipleCategoriesDetected:
    """Test detection across multiple categories in a single text."""

    def test_multiple_categories_in_french(self, fr_corpus: Corpus) -> None:
        text = (
            "Donc voilà, il faut créer une synergie entre les équipes. "
            "Je reviens vers toi avec le feedback du brainstorming. "
            "Tout le monde est aligné, clairement."
        )
        hits = detect_synergy_contamination(text, fr_corpus)
        categories = {h.category for h in hits}
        assert len(categories) >= 3, f"Expected 3+ categories, got {categories}"

    def test_multiple_categories_in_english(self, en_corpus: Corpus) -> None:
        text = (
            "Let's circle back on the synergy from our deep dive. "
            "Going forward, does that make sense? Basically, honestly."
        )
        hits = detect_synergy_contamination(text, en_corpus)
        categories = {h.category for h in hits}
        assert len(categories) >= 3, f"Expected 3+ categories, got {categories}"


class TestCaseInsensitiveDetection:
    """Test that detection is case-insensitive."""

    def test_uppercase_synergy_detected(self, fr_corpus: Corpus) -> None:
        text = "SYNERGIE MAXIMALE ENTRE LES DÉPARTEMENTS"
        hits = detect_synergy_contamination(text, fr_corpus)
        assert any(h.word.lower() == "synergie" for h in hits)

    def test_mixed_case_detected(self, en_corpus: Corpus) -> None:
        text = "We need to Circle Back on the Low-Hanging Fruit."
        hits = detect_synergy_contamination(text, en_corpus)
        assert any(h.word == "circle back" for h in hits)
        assert any(h.word == "low-hanging fruit" for h in hits)

    def test_all_caps_english(self, en_corpus: Corpus) -> None:
        text = "SYNERGY IS KEY GOING FORWARD"
        hits = detect_synergy_contamination(text, en_corpus)
        assert any(h.word.lower() == "synergy" for h in hits)


class TestCorpusLoading:
    """Test that all corpus files load correctly."""

    @pytest.mark.parametrize("lang", ["fr", "en", "de", "universal"])
    def test_load_corpus(self, lang: str) -> None:
        corpus = load_the_buzzword_bible(lang)
        assert corpus.language == lang
        assert len(corpus.categories) > 0

    @pytest.mark.parametrize("lang", ["fr", "en", "de", "universal"])
    def test_corpus_has_words(self, lang: str) -> None:
        corpus = load_the_buzzword_bible(lang)
        for cat_name, cat_data in corpus.categories.items():
            assert "words" in cat_data, f"Category {cat_name} in {lang} has no words"
            assert len(cat_data["words"]) > 0, f"Category {cat_name} in {lang} is empty"

    @pytest.mark.parametrize("lang", ["fr", "en", "de", "universal"])
    def test_corpus_has_weights(self, lang: str) -> None:
        corpus = load_the_buzzword_bible(lang)
        for cat_name, cat_data in corpus.categories.items():
            assert "weight" in cat_data, f"Category {cat_name} in {lang} missing weight"
            assert cat_data["weight"] > 0


class TestThresholdLabels:
    """Test that threshold labels are correctly assigned."""

    def test_zero_score_label(self) -> None:
        from meeting_entropy.detector.entropy_oracle import get_threshold_label

        label, _ = get_threshold_label(0.0)
        assert "CLEAN" in label

    def test_high_score_label(self) -> None:
        from meeting_entropy.detector.entropy_oracle import get_threshold_label

        label, _ = get_threshold_label(0.85)
        assert "CRITICAL" in label

    def test_max_score_label(self) -> None:
        from meeting_entropy.detector.entropy_oracle import get_threshold_label

        label, _ = get_threshold_label(1.0)
        assert "EXISTENTIAL" in label

    def test_moderate_score_label(self) -> None:
        from meeting_entropy.detector.entropy_oracle import get_threshold_label

        label, _ = get_threshold_label(0.5)
        assert "MODERATE" in label
