"""
General purpose helper functions
"""

import psutil
import GPUtil
import cpuinfo
import platform
import urllib.parse

from typing import Dict, List
from datetime import datetime
from translate import Translator

from .exception_handler import log_exception
from .json_loader import get_lang

def get_specs() -> Dict[str, str]:
    """
    Returns a dict containing the current system specifications

    Returns:
        Dict[str, str]: ['os', 'cpu', 'ram', 'gpu']
    """

    text = get_lang()
    sys_info = {}

    try:
        gpu_list = GPUtil.getGPUs()
        gpu_info: GPUtil.GPU = gpu_list[0]

        sys_info["gpu"] = f"{gpu_info.name} ({meg_to_gig(gpu_info.memoryTotal)}GB)"
    except:
        sys_info["gpu"] = f"{text['HELPERS_NO_GPU']}"

    sys_info["os"] = f"{platform.system()} {platform.version()}"
    sys_info["cpu"] = f"{cpuinfo.get_cpu_info()['brand_raw']} {psutil.cpu_freq().max / 1000:.1f}gHz"
    sys_info["ram"] = f"{psutil.virtual_memory().total / (1024 ** 3):.2f}GB"

    return sys_info

def get_expiration_time(expiration_time: datetime) -> str:
    """
    Receives a datetime and returns a string that shows how much time you have from now to the input time

    Args:
        expiration_time (datetime): Example '2024-01-22 23:59:44.779790'

    Returns:
        str: Expiration time
    """
    
    text = get_lang()
    current_time = datetime.utcnow()
    time_difference = expiration_time - current_time
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if time_difference.days > 0:
        return f"{time_difference.days} {text['DAYS']} {hours} {text['HOURS']}"
    elif hours > 0:
        return f"{hours} {text['HOURS']}"
    else:
        return text['NOW']

def remove_nl(your_list: List[str]) -> List:
    """
    Removes newlines from a list of strings

    Args:
        your_list (list): Your list containing newlines

    Returns:
        list: The list without newlines
    """

    try:
        return [x.strip() for x in your_list]
    except Exception as e:
        log_exception(e)

def is_url(url: str) -> bool:
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_hex(value: str) -> bool:
    """
    Checks if your HEX value is valid

    Args:
        value (str): The value (Ex.: 0xFFFFF)

    Returns:
        bool: Converted int value
    """

    try:
        if value.startswith("0x") or value.startswith("0X"):
            value = value[2:]
        
        elif value.startswith("#"):
            value = value[1:]

        if len(value) != 6:
            return False

        if not all(c in "0123456789abcdefABCDEF" for c in value):
            return False

        return True
    except Exception as e:
        log_exception(e)

def hex_to_int(value: str) -> int:
    """
    Converts a HEX value to an integer

    Args:
        value (str): The hex value (Ex.: 0xFFFFF)

    Returns:
        int: Converted int value
    """
    
    try:
        return int(value[1:], 16)
    except Exception as e:
        log_exception(e)

def meg_to_gig(m: int) -> float:
    """
    Converts a value in megabytes to gigabytes

    Args:
        m (int): Number in megabyes

    Returns:
        float: Floating point number in gigabytes (one decimal)
    """

    try:
        g = m / 1024
        return float(f"{g:.1f}")
    except Exception as e:
        log_exception(e)

def ms_to_str(ms: int) -> str:
    """
    Formats milliseconds into a HH:MM:SS format

    Args:
        ms (int): Quantity in milliseconds

    Returns:
        str: HH:MM:SS or MM:SS format
    """
    
    try:
        seconds = ms // 1000
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except Exception as e:
        log_exception(e)

def translate(text: str, from_lang: str, to_lang: str="pt-br") -> str:
    """
    Translates a string from one language to another

    Args:
        text (str): The text to be translated
        from_lang (str): The language input (Ex.: 'en', 'pt-br', 'hu')
        to_lang (str, optional): The language output. Defaults to 'pt-br'.

    Returns:
        str: The translated string (hopefuly)
    """

    try:
        translator = Translator(from_lang=from_lang, to_lang=to_lang)
        return translator.translate(text)
    except Exception as e:
        log_exception(e)
