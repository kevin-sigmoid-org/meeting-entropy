"""Awkward silence detection and qualitative appreciation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from meeting_entropy.audio.the_uncomfortable_listener import AudioChunk


@dataclass
class SilenceEvent:
    """A detected period of awkward silence."""

    start_time: float
    duration_ms: float
    appreciation: str  # qualitative assessment


# Silence duration categories and their appreciations
_SILENCE_APPRECIATIONS = {
    3000: "Un ange passe.",
    5000: "Deux anges passent. Ils sont gênés aussi.",
    8000: "Le silence devient une entité consciente dans la pièce.",
    12000: "Quelqu'un devrait parler. Personne ne le fera.",
    20000: "Ce silence a maintenant sa propre page LinkedIn.",
}


def appreciate_the_awkward_silence(
    audio: AudioChunk, threshold_ms: int = 3000
) -> Optional[SilenceEvent]:
    """Detect and appreciate an awkward silence in an audio chunk.

    Monitors audio energy levels to detect silences that exceed the
    threshold duration. When silence is detected, it is classified
    with an appropriate level of appreciation.

    Silence duration categories:
        - 3-5s: "Un ange passe."
        - 5-8s: "Deux anges passent. Ils sont gênés aussi."
        - 8-12s: "Le silence devient une entité consciente dans la pièce."
        - 12-20s: "Quelqu'un devrait parler. Personne ne le fera."
        - 20s+: "Ce silence a maintenant sa propre page LinkedIn."

    Args:
        audio: An AudioChunk captured from the microphone.
        threshold_ms: Minimum silence duration in milliseconds to
            trigger detection. Default is 3000ms (3 seconds).

    Returns:
        A SilenceEvent if an awkward silence was detected, None otherwise.
        The appreciation field contains a qualitative assessment of the
        silence's existential weight.
    """
    # Compute RMS energy of the audio chunk
    if audio.data.size == 0:
        return None

    rms = np.sqrt(np.mean(audio.data.astype(np.float64) ** 2))

    # Ambient noise threshold — below this, we consider it silence
    ambient_threshold = 0.01

    if rms >= ambient_threshold:
        return None

    # Check if the silence duration meets the threshold
    if audio.duration_ms < threshold_ms:
        return None

    # Determine appreciation based on duration
    appreciation = "Un ange passe."
    for duration_limit, message in sorted(_SILENCE_APPRECIATIONS.items(), reverse=True):
        if audio.duration_ms >= duration_limit:
            appreciation = message
            break

    return SilenceEvent(
        start_time=audio.timestamp,
        duration_ms=audio.duration_ms,
        appreciation=appreciation,
    )
