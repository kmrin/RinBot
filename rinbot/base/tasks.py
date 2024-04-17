"""
Tasks and schedulers
"""

import random
import asyncio
import discord
import contextlib

from discord.ext import tasks
from typing import TYPE_CHECKING
from datetime import datetime

from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.valorant.daily_shop import show_val_daily_shop
from rinbot.valorant import cache as Cache

from .exception_handler import log_exception
from .json_loader import get_conf, get_lang
from .logger import logger

if TYPE_CHECKING:
    from client import RinBot

conf = get_conf()
text = get_lang()

class TaskHandler:
    def __init__(self, bot: "RinBot") -> None:
        self.bot = bot
    
    async def start(self) -> None:
        # Run normal tasks
        self._status_loop.start()
        
        # Run schedulers
        asyncio.create_task(self._fortnite_daily_shop())
        asyncio.create_task(self._valorant_daily_shop())
    
    @tasks.loop(minutes=int(conf['ACTIVITY_SWITCH_INTERVAL']))
    async def _status_loop(self) -> None:
        chosen = random.choice(text['ACTIVITY'])
        logger.info(text['TASKS_CHANGING_STATUS'].format(status=chosen))
        await self.bot.change_presence(activity=discord.CustomActivity(name=chosen))        
    
    # Schedulers
    async def _fortnite_daily_shop(self):
        logger.info(text['TASKS_FN_DS_STARTED'])
        
        try:
            while True and conf['FORTNITE_DAILY_SHOP_ENABLED']:
                time = conf["FORTNITE_DAILY_SHOP_UPDATE_TIME"].split(":")
                curr_time = datetime.now(self.bot.utc).strftime("%H:%M:%S")
                target_time = f"{time[0]}:{time[1]}:{time[2]}"
                
                if curr_time == target_time:
                    await show_fn_daily_shop(self.bot)
                
                await asyncio.sleep(1)
        except Exception as e:
            log_exception(e)
    
    async def _valorant_daily_shop(self):
        logger.info(text["TASKS_VL_DS_STARTED"])
        
        try:
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
        except Exception as e:
            log_exception(e)
