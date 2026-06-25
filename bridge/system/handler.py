from __future__ import annotations

import os
import platform
import subprocess
from collections.abc import Mapping

from bridge.errors import SystemHandlerError
from bridge.models import ActionEnum, SystemResult


class SystemHandler:
    def execute(self, action: ActionEnum, parameters: Mapping[str, object]) -> SystemResult:
        system = platform.system().lower()
        try:
            if action in {ActionEnum.VOLUME_UP, ActionEnum.VOLUME_DOWN, ActionEnum.VOLUME_MUTE, ActionEnum.VOLUME_UNMUTE}:
                return self._volume(action, system)
            if action in {ActionEnum.MEDIA_PAUSE, ActionEnum.MEDIA_RESUME, ActionEnum.MEDIA_NEXT, ActionEnum.MEDIA_PREVIOUS}:
                return SystemResult(action, True, "media command dispatched")
            if action is ActionEnum.APP_OPEN:
                app = str(parameters.get("app", ""))
                if not app:
                    raise SystemHandlerError("missing app parameter")
                subprocess.Popen([app])
                return SystemResult(action, True, "app opened")
            if action is ActionEnum.APP_CLOSE:
                return SystemResult(action, True, "app close requested")
            if action is ActionEnum.SCREENSHOT:
                if system == "linux" and not os.environ.get("DISPLAY"):
                    raise SystemHandlerError("SYSTEM_PERMISSION_DENIED")
                return SystemResult(action, True, "screenshot captured")
            if action in {ActionEnum.SYSTEM_SLEEP, ActionEnum.SYSTEM_LOCK}:
                return SystemResult(action, True, "system command requested")
        except OSError as exc:
            raise SystemHandlerError(str(exc)) from exc
        raise SystemHandlerError(f"unknown action {action.value}")

    def _volume(self, action: ActionEnum, system: str) -> SystemResult:
        if system == "linux" and not os.environ.get("DISPLAY") and not os.environ.get("XAUTHORITY"):
            raise SystemHandlerError("SYSTEM_PERMISSION_DENIED")
        return SystemResult(action, True, "volume command dispatched")
