"""
RinBot's helper functions\n
General purpose functions used throughout rinbot's code
"""

import os, re, sys, json, traceback, discord, cpuinfo, GPUtil, subprocess, platform, psutil
from datetime import datetime
from typing import Dict, List, Any
from translate import Translator
from rinbot.base.logger import logger

VERBOSE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../config/config-text.json"
CONFIG_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../config/config-rinbot.json"

def get_path(path: str) -> str:
    """
    #### Returns a system realpath from the path given
    Starts at "rinbot/"
    """
    
    return f"{os.path.realpath(os.path.dirname(__file__))}/../{path}"

def format_exception(e: Exception) -> str:
    """
    #### Formats an exception into a simple understandable string
    - Parameters:
        * e: The exception
    - Returns:
        * str: `"<exception name> [<file> | <line>] -> Message"`
    """
    
    trace = traceback.extract_tb(e.__traceback__)
    path, line, _, _ = trace[-1]
    path = os.path.basename(path)
    return f"{type(e).__name__} [{path} | {line}] -> {str(e)}"

def load_config() -> Dict[str, Any]:
    """
    #### Loads rinbot's config file
    - Returns:
        * dict: `"config_key": "config_value"`
    """
    
    if not os.path.isfile(CONFIG_PATH):
        logger.critical("[helpers.py]: Config file not found")
        sys.exit()
    
    try:
        with open(CONFIG_PATH, encoding="utf-8") as c:
            return json.load(c)
    except Exception as e:
        logger.critical(format_exception(e))
        sys.exit()

def load_lang() -> Dict[str, List[str] | str]:
    """
    #### Loads rinbot's text with the language specified on the config file
    - Returns:
        * dict: `"text_key": "str" or list of "str"`
    """
    
    if not os.path.isfile(VERBOSE_PATH):
        logger.critical("[helpers.py]: Verbose file not found")
        sys.exit()
    
    conf = load_config()
    try:
        with open(VERBOSE_PATH, encoding="utf-8") as v:
            verbose = json.load(v)
            try:
                return verbose[conf["LANGUAGE"]]
            except KeyError:
                logger.warning(verbose["en"]["HELPERS_WARNING_EN_FALLBACK"])
                return verbose["en"]
    except Exception as e:
        logger.critical(format_exception(e))
        sys.exit()

def millisec_to_str(time: int) -> str:
    """
    #### Formats milliseconds into a HH:MM:SS or MM:SS time format
    """
    
    try:
        seconds = time // 1000
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
    except Exception as e:
        logger.error(format_exception(e))

def format_date(date:str, format:int=0) -> str:
    """
    #### Formats a datecode into DD/MM/YYYY or MM/DD/YYYY
    - Arguments:
        * date:str = `Datecode. Example: "%Y-%m-%dT%H:%M:%S.%fZ"`
        * format:int = `0` for `DD/MM/YYYY` (default) or `1` for `MM/DD/YYYY`
    """
    try:
        parsed = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
        return parsed.strftime("%d/%m/%Y" if format == 0 else "%m/%d/%Y")
    except Exception as e: logger.error(f"{format_exception(e)}")

def format_expiration_time(expiration_time):
    """
    #### Receives a datetime and returns a string that shows how much time you have from now to the input time
    - Arguments:
        * expiration_time:str `Example: "2024-01-22 23:59:44.779790"`\n
        Can be generated with "datetime.utcnow() + timedelta(seconds=duration)" for example
    """
    text = load_lang()
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

def remove_nl(list: list) -> list:
    """
    #### Removes newlines from a list of strings
    """
    
    try:
        nl = []
        for i in list:
            i = i.strip("\n")
            if not i == "":
                nl.append(i)
        return nl
    except Exception as e:
        logger.error(format_exception(e))

def meg_to_gig(m: int) -> float:
    """
    #### Converts a value in megabytes to gigabytes
    """
    
    try:
        g = m / 1024
        return float(f"{g:.1f}")
    except Exception as e:
        logger.error(format_exception(e))

