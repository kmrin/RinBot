"""
RinBot v1.8.0 (GitHub release)
made by rin
"""

# Imports
import urllib.parse, re
from translate import Translator

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
    m, s = time // 60, time % 60
    time = f"{m:02d}:{s:02d}"
    return time

# Removes duplicate items from a list
def removeListDuplicates(list):
    nodupe = []
    for i in list:
        if i not in nodupe:
            nodupe.append(i)
    return nodupe