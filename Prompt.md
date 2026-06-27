\# OkComputer — Codex Autonomous Build Prompt v0.5



> \*\*Execution model:\*\* You are an autonomous coding agent. Work through every

> phase sequentially without stopping for clarification. Record every

> non-obvious decision in `DECISIONS.md` with a one-line rationale. Do not

> emit partial implementations — each file must compile/parse/lint cleanly

> before moving to the next.



\---



\## Global Constraints



These rules are absolute and override any per-phase instruction.



1\. \*\*Zero paid services.\*\* Every library, binary, model, and API must be

&#x20;  free and open-source. No cloud STT, TTS, or LLM endpoints.

2\. \*\*Zero model duplication.\*\* All model files are owned and resolved by

&#x20;  `CppLmmModelStore`. OkComputer never downloads, copies, or stores models

&#x20;  itself. Any code path that previously referenced a local `models/` path

&#x20;  must call `ModelStore::ResolveModelPath()` or `ensure\_models.py` instead.

3\. \*\*Single source of truth.\*\* All runtime behaviour is driven by

&#x20;  `okcomputer.config.json`. No hardcoded paths, ports, model names, or

&#x20;  voice IDs anywhere in the codebase.

4\. \*\*Pinned versions.\*\* Every dependency must be pinned to an exact version.

&#x20;  No `>=`, `\~=`, `^`, or `\*` version specifiers.

5\. \*\*Typed everywhere.\*\* C++23 with `std::expected<T,E>` for fallible

&#x20;  operations. Python with typed signatures; `mypy --strict` must pass.

&#x20;  TypeScript strict mode; ESLint zero warnings; no `any`.

6\. \*\*Platform tags.\*\* Every platform-conditional code path must be marked:

&#x20;  `// \[WIN32]`, `// \[LINUX]`, `// \[MACOS]`.

7\. \*\*Warnings are errors.\*\* C++: `-Wall -Wextra -Werror`. Zero warnings policy.

8\. \*\*Tests are written against contracts, not implementation.\*\* No test file

&#x20;  may import an implementation module directly — only the public interface

&#x20;  defined in `CONTRACTS.md`.

9\. \*\*Audio pipeline interop.\*\* The C++ `AudioCapture` component captures in

&#x20;  `float32`. The C++ `KeywordDetector` must convert these frames to 16-bit

&#x20;  signed PCM (`int16\_t`) mono before passing them to the native Vosk

&#x20;  processing loop or over IPC. The Python bridge `vosk\_backend.py` explicitly

&#x20;  expects this converted `int16\_t` stream to bypass runtime translation

&#x20;  overhead.

10\. \*\*Non-blocking system calls.\*\* Any C++ interface method wrapping an IPC

&#x20;   operation (such as `ITTSEngine::Speak`) must return

&#x20;   `std::expected<void, E>` immediately upon successful serialization and

&#x20;   delivery to the local IPC channel. It must never block the calling

&#x20;   execution loop during the remote operation's lifecycle.

11\. \*\*Config read resiliency.\*\* To eliminate race conditions during

&#x20;   text-editor save cycles, the C++ configuration watcher must sleep 50 ms

&#x20;   and perform exactly one retry pass if an initial file lock or read

&#x20;   operation fails, before reverting to the last valid cache.



\---



\## Repository Layout



Create this layout before touching anything else.



```

OkComputer/

├── CONTRACTS.md                  # generated in Phase A — never modified after

├── DECISIONS.md                  # append-only log of every non-obvious choice

├── okcomputer.config.json        # canonical runtime config (see schema below)

├── okcomputer.config.schema.json # JSON Schema for validation

│

├── core/                         # C++23 — keyword detection, routing, IPC, TTS

│   ├── include/

│   ├── src/

│   └── CMakeLists.txt

│

├── bridge/                       # Python 3.11+ — STT, TTS, LLM, system control

│   ├── stt/

│   │   ├── vosk\_backend.py       # wake-word detection only (int16)

│   │   └── whisper\_backend.py    # post-wake transcription (faster-whisper)

│   ├── tts/

│   │   ├── kokoro\_backend.py     # primary TTS (Kokoro ONNX, streaming)

│   │   └── espeak\_backend.py     # fallback TTS

│   ├── llm/

│   │   └── router.py             # LLM routing, context, failover

│   ├── system/

│   │   └── handler.py            # OS command dispatch

│   ├── ipc/

│   │   └── client.py             # IPC connection to core

│   ├── ws\_relay.py               # WebSocket relay + static file server

│   └── main.py                   # asyncio entry point

│

├── webapp/                       # TypeScript + React 19 + Vite 5 + Tailwind v4

│   ├── src/

│   │   ├── components/

│   │   ├── store/

│   │   └── main.tsx

│   ├── package.json

│   └── vite.config.ts

│

├── service/

│   ├── win/                      # Windows Service wrapper (C++)

│   ├── linux/                    # systemd unit file

│   ├── macos/                    # launchd plist

│   └── OkComputerService.ps1     # PS7 shim (no-admin fallback)

│

├── third\_party/

│   └── CppLmmModelStore/         # git submodule

│

├── tests/

│   ├── unit/

│   │   ├── core/                 # GTest 1.14.0

│   │   ├── bridge/               # pytest 8.1.0

│   │   └── webapp/               # Vitest 1.4.0

│   ├── functional/               # pytest + Playwright 1.43.0

│   └── integration/              # pytest

│

├── logs/                         # runtime logs — git-ignored

└── scripts/

&#x20;   ├── setup.ps1                 # Win11: prerequisites + submodule + pip + pnpm

&#x20;   ├── build.ps1

&#x20;   └── run.ps1

```



\---



\## Configuration Schema — `okcomputer.config.json`



