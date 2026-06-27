from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from bridge.controller import BridgeController
from bridge.audio_monitor import MicrophoneMonitor
from bridge.errors import LLMError, STTInitError, STTProcessingError, SystemHandlerError
from bridge.ipc.client import IPCClient
from bridge.llm.router import LLMRouter
from bridge.models import ActionEnum
from bridge.stt.vosk_backend import VoskBackend
from bridge.system.handler import SystemHandler
from bridge.text import strip_markdown
from bridge.tts.kokoro_backend import KokoroBackend
from bridge.ws_relay import WSRelay
import bridge.runtime as bridge_runtime


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


def test_microphone_monitor_reacts_to_pcm_without_model(tmp_path: Path) -> None:
    async def run() -> None:
        events: list[dict[str, object]] = []

        async def broadcast(frame: dict[str, object]) -> None:
            events.append(frame)

        monitor = MicrophoneMonitor(broadcast, tmp_path / "missing-model", "ok computer", 16000, 1, cooldown_seconds=0)
        monitor._energy_fallback = True
        await monitor.process_pcm(b"\x01\x00")
        assert events[0] == {"type": "state", "state": "LISTENING"}
        assert events[1]["type"] == "transcript"
        assert events[1]["text"] == "microphone activity detected"

    asyncio.run(run())


def test_kokoro_chunks_and_interrupt() -> None:
    async def run() -> None:
        deltas: list[tuple[str, int, str, bool]] = []
        entries: list[tuple[str, str, str]] = []

        async def on_delta(utterance_id: str, sequence: int, text: str, final: bool) -> None:
            deltas.append((utterance_id, sequence, text, final))

        async def on_entry(utterance_id: str, text: str, status: str) -> None:
            entries.append((utterance_id, text, status))

        backend = KokoroBackend(chunk_chars=5)
        await backend.speak("**hello** world.")
        assert backend.spoken_chunks == ["hello", "world", "."]

        instrumented = KokoroBackend(chunk_chars=5, on_transcript_delta=on_delta, on_transcript_entry=on_entry)
        await instrumented.speak("**hello** world.")
        assert [item[1:] for item in deltas] == [(0, "hello", False), (1, "world", False), (2, ".", False)]
        assert len({item[0] for item in deltas}) == 1
        assert entries == [(deltas[0][0], "hello world.", "complete")]

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

        await relay.attach_client(capture)
        await relay.broadcast({"type": "transcript", "speaker": "USER", "text": "hello"})
        assert received[-1]["type"] == "transcript"

    asyncio.run(run())


def test_ws_relay_replays_tts_transcript_entries() -> None:
    async def run() -> None:
        relay = WSRelay(5003, transcript_retention_turns=1)
        await relay.start()
        await relay.broadcast(
            {
                "type": "transcript_entry",
                "speaker": "ASSISTANT",
                "utterance_id": "old",
                "text": "old response",
                "timestamp": "2026-06-26T00:00:00Z",
                "source": "tts",
                "status": "complete",
            }
        )
        await relay.broadcast(
            {
                "type": "transcript_entry",
                "speaker": "ASSISTANT",
                "utterance_id": "new",
                "text": "new response",
                "timestamp": "2026-06-26T00:00:01Z",
                "source": "tts",
                "status": "complete",
            }
        )
        received: list[dict[str, object]] = []

        async def capture(frame: dict[str, object]) -> None:
            received.append(frame)

        await relay.attach_client(capture)
        assert received == [
            {
                "type": "transcript_entry",
                "speaker": "ASSISTANT",
                "utterance_id": "new",
                "text": "new response",
                "timestamp": "2026-06-26T00:00:01Z",
                "source": "tts",
                "status": "complete",
            }
        ]

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
        def __init__(self, port: int, transcript_retention_turns: int = 32) -> None:
            self.port = port
            self.transcript_retention_turns = transcript_retention_turns
            self.session_token = "session-token"
            self.events: list[dict[str, object]] = []

        async def start(self) -> None:
            return None

        async def broadcast(self, frame: dict[str, object]) -> None:
            self.events.append(frame)

        async def attach_client(self, handler: object) -> None:
            return None

    monkeypatch.setattr(
        bridge_runtime,
        "load_config",
        lambda: {
            "ipc": {"ws_port": 5003},
            "tts": {
                "chunk_chars": 600,
                "speed": 0.85,
                "live_transcription": True,
                "retroactive_transcription": True,
                "transcript_retention_turns": 32,
            },
        },
    )
    monkeypatch.setattr(bridge_runtime, "IPCClient", FakeIPCClient)
    monkeypatch.setattr(bridge_runtime, "WSRelay", FakeRelay)
    monkeypatch.setattr(bridge_runtime, "KokoroBackend", lambda *args, **kwargs: object())
    monkeypatch.setattr(bridge_runtime, "SystemHandler", lambda: object())

    async def run() -> None:
        await bridge_runtime.initialize_bridge()

    asyncio.run(run())


def test_bridge_controller_stop_sequence(tmp_path: Path) -> None:
    async def run() -> None:
        relay = WSRelay(5003)
        await relay.start()
        controller = BridgeController(tmp_path / "okcomputer.config.json", relay, SystemHandler())
        await controller.process_frame({"type": "command", "action": "STOP"})
        assert relay.events == [
            {"type": "state_change", "requested_state": "IDLE"},
            {"type": "state_confirm", "state": "IDLE"},
        ]

    asyncio.run(run())


def test_bridge_controller_config_update_and_reload(tmp_path: Path) -> None:
    async def run() -> None:
        relay = WSRelay(5003)
        await relay.start()
        config_path = tmp_path / "okcomputer.config.json"
        config_path.write_text('{"version":"1","wake_word":"ok computer"}', encoding="utf-8")
        controller = BridgeController(config_path, relay, SystemHandler())
        await controller.process_frame({"type": "config_update", "config": {"version": "1", "wake_word": "updated"}})
        await controller.process_frame({"type": "reload_config"})
        assert json.loads(config_path.read_text(encoding="utf-8"))["wake_word"] == "updated"
        assert relay.events[-1]["type"] == "config"

    asyncio.run(run())
