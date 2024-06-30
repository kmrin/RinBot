import re
import string
import random
import nextcord
import platform
import cpuinfo
import psutil
import GPUtil
import urllib.parse

from nextlink import Playable
from nextcord import Interaction, Locale
from typing import Optional, Union, Dict, List
from datetime import datetime, UTC
from translate import Translator

from .loggers import Loggers
from .json_manager import get_locale
from .types import SystemSpecs

logger = Loggers.HELPERS

def get_interaction_locale(interaction: Interaction) -> str:
    locale = interaction.locale or Locale.en_GB
    
    if locale == Locale.en_US:
        locale = Locale.en_GB
    
    return locale

def get_localized_string(locale: str, key: str, *args, **kwargs) -> Optional[Union[str, List[str]]]:
    if isinstance(locale, tuple):
        locale = locale[0]  # ???????
    
    text = get_locale(locale)
    
    if not text:
        logger.error(f"Locale code '{locale}' not present in locale list, defaulting to english")
        
        text = get_locale(Locale.en_GB)
    
    try:
        verbose = text[key]
        if isinstance(verbose, List):
            return verbose
        
        return verbose.format(*args, **kwargs)
    except KeyError:
        logger.error(f"Missing localized string '{key}' for locale '{locale}'")
        
        return None

def get_random_string(lenght: int) -> str:
    """
    Generates a random string of a given lenght

    Args:
        lenght (int): How long the string would be

    Returns:
        str: The string
    """
    
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(lenght))

def get_expiration_time(expiration_time: datetime, locale: str) -> str:
    text = get_locale(locale)
    
    current_time = datetime.now(UTC)
    time_difference = expiration_time - current_time
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if time_difference.days > 0:
        return f"{time_difference.days} {text['DAYS']} {hours} {text['HOURS']}"
    elif hours > 0:
        return f"{hours} {text['HOURS']}"
    else:
        return text['NOW']

def gen_intents(intents_config: Dict[str, bool]) -> nextcord.Intents:
    intents = nextcord.Intents.default()
    
    for intent, enabled in intents_config.items():
        if hasattr(nextcord.Intents, intent) and enabled:
            setattr(intents, intent, True)
    
    return intents

def remove_nl_from_string_iterable(iterable: List[str]) -> List:
    """
    Removes newlines from a list of strings

    Args:
        iterable (List[str]): Your list containing newlines

    Returns:
        List: The list without newlines :)
    """
    
    return [x.strip() for x in iterable]

def translate(text: str, from_lang: str, to_lang: str='pt-br') -> str:
    """
    Translated a string from one language to another

    Args:
        text (str): The text to be translated
        from_lang (str): The input language (Ex.: 'en', 'pt-br', 'hu')
        to_lang (str, optional): The output launguage. Defaults to 'pt-br'.

    Returns:
        str: The translated string (hopefuly)
    """
    
    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    return translator.translate(text)

def get_specs() -> SystemSpecs:
    sys_info = SystemSpecs(
        os=f'{platform.system()} {platform.version()}',
        cpu=f'{cpuinfo.get_cpu_info()["brand_raw"]} {psutil.cpu_freq().max / 1000:.1f}GHz',
        ram=f'{psutil.virtual_memory().total / (1024 ** 3):.2f}GB'
    )
    
    try:
        gpu_list = GPUtil.getGPUs()
        gpu_info: GPUtil.GPU = gpu_list[0]
        sys_info.gpu = f'{gpu_info.name} ({meg_to_gig(gpu_info.memoryTotal)}GB)'
    except IndexError:
        pass  # No GPU detected
    
    return sys_info

def is_url(url: str) -> bool:
    result = urllib.parse.urlparse(url)
    return all([result.scheme, result.netloc])

def meg_to_gig(m: int) -> float:
    return float(f'{m / 1024:.1f}')

def is_hex_colour(c: str) -> bool:
    return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', c))

def hex_to_colour(c: str) -> nextcord.Colour:
    hex_colour = c.lstrip('#')
    if len(hex_colour) != 6:
        raise ValueError(f'Invalid HEX code: {c}')
    
    r, g, b = tuple(int(hex_colour[i:i+2], 16) for i in (0, 2, 4))
    return nextcord.Color.from_rgb(r, g, b)

def hex_to_int(val: str) -> int:
    return int(val[1:], 16)

def ms_to_str(ms: int) -> str:
    seconds = ms // 1000
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    
    return f'{h:02d}:{m:02d}:{s:02d}' if h > 0 else f'{m:02d}:{s:02d}'

async def url_to_playable(url: str) -> Playable:
    search = await Playable.search(url,)
    return search[0]