```jsonc

{

&#x20; "$schema": "./okcomputer.config.schema.json",

&#x20; "version": "1",



&#x20; // ── Wake word ──────────────────────────────────────────────────────────

&#x20; "wake\_word": "ok computer",

&#x20; "wake\_word\_sensitivity": 0.5,

&#x20; "confirm\_before\_execute": true,

&#x20; "confirmation\_phrase": "doing that now",

&#x20; "privacy\_mode\_phrase": "stop listening",

&#x20; "resume\_phrase": "start listening",



&#x20; // ── Conversation ───────────────────────────────────────────────────────

&#x20; "conversation": {

&#x20;   "context\_turns": 6,

&#x20;   "max\_history": 16,

&#x20;   "keep\_recent": 8,

&#x20;   "max\_memory\_chars": 1500,

&#x20;   "reset\_after\_silence\_seconds": 120

&#x20; },



&#x20; // ── STT ────────────────────────────────────────────────────────────────

&#x20; // Vosk: wake-word spotting only (low CPU, streaming, int16)

&#x20; // faster-whisper: post-wake full transcription (accuracy)

&#x20; "stt": {

&#x20;   "wake\_backend": "vosk",

&#x20;   "vosk\_model\_name": "vosk-model-small-en-us-0.15",

&#x20;   "transcribe\_backend": "faster-whisper",

&#x20;   "whisper\_model\_name": "faster-whisper-small-en",

&#x20;   "language": "en",

&#x20;   "silence\_seconds": 3.0

&#x20; },



&#x20; // ── TTS ────────────────────────────────────────────────────────────────

&#x20; // Primary: Kokoro ONNX (neural, multi-voice, sentence-streaming)

&#x20; // Fallback: espeak-ng (subprocess)

&#x20; "tts": {

&#x20;   "backend": "kokoro",

&#x20;   "kokoro\_model\_name": "kokoro-v0\_19",

&#x20;   "voice": "af\_nicole",

&#x20;   "speed": 0.85,

&#x20;   "chunk\_chars": 600,

&#x20;   "live\_transcription": true,

&#x20;   "retroactive\_transcription": true,

&#x20;   "transcript\_retention\_turns": 32,

&#x20;   "fallback\_backend": "espeak",

&#x20;   "espeak\_voice": "en-us",

&#x20;   "espeak\_speed": 160

&#x20; },



&#x20; // ── LLM ────────────────────────────────────────────────────────────────

&#x20; // primary\_endpoint: NodeGLM-5 (wraps llama-server / Ollama)

&#x20; // fallback\_endpoint: CppLmmModelStore direct endpoint

&#x20; "llm": {

&#x20;   "primary\_endpoint": "http://localhost:5001/v1",

&#x20;   "primary\_model": "qwen2.5-coder:7b",

&#x20;   "fallback\_endpoint": "http://localhost:5002/v1",

&#x20;   "fallback\_model": "llama3.2:3b",

&#x20;   "system\_prompt": "You are a concise voice assistant. Reply in one or two plain sentences. No markdown.",

&#x20;   "timeout\_seconds": 8,

&#x20;   "max\_tokens": 150,

&#x20;   "temperature": 0.4

&#x20; },



&#x20; // ── Audio ──────────────────────────────────────────────────────────────

&#x20; "audio": {

&#x20;   "input\_device": "default",

&#x20;   "output\_device": "default",

&#x20;   "sample\_rate": 16000,

&#x20;   "channels": 1,

&#x20;   "chunk\_ms": 30

&#x20; },



&#x20; // ── Model store ────────────────────────────────────────────────────────

&#x20; // All paths resolved through CppLmmModelStore.

&#x20; // home\_override: leave empty to use DEEPSEEK\_MODEL\_HOME env var.

&#x20; "model\_store": {

&#x20;   "home\_override": "",

&#x20;   "auto\_ensure\_on\_missing": true,

&#x20;   "models": \[

&#x20;     {

&#x20;       "name": "vosk-model-small-en-us-0.15",

&#x20;       "source": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",

&#x20;       "type": "vosk"

&#x20;     },

&#x20;     {

&#x20;       "name": "faster-whisper-small-en",

&#x20;       "source": "Systran/faster-whisper-small.en",

&#x20;       "type": "huggingface"

&#x20;     },

&#x20;     {

&#x20;       "name": "kokoro-v0\_19",

&#x20;       "source": "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/kokoro-v0\_19.onnx",

&#x20;       "type": "onnx",

&#x20;       "aux": \[

&#x20;         "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/af\_nicole.pt",

&#x20;         "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/af\_bella.pt",

&#x20;         "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/am\_adam.pt",

&#x20;         "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/bm\_george.pt"

&#x20;       ]

&#x20;     }

&#x20;   ]

&#x20; },



&#x20; // ── IPC ───────────────────────────────────────────────────────────────

&#x20; "ipc": {

&#x20;   "pipe\_name": "okcomputer",

&#x20;   "ws\_port": 5003

&#x20; },



&#x20; // ── WebApp ────────────────────────────────────────────────────────────

&#x20; "webapp": {

&#x20;   "port": 5173,

&#x20;   "open\_on\_start": true

&#x20; },



&#x20; // ── Service ───────────────────────────────────────────────────────────

&#x20; "service": {

&#x20;   "auto\_start": true,

&#x20;   "log\_path": "logs/okcomputer.log",

&#x20;   "log\_level": "info",

&#x20;   "restart\_on\_crash": true,

&#x20;   "crash\_cooldown\_seconds": 5,

&#x20;   "max\_restarts": 3

&#x20; }

}

```



\### Config loading rules



\- Validate against `okcomputer.config.schema.json` on startup and on every

&#x20; hot-reload.

\- On validation failure: log the error, retain the last valid state, do not

&#x20; crash.

\- Hot-reload: watch the file for changes; re-validate and apply within 1

&#x20; second without restarting any process.

\- Read resiliency: on file-lock or read failure, sleep 50 ms and retry once

&#x20; before reverting to the last valid cache (see Global Constraint 11).

\- Migration: if `version` is absent or below current, run the migration

&#x20; function, write the upgraded file back, and append a note to `DECISIONS.md`.



\---



\## Phase A — Generate `CONTRACTS.md`



\*\*Do not write any implementation code until `CONTRACTS.md` is complete.\*\*



\### A1. IPC Message Protocol



Define all message types as a tagged union with exact JSON field names and

types. Cover every direction:



\- `core -> bridge`

\- `bridge -> core`

\- `bridge -> webapp`

\- `webapp -> bridge`



Provide a complete example payload for every message type. Include a standard

error envelope:



```json

{

&#x20; "type": "error",

&#x20; "code": "STT\_MODEL\_MISSING",

&#x20; "message": "Vosk model not found at resolved path",

&#x20; "request\_id": "uuid-v4"

}

```



Include TTS transcription events in the protocol. While any assistant response

is being spoken, the Bridge must emit live transcript deltas to the WebApp:

```json

{

&#x20; "type": "transcript_delta",

&#x20; "speaker": "ASSISTANT",

&#x20; "utterance_id": "uuid-v4",

&#x20; "sequence": 3,

&#x20; "text": "spoken text for this chunk",

&#x20; "final": false

}

```

After playback completes, is interrupted, or a client reconnects, the Bridge

must emit or replay a retroactive transcript entry containing the complete

normalised TTS text actually submitted to synthesis:

```json

{

&#x20; "type": "transcript_entry",

&#x20; "speaker": "ASSISTANT",

&#x20; "utterance_id": "uuid-v4",

&#x20; "text": "complete spoken assistant response",

&#x20; "timestamp": "2026-06-26T10:15:30.000Z",

&#x20; "source": "tts",

&#x20; "status": "complete"

}

```

If TTS is interrupted, `status` must be `"interrupted"` and `text` must contain

the full intended spoken response, while live deltas reflect only chunks that

actually began playback.



\*\*Unified Stop sequence specification.\*\* To prevent deadlocks or audio

run-on, specify these exact sequence frames:



1\. `WebApp -> Bridge` (via WS): `{"type": "command", "action": "STOP"}`

2\. `Bridge -> Core` (via IPC socket/pipe): `{"type": "state\_change", "requested\_state": "IDLE"}`

3\. `Core -> Bridge` (via IPC socket/pipe): `{"type": "state\_confirm", "state": "IDLE"}`



The Core's `Stop()` fans out interruption calls to all active child scopes

(TTS, STT, pending LLM) concurrently, then emits `state\_confirm` only after

every scope has acknowledged. The Bridge must not consider the stop complete

until `state\_confirm` is received.



\### A2. C++ Public Interfaces



For each of the following, write the full abstract class declaration with

every method signature, parameter types, return types, and a one-line doc

comment. Use `std::expected<T,E>` for all fallible operations.



\- `IKeywordDetector`

\- `ICommandRouter`

\- `ITTSEngine`

\- `IIPCServer`

\- `IConfigLoader`

\- `IAudioCapture`

\- `IStateMachine`



\### A3. Python Module Contracts



For each module, write the full abstract base class with typed method

signatures, docstrings, and the exact exception types each method may raise.



\- `stt.vosk\_backend.VoskBackend`

\- `stt.whisper\_backend.WhisperBackend`

\- `tts.kokoro\_backend.KokoroBackend`

\- `tts.espeak\_backend.EspeakBackend`

\- `llm.router.LLMRouter`

\- `system.handler.SystemHandler`

\- `ipc.client.IPCClient`

Both TTS backend contracts must expose typed transcript callbacks for

`on_transcript_delta(utterance_id: str, sequence: int, text: str, final: bool)`

and `on_transcript_entry(utterance_id: str, text: str, status: Literal["complete",

"interrupted"])`. These callbacks are the source of live and retroactive

assistant transcript events; callers must receive them even when the backend

falls back from Kokoro to espeak.



\### A4. TypeScript/React Contracts



\- Full Zustand store shape as a TypeScript interface.

\- WebSocket message types as a discriminated union.

\- Include `transcript_delta` and `transcript_entry` variants in the WebSocket

&#x20; discriminated union. The store must merge deltas by `utterance_id` for live

&#x20; display and replace them with the final retroactive `transcript_entry` when

&#x20; received.

\- Props interface for every React component.



\### A5. Command Registry



List every built-in system command with: `name`, `trigger\_phrases`,

`action\_enum`, `parameters`, `confirmation\_text`, `platforms\_supported`.



Required minimum:



| Enum | Example trigger phrases |

|---|---|

| `VOLUME\_UP` | "volume up", "louder", "turn it up" |

| `VOLUME\_DOWN` | "volume down", "quieter", "turn it down" |

| `VOLUME\_MUTE` | "mute", "silence" |

| `VOLUME\_UNMUTE` | "unmute", "sound on" |

| `MEDIA\_PAUSE` | "pause", "stop music" |

| `MEDIA\_RESUME` | "resume", "play", "unpause" |

| `MEDIA\_NEXT` | "next track", "skip" |

| `MEDIA\_PREVIOUS` | "previous track", "go back" |

| `APP\_OPEN` | "open \[app]", "launch \[app]" |

| `APP\_CLOSE` | "close \[app]", "quit \[app]" |

| `SCREENSHOT` | "take a screenshot", "screenshot" |

| `PRIVACY\_MODE\_ON` | configured via `privacy\_mode\_phrase` |

| `PRIVACY\_MODE\_OFF` | configured via `resume\_phrase` |

| `SYSTEM\_SLEEP` | "sleep", "go to sleep" |

| `SYSTEM\_LOCK` | "lock", "lock the screen" |



\### A6. Error Catalogue



Every named error code used anywhere in the system, its meaning, and the

automatic recovery action taken.



\### A7. Dependency Manifest



Every external dependency with: `name`, `exact\_version`, `license`,

`purpose`, `source`.



\---



\## Phase B — Implementation



Implement in this exact order. Each step must be complete and clean before

starting the next.



\---



\### B1. Setup Scripts



`scripts/setup.ps1` must:



1\. Check for: `cmake >= 3.28`, `python >= 3.11`, `node >= 20`, `pnpm >= 9`.

&#x20;  On any failure: print the exact install command and exit with code 1.

2\. Clone CppLmmModelStore as a git submodule:

&#x20;  ```powershell

&#x20;  git submodule add https://github.com/cschladetsch/CppLmmModelStore \\

&#x20;      third\_party/CppLmmModelStore

&#x20;  git submodule update --init --recursive

&#x20;  ```

3\. Set `DEEPSEEK\_MODEL\_HOME` persistently:

&#x20;  - Win11: `\[Environment]::SetEnvironmentVariable` in user scope + update

&#x20;    PowerShell profile.

&#x20;  - Default:

&#x20;    - Win11: `%LOCALAPPDATA%\\OkComputer\\models`

4\. Run `python3 third\_party/CppLmmModelStore/scripts/ensure\_models.py` for

&#x20;  each model listed in `model\_store.models`. OkComputer never fetches models

&#x20;  itself — this script is the only downloader.

5\. `pip install -r bridge/requirements.txt`

6\. `cd webapp \&\& pnpm install --frozen-lockfile`

7\. Print: `"Setup complete. Run scripts/build.ps1 to build."`



\---



\### B2. Core (C++23)



Implement all interfaces from `CONTRACTS.md §A2` exactly.



\#### `core/src/Config.hpp` / `Config.cpp`



\- Load and watch `okcomputer.config.json` using `nlohmann/json 3.11.3`.

\- Validate against schema on load and on every hot-reload.

\- Typed getter: `Config::get<T>(std::string\_view key)`.

\- On invalid config: emit `ConfigError`, continue with last valid state.

\- On file-lock/read failure: sleep 50 ms, retry exactly once, then revert to

&#x20; last valid cache (Global Constraint 11).



\#### `core/src/AudioCapture.hpp` / `AudioCapture.cpp` `\[WIN32]\[LINUX]\[MACOS]`



\- `miniaudio 0.11.21` single-header.

\- Capture at `config.audio.sample\_rate`, `channels`, `chunk\_ms` in `float32`.

\- Convert internally from `float32` to `int16\_t` mono frames.

\- Emit chunks as `std::span<const int16\_t>` via callback (Global Constraint 9).



\#### `core/src/KeywordDetector.hpp` / `KeywordDetector.cpp`



\- Vosk C API (`libvosk`) for always-on keyword spotting only.

\- Consume the `int16\_t` stream from `AudioCapture` directly — no float

&#x20; reconversion.

\- On wake word match (score > `wake\_word\_sensitivity`): emit `OnWakeWord`,

&#x20; enter `SUPPRESSED` state.

\- In `SUPPRESSED` state: ignore all audio until `CommandRouter` signals

&#x20; `OnCommandComplete`.

\- Privacy mode: on `PRIVACY\_MODE\_ON`, enter `PRIVACY` state; only listen for

&#x20; `resume\_phrase` on a second lightweight Vosk instance. On match: emit

&#x20; `OnPrivacyModeOff`, return to `IDLE`.



\#### `core/src/CommandRouter.hpp` / `CommandRouter.cpp`



\- Step 1: strip wake word prefix from transcript.

\- Step 2: exact match against command registry.

\- Step 3: fuzzy match (Levenshtein distance <= 2).

\- Step 4: if no match, classify as `GENERAL\_QUERY`.

\- Step 5: if `confirm\_before\_execute`, call TTS with `confirmation\_phrase`.

\- Step 6: dispatch via IPC to bridge.

\- Maintain conversation history ring buffer of `context\_turns` entries.

\- History compression: when `len(history) > max\_history`, pass oldest

&#x20; `(max\_history - keep\_recent)` entries to the LLM for summarisation; store

&#x20; result as `memory\_summary`; prepend to every subsequent LLM system prompt.

&#x20; Cap the summary at `max\_memory\_chars`, trimming at a sentence boundary.

\- Reset context after `reset\_after\_silence\_seconds` of silence.



\#### `core/src/TTS.hpp` / `TTS.cpp` `\[WIN32]\[LINUX]\[MACOS]`



\- Thin C++ wrapper spawning and interfacing with the Python bridge TTS

&#x20; endpoint via IPC.

\- `std::expected<void, TTSError> Speak(std::string\_view text)` — returns

&#x20; immediately once text is serialized and delivered to the IPC channel; never

&#x20; blocks on synthesis (Global Constraint 10).

\- `bool Interrupt()` — signals the bridge to stop current synthesis

&#x20; immediately.

\- Actual synthesis lives in `bridge/tts/kokoro\_backend.py`; this class owns

&#x20; only the IPC contract.



\#### `core/src/IPCServer.hpp` / `IPCServer.cpp` `\[WIN32]\[LINUX]\[MACOS]`



\- Win11: named pipe `\\\\.\\pipe\\okcomputer`.

\- Linux/macOS: Unix domain socket `/tmp/okcomputer.sock`.

\- Protocol: newline-delimited JSON per `CONTRACTS.md §A1`.

\- Async: one `std::jthread` per connection; max 4 connections.



\#### `core/src/StateMachine.hpp` / `StateMachine.cpp`



States: `IDLE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `PRIVACY`, `ERROR`.



\- All transitions logged at `info` level.

\- On `ERROR`: attempt self-recovery after `crash\_cooldown\_seconds`, max

&#x20; `max\_restarts` times, then emit `FatalError` and request service restart.

\- \*\*Unified Stop:\*\* a single `Stop()` method halts TTS, STT recording, and any

&#x20; pending LLM call concurrently (not sequentially). All subsystems register a

&#x20; stop handler at startup. `Stop()` emits `state\_confirm` only after every

&#x20; registered handler acknowledges.



\#### `core/CMakeLists.txt`



```cmake

cmake\_minimum\_required(VERSION 3.28)

project(OkComputerCore CXX)

set(CMAKE\_CXX\_STANDARD 23)

set(CMAKE\_CXX\_STANDARD\_REQUIRED ON)

add\_compile\_options(-Wall -Wextra -Werror)



add\_subdirectory(${CMAKE\_SOURCE\_DIR}/../third\_party/CppLmmModelStore

&#x20;                ${CMAKE\_BINARY\_DIR}/CppLmmModelStore)



include(FetchContent)

FetchContent\_Declare(nlohmann\_json

&#x20; GIT\_REPOSITORY https://github.com/nlohmann/json.git

&#x20; GIT\_TAG v3.11.3)

FetchContent\_Declare(googletest

&#x20; GIT\_REPOSITORY https://github.com/google/googletest.git

&#x20; GIT\_TAG v1.14.0)

FetchContent\_MakeAvailable(nlohmann\_json googletest)



add\_library(okcomputer\_core SHARED ${CORE\_SOURCES})

target\_link\_libraries(okcomputer\_core PRIVATE

&#x20; ModelStore::ModelStore nlohmann\_json::nlohmann\_json)



add\_executable(okcomputer\_app src/main.cpp)

target\_link\_libraries(okcomputer\_app PRIVATE okcomputer\_core)

```



\---



\### B3. Bridge (Python 3.11+)



All modules: fully typed, `mypy --strict` clean, no bare `except`.



Implement all interfaces from `CONTRACTS.md §A3` exactly.



\#### `bridge/stt/vosk\_backend.py` — Wake word only



\- Load model via `ModelStore.resolve("vosk-model-small-en-us-0.15")`.

\- Accept the structural `int16` raw PCM stream delivered from core via IPC —

&#x20; no float reconversion (Global Constraint 9).

\- On wake word match: emit `WakeWordEvent` back to core via IPC.

\- No transcription — keyword spotting only.

\- On model load failure: raise `STTInitError`; bridge triggers fallback (log

&#x20; warning, disable wake-word detection, require manual webapp button trigger).



\#### `bridge/stt/whisper\_backend.py` — Post-wake transcription



\- `faster-whisper==1.0.3`, model resolved via

&#x20; `ModelStore.resolve("faster-whisper-small-en")`.

\- VAD: `webrtcvad==2.0.10` energy threshold.

\- Record until silence detected (> `stt.silence\_seconds` of continuous

&#x20; silence after at least 0.5 s of speech).

\- Transcribe the full buffer in one pass.

\- Return `STTResult(text: str, confidence: float)`.



\#### `bridge/tts/kokoro\_backend.py` — Primary TTS



\- `kokoro-onnx==0.4.1`, model resolved via

&#x20; `ModelStore.resolve("kokoro-v0\_19")`.

\- Voice: `config.tts.voice` (default `af\_nicole`).

\- Available voices: `af\_nicole`, `af\_bella`, `af\_sarah`, `af\_sky`,

&#x20; `am\_adam`, `am\_michael`, `bf\_emma`, `bf\_isabella`, `bm\_george`, `bm\_lewis`.



\*\*Streaming architecture (critical):\*\*



```

speak(text: str) -> None

&#x20; 1. Strip all markdown: \*\*, \*, #, `, \_, \~, >, \[](), etc.

&#x20; 2. Split into sentences on \[.!?] boundaries.

&#x20; 3. Split sentences longer than chunk\_chars at that boundary.

&#x20; 4. For each unit:

&#x20;      a. Synthesise -> raw PCM bytes (Kokoro ONNX in-process)

&#x20;      b. Enqueue PCM chunk into asyncio.Queue

&#x20; 5. Consumer coroutine: dequeue chunks, play via sounddevice.

&#x20; 6. Unit 1 plays while units 2..N are still being synthesised.

&#x20; 7. Emit `transcript_delta` when each playback unit begins, preserving

&#x20;    `utterance_id` and monotonically increasing `sequence`.

&#x20; 8. Check stop\_event between every chunk; return immediately if set.

&#x20; 9. Emit one retroactive `transcript_entry` at completion or interruption

&#x20;    using the complete markdown-stripped text submitted to synthesis.

```



\- `interrupt() -> None`: set `stop\_event`; current chunk drains within

&#x20; \~200 ms; producer and consumer both exit.

\- Speed: `config.tts.speed` (float, default `0.85`).

\- Chunk chars: `config.tts.chunk\_chars` (int, default `600`).

\- Live transcription: when `config.tts.live\_transcription` is true, publish

&#x20; assistant transcript deltas for each playback unit before audio starts.

\- Retroactive transcription: when `config.tts.retroactive\_transcription` is

&#x20; true, persist and publish final assistant transcript entries for the last

&#x20; `config.tts.transcript\_retention\_turns` TTS utterances, including entries

&#x20; replayed to newly connected WebApp clients.



\#### `bridge/tts/espeak\_backend.py` — Fallback TTS `\[WIN32]\[LINUX]\[MACOS]`



\- Win11/Linux/macOS: `espeak-ng` subprocess.

\- `interrupt()`: `Popen.terminate()`.

\- Emit the same live `transcript_delta` and retroactive `transcript_entry`

&#x20; callbacks as Kokoro so fallback speech is never missing from transcripts.



\#### `bridge/llm/router.py`



\- Maintain conversation history

&#x20; `deque(maxlen=config.conversation.context\_turns)`.

\- Prepend `memory\_summary` (from core's compression pass) to the system prompt

&#x20; when present.

\- Strip all markdown from the response before returning.

\- `POST` to `primary\_endpoint`; on timeout or HTTP error: retry once, then

&#x20; failover to `fallback\_endpoint`.

\- On both failing: return `LLMError("LLM\_UNAVAILABLE")`; bridge calls TTS to

&#x20; speak `"I'm having trouble reaching the language model right now."`.

\- Reset history on `ConversationResetEvent` from core.



\#### `bridge/system/handler.py` `\[WIN32]\[LINUX]\[MACOS]`



Dispatch table keyed on `ActionEnum`. Catch and gracefully handle session

permission faults (headless display omissions, missing `DISPLAY` or

`XAUTHORITY`) by returning `SystemHandlerError` rather than throwing an

unhandled exception.



| Platform | Volume | Media keys | App open/close | Screenshot | Sleep | Lock |

|---|---|---|---|---|---|---|

| Win11 | `pycaw==20240210` | `ctypes` + `win32con` VK codes | `subprocess` + `psutil==5.9.8` | `Pillow==10.2.0` `ImageGrab` | `ctypes SetSuspendState` | `ctypes LockWorkStation` |

| Linux | `pactl` subprocess | `dbus-python==1.3.2` MPRIS2 | `subprocess` + `psutil` | `scrot` subprocess | `systemctl suspend` | `loginctl lock-session` |

| macOS | `osascript` subprocess | `osascript` subprocess | `subprocess` + `psutil` | `screencapture` subprocess | `pmset sleepnow` | `osascript` subprocess |



\#### `bridge/ipc/client.py`



\- Connect to core IPC (named pipe / Unix socket per platform).

\- Async send/receive JSON frames.

\- Reconnect with exponential backoff on disconnect (max 30 s).



\#### `bridge/ws\_relay.py`



\- `websockets==12.0` server on `config.ipc.ws\_port`.

\- Relay all IPC events to connected WebSocket clients in real time.

\- Maintain an in-memory ring buffer of assistant TTS `transcript_entry`

&#x20; events sized by `config.tts.transcript\_retention\_turns`; replay it to each

&#x20; WebApp client immediately after connection before streaming new deltas.

\- Serve `webapp/dist/` as static files on the same port under `/`.

\- Session token generated at startup, logged to console only — no network

&#x20; exposure.



\#### `bridge/main.py`



\- `asyncio.run()` entry point.

\- Load and validate config first; abort with a clear error if invalid.

\- Start: `IPCClient`, STT pipeline, TTS engine, `SystemHandler`, `WSRelay`.

\- Wire all event handlers.

\- Register `Stop` with the state machine to halt TTS + STT + pending LLM calls

&#x20; concurrently.

\- Graceful shutdown on `SIGINT`/`SIGTERM`: drain queues, close IPC, flush logs.



\#### `bridge/requirements.txt` (exact versions)



```

vosk==0.3.45

faster-whisper==1.0.3

webrtcvad==2.0.10

kokoro-onnx==0.4.1

pycaw==20240210

pywin32==306

psutil==5.9.8

Pillow==10.2.0

sounddevice==0.4.6

websockets==12.0

dbus-python==1.3.2

aiohttp==3.9.3

aiofiles==23.2.1

```



\---



\### B4. WebApp (TypeScript + React 19 + Vite 5 + Tailwind v4)



Implement all interfaces from `CONTRACTS.md §A4` exactly. Account for React 19

concurrent hydration: do not read from the Zustand store during render in a way

that assumes synchronous WebSocket state; gate first paint on a `connected`

flag.



\#### `webapp/package.json` (pinned versions)



```json

{

&#x20; "dependencies": {

&#x20;   "react": "19.0.0",

&#x20;   "react-dom": "19.0.0",

&#x20;   "zustand": "5.0.1"

&#x20; },

&#x20; "devDependencies": {

&#x20;   "vite": "5.2.0",

&#x20;   "@vitejs/plugin-react": "4.2.1",

&#x20;   "tailwindcss": "4.0.0",

&#x20;   "typescript": "5.4.5",

&#x20;   "vitest": "1.4.0",

&#x20;   "@testing-library/react": "15.0.2",

&#x20;   "playwright": "1.43.0",

&#x20;   "eslint": "9.1.0"

&#x20; }

}

```



\#### Components



\*\*`<WakeWordStatus />`\*\* — five distinct visual states:



| State | Visual |

|---|---|

| `IDLE` | Grey slow pulse |

| `LISTENING` | Green fast pulse |

| `PROCESSING` | Amber spinner |

| `SPEAKING` | Blue wave animation (CSS only) |

| `PRIVACY` | Red lock icon, persistent pulse |



`aria-label` updates with the state name on every transition.



\*\*`<TranscriptFeed />`\*\*



\- Scrolling feed, auto-scroll to bottom on new entry.

\- Each entry: timestamp, speaker (`USER` / `ASSISTANT`), text.

\- User: right-aligned. Assistant: left-aligned.

\- Live assistant TTS deltas update a single in-progress assistant row keyed by

&#x20; `utterance_id` without duplicating text.

\- Retroactive assistant TTS entries replace any in-progress row with the final

&#x20; complete entry and are shown after reconnect even if playback occurred while

&#x20; the WebApp was disconnected.

\- Monospace font (JetBrains Mono).



\*\*`<CommandPalette />`\*\*



\- List all commands from the registry with trigger phrases.

\- Click any command to send it immediately via WebSocket.

\- Filter input narrows the list in real time.



\*\*`<LLMStatus />`\*\*



\- Primary endpoint: health dot (green/red) + model name + last latency ms.

\- Fallback endpoint: same.

\- Last 5 query latencies as an inline SVG sparkline — no charting library.



\*\*`<SettingsPanel />`\*\*



\- Render all `okcomputer.config.json` fields as typed form controls.

\- Save sends updated config via WebSocket; bridge writes to disk.

\- Show validation errors inline per field.

\- "Reload Config" button forces hot-reload.



\*\*`<PrivacyBadge />`\*\*



\- Persistent top-right badge.

\- Normal: `LISTENING` (green).

\- Privacy mode: `PRIVACY MODE` (red, pulsing, cannot be dismissed by user).



\*\*`<StopButton />`\*\*



\- Absolute-positioned, always visible, always enabled.

\- Sends `{"type": "command", "action": "STOP"}` via WebSocket.

\- Bridge halts TTS + STT + pending LLM call concurrently per the Unified Stop

&#x20; sequence.



\#### Styling rules



\- Dark mode only.

\- Palette: `background #0d0d0d`, `surface #1a1a1a`, `accent #e53e3e`.

\- Font: JetBrains Mono (self-hosted fallback — no Google Fonts CDN).

\- No external component libraries (no shadcn, no MUI, no Radix).

\- All animations via CSS only — no JS animation libraries.



\---



\### B5. Service Wrapper



\#### `service/win/OkComputerService.cpp` `\[WIN32]`



\- Windows Service via `CreateService` / `StartServiceCtrlDispatcher`.

\- On `SERVICE\_START`: launch `okcomputer\_app.exe` + `python bridge/main.py`

&#x20; as child processes; redirect stdout/stderr to `config.service.log\_path`.

\- On `SERVICE\_CONTROL\_STOP`: send `CTRL\_C\_EVENT`, wait 5 s, then

&#x20; `TerminateProcess` if still running.

\- On `SERVICE\_CONTROL\_PAUSE` / `CONTINUE`: forward to children via IPC.

\- On child crash: restart after `crash\_cooldown\_seconds`, max `max\_restarts`

&#x20; times; then `SERVICE\_STOPPED` with a non-zero exit code.

\- Install/uninstall: `OkComputerService.exe --install` / `--uninstall`.



\#### `service/linux/okcomputer.service`



```ini

\[Unit]

Description=OkComputer Voice Assistant

After=network.target sound.target



\[Service]

Type=simple

ExecStart=/usr/local/bin/okcomputer-launch.sh

Restart=on-failure

RestartSec=5

StandardOutput=append:/var/log/okcomputer.log

StandardError=append:/var/log/okcomputer.log



\[Install]

WantedBy=default.target

```



\#### `service/macos/com.okcomputer.plist`



Standard `KeepAlive` launchd plist targeting `pwsh -File scripts/run.ps1`.



\#### `service/OkComputerService.ps1` `\[WIN32 PS7 no-admin fallback]`



`Register-ScheduledTask` triggered at logon; action:

`pwsh -File scripts/run.ps1`.



\---



\### B6. Tests



\*\*Rule:\*\* every test is written against `CONTRACTS.md` interfaces. No test

imports an implementation module directly.



\#### Unit — Core (GTest 1.14.0)



\*\*`test\_config.cpp`\*\*

\- Valid JSON loads without error.

\- Invalid JSON emits `ConfigError` and retains last valid state.

\- Missing required field uses safe default and logs warning.

\- Version migration upgrades correctly.

\- Hot-reload: modify file on disk; assert updated value visible within 500 ms.

\- Read resiliency: simulate a mid-save lock; assert exactly one retry then

&#x20; cache fallback.



\*\*`test\_audio\_capture.cpp`\*\*

\- Feed a known float32 sine buffer; assert emitted frames are `int16\_t` mono.

\- Assert sample-rate and channel conversion match config.



\*\*`test\_keyword\_detector.cpp`\*\*

\- Feed PCM silence: assert no `OnWakeWord`.

\- Feed PCM containing "ok computer": assert `OnWakeWord` fires exactly once.

\- While `SUPPRESSED`: feed wake word again; assert `OnWakeWord` does not fire.

\- Privacy mode: feed `resume\_phrase`; assert `OnPrivacyModeOff` fires.



\*\*`test\_command\_router.cpp`\*\* — table-driven, minimum 20 rows covering:

\- Exact system command matches.

\- Fuzzy matches (Levenshtein <= 2).

\- General query passthrough.

\- Wake word prefix stripping.

\- Context reset after silence.

\- Memory compression triggers at `max\_history`.



\*\*`test\_tts.cpp`\*\*

\- Mock bridge IPC: assert correct `Speak` message sent.

\- Assert `Speak` returns before synthesis completes (non-blocking).

\- `Interrupt()`: assert stop signal sent within 50 ms.



\*\*`test\_ipc\_server.cpp`\*\*

\- Connect client; send JSON frame; assert echoed correctly.

\- Send malformed JSON; assert error envelope returned.

\- Disconnect client; assert server remains healthy.



\*\*`test\_state\_machine.cpp`\*\*

\- All valid state transitions succeed.

\- Invalid transitions return error.

\- `Stop()` fans out to all registered handlers; `state\_confirm` emitted only

&#x20; after all acknowledge.



\#### Unit — Bridge (pytest 8.1.0)



\*\*`test\_vosk\_backend.py`\*\*

\- Feed known int16 audio fixture; assert `WakeWordEvent` emitted.

\- Feed silence; assert no event.

\- Model missing: assert `STTInitError` raised.



\*\*`test\_whisper\_backend.py`\*\*

\- Feed known audio fixture; assert correct transcript returned.

\- VAD: silence detection triggers result emission.

\- Model missing: assert `STTInitError` raised.



\*\*`test\_kokoro\_backend.py`\*\*

\- `speak()`: mock Kokoro ONNX; assert text synthesised sentence by sentence.

\- Markdown stripped before synthesis: `\*\*bold\*\*` becomes `bold`.

\- Live transcription: assert one `transcript_delta` emitted per playback unit

&#x20; with stable `utterance_id` and increasing `sequence`.

\- Retroactive transcription: assert one final `transcript_entry` emitted with

&#x20; the full markdown-stripped text and `status = "complete"`.

\- `interrupt()`: assert `stop\_event` is set; assert consumer exits.

\- Interrupted transcription: assert final `transcript_entry` has

&#x20; `status = "interrupted"` and contains the full intended spoken response.

\- Long text split at `chunk\_chars` boundary.



\*\*`test\_llm\_router.py`\*\*

\- Mock HTTP server returns valid response: assert markdown stripped.

\- Timeout: assert failover to fallback triggered.

\- Both endpoints fail: assert `LLMError("LLM\_UNAVAILABLE")` returned.

\- Context maintained across 6 turns.

\- Context resets on `ConversationResetEvent`.

\- `memory\_summary` prepended to system prompt when present.



\*\*`test\_system\_handler.py`\*\*

\- Each `ActionEnum`: mock OS call; assert correct backend called with correct

&#x20; args on the correct platform.

\- Unknown action: assert `SystemHandlerError` raised.

\- Headless Linux (no `DISPLAY`): assert `SystemHandlerError` returned, not

&#x20; an unhandled exception.



\#### Unit — WebApp (Vitest 1.4.0 + React Testing Library)



\- `WakeWordStatus.test.tsx` — all 5 states; `aria-label` updates.

\- `TranscriptFeed.test.tsx` — append entries; auto-scroll; merge live

&#x20; assistant `transcript_delta` messages by `utterance_id`; replace the

&#x20; in-progress row when the retroactive `transcript_entry` arrives.

\- `CommandPalette.test.tsx` — filter; click sends WS message.

\- `LLMStatus.test.tsx` — health dots; sparkline point count.

\- `SettingsPanel.test.tsx` — field render; invalid value shows error; save

&#x20; sends WS message.

\- `StopButton.test.tsx` — always enabled; click sends `STOP` action frame.



\#### Functional (pytest + Playwright)



\*\*`test\_wake\_to\_system\_command.py`\*\*

\- Inject synthetic PCM: `"ok computer volume up"`.

\- Assert: wake word fires → `VOLUME\_UP` dispatched → system handler called →

&#x20; confirmation TTS spoken → state returns to `IDLE`.



\*\*`test\_wake\_to\_general\_query.py`\*\*

\- Inject: `"ok computer what is the capital of france"`.

\- Mock LLM returns `"The capital of France is Paris."`.

\- Assert: routed to `LLMRouter` → TTS speaks response → context updated.

\- Assert: no markdown reaches TTS.



\*\*`test\_conversation\_context.py`\*\*

\- Query 1: `"ok computer who is the prime minister of australia"`.

\- Query 2: `"ok computer how old are they"`.

\- Assert: second LLM request includes first turn in history.



\*\*`test\_memory\_compression.py`\*\*

\- Send `max\_history + 1` queries.

\- Assert: LLM called for summary compression.

\- Assert: `memory\_summary` present in next system prompt.



\*\*`test\_privacy\_mode.py`\*\*

\- Say `privacy\_mode\_phrase` → assert state = `PRIVACY`, wake word suppressed.

\- Say `resume\_phrase` → assert state = `IDLE`, wake word active.



\*\*`test\_stop\_is\_unified.py`\*\*

\- Start TTS speaking a long response.

\- Send the `STOP` frame while TTS is mid-sentence.

\- Assert: full sequence frames exchanged (`command` → `state\_change` →

&#x20; `state\_confirm`).

\- Assert: TTS stops within 300 ms.

\- Assert: any pending LLM call is cancelled.

\- Assert: state returns to `IDLE`.



\*\*`test\_webapp\_reflects\_core\_state.py`\*\* (Playwright)

\- Launch webapp (`pnpm preview`).

\- Simulate `LISTENING` event from bridge via WebSocket.

\- Assert `WakeWordStatus` shows `LISTENING` in DOM within 500 ms.



\*\*`test\_config\_hot\_reload.py`\*\*

\- Modify `wake\_word` in `okcomputer.config.json`.

\- Assert new wake word triggers within 1 second.

\- Assert old wake word no longer triggers.



\#### Integration (pytest)



\*\*`test\_service\_lifecycle.py`\*\*

\- Start service (subprocess).

\- Send IPC ping; assert pong within 2 s.

\- Stop service; assert child processes terminated within 5 s.



\*\*`test\_llm\_failover.py`\*\*

\- Primary endpoint returns 503.

\- Assert fallback receives request within `timeout\_seconds`.

\- Both fail: assert TTS speaks the user-facing error message.



\*\*`test\_model\_store\_no\_duplication.py`\*\*

\- Assert OkComputer never writes to any path outside `DEEPSEEK\_MODEL\_HOME`.

\- Assert model files exist at exactly one location on disk.



\*\*`test\_full\_roundtrip.py`\*\*

\- Inject PCM `"ok computer what year was python created"`.

\- Mock LLM: `"Python was created in 1991."`.

\- Assert: TTS received `"Python was created in 1991."` (no markdown).

\- Assert: live assistant TTS transcript deltas appear in webapp via WebSocket

&#x20; while audio is playing.

\- Assert: final retroactive TTS transcript entry appears in webapp via

&#x20; WebSocket and is replayed after a reconnect.



\---



\### B7. Build Scripts



\#### `scripts/build.ps1` `\[WIN32]`



```powershell

Set-StrictMode -Version Latest

$ErrorActionPreference = "Stop"



cmake -B build/win -S core `

&#x20; -DCMAKE\_BUILD\_TYPE=Release `

&#x20; -DCMAKE\_EXPORT\_COMPILE\_COMMANDS=ON

cmake --build build/win --config Release --parallel

ctest --test-dir build/win --output-on-failure



python -m mypy bridge --strict

python -m pytest tests/unit/bridge tests/unit/core -x -v



Set-Location webapp

pnpm install --frozen-lockfile

pnpm run type-check

pnpm run lint

pnpm run test --run

pnpm run build

Set-Location ..



Write-Host "Build complete."

```



\---



\### B8. Run Scripts



\#### `scripts/run.ps1` `\[WIN32]`



1\. Validate `okcomputer.config.json` against schema; abort on failure.

2\. Start `python bridge/main.py` as a background job; pipe to `logs/bridge.log`.

3\. Start `build/win/Release/okcomputer\_app.exe`; pipe to `logs/core.log`.

4\. If `config.webapp.open\_on\_start`: open

&#x20;  `http://localhost:{config.webapp.port}`.

5\. Print: `"OkComputer running. Say 'Ok Computer' to begin."`.

6\. `Wait-Job` — block until all jobs exit; on any exit, kill siblings.



\---



\## Completion Criteria



All of the following must pass before halting:



\- \[ ] `cmake --build` succeeds with zero warnings

\- \[ ] `ctest --test-dir build/win` passes (all C++ tests)

\- \[ ] `mypy bridge --strict` passes

\- \[ ] `pytest tests/ -x` passes (all Python unit, functional, integration)

\- \[ ] `pnpm test --run` passes (all Vitest tests)

\- \[ ] `pnpm exec playwright test` passes (all E2E tests)

\- \[ ] `scripts/run.ps1` executes without error on Win11

\- \[ ] `"ok computer"` detected from microphone within 3 seconds of speaking

\- \[ ] `"volume up"` increases system volume

\- \[ ] `"what is the capital of france"` returns a spoken TTS response

\- \[ ] Spoken TTS responses produce live transcript deltas and retroactive

&#x20; transcript entries visible in the WebApp, including after reconnect

\- \[ ] No model file exists outside `DEEPSEEK\_MODEL\_HOME`

\- \[ ] `okcomputer.config.json` hot-reload takes effect within 1 second

\- \[ ] Unified Stop halts TTS within 300 ms and returns state to `IDLE`



\---



\## Quick-Start (after setup and build)



\*\*Win11 PowerShell 7+:\*\*



```powershell

git clone https://github.com/cschladetsch/OkComputer

cd OkComputer

.\\s.ps1

```

