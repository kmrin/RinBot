import os, sys, json, urllib.parse, re, platform, psutil, cpuinfo, GPUtil, datetime
from translate import Translator
from dotenv import load_dotenv

def load_lang() -> dict:
    """Loads and returns rinbot's text as a dict"""
    VERBOSE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../lang/verbose.json"
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

def format_exception(e:Exception) -> str:
    """Formats an exception into `"Exception name -> Exception"` """
    return f"{type(e).__name__} -> {e}"

def remove_nl(list:list) -> list:
    """Removes newlines from a list of strings"""
    nl = []
    for i in list:
        i = i.strip("\n")
        if not i == "": nl.append(i)
    return nl

def meg_to_gig(m:int) -> str:
    """Converts a value in megabytes to gigabytes"""
    g = m / 1024
    return f"{g:.1f}"

def hex_to_int(value) -> int:
    """Converts a HEX value to a integer value"""
    return int(value[1:],16)

def is_hex_color(value) -> bool:
    """Checks if a HEX value is a valid color"""
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, value))

def is_url(str:str) -> bool:
    """Checks if a string is a valid URL"""
    try:
        result = urllib.parse.urlparse(str)
        return all([result.scheme, result.netloc])
    except: return False

def strtobool(val) -> bool:
    """Converts a string to a boolean value"""
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'): return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'): return False
    else: raise ValueError("Invalid value %r" % (val,))

def translate_to(text, to_lang="pt-br") -> str:
    """Translates a string into another language, translates to pt-br by default"""
    translator = Translator(to_lang=to_lang)
    translated = translator.translate(text)
    return translated

def format_time(time:int) -> str:
    """Formats secodns into a HH:MM:SS or MM:SS time format"""
    if int(time) // 3600 > 0: h = int(time) // 3600
    m,s = int(time) // 60, int(time) % 60
    return f"{h:02d}{m:02d}:{s:02d}" if int(time) // 3600 > 0 else f"{m:02d}:{s:02d}"

def format_date(date:str, format=0) -> str:
    """Formats a datecode into DD/MM/YYYY or MM/DD/YYYY"""
    parsed = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    return parsed.strftime("%d/%m/%Y" if format==0 else "%m/%d/%Y")

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