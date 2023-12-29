# Imports
import os, sys, json, urllib.parse, re, platform, psutil, cpuinfo, GPUtil
from translate import Translator
from dotenv import load_dotenv

# Lang file path
VERBOSE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../lang/verbose.json"

# Removes newlines from a list of strings
def remove_nl(list):
    nl = []
    for i in list:
        i = i.strip("\n")
        if not i == '':
            nl.append(i)
    return nl

# Formats an exception into "Exception name -> Exception"
def format_exception(e):
    return f"{type(e).__name__} -> {e}"

# Loads verbose
def load_lang():
    load_dotenv()
    lang = os.getenv("DISCORD_BOT_LANGUAGE")
    if not os.path.isfile(VERBOSE_PATH):
        sys.exit(f"[helpers.py]-[ERROR]: Verbose file not found")
    with open(VERBOSE_PATH, encoding='utf-8') as f:
        verbose = json.load(f)
        try:
            return verbose[lang]
        except KeyError:
            print(verbose["en"]["HELPERS_WARNING_EN_FALLBACK"])
            return verbose["en"]

# Returns a dict with the current system specs
async def get_specs() -> dict:
    sys_info = {}
    os_info = f"{platform.system()} {platform.version()}"
    cpu_info = f"{cpuinfo.get_cpu_info()['brand_raw']} {psutil.cpu_freq().max / 1000:.1f}GHz"
    ram_info = f"{psutil.virtual_memory().total / (1024**3):.2f}GB"
    try:
        gpu_list = GPUtil.getGPUs()
        gpu_info:GPUtil.GPU = gpu_list[0]
        gpu_name = gpu_info.name
        gpu_memory = gpu_info.memoryTotal
        gpu_info_str = f"{gpu_name} ({meg_to_gig(gpu_memory)}GB)"
    except:
        gpu_info_str = f"GPU Not Available"
    sys_info['os'] = os_info
    sys_info['cpu'] = cpu_info
    sys_info['ram'] = ram_info
    sys_info['gpu'] = gpu_info_str
    return sys_info

# Converts a value in megabytes to gigabytes
def meg_to_gig(m):
    g = m / 1024
    return f"{g:.1f}"

# Converts a HEX #FFFFFF value to a integer 0xFFFFFF value
def hexToInt(value):
    value = int(value[1:],16)
    return value

# Checks if a HEX value is a valid color
def isHexColor(value):
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, value))

# Checks if a string is a valid URL
def is_url(str):
    try:
        result = urllib.parse.urlparse(str)
        return all([result.scheme, result.netloc])
    except:
        return False

# Translates a string to a boolean value
def strtobool(val):
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("Invalid value %r" % (val,))

# Translates a string from one language to another
def translate_to(text, from_lang, to_lang):
    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    translated = translator.translate(text)
    return translated

# Formats seconds into a HH:MM time format
def formatTime(time:int):
    if int(time) // 3600 > 0:
        h,m,s = int(time) // 3600, int(time) % 3600 // 60, int(time) % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    m,s = int(time) // 60, int(time) % 60
    return f"{m:02d}:{s:02d}"

# Removes duplicate items from a list
def removeListDuplicates(lst):
    return list(set(lst))