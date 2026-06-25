from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ActionEnum(str, Enum):
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    VOLUME_MUTE = "VOLUME_MUTE"
    VOLUME_UNMUTE = "VOLUME_UNMUTE"
    MEDIA_PAUSE = "MEDIA_PAUSE"
    MEDIA_RESUME = "MEDIA_RESUME"
    MEDIA_NEXT = "MEDIA_NEXT"
    MEDIA_PREVIOUS = "MEDIA_PREVIOUS"
    APP_OPEN = "APP_OPEN"
    APP_CLOSE = "APP_CLOSE"
    SCREENSHOT = "SCREENSHOT"
    PRIVACY_MODE_ON = "PRIVACY_MODE_ON"
    PRIVACY_MODE_OFF = "PRIVACY_MODE_OFF"
    SYSTEM_SLEEP = "SYSTEM_SLEEP"
    SYSTEM_LOCK = "SYSTEM_LOCK"
    STOP = "STOP"


@dataclass(frozen=True)
class WakeWordEvent:
    phrase: str
    confidence: float


@dataclass(frozen=True)
class STTResult:
    text: str
    confidence: float


@dataclass(frozen=True)
class SystemResult:
    action: ActionEnum
    success: bool
    message: str


JsonMap = Mapping[str, object]
