from __future__ import annotations

import asyncio

from bridge.runtime import initialize_bridge


async def main() -> None:
    await initialize_bridge()


if __name__ == "__main__":
    asyncio.run(main())
