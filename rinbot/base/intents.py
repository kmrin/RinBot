"""
Bot intents manipulation
"""

from discord import Intents

from .json_loader import get_conf

conf = get_conf()

def gen_intents():
    """
    Generates rinbot's intents from her config file and returns them
    """
    
    intents = Intents.default()
    attributes: dict = conf['INTENTS']
    
    for attr, value in attributes.items():
        setattr(intents, attr, value)
    
    return intents
