"""Audio buffer management for capturing microphone input."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pyaudio


@dataclass
class AudioChunk:
    """A chunk of audio data captured from the microphone."""

    data: np.ndarray
    sample_rate: int
    timestamp: float
    duration_ms: float


class TheUncomfortableListener:
    """Captures audio from the default microphone using PyAudio."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self._audio: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None

    def start(self) -> None:
        """Open the audio stream and begin capturing from the default microphone."""
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

    def stop(self) -> None:
        """Stop capturing and release audio resources."""
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._audio is not None:
            self._audio.terminate()
            self._audio = None

    def read_chunk(self) -> AudioChunk:
        """Read a single chunk of audio from the microphone stream.

        Returns:
            An AudioChunk containing the captured audio data.

        Raises:
            RuntimeError: If the listener has not been started.
        """
        if self._stream is None:
            raise RuntimeError(
                "Listener not started. Call start() or use as a context manager."
            )

        raw_data = self._stream.read(self.chunk_size, exception_on_overflow=False)
        timestamp = time.time()
        audio_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
        duration_ms = (self.chunk_size / self.sample_rate) * 1000.0

        return AudioChunk(
            data=audio_array,
            sample_rate=self.sample_rate,
            timestamp=timestamp,
            duration_ms=duration_ms,
        )

    def __enter__(self) -> TheUncomfortableListener:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.stop()


def capture_the_corporate_suffering() -> AudioChunk:
    """Écoute le micro et retourne un chunk audio."""
    with TheUncomfortableListener() as listener:
        return listener.read_chunk()
