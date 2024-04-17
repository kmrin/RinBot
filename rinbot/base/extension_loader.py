"""
Command cog (extension) loader
"""

import os

from typing import TYPE_CHECKING

from .exception_handler import log_exception
from .get_os_path import get_os_path
from .json_loader import get_conf, get_lang
from .logger import logger

if TYPE_CHECKING:
    from .client import RinBot

conf = get_conf()
text = get_lang()

async def load_extensions(bot: "RinBot") -> None:
    async def __load(ext, ai=False):
        try:
            if ai:
                await bot.load_extension(f'rinbot.kobold.cogs.{ext}')
                if ext == 'languagemodel':
                    bot.endpoint_connected = True
                
                logger.info(f'{text["LOADER_LOADED"].format(extension=ext)} (AI)')
                return
            
            await bot.load_extension(f'rinbot.extensions.{ext}')
            logger.info(text['LOADER_LOADED'].format(extension=ext))
        except Exception as e:
            log_exception(e)
    
    if conf['AI_ENABLED']:
        for file in os.listdir(get_os_path('kobold/cogs')):
            if file.endswith('.py'):
                await __load(file[:-3], ai=True)
    
    booru_ext = ['booru']
    rule34_ext = ['rule34']
    
    everything = booru_ext + rule34_ext
    
    for file in os.listdir(get_os_path('extensions')):
        if file.endswith('.py'):
            ext = file[:-3]
            
            if conf['BOORU_ENABLED'] and ext in booru_ext:
                await __load(ext)
            elif conf['RULE34_ENABLED'] and ext in rule34_ext:
                await __load(ext)
            
            if all(ext not in sl for sl in everything):
                await __load(ext)
