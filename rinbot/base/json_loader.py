"""
Functions to load RinBot's JSON files (config and language)
"""

import os
import sys
import json

from typing import Union, Dict, List, Any

from .exception_handler import log_exception
from .get_os_path import get_os_path
from .logger import logger
from .paths import Path

def read(path: str) -> Union[List, Dict, None]:
    """
    Loads a JSON file from a path starting at 'rinbot/' and returns it

    Args:
        path (str): The path starting at 'rinbot/'

    Returns:
        Union[List, Dict, None]: The loaded JSON. Will return None if not found
    """
    
    json_path = get_os_path(path)
    
    if not os.path.exists(json_path):
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_exception(e)

def write(path: str, data: Union[List, Dict, None]) -> None:
    """
    Saves your data to a JSON file or creates a new one\n
    Path starts at 'rinbot/'

    Args:
        path (str): The path starting at 'rinbot/'
        data (Union[List, Dict, None]): Your JSON formatted data
    """
    
    json_path = get_os_path(path)
    json_dir = os.path.dirname(json_path)
    
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_exception(e)

def get_conf() -> Dict[str, Any]:
    """
    Returns the config file as a dictionary

    Returns:
        Dict[str, Any]: The config file as a dictionary
    """
    
    # Quit if no config file (corrupted instance)
    if not os.path.exists(Path.config):
        logger.critical('Config file not found, check your rinbot instance.')
        sys.exit()
    
    try:
        with open(Path.config, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_exception(e)

def get_lang() -> Dict[str, Union[str, List[str]]]:
    """
    Loads rinbot's text with the language specified in the config file

    Returns:
        Dict[str, Union[str, List[str]]]: The text dict
    """
    
    conf = get_conf()
    
    try:
        with open(Path.verbose.format(lang=conf['LANGUAGE']), 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Instead of crashing, fallback to english
    except FileNotFoundError:
        logger.warning('Invalid language specified in config file, trying to fall back to english...')
        
        try:
            with open(Path.verbose.format(lang='en'), 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # If the default language is not present, something is wrong
        except FileNotFoundError:
            logger.critical('Default language not found, check your rinbot instance.')
            sys.exit()
    except Exception as e:
        log_exception(e)

# TEST
if __name__ == '__main__':
    import time
    
    conf = get_conf()
    text = get_lang()
    
    print(text['SPLASH_NAME'].format(ver=conf['VERSION']))
    
    print('Testing JSON writing')
    write('../instance/haha.json', {'funny_man': 'really_funny'})
    
    time.sleep(0.5)
    
    print('Testing JSON loading')
    load = read('../instance/haha.json')
    print(load)
