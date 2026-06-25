# OkComputer Contracts

This file is the public interface for tests and implementations. Tests must target these contracts rather than private implementation details.

## A1. IPC Message Protocol

All frames are UTF-8 JSON objects with a required `type` field and optional `request_id` as UUID v4 text.

### core -> bridge

- `audio_chunk`: `{ "type": "audio_chunk", "format": "pcm_s16le", "sample_rate": 16000, "channels": 1, "payload_b64": "..." }`
- `wake_word`: `{ "type": "wake_word", "phrase": "ok computer", "score": 0.91, "timestamp_ms": 1710000000000 }`
- `state_confirm`: `{ "type": "state_confirm", "state": "IDLE", "request_id": "uuid-v4" }`
- `conversation_reset`: `{ "type": "conversation_reset", "reason": "silence_timeout" }`
- `memory_summary`: `{ "type": "memory_summary", "summary": "User has been asking about Python history." }`
- `error`: `{ "type": "error", "code": "STT_MODEL_MISSING", "message": "Vosk model not found at resolved path", "request_id": "uuid-v4" }`

### bridge -> core

- `state_change`: `{ "type": "state_change", "requested_state": "IDLE", "request_id": "uuid-v4" }`
- `wake_word_event`: `{ "type": "wake_word_event", "phrase": "ok computer", "confidence": 0.89 }`
- `command_complete`: `{ "type": "command_complete", "action": "VOLUME_UP", "success": true }`
- `tts_started`: `{ "type": "tts_started", "text": "Turning it up." }`
- `tts_finished`: `{ "type": "tts_finished", "interrupted": false }`
- `error`: `{ "type": "error", "code": "IPC_DISCONNECTED", "message": "Core IPC channel closed", "request_id": "uuid-v4" }`

### bridge -> webapp

- `state`: `{ "type": "state", "state": "LISTENING" }`
- `transcript`: `{ "type": "transcript", "speaker": "USER", "text": "volume up", "timestamp": "2026-06-25T00:00:00Z" }`
- `llm_status`: `{ "type": "llm_status", "primary": { "healthy": true, "model": "qwen2.5-coder:7b", "latency_ms": 93 }, "fallback": { "healthy": false, "model": "llama3.2:3b", "latency_ms": null }, "latencies_ms": [93, 101] }`
- `config`: `{ "type": "config", "config": { "version": "1" } }`
- `validation_error`: `{ "type": "validation_error", "field": "audio.sample_rate", "message": "must be positive" }`
- `error`: `{ "type": "error", "code": "CONFIG_INVALID", "message": "Config validation failed", "request_id": "uuid-v4" }`

### webapp -> bridge

- `command`: `{ "type": "command", "action": "STOP" }`
- `system_command`: `{ "type": "system_command", "action": "VOLUME_UP", "parameters": {} }`
- `config_update`: `{ "type": "config_update", "config": { "version": "1" } }`
- `reload_config`: `{ "type": "reload_config" }`

### Unified Stop Sequence

1. `WebApp -> Bridge`: `{ "type": "command", "action": "STOP" }`
2. `Bridge -> Core`: `{ "type": "state_change", "requested_state": "IDLE" }`
3. `Core -> Bridge`: `{ "type": "state_confirm", "state": "IDLE" }`

Core `Stop()` fans interruption to TTS, STT, and pending LLM scopes concurrently, then emits `state_confirm` only after every scope acknowledges. Bridge must not consider stop complete until `state_confirm` is received.

## A2. C++ Public Interfaces

