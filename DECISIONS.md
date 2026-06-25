# Decisions

- 2026-06-25: Use lightweight local contract tests instead of downloading GTest during the initial scaffold so the repository can build without network access.
- 2026-06-25: Keep model resolution delegated to `third_party/CppLmmModelStore/scripts/ensure_models.py` and environment-derived paths to avoid OkComputer-owned model storage.
- 2026-06-25: Provide deterministic bridge fallbacks when optional native audio/model packages are unavailable so imports and contract tests remain runnable on developer machines.
- 2026-06-25: Add `typescript-eslint` as a pinned dev dependency because ESLint 9 cannot parse strict TypeScript/TSX files without a parser.
- 2026-06-25: Add `@playwright/test` alongside `playwright` because the E2E completion command uses the Playwright test-runner binary.
- 2026-06-26: Prefer `.venv/Scripts/python.exe` in PowerShell scripts when present so workspace checks avoid a broken WindowsApps Python shim.
- 2026-06-26: Pass `-C Release` to Windows CTest because Visual Studio multi-config builds cannot run tests without a selected configuration.
- 2026-06-26: Fall back to `corepack pnpm` in PowerShell scripts because Corepack can provide pinned pnpm even when no pnpm shim is on PATH.
- 2026-06-26: Launch the bridge as `python -m bridge.main` so package imports resolve consistently from run scripts.
- 2026-06-26: Validate setup tool minimum versions explicitly so broken shims or too-old tools fail with install guidance.
- 2026-06-26: Resolve Python 3.11+ from known install locations in `setup.ps1` because the WindowsApps `python` shim can remain broken after installation.
- 2026-06-26: Keep C++ config parsing dependency-free for this scaffold while adding nested-key extraction and cache fallback so the local build remains network-independent.
- 2026-06-26: Expose LLM mock endpoint attempts in tests so retry and failover contracts are verifiable without a real local model server.
- 2026-06-26: Add a lightweight in-process IPC/relay event bus so bridge startup can broadcast state frames without requiring an external websocket backend in tests.
- 2026-06-26: Pin bridge startup with a unit test that asserts the initial `IDLE` broadcast so runtime wiring stays observable.
- 2026-06-26: Route webapp command frames through a dedicated bridge controller so `STOP`, config save, and config reload logic stay isolated from the startup shim.
- 2026-06-26: Keep `r.py` as a thin wrapper and move orchestration into `bridge.runtime` so the entry point stays simple while runtime logic remains importable and testable.
