"""
RinBot v4.0.1
made by rin
"""

import asyncio
from rinbot.base.client import RinBot

async def main() -> None:
    client = RinBot()
    
    # Start
    await client.init()

# RUN
if __name__ == "__main__":
    asyncio.run(main())