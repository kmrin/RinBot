"""
RinBot v1.5.0 (GitHub release)
made by rin
"""

# Imports
import urllib.parse
from translate import Translator

# Checks if a string is a valid URL
def is_url(str):
    try:
        result = urllib.parse.urlparse(str)
        return all([result.scheme, result.netloc])
    except:
        return False

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