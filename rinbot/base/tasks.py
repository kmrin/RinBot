"""
#### Tasks and schedulers
"""

import random, asyncio, discord, contextlib
from discord.ext import tasks
from datetime import datetime
from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.valorant.daily_shop import show_val_daily_shop
from rinbot.valorant import cache as Cache
from rinbot.base.helpers import load_config, load_lang
from rinbot.base.logger import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

conf = load_config()
text = load_lang()

class TaskHandler:
    def __init__(self, bot: "RinBot"):
        self.bot = bot
    
    async def start(self):
        # Run tasks
        self.status_loop.start()
        
        # Run schedulers
        asyncio.create_task(self.fortnite_daily_shop_scheduler())
        asyncio.create_task(self.valorant_daily_shop_scheduler())
    
    @tasks.loop(minutes=int(conf["ACTIVITY_SWITCH_INTERVAL"]))
    async def status_loop(self):
        chosen = random.choice(text["INIT_ACTIVITY"])
        await self.bot.change_presence(activity=discord.CustomActivity(name=chosen))
    
    # Schedulers
    async def fortnite_daily_shop_scheduler(self):
        logger.info(text["INIT_FN_DAILY_SHOP_STARTED"])
        while True and conf["FORTNITE_DAILY_SHOP_ENABLED"]:
            time = conf["FORTNITE_DAILY_SHOP_UPDATE_TIME"].split(":")
            curr_time = datetime.now(self.bot.utc).strftime("%H:%M:%S")
            target_time = f"{time[0]}:{time[1]}:{time[2]}"
            if curr_time == target_time:
                await show_fn_daily_shop(self.bot)
            await asyncio.sleep(1)
    
    async def valorant_daily_shop_scheduler(self):
        logger.info(text["INIT_VL_DAILY_SHOP_STARTED"])
        with contextlib.suppress(Exception):
            cache = self.bot.val_db.read_cache()
            version = Cache.get_valorant_version()
            if version != cache["valorant_version"]:
                Cache.get_cache()
                cache["valorant_version"] = version
                # self.bot.val_db.insert_cache(cache)
                logger.info(text["VALORANT_UPDATED_CACHE"])
        while True and conf["VALORANT_DAILY_SHOP_ENABLED"]:
            time = conf["VALORANT_DAILY_SHOP_UPDATE_TIME"].split(":")
            curr_time = datetime.now(self.bot.utc).strftime("%H:%M:%S")
            target_time = f"{time[0]}:{time[1]}:{time[2]}"
            if curr_time == target_time:
                await show_val_daily_shop(self.bot)
            await asyncio.sleep(1)