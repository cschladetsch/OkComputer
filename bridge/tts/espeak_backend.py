from __future__ import annotations

import asyncio
import subprocess
import uuid
from collections.abc import Awaitable, Callable
from typing import Literal

from bridge.errors import TTSError
from bridge.text import strip_markdown

TranscriptStatus = Literal["complete", "interrupted"]
TranscriptDeltaCallback = Callable[[str, int, str, bool], Awaitable[None]]
TranscriptEntryCallback = Callable[[str, str, TranscriptStatus], Awaitable[None]]


class EspeakBackend:
    def __init__(
        self,
        voice: str = "en-us",
        speed: int = 160,
        on_transcript_delta: TranscriptDeltaCallback | None = None,
        on_transcript_entry: TranscriptEntryCallback | None = None,
        live_transcription: bool = True,
        retroactive_transcription: bool = True,
    ) -> None:
        self.voice = voice
        self.speed = speed
        self.on_transcript_delta = on_transcript_delta
        self.on_transcript_entry = on_transcript_entry
        self.live_transcription = live_transcription
        self.retroactive_transcription = retroactive_transcription
        self._process: subprocess.Popen[str] | None = None
        self._interrupted = False

    async def speak(self, text: str) -> None:
        cleaned = strip_markdown(text)
        if not cleaned:
            return
        utterance_id = str(uuid.uuid4())
        self._interrupted = False
        try:
            if self.live_transcription and self.on_transcript_delta is not None:
                await self.on_transcript_delta(utterance_id, 0, cleaned, False)
            self._process = subprocess.Popen(
                ["espeak-ng", "-v", self.voice, "-s", str(self.speed), cleaned],
                text=True,
            )
            await asyncio.to_thread(self._process.wait)
            if self.retroactive_transcription and self.on_transcript_entry is not None:
                status: TranscriptStatus = "interrupted" if self._interrupted else "complete"
                await self.on_transcript_entry(utterance_id, cleaned, status)
        except FileNotFoundError as exc:
            raise TTSError("espeak-ng not found") from exc

    def interrupt(self) -> None:
        self._interrupted = True
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
