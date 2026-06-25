from __future__ import annotations

import asyncio
import json
import signal
import sys
import webbrowser
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO, cast

from bridge.config import load_config
from bridge.controller import BridgeController
from bridge.ipc.client import IPCClient
from bridge.system.handler import SystemHandler
from bridge.tts.kokoro_backend import KokoroBackend
from bridge.ws_relay import WSRelay

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "okcomputer.config.json"
BRIDGE_LOG = ROOT / "logs" / "bridge.log"
CORE_LOG = ROOT / "logs" / "core.log"


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


async def run() -> None:
    config = load_runtime_config()
    webapp = config_section(config, "webapp")
    logs_dir = ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)

    bridge_log = BRIDGE_LOG.open("w", encoding="utf-8")
    core_log = CORE_LOG.open("w", encoding="utf-8")
    bridge = await spawn([python_executable(), "-m", "bridge.main"], bridge_log, bridge_log)
    core_path = core_executable()
    if not core_path.exists():
        core_log.write("core executable missing\n")
        core_log.flush()
        bridge.terminate()
        await bridge.wait()
        bridge_log.close()
        core_log.close()
        raise SystemExit(1)
    core = await spawn([str(core_path)], core_log, core_log)

    if bool(webapp.get("open_on_start", False)):
        webbrowser.open(f"http://localhost:{int(webapp['port'])}")

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
    done, pending = await asyncio.wait({wait_task, core_task, bridge_task}, return_when=asyncio.FIRST_COMPLETED)

    stop_event.set()
    for task in pending:
        task.cancel()

    if core.returncode is None:
        core.terminate()
    if bridge.returncode is None:
        bridge.terminate()

    await asyncio.gather(core.wait(), bridge.wait(), return_exceptions=True)
    bridge_log.close()
    core_log.close()

    if any(task is core_task or task is bridge_task for task in done):
        raise SystemExit(0)


async def initialize_bridge() -> None:
    config = load_config()
    ipc = IPCClient()
    await ipc.connect()
    relay = WSRelay(int(config["ipc"]["ws_port"]))
    await relay.start()
    _tts = KokoroBackend(int(config["tts"]["chunk_chars"]), float(config["tts"]["speed"]))
    _system = SystemHandler()
    controller = BridgeController(Path("okcomputer.config.json"), relay, _system)
    ipc.subscribe(controller.process_frame)
    await relay.broadcast({"type": "state", "state": "IDLE"})
    print(f"Bridge ready. Session token: {relay.session_token}")
    await asyncio.sleep(0)
