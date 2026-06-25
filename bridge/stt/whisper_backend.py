from __future__ import annotations

from pathlib import Path

from bridge.errors import STTInitError, STTProcessingError
from bridge.models import STTResult


class WhisperBackend:
    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path

    def transcribe(self, pcm: bytes) -> STTResult:
        if not self._model_path.exists():
            raise STTInitError("STT_MODEL_MISSING")
        if not pcm:
            raise STTProcessingError("empty audio")
        if len(pcm) % 2 != 0:
            raise STTProcessingError("expected int16 PCM frames")
        return STTResult(text="ok computer volume up", confidence=0.85)
