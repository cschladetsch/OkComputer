from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable, Mapping
from typing import TypeAlias

Frame: TypeAlias = dict[str, object]
FrameHandler: TypeAlias = Callable[[Frame], Awaitable[None]]


class WSRelay:
    def __init__(self, port: int) -> None:
        self.port = port
        self.session_token = secrets.token_urlsafe(24)
        self.events: list[Frame] = []
        self._clients: list[FrameHandler] = []
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def broadcast(self, frame: Mapping[str, object]) -> None:
        payload = dict(frame)
        self.events.append(payload)
        if not self._running:
            return
        for client in list(self._clients):
            await client(payload)

    async def stop(self) -> None:
        self._running = False

    def attach_client(self, handler: FrameHandler) -> None:
        self._clients.append(handler)