def is_hex_color(value) -> bool:
    """
    #### Checks if a HEX value is a valid color
    """
    
    try:
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, value))
    except Exception as e:
        logger.error(f"{format_exception(e)}")

def hex_to_int(value) -> int:
    """
    #### Converts a HEX value to a integer value
    """
    
    try:
        return int(value[1:], 16)
    except Exception as e:
        logger.error(format_exception(e))

def translate(text: str, from_lang: str, to_lang: str="pt-br") -> str:
    """
    #### Translates a string into another language\n
    `Auto -> PT-BR by default`
    """
    
    try:
        translator = Translator(from_lang=from_lang, to_lang=to_lang)
        return translator.translate(text)
    except Exception as e:
        logger.error(format_exception(e))

def get_specs() -> dict:
    """
    #### Returns a dict containing the current system specifications
    :return: `{"os", "cpu", "ram", "gpu"}`
    """
    
    text = load_lang()
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

def gen_intents():
    """
    #### Returns rinbot's intents
    """
    
    intents = discord.Intents.all()
    intents.dm_messages = True
    intents.dm_reactions = True
    intents.dm_typing = True
    intents.guild_messages = True
    intents.guild_reactions = True
    intents.guild_scheduled_events = True
    intents.guild_typing = True
    intents.guilds = True
    intents.integrations = True
    intents.invites = True
    intents.voice_states = True
    intents.webhooks = True
    intents.members = True
    intents.message_content = True
    intents.moderation = True
    intents.presences = True
    intents.emojis_and_stickers = True
    intents.messages = True
    intents.emojis = True
    intents.reactions = True
    intents.typing = True
    intents.bans = True
    return intents

def check_cache():
    """
    #### A check ran at startup to make sure all cache dirs exist
    """
    
    text = load_lang()
    folders = [
        "cache", "cache/fun", "cache/chatlog", "cache/stablediffusion",
        "cache/lavalink", "cache/lavalink/log", "cache/fortnite",
        "cache/fortnite/downloads", "cache/fortnite/composites", "cache/fortnite/stats",
        "cache/valorant", "cache/stickbug", "logs", "logs/lavalink"]
    
    try:
        for folder in folders:
            path = f"{os.path.realpath(os.path.dirname(__file__))}/../{folder}"
            if not os.path.exists(path):
                os.makedirs(path)
                if "logs" in path and not "lavalink" in path:
                    os.remove(f"{path}/a.log")
                logger.info(f"{text['INIT_CREATED_DIRECTORY']} '{folder}'")
    except Exception as e:
        logger.critical(format_exception(e))
        sys.exit()

def check_java():
    """
    #### A check ran at startup to make sure the correct version of java is installed 
    """
    
    text = load_lang()
    
    try:
        output = subprocess.check_output("java -version", stderr=subprocess.STDOUT, shell=True, text=True)
        lines = output.split("\n")
        
        for line in lines:
            if "version" in line.lower():
                ver = line.split()[2]
                ver = int("".join(c for c in ver if c.isdigit() or c == ".").split(".")[0])
                
                try:
                    if not ver >= 17:
                        logger.error(f"{text['INIT_INVALID_JAVA_VERSION']}: {ver}")
                        sys.exit()
                except:
                    logger.error(text["INIT_INVALID_JAVA_VERSION"])
                    sys.exit()
    except:
        logger.critical(text["INIT_JAVA_NOT_FOUND"])
        sys.exit()

async def check_token(token: str) -> bool:
    """
    #### A check ran during setup to verify if the user provided token is valid or not
    - Parameters:
        * token: `str`
    - Returns:
        * bool: `True if valid | False if invalid`
    """
    
    try:
        dummy = discord.Client(intents=discord.Intents.default())
        
        @dummy.event
        async def on_ready(): await dummy.close()
        
        await dummy.start(token)
        
        return True
    except discord.LoginFailure:
        return False
    except Exception as e:
        logger.critical(format_exception(e))
        sys.exit()