from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from bridge.errors import LLMError, STTInitError, SystemHandlerError
from bridge.ipc.client import IPCClient
from bridge.llm.router import LLMRouter
from bridge.models import ActionEnum
from bridge.stt.vosk_backend import VoskBackend
from bridge.system.handler import SystemHandler
from bridge.text import strip_markdown
from bridge.tts.kokoro_backend import KokoroBackend


def test_markdown_stripped() -> None:
    assert strip_markdown("**bold** [x](y)") == "bold xy"


def test_vosk_missing_model_raises() -> None:
    backend = VoskBackend(Path("__missing__"))
    with pytest.raises(STTInitError):
        backend.start()


def test_vosk_wake_event(tmp_path: Path) -> None:
    model = tmp_path / "model"
    model.mkdir()
    backend = VoskBackend(model)
    backend.start()
    assert backend.accept_pcm(b"\x01\x00") is not None
    assert backend.accept_pcm(b"\x00\x00") is None


def test_kokoro_chunks_and_interrupt() -> None:
    async def run() -> None:
        backend = KokoroBackend(chunk_chars=5)
        await backend.speak("**hello** world.")
        assert backend.spoken_chunks == ["hello", "world", "."]
        backend.interrupt()
        assert backend.stop_event.is_set()

    asyncio.run(run())


def test_llm_failover_and_markdown() -> None:
    async def run() -> None:
        router = LLMRouter("fail://primary", "local://fallback", "primary", "fallback")
        assert await router.complete("what is the capital of france") == "The capital of France is Paris."
        failing = LLMRouter("fail://primary", "fail://fallback", "primary", "fallback")
        with pytest.raises(LLMError):
            await failing.complete("hello")

    asyncio.run(run())


def test_ipc_echo_queue() -> None:
    async def run() -> None:
        client = IPCClient()
        await client.connect()
        await client.send({"type": "ping"})
        assert await client.receive() == {"type": "ping"}

    asyncio.run(run())


def test_system_handler_unknown_action() -> None:
    handler = SystemHandler()
    with pytest.raises(SystemHandlerError):
        handler.execute(ActionEnum.STOP, {})
