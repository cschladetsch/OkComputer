from __future__ import annotations

import asyncio
from collections.abc import Mapping

from bridge.errors import IPCError


class IPCClient:
    def __init__(self) -> None:
        self.connected = False
        self._queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()

    async def connect(self) -> None:
        self.connected = True

    async def send(self, frame: Mapping[str, object]) -> None:
        if not self.connected:
            raise IPCError("IPC_DISCONNECTED")
        await self._queue.put(dict(frame))

    async def receive(self) -> dict[str, object]:
        if not self.connected:
            raise IPCError("IPC_DISCONNECTED")
        return await self._queue.get()

    async def close(self) -> None:
        self.connected = False
