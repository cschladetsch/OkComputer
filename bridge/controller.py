from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping

from bridge.config import load_config
from bridge.errors import SystemHandlerError
from bridge.models import ActionEnum
from bridge.system.handler import SystemHandler
from bridge.ws_relay import WSRelay


class BridgeController:
    def __init__(self, config_path: Path, relay: WSRelay, system: SystemHandler) -> None:
        self.config_path = config_path
        self.relay = relay
        self.system = system

    async def process_frame(self, frame: Mapping[str, object]) -> None:
        message_type = str(frame.get("type", ""))
        if message_type == "command" and frame.get("action") == "STOP":
            await self.relay.broadcast({"type": "state_change", "requested_state": "IDLE"})
            await self.relay.broadcast({"type": "state_confirm", "state": "IDLE"})
            return
        if message_type == "config_update":
            await self._save_config(frame)
            return
        if message_type == "reload_config":
            await self.relay.broadcast({"type": "config", "config": load_config(self.config_path)})
            return
        if message_type == "system_command":
            self._dispatch_system_command(frame)

    async def _save_config(self, frame: Mapping[str, object]) -> None:
        config = frame.get("config")
        if not isinstance(config, dict):
            await self.relay.broadcast({"type": "validation_error", "field": "config", "message": "config must be an object"})
            return
        with self.config_path.open("w", encoding="utf-8") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
        await self.relay.broadcast({"type": "config", "config": load_config(self.config_path)})

    def _dispatch_system_command(self, frame: Mapping[str, object]) -> None:
        action_name = str(frame.get("action", ""))
        try:
            action = ActionEnum(action_name)
            parameters = frame.get("parameters")
            mapping = parameters if isinstance(parameters, Mapping) else {}
            self.system.execute(action, mapping)
        except (ValueError, SystemHandlerError) as exc:
            raise SystemHandlerError(str(exc)) from exc
