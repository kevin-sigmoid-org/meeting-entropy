"""Whisper-based transcription for audio chunks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from meeting_entropy.audio.the_uncomfortable_listener import AudioChunk


class MicrophoneWhisperer:
    """Transcribes audio chunks using faster-whisper."""

    def __init__(
        self,
        model_name: str = "small",
        language: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.language = language

        self._model_dir = Path.home() / ".meeting-entropy" / "models"
        self._model_dir.mkdir(parents=True, exist_ok=True)

        self._model = WhisperModel(
            model_name,
            download_root=str(self._model_dir),
            device="auto",
            compute_type="default",
        )

    def transcribe_the_meaningless_words(self, audio: AudioChunk) -> str:
        """Passe l'audio à Whisper. Retourne du texte probablement inutile."""
        audio_data = audio.data.astype(np.float32)

        # Ensure mono 1-D array
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        segments, _info = self._model.transcribe(
            audio_data,
            language=self.language,
            beam_size=5,
        )

        return "".join(segment.text for segment in segments)
