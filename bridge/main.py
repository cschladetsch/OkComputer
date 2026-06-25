from __future__ import annotations

import asyncio

from bridge.config import load_config
from bridge.ipc.client import IPCClient
from bridge.system.handler import SystemHandler
from bridge.tts.kokoro_backend import KokoroBackend
from bridge.ws_relay import WSRelay


async def main() -> None:
    config = load_config()
    ipc = IPCClient()
    await ipc.connect()
    relay = WSRelay(int(config["ipc"]["ws_port"]))
    await relay.start()
    _tts = KokoroBackend(int(config["tts"]["chunk_chars"]), float(config["tts"]["speed"]))
    _system = SystemHandler()
    ipc.subscribe(relay.broadcast)
    await relay.broadcast({"type": "state", "state": "IDLE"})
    print(f"Bridge ready. Session token: {relay.session_token}")
    await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
