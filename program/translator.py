"""
RinBot v1.4.3
feita por rin
"""

# Imports
from translate import Translator

# Traduz uma string de uma linguagem pra outra
def translate_to(text, from_lang, to_lang):
    translator = Translator(from_lang=from_lang, to_lang=to_lang)
    translated_text = translator.translate(text)
    return translated_text