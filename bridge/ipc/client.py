from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import TypeAlias

from bridge.errors import IPCError

Frame: TypeAlias = dict[str, object]
FrameHandler: TypeAlias = Callable[[Frame], Awaitable[None]]


class IPCClient:
    def __init__(self) -> None:
        self.connected = False
        self._queue: asyncio.Queue[Frame] = asyncio.Queue()
        self._handlers: list[FrameHandler] = []

    async def connect(self) -> None:
        self.connected = True

    async def send(self, frame: Mapping[str, object]) -> None:
        if not self.connected:
            raise IPCError("IPC_DISCONNECTED")
        payload = dict(frame)
        await self._queue.put(payload)
        for handler in list(self._handlers):
            await handler(payload)

    async def receive(self) -> dict[str, object]:
        if not self.connected:
            raise IPCError("IPC_DISCONNECTED")
        return await self._queue.get()

    async def close(self) -> None:
        self.connected = False

    def subscribe(self, handler: FrameHandler) -> None:
        self._handlers.append(handler)
