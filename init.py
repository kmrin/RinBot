"""
RinBot v6.4.0 'Alvorada'
development started on 11/06/2024
made by rin (https://github.com/kmrin, km.rin on https://discord.gg)
"""

import asyncio
from rinbot.core import RinBot

async def main() -> None:
    # Load client
    client = RinBot()
    
    # Start
    await client.init()

# RUN
if __name__ == '__main__':
    asyncio.run(main())
