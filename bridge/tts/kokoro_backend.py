from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable
from typing import Literal

from bridge.errors import TTSError
from bridge.text import sentence_chunks, strip_markdown

TranscriptStatus = Literal["complete", "interrupted"]
TranscriptDeltaCallback = Callable[[str, int, str, bool], Awaitable[None]]
TranscriptEntryCallback = Callable[[str, str, TranscriptStatus], Awaitable[None]]


class KokoroBackend:
    def __init__(
        self,
        chunk_chars: int = 600,
        speed: float = 0.85,
        on_transcript_delta: TranscriptDeltaCallback | None = None,
        on_transcript_entry: TranscriptEntryCallback | None = None,
        live_transcription: bool = True,
        retroactive_transcription: bool = True,
    ) -> None:
        self.chunk_chars = chunk_chars
        self.speed = speed
        self.on_transcript_delta = on_transcript_delta
        self.on_transcript_entry = on_transcript_entry
        self.live_transcription = live_transcription
        self.retroactive_transcription = retroactive_transcription
        self.stop_event = asyncio.Event()
        self.spoken_chunks: list[str] = []

    async def speak(self, text: str) -> None:
        if self.chunk_chars <= 0:
            raise TTSError("chunk_chars must be positive")
        self.stop_event.clear()
        utterance_id = str(uuid.uuid4())
        cleaned = strip_markdown(text)
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def producer() -> None:
            for chunk in sentence_chunks(cleaned, self.chunk_chars):
                if self.stop_event.is_set():
                    break
                await queue.put(chunk)
            await queue.put(None)

        async def consumer() -> None:
            sequence = 0
            while True:
                item = await queue.get()
                if item is None or self.stop_event.is_set():
                    return
                if self.live_transcription and self.on_transcript_delta is not None:
                    await self.on_transcript_delta(utterance_id, sequence, item, False)
                self.spoken_chunks.append(item)
                sequence += 1
                await asyncio.sleep(0)

        await asyncio.gather(producer(), consumer())
        if self.retroactive_transcription and self.on_transcript_entry is not None:
            status: TranscriptStatus = "interrupted" if self.stop_event.is_set() else "complete"
            await self.on_transcript_entry(utterance_id, cleaned, status)

    def interrupt(self) -> None:
        self.stop_event.set()
