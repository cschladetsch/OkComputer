class OkComputerError(Exception):
    """Base bridge error."""


class STTInitError(OkComputerError):
    """STT model or backend failed to initialize."""


class STTProcessingError(OkComputerError):
    """STT failed while processing audio."""


class TTSError(OkComputerError):
    """TTS failed."""


class LLMError(OkComputerError):
    """LLM routing failed."""


class SystemHandlerError(OkComputerError):
    """System command failed in a handled way."""


class IPCError(OkComputerError):
    """IPC send or receive failed."""
