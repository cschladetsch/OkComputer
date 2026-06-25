from __future__ import annotations

import asyncio

from bridge.errors import TTSError
from bridge.text import sentence_chunks


class KokoroBackend:
    def __init__(self, chunk_chars: int = 600, speed: float = 0.85) -> None:
        self.chunk_chars = chunk_chars
        self.speed = speed
        self.stop_event = asyncio.Event()
        self.spoken_chunks: list[str] = []

    async def speak(self, text: str) -> None:
        if self.chunk_chars <= 0:
            raise TTSError("chunk_chars must be positive")
        self.stop_event.clear()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def producer() -> None:
            for chunk in sentence_chunks(text, self.chunk_chars):
                if self.stop_event.is_set():
                    break
                await queue.put(chunk)
            await queue.put(None)

        async def consumer() -> None:
            while True:
                item = await queue.get()
                if item is None or self.stop_event.is_set():
                    return
                self.spoken_chunks.append(item)
                await asyncio.sleep(0)

        await asyncio.gather(producer(), consumer())

    def interrupt(self) -> None:
        self.stop_event.set()