```cpp
class IKeywordDetector {
public:
  virtual ~IKeywordDetector() = default;
  virtual std::expected<void, OkError> Start() = 0; // Begin keyword detection.
  virtual std::expected<void, OkError> Stop() = 0; // Stop keyword detection.
  virtual std::expected<void, OkError> AcceptPcm(std::span<const int16_t> frames) = 0; // Process converted mono PCM.
  virtual void OnCommandComplete() = 0; // Leave suppressed state after a command.
};

class ICommandRouter {
public:
  virtual ~ICommandRouter() = default;
  virtual std::expected<RouteResult, OkError> Route(std::string_view text) = 0; // Map text to a command or query.
  virtual std::expected<void, OkError> ResetConversation() = 0; // Clear short-term context.
};

class ITTSEngine {
public:
  virtual ~ITTSEngine() = default;
  virtual std::expected<void, OkError> Speak(std::string_view text) = 0; // Serialize speak request without blocking synthesis.
  virtual std::expected<void, OkError> Interrupt() = 0; // Request speech cancellation.
};

class IIPCServer {
public:
  virtual ~IIPCServer() = default;
  virtual std::expected<void, OkError> Start() = 0; // Start local IPC.
  virtual std::expected<void, OkError> Stop() = 0; // Stop local IPC.
  virtual std::expected<void, OkError> SendJson(std::string_view frame) = 0; // Send one JSON frame.
};

class IConfigLoader {
public:
  virtual ~IConfigLoader() = default;
  virtual std::expected<void, OkError> Load() = 0; // Load and validate config.
  virtual std::expected<void, OkError> Watch() = 0; // Start hot-reload watch.
  virtual std::expected<std::string, OkError> Get(std::string_view key) const = 0; // Read a config value.
};

class IAudioCapture {
public:
  virtual ~IAudioCapture() = default;
  virtual std::expected<void, OkError> Start(AudioCallback callback) = 0; // Start float32 capture and emit int16 mono chunks.
  virtual std::expected<void, OkError> Stop() = 0; // Stop capture.
};

class IStateMachine {
public:
  virtual ~IStateMachine() = default;
  virtual std::expected<void, OkError> Transition(State state) = 0; // Apply a legal state transition.
  virtual std::expected<void, OkError> Stop() = 0; // Fan out interrupt handlers and confirm IDLE.
  virtual State CurrentState() const = 0; // Return current state.
};
```

## A3. Python Module Contracts

Every public method is typed and may raise only its documented domain exception.

- `stt.vosk_backend.VoskBackend`: `start() -> None`, `accept_pcm(frame: bytes) -> WakeWordEvent | None`, `stop() -> None`; raises `STTInitError`, `STTProcessingError`.
- `stt.whisper_backend.WhisperBackend`: `transcribe(pcm: bytes) -> STTResult`; raises `STTInitError`, `STTProcessingError`.
- `tts.kokoro_backend.KokoroBackend`: `async speak(text: str) -> None`, `interrupt() -> None`; raises `TTSError`.
- `tts.espeak_backend.EspeakBackend`: `async speak(text: str) -> None`, `interrupt() -> None`; raises `TTSError`.
- `llm.router.LLMRouter`: `async complete(text: str, memory_summary: str | None = None) -> str`, `reset() -> None`; raises `LLMError`.
- `system.handler.SystemHandler`: `execute(action: ActionEnum, parameters: Mapping[str, object]) -> SystemResult`; raises `SystemHandlerError`.
- `ipc.client.IPCClient`: `async connect() -> None`, `async send(frame: Mapping[str, object]) -> None`, `async receive() -> dict[str, object]`, `async close() -> None`; raises `IPCError`.

## A4. TypeScript/React Contracts

`OkComputerStore` contains `connected`, `state`, `privacyMode`, `transcripts`, `config`, `commands`, `llmStatus`, `validationErrors`, and actions `connect`, `sendCommand`, `saveConfig`, `reloadConfig`.

`WSMessage` is a discriminated union covering `state`, `transcript`, `llm_status`, `config`, `validation_error`, `error`, `command`, `system_command`, `config_update`, and `reload_config`.

Component props:

- `WakeWordStatusProps { state: AssistantState }`
- `TranscriptFeedProps { entries: TranscriptEntry[] }`
- `CommandPaletteProps { commands: CommandDefinition[]; onCommand(action: ActionEnum): void }`
- `LLMStatusProps { status: LLMStatusSnapshot }`
- `SettingsPanelProps { config: OkConfig; errors: Record<string, string>; onSave(config: OkConfig): void; onReload(): void }`
- `PrivacyBadgeProps { privacyMode: boolean }`
- `StopButtonProps { onStop(): void }`

## A5. Command Registry

| name | trigger_phrases | action_enum | parameters | confirmation_text | platforms_supported |
|---|---|---|---|---|---|
| Volume up | volume up; louder; turn it up | VOLUME_UP | step | Turning it up. | win32, linux, macos |
| Volume down | volume down; quieter; turn it down | VOLUME_DOWN | step | Turning it down. | win32, linux, macos |
| Mute | mute; silence | VOLUME_MUTE | none | Muting. | win32, linux, macos |
| Unmute | unmute; sound on | VOLUME_UNMUTE | none | Sound on. | win32, linux, macos |
| Pause media | pause; stop music | MEDIA_PAUSE | none | Pausing. | win32, linux, macos |
| Resume media | resume; play; unpause | MEDIA_RESUME | none | Playing. | win32, linux, macos |
| Next track | next track; skip | MEDIA_NEXT | none | Skipping. | win32, linux, macos |
| Previous track | previous track; go back | MEDIA_PREVIOUS | none | Going back. | win32, linux, macos |
| Open app | open [app]; launch [app] | APP_OPEN | app | Opening app. | win32, linux, macos |
| Close app | close [app]; quit [app] | APP_CLOSE | app | Closing app. | win32, linux, macos |
| Screenshot | take a screenshot; screenshot | SCREENSHOT | path | Taking a screenshot. | win32, linux, macos |
| Privacy on | configured privacy_mode_phrase | PRIVACY_MODE_ON | none | Privacy mode on. | win32, linux, macos |
| Privacy off | configured resume_phrase | PRIVACY_MODE_OFF | none | Listening again. | win32, linux, macos |
| Sleep | sleep; go to sleep | SYSTEM_SLEEP | none | Going to sleep. | win32, linux, macos |
| Lock | lock; lock the screen | SYSTEM_LOCK | none | Locking. | win32, linux, macos |

