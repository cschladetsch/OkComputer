from __future__ import annotations

import asyncio
import json
import signal
import sys
import subprocess
import webbrowser
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast

from bridge.config import load_config
from bridge.config import model_home
from bridge.controller import BridgeController
from bridge.audio_monitor import MicrophoneMonitor
from bridge.ipc.client import IPCClient
from bridge.system.handler import SystemHandler
from bridge.tts.kokoro_backend import KokoroBackend
from bridge.ws_relay import WSRelay

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "okcomputer.config.json"
BRIDGE_LOG = ROOT / "logs" / "bridge.log"
CORE_LOG = ROOT / "logs" / "core.log"
WEBAPP_LOG = ROOT / "logs" / "webapp.log"


@dataclass
class InitializedBridge:
    relay: WSRelay
    microphone: MicrophoneMonitor | None


def load_runtime_config() -> dict[str, object]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("config root must be an object")
    return data


def config_section(config: dict[str, object], name: str) -> dict[str, Any]:
    section = config.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"config section {name} must be an object")
    return cast(dict[str, Any], section)


def python_executable() -> str:
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    return str(venv_python) if venv_python.exists() else sys.executable


def core_executable() -> Path:
    windows = ROOT / "build" / "win" / "Release" / "okcomputer_app.exe"
    unix = ROOT / "build" / "unix" / "okcomputer_app"
    if windows.exists():
        return windows
    return unix


async def spawn(command: Sequence[str], stdout: TextIO, stderr: TextIO) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_exec(*command, stdout=stdout, stderr=stderr, cwd=str(ROOT))


def start_webapp(port: int, log: TextIO) -> subprocess.Popen[Any]:
    webapp_dir = ROOT / "webapp"
    command = [python_executable(), "-m", "http.server", str(port)]
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        return subprocess.Popen(command, stdout=log, stderr=log, cwd=str(webapp_dir / "dist"), creationflags=creationflags)
    return subprocess.Popen(command, stdout=log, stderr=log, cwd=str(webapp_dir / "dist"), start_new_session=True)


async def run() -> None:
    config = load_runtime_config()
    webapp_config = config_section(config, "webapp")
    logs_dir = ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)

    bridge_log = BRIDGE_LOG.open("w", encoding="utf-8")
    core_log = CORE_LOG.open("w", encoding="utf-8")
    webapp_log = WEBAPP_LOG.open("w", encoding="utf-8")
    bridge = await spawn([python_executable(), "-m", "bridge.main"], bridge_log, bridge_log)
    core_path = core_executable()
    if not core_path.exists():
        core_log.write("core executable missing\n")
        core_log.flush()
        bridge.terminate()
        await bridge.wait()
        bridge_log.close()
        core_log.close()
        webapp_log.close()
        raise SystemExit(1)
    core = await spawn([str(core_path)], core_log, core_log)
    webapp_process = start_webapp(int(webapp_config["port"]), webapp_log) if bool(webapp_config.get("open_on_start", False)) else None

    if webapp_process is not None:
        webbrowser.open(f"http://localhost:{int(webapp_config['port'])}")

    print("OkComputer running. Say 'Ok Computer' to begin.")

    stop_event = asyncio.Event()

    def request_stop() -> None:
        stop_event.set()

    running_loop = asyncio.get_running_loop()
    for sig_name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                running_loop.add_signal_handler(sig, request_stop)
            except NotImplementedError:
                pass

    wait_task = asyncio.create_task(stop_event.wait())
    core_task = asyncio.create_task(core.wait())
    bridge_task = asyncio.create_task(bridge.wait())
    waiters = {wait_task, core_task, bridge_task}
    done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)

    stop_event.set()
    for task in pending:
        task.cancel()

    if core.returncode is None:
        core.terminate()
    if bridge.returncode is None:
        bridge.terminate()
    waits = [core.wait(), bridge.wait()]
    await asyncio.gather(*waits, return_exceptions=True)
    bridge_log.close()
    core_log.close()
    webapp_log.close()

    if any(task is core_task or task is bridge_task for task in done):
        raise SystemExit(0)


async def initialize_bridge(start_microphone: bool = False) -> InitializedBridge:
    config = load_config()
    ipc = IPCClient()
    await ipc.connect()
    tts_config = config_section(config, "tts")
    relay = WSRelay(int(config["ipc"]["ws_port"]), int(tts_config.get("transcript_retention_turns", 32)))
    await relay.start()

    async def broadcast_transcript_delta(utterance_id: str, sequence: int, text: str, final: bool) -> None:
        await relay.broadcast(
            {
                "type": "transcript_delta",
                "speaker": "ASSISTANT",
                "utterance_id": utterance_id,
                "sequence": sequence,
                "text": text,
                "final": final,
            }
        )

    async def broadcast_transcript_entry(utterance_id: str, text: str, status: str) -> None:
        await relay.broadcast(
            {
                "type": "transcript_entry",
                "speaker": "ASSISTANT",
                "utterance_id": utterance_id,
                "text": text,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "source": "tts",
                "status": status,
            }
        )

    _tts = KokoroBackend(
        int(tts_config["chunk_chars"]),
        float(tts_config["speed"]),
        on_transcript_delta=broadcast_transcript_delta,
        on_transcript_entry=broadcast_transcript_entry,
        live_transcription=bool(tts_config.get("live_transcription", True)),
        retroactive_transcription=bool(tts_config.get("retroactive_transcription", True)),
    )
    _system = SystemHandler()
    controller = BridgeController(Path("okcomputer.config.json"), relay, _system)
    ipc.subscribe(controller.process_frame)
    await relay.broadcast({"type": "state", "state": "IDLE"})
    microphone: MicrophoneMonitor | None = None
    if start_microphone:
        stt_config = config_section(config, "stt")
        audio_config = config_section(config, "audio")
        microphone = MicrophoneMonitor(
            relay.broadcast,
            model_home(config) / str(stt_config["vosk_model_name"]),
            str(config["wake_word"]),
            int(audio_config["sample_rate"]),
            int(audio_config["channels"]),
        )
        try:
            await microphone.start()
        except Exception as exc:
            await relay.broadcast({"type": "error", "code": "AUDIO_INIT_FAILED", "message": str(exc)})
            microphone = None
    print(f"Bridge ready. Session token: {relay.session_token}")
    await asyncio.sleep(0)
    return InitializedBridge(relay=relay, microphone=microphone)
