from __future__ import annotations

import asyncio
import importlib
import time
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, cast

from bridge.errors import STTInitError, STTProcessingError
from bridge.stt.vosk_backend import VoskBackend

Frame = dict[str, object]
FrameHandler = Callable[[Frame], Coroutine[Any, Any, None]]


class MicrophoneMonitor:
    def __init__(
        self,
        broadcast: FrameHandler,
        model_path: Path,
        wake_word: str,
        sample_rate: int,
        channels: int,
        cooldown_seconds: float = 2.0,
    ) -> None:
        self._broadcast = broadcast
        self._backend = VoskBackend(model_path, wake_word)
        self._sample_rate = sample_rate
        self._channels = channels
        self._cooldown_seconds = cooldown_seconds
        self._last_event_at = 0.0
        self._stream: Any | None = None
        self._running = False
        self._energy_fallback = False

    async def start(self) -> None:
        try:
            self._backend.start()
        except STTInitError:
            self._energy_fallback = True
        sounddevice = importlib.import_module("sounddevice")
        loop = asyncio.get_running_loop()

        def schedule(frame: Frame) -> None:
            loop.create_task(self._broadcast(frame))

        def callback(indata: bytes, _frames: int, _time_info: object, status: object) -> None:
            if status:
                status_frame: Frame = {"type": "error", "code": "AUDIO_STATUS", "message": str(status)}
                loop.call_soon_threadsafe(schedule, status_frame)
            loop.call_soon_threadsafe(lambda: loop.create_task(self.process_pcm(bytes(indata))))

        self._stream = cast(Any, sounddevice).RawInputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="int16",
            callback=callback,
        )
        self._stream.start()
        self._running = True
        await self._broadcast({"type": "state", "state": "IDLE"})

    async def process_pcm(self, pcm: bytes) -> None:
        if not pcm or time.monotonic() - self._last_event_at < self._cooldown_seconds:
            return
        try:
            detected = self._has_energy(pcm) if self._energy_fallback else self._backend.accept_pcm(pcm) is not None
        except STTProcessingError as exc:
            await self._broadcast({"type": "error", "code": "STT_PROCESSING", "message": str(exc)})
            return
        if not detected:
            return
        self._last_event_at = time.monotonic()
        await self._broadcast({"type": "state", "state": "LISTENING"})
        await self._broadcast(
            {
                "type": "transcript",
                "speaker": "USER",
                "text": "microphone activity detected",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    async def stop(self) -> None:
        self._running = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._backend.stop()

    @staticmethod
    def _has_energy(pcm: bytes) -> bool:
        return any(byte != 0 for byte in pcm)