## A6. Error Catalogue

| code | meaning | automatic recovery |
|---|---|---|
| CONFIG_INVALID | Config failed validation | Keep last valid config and report field errors |
| CONFIG_READ_FAILED | Config read failed after retry | Keep last valid cache |
| STT_MODEL_MISSING | STT model cannot be resolved | Disable wake detection and allow manual trigger |
| STT_PROCESSING_FAILED | STT frame processing failed | Drop frame and continue |
| TTS_UNAVAILABLE | Primary and fallback TTS unavailable | Emit error and keep assistant responsive |
| LLM_UNAVAILABLE | Primary and fallback LLM failed | Speak user-facing outage message |
| IPC_DISCONNECTED | Local IPC channel closed | Reconnect with exponential backoff |
| SYSTEM_PERMISSION_DENIED | OS command lacks session permission | Return handled failure to caller |
| INVALID_STATE_TRANSITION | State transition is illegal | Keep current state |
| STOP_TIMEOUT | Stop handlers did not acknowledge in time | Force IDLE and report error |

## A7. Dependency Manifest

| name | exact_version | license | purpose | source |
|---|---:|---|---|---|
| CMake | 3.28 | BSD-3-Clause | C++ build | https://cmake.org |
| nlohmann/json | 3.11.3 | MIT | JSON config | https://github.com/nlohmann/json |
| miniaudio | 0.11.21 | MIT-0 | Audio capture | https://github.com/mackron/miniaudio |
| Vosk | 0.3.45 | Apache-2.0 | Wake-word STT | https://alphacephei.com/vosk |
| faster-whisper | 1.0.3 | MIT | Transcription | https://github.com/SYSTRAN/faster-whisper |
| webrtcvad | 2.0.10 | MIT | Voice activity detection | https://github.com/wiseman/py-webrtcvad |
| kokoro-onnx | 0.4.1 | Apache-2.0 | Neural TTS | https://github.com/thewh1teagle/kokoro-onnx |
| pycaw | 20240210 | MIT | Windows audio control | https://github.com/AndreMiras/pycaw |
| pywin32 | 306 | PSF | Windows APIs | https://github.com/mhammond/pywin32 |
| psutil | 5.9.8 | BSD-3-Clause | Process control | https://github.com/giampaolo/psutil |
| Pillow | 10.2.0 | HPND | Screenshots | https://python-pillow.org |
| sounddevice | 0.4.6 | MIT | Audio playback | https://python-sounddevice.readthedocs.io |
| websockets | 12.0 | BSD-3-Clause | WebSocket relay | https://websockets.readthedocs.io |
| dbus-python | 1.3.2 | MIT | Linux media control | https://dbus.freedesktop.org |
| aiohttp | 3.9.3 | Apache-2.0 | HTTP client/server | https://docs.aiohttp.org |
| aiofiles | 23.2.1 | Apache-2.0 | Async static files | https://github.com/Tinche/aiofiles |
| React | 19.0.0 | MIT | UI | https://react.dev |
| Vite | 5.2.0 | MIT | Web build | https://vitejs.dev |
| Zustand | 5.0.1 | MIT | Store | https://github.com/pmndrs/zustand |
| Tailwind CSS | 4.0.0 | MIT | Styling | https://tailwindcss.com |
| TypeScript | 5.4.5 | Apache-2.0 | Typed web code | https://www.typescriptlang.org |
| typescript-eslint | 8.0.0 | MIT | TypeScript lint parsing | https://typescript-eslint.io |
| Vitest | 1.4.0 | MIT | Web unit tests | https://vitest.dev |
| Playwright | 1.43.0 | Apache-2.0 | E2E tests | https://playwright.dev |
| @playwright/test | 1.43.0 | Apache-2.0 | E2E runner | https://playwright.dev |
| pytest | 8.1.0 | MIT | Python tests | https://pytest.org |
| mypy | 1.9.0 | MIT | Python type checking | https://mypy-lang.org |
