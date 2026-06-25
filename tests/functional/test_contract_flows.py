from __future__ import annotations

import asyncio

from bridge.llm.router import LLMRouter
from bridge.models import ActionEnum
from bridge.system.handler import SystemHandler
from bridge.tts.kokoro_backend import KokoroBackend


def test_wake_to_general_query() -> None:
    async def run() -> None:
        router = LLMRouter("local://primary", "local://fallback", "primary", "fallback")
        tts = KokoroBackend()
        response = await router.complete("ok computer what is the capital of france")
        await tts.speak(response)
        assert "Paris" in " ".join(tts.spoken_chunks)

    asyncio.run(run())


def test_stop_is_unified() -> None:
    tts = KokoroBackend()
    tts.interrupt()
    assert tts.stop_event.is_set()


def test_volume_up_dispatch_contract() -> None:
    result = SystemHandler().execute(ActionEnum.VOLUME_UP, {})
    assert result.success
