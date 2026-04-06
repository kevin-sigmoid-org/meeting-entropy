"""Corporate noise detection engine. Scans transcripts for corporate nonsense."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class BuzzwordHit:
    word: str
    category: str
    weight: int
    timestamp: float
    sarcasm_level: str = "MODÉRÉ"


@dataclass
class Corpus:
    language: str
    categories: dict  # category_name -> {weight, words, sarcasm_level}


@dataclass
class MeetingState:
    start_time: float = 0.0
    duration: float = 0.0
    hits: list = field(default_factory=list)  # List[BuzzwordHit]
    transcripts: list = field(default_factory=list)  # List[str]
    silence_events: list = field(default_factory=list)
    voices_detected: int = 0
    languages: list = field(default_factory=list)
    is_running: bool = False
    entropy_score: float = 0.0
    email_score: float = 0.0
    last_transcript: str = ""


def load_the_buzzword_bible(lang: str) -> Corpus:
    """Charge le corpus YAML de la langue demandée. C'est la bible du BS."""
    corpus_dir = Path(__file__).resolve().parent.parent.parent / "corpus"
    corpus_path = corpus_dir / f"{lang}.yaml"

    with open(corpus_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Corpus(
        language=data["metadata"]["language"],
        categories=data["categories"],
    )


def detect_synergy_contamination(text: str, corpus: Corpus) -> list[BuzzwordHit]:
    """Cherche les mots du corpus dans le texte. Pleure intérieurement."""
    hits: list[BuzzwordHit] = []
    text_lower = text.lower()

    for category_name, category_data in corpus.categories.items():
        weight = category_data.get("weight", 1)
        sarcasm_level = category_data.get("sarcasm_level", "MODÉRÉ")
        words = category_data.get("words", [])

        for word in words:
            if word.lower() in text_lower:
                hits.append(
                    BuzzwordHit(
                        word=word,
                        category=category_name,
                        weight=weight,
                        timestamp=time.time(),
                        sarcasm_level=sarcasm_level,
                    )
                )

    return hits
