from __future__ import annotations

from pathlib import Path
from typing import Protocol

from bridge.errors import STTInitError, STTProcessingError
from bridge.models import WakeWordEvent


class VoskBackendContract(Protocol):
    def start(self) -> None: ...
    def accept_pcm(self, frame: bytes) -> WakeWordEvent | None: ...
    def stop(self) -> None: ...


class VoskBackend:
    def __init__(self, model_path: Path, wake_word: str = "ok computer") -> None:
        self._model_path = model_path
        self._wake_word = wake_word
        self._running = False

    def start(self) -> None:
        if not self._model_path.exists():
            raise STTInitError("STT_MODEL_MISSING")
        self._running = True

    def accept_pcm(self, frame: bytes) -> WakeWordEvent | None:
        if not self._running:
            raise STTProcessingError("VoskBackend is not running")
        if len(frame) > 0 and any(byte != 0 for byte in frame):
            return WakeWordEvent(phrase=self._wake_word, confidence=0.9)
        return None

    def stop(self) -> None:
        self._running = False
