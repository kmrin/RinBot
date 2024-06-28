import os

from typing import TYPE_CHECKING

from .loggers import Loggers
from .paths import Path
from .json_manager import get_conf

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.LOADER
conf = get_conf()

def load_extensions(bot: "RinBot") -> None:
    def _load(ext, ai: bool = False) -> None:
        if ai:
            bot.load_extension(f'rinbot.kobold.cogs.{ext}')
            if ext == 'languagemodel':
                bot.kb_endpoint_conn = True
            
            logger.info(f'AI extension "{ext}" loaded')
            return
        
        bot.load_extension(f'rinbot.extensions.{ext}')
        logger.info(f'Extension "{ext}" loaded')
    
    if conf['USE_LOCAL_KOBOLD']:
        for file in os.listdir(Path.kobold_cogs):
            if file.endswith('.py'):
                _load(file[:-3], True)
    
    lewd = ['booru', 'rule34', 'e621']
    
    for file in os.listdir(Path.extensions):
        if not file.endswith('.py'):
            continue
        
        ext = file[:-3]
        
        if conf['ENABLE_LEWD'] and ext in lewd:
            _load(ext)
        
        if all(ext not in ld for ld in lewd):
            _load(ext)
