"""
#### Helper functions
The home of general purpose functions used throughout RinBot's code
"""

# Imports
import os, sys, json, discord, urllib.parse, re, platform, psutil, cpuinfo, GPUtil, datetime, traceback
from translate import Translator
from rinbot.base.logger import logger

def format_exception(e:Exception) -> str:
    """
    #### Formats an exception into a understandable string
    Struct: str:\n
        `"Exception name [<file> | <line_number>] -> Message"`
    """
    trace = traceback.extract_tb(e.__traceback__)
    path, line, _, _ = trace[-1]
    path = os.path.basename(path)
    return f"{type(e).__name__} [{path} | {line}] -> {str(e)}"

def load_lang() -> dict:
    """
    #### Loads and returns RinBot's text as a dict
    Struct: dict:\n
        `{"lang_name": KEY: VALUE}`\n
    The value can either be a string, or a list of strings
    """
    VERBOSE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../config/config-text.json"
    CONFIG_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../config/config-rinbot.json"
    if not os.path.isfile(VERBOSE_PATH):
        logger.critical("[helpers.py]: Verbose file not found")
        sys.exit()
    elif not os.path.isfile(CONFIG_PATH):
        logger.critical("[helpers.py]: Config file not found")
        sys.exit()
    try:
        with open(CONFIG_PATH, encoding="utf-8") as c:
            conf = json.load(c)
        with open(VERBOSE_PATH, encoding="utf-8") as v:
            verbose = json.load(v)
            try:
                return verbose[conf["LANGUAGE"]]
            except KeyError:
                logger.warning(verbose["en"]["HELPERS_WARNING_EN_FALLBACK"])
                return verbose["en"]
    except Exception as e:
        logger.critical(f"{format_exception(e)}")
        sys.exit()

def remove_nl(list:list) -> list:
    """
    #### Removes newlines from a list of strings
    """
    try:
        nl = []
        for i in list:
            i = i.strip("\n")
            if not i == "": nl.append(i)
        return nl
    except Exception as e: logger.error(f"{format_exception(e)}")

def meg_to_gig(m:int) -> float:
    """
    #### Converts a value in megabytes to gigabytes
    """
    try:
        g = m / 1024
        return float(f"{g:.1f}")
    except Exception as e: logger.error(f"{format_exception(e)}")

def hex_to_int(value) -> int:
    """
    #### Converts a HEX value to a integer value
    """
    try: return int(value[1:],16)
    except Exception as e: logger.error(f"{format_exception(e)}")

def is_hex_color(value) -> bool:
    """
    #### Checks if a HEX value is a valid color
    """
    try:
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, value))
    except Exception as e: logger.error(f"{format_exception(e)}")

def is_url(str:str) -> bool:
    """
    #### Checks if a string is a valid URL and returns a bool accordingly
    """
    try:
        try:
            result = urllib.parse.urlparse(str)
            return all([result.scheme, result.netloc])
        except: return False
    except Exception as e: logger.error(f"{format_exception(e)}")

def strtobool(val:str) -> bool:
    """
    #### Converts a string into a boolean value
    - Arguments:
        * val: str = `"y, yes, t, true, on, 1, n, no, f, false, off, 0"`
    \nWill return false if no matches are found
    """
    try:
        if val.lower() in ('y', 'yes', 't', 'true', 'on', '1'): return True
        elif val.lower() in ('n', 'no', 'f', 'false', 'off', '0'): return False
        else: return False
    except Exception as e: logger.error(f"{format_exception(e)}")

def translate(text:str, to_lang:str="pt-br") -> str:
    """
    #### Translates a string into another language
    `Auto -> PT-BR by default`
    """
    try:
        translator = Translator(to_lang=to_lang)
        return translator.translate(text)
    except Exception as e: logger.error(f"{format_exception(e)}")

def format_time(time:int) -> str:
    """
    #### Formats seconds into a HH:MM:SS or MM:SS time format
    """
    try:
        if int(time) // 3600 > 0: h = int(time) // 3600
        m,s = int(time) // 60, int(time) % 60
        return f"{h:02d}{m:02d}:{s:02d}" if int(time) // 3600 > 0 else f"{m:02d}:{s:02d}"
    except Exception as e: logger.error(f"{format_exception(e)}")

def format_millsec(time:int) -> str:
    """
    #### Formats milliseconds into a HH:MM:SS or MM:SS time format
    """
    try:
        seconds = time // 1000
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except Exception as e: logger.error(f"{format_exception(e)}")

def format_date(date:str, format:int=0) -> str:
    """
    #### Formats a datecode into DD/MM/YYYY or MM/DD/YYYY
    - Arguments:
        * date:str = `Datecode. Example: "%Y-%m-%dT%H:%M:%S.%fZ"`
        * format:int = `0` for `DD/MM/YYYY` (default) or `1` for `MM/DD/YYYY`
    """
    try:
        parsed = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
        return parsed.strftime("%d/%m/%Y" if format == 0 else "%m/%d/%Y")
    except Exception as e: logger.error(f"{format_exception(e)}")

async def get_specs() -> dict:
    """Returns a dict containing the current system specifications
    - dict structure: `{'os', 'cpu', 'ram', 'gpu'}`"""
    text = load_lang()
    sys_info = {}
    try:
        gpu_list = GPUtil.getGPUs()
        gpu_info:GPUtil.GPU = gpu_list[0]
        sys_info["gpu"] = f"{gpu_info.name} ({meg_to_gig(gpu_info.memoryTotal)}GB)"
    except: sys_info["gpu"] = f"{text['HELPERS_NO_GPU']}"
    sys_info["os"] = f"{platform.system()} {platform.version()}"
    sys_info["cpu"] = f"{cpuinfo.get_cpu_info()['brand_raw']} {psutil.cpu_freq().max / 1000:.1f}gHz"
    sys_info["ram"] = f"{psutil.virtual_memory().total / (1024**3):.2f}GB"
    return sys_info

async def check_token(token:str) -> bool:
    """
    #### Check if a bot token is valid or not
    Creates a dummy bot object and tries to log-in to discord using the provided token\n
    If the login is successful, closes the bot and returns True, else it returns False
    """
    try:
        dummy = discord.Client(intents=discord.Intents.default())
        @dummy.event
        async def on_ready() -> None: await dummy.close()
        await dummy.start(token)
        return True
    except discord.LoginFailure: 
        return False
    except Exception as e:
        logger.critical(f"{format_exception(e)}")
        sys.exit()