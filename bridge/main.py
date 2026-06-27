from __future__ import annotations

import asyncio

from bridge.runtime import initialize_bridge


async def main() -> None:
    await initialize_bridge(start_microphone=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
