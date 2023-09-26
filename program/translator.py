"""
RinBot v1.4.3 (GitHub release)
made by rin
"""

# Imports
from translate import Translator

# Translates a string from one language to another
def translate_to(text, from_lang, to_lang):
    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    translated_text = translator.translate(text)
    return translated_text