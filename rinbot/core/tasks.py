import random
import asyncio
import nextcord
import contextlib

from nextcord.ext import tasks
from typing import TYPE_CHECKING
from datetime import datetime

from .loggers import Loggers
from .json_manager import get_conf, read
from .paths import Path, get_os_path

from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.valorant.daily_shop import show_val_daily_shop
from rinbot.valorant import cache as Cache

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.TASKS
conf = get_conf()

class TaskHandler:
    def __init__(self, bot: 'RinBot') -> None:
        self.bot = bot
    
    async def start(self) -> None:
        # Run normal tasks
        self._status_loop.start()
        
        # Run schedulers
        asyncio.create_task(self._fortnite_daily_shop())
        asyncio.create_task(self._valorant_daily_shop())
    
    @tasks.loop(minutes=int(conf['STATUS_CHANGE_INTERVAL']))
    async def _status_loop(self) -> None:
        def _get_lang() -> None:
            txt = read(get_os_path(f'{Path.locale}/en-GB.json'), silent=True)
            if not txt:
                logger.error('huh? what?')
        
        status_lang = conf['STATUS_LANG']
        txt = read(get_os_path(f'{Path.locale}/{status_lang}.json'), silent=True)
        if not txt:
            _get_lang()
        
        try:
            statuses = txt['STATUSES']
        except KeyError:
            logger.error(f"STATUSES key not found in locale '{status_lang}, defaulting to english'")
            
            _get_lang()
            
            try:
                statuses = txt['STATUSES']
            except KeyError:
                logger.error('bro what the f*ck')
        
        status = random.choice(statuses)
        if conf['LOG_STATUS_CHANGE']:
            logger.info(f"Changing status to '{status}'")
        
        await self.bot.change_presence(activity=nextcord.CustomActivity(name=status))

    # Schedulers
    async def _fortnite_daily_shop(self) -> None:
        logger.info('Fortnite daily shop task started')
    
        while conf['FORTNITE_DAILY_SHOP_ENABLED']:
            target = conf['FORTNITE_DAILY_SHOP_UPDATE_TIME']
            curr = datetime.now(self.bot.utc).strftime('%H:%M:%S')
            
            if curr == target:
                await show_fn_daily_shop(self.bot)
            
            await asyncio.sleep(1)

    async def _valorant_daily_shop(self) -> None:
        logger.info('Valorant daily shop task started')
        
        with contextlib.suppress(Exception):
            Cache.get_cache()
            cache = self.bot.val_db.read_cache()
            version = Cache.get_valorant_version()
            
            if version != cache['valorant_version']:
                Cache.get_cache()
                cache['valorant_version'] = version
                        
        while conf['VALORANT_DAILY_SHOP_ENABLED']:
            target = conf['VALORANT_DAILY_SHOP_UPDATE_TIME']
            curr = datetime.now(self.bot.utc).strftime('%H:%M:%S')
            
            if curr == target:
                await show_val_daily_shop(self.bot)
            
            await asyncio.sleep(1)
