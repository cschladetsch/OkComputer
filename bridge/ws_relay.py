from __future__ import annotations

import secrets
from collections.abc import Mapping


class WSRelay:
    def __init__(self, port: int) -> None:
        self.port = port
        self.session_token = secrets.token_urlsafe(24)
        self.events: list[dict[str, object]] = []

    async def start(self) -> None:
        return None

    async def broadcast(self, frame: Mapping[str, object]) -> None:
        self.events.append(dict(frame))

    async def stop(self) -> None:
        return None
