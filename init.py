"""
RinBot v5.0.0 'Aurora'

made by rin (https://github.com/kmrin, km.rin on https://discord.gg)
"""

import asyncio
from rinbot.base import RinBot

async def main() -> None:
    # Load client
    client = RinBot()
    
    # Start
    await client.init()

# RUN
if __name__ == '__main__':
    asyncio.run(main())
