from __future__ import annotations

import asyncio
import subprocess

from bridge.errors import TTSError
from bridge.text import strip_markdown


class EspeakBackend:
    def __init__(self, voice: str = "en-us", speed: int = 160) -> None:
        self.voice = voice
        self.speed = speed
        self._process: subprocess.Popen[str] | None = None

    async def speak(self, text: str) -> None:
        cleaned = strip_markdown(text)
        if not cleaned:
            return
        try:
            self._process = subprocess.Popen(
                ["espeak-ng", "-v", self.voice, "-s", str(self.speed), cleaned],
                text=True,
            )
            await asyncio.to_thread(self._process.wait)
        except FileNotFoundError as exc:
            raise TTSError("espeak-ng not found") from exc

    def interrupt(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
