from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

import bridge.main as bridge_main
from bridge.errors import LLMError, STTInitError, STTProcessingError, SystemHandlerError
from bridge.ipc.client import IPCClient
from bridge.llm.router import LLMRouter
from bridge.models import ActionEnum
from bridge.stt.vosk_backend import VoskBackend
from bridge.system.handler import SystemHandler
from bridge.text import strip_markdown
from bridge.tts.kokoro_backend import KokoroBackend
from bridge.ws_relay import WSRelay


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
    with pytest.raises(STTProcessingError):
        backend.accept_pcm(b"\x01")


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
        assert router.endpoint_attempts["fail://primary"] == 2
        assert router.endpoint_attempts["local://fallback"] == 1
        flaky = LLMRouter("fail-once://primary", "local://fallback", "primary", "fallback")
        assert await flaky.complete("hello", memory_summary="memory") == "primary: memory hello"
        assert flaky.endpoint_attempts["fail-once://primary"] == 2
        assert flaky.endpoint_attempts["local://fallback"] == 0
        assert flaky.last_prompts[-1] == "memory\nhello"
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


def test_ws_relay_broadcast_and_ipc_subscription() -> None:
    async def run() -> None:
        relay = WSRelay(5003)
        await relay.start()
        client = IPCClient()
        await client.connect()
        client.subscribe(relay.broadcast)
        await client.send({"type": "state", "state": "LISTENING"})
        assert relay.events[-1] == {"type": "state", "state": "LISTENING"}

        received: list[dict[str, object]] = []

        async def capture(frame: dict[str, object]) -> None:
            received.append(frame)

        relay.attach_client(capture)
        await relay.broadcast({"type": "transcript", "speaker": "USER", "text": "hello"})
        assert received[-1]["type"] == "transcript"

    asyncio.run(run())


def test_system_handler_unknown_action() -> None:
    handler = SystemHandler()
    with pytest.raises(SystemHandlerError):
        handler.execute(ActionEnum.STOP, {})


def test_bridge_main_broadcasts_initial_state(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeIPCClient:
        def __init__(self) -> None:
            self.connected = False
            self.handlers: list[object] = []

        async def connect(self) -> None:
            self.connected = True

        def subscribe(self, handler: object) -> None:
            self.handlers.append(handler)

    class FakeRelay:
        def __init__(self, port: int) -> None:
            self.port = port
            self.session_token = "session-token"
            self.events: list[dict[str, object]] = []

        async def start(self) -> None:
            return None

        async def broadcast(self, frame: dict[str, object]) -> None:
            self.events.append(frame)

        def attach_client(self, handler: object) -> None:
            return None

    monkeypatch.setattr(bridge_main, "load_config", lambda: {"ipc": {"ws_port": 5003}, "tts": {"chunk_chars": 600, "speed": 0.85}})
    monkeypatch.setattr(bridge_main, "IPCClient", FakeIPCClient)
    monkeypatch.setattr(bridge_main, "WSRelay", FakeRelay)
    monkeypatch.setattr(bridge_main, "KokoroBackend", lambda chunk_chars, speed: object())
    monkeypatch.setattr(bridge_main, "SystemHandler", lambda: object())

    async def run() -> None:
        await bridge_main.main()

    asyncio.run(run())
