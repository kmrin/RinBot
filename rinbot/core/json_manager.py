import os
import sys
import json

from typing import Optional, Union, Dict, List, Any

from .loggers import Loggers, log_exception
from .paths import Path, get_os_path

logger = Loggers.JSON

def read(p: str, create: bool = False, silent: bool = False) -> Optional[Union[List, Dict, None]]:
    """
    Loads a JSON file from a path starting at 'rinbot/' and returns it

    Args:
        p (str): The path

    Returns:
        Union[List, Dict, None]: The loaded JSON. Will return None if not found
    """
    
    json_path = get_os_path(p)
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            file = json.load(f)
            
            if not silent:
                logger.info(f"Read file at: '{p}'")
            
            return file
    except json.JSONDecodeError as e:
        logger.error(f'Tried reading a file at: "{p}" but there was a JSON decode error at: '
            f'[POS: {e.pos} | LINE NO.: {e.lineno} | COL NO.: {e.colno}]')

        return None
    except FileNotFoundError:
        if create:
            logger.warning(f"Tried reading a file at: {p} but the file doesn't exist, creating it.")
            write(p, {}, silent)
            return read(p, silent=silent)
        
        logger.error(f"Tried reading a file at: '{p}' but the file doesn't exist.")

        return None
    except Exception as e:
        log_exception(e, logger)

def write(p: str, data: Union[List, Dict, None], silent: bool = False) -> bool:
    """
    Saves your data to a JSON file or creates a new one, path starts at 'rinbot/'

    Args:
        p (str): The path
        data (Union[List, Dict, None]): Your JSON formatted data

    Returns:
        bool: True if correctly writen to, otherwise False
    """
    
    try:
        json_path = get_os_path(p)
        json_dir = os.path.dirname(json_path)
        
        os.makedirs(json_dir, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        if not silent:
            logger.info(f"Wrote file at: '{p}'")
        
        file = read(p, silent=silent)
        
        if file == data:
            if not silent:
                logger.info('Writen file validated')
            
            return True
        
        logger.error('Writen file did not pass validation')
        
        return False
    except json.JSONDecodeError as e:
        logger.error(f'Tried writing to a file at: "{p}" but there was a JSON decode error at: '
            f'[POS: {e.pos} | LINE NO.: {e.lineno} | COL NO.: {e.colno}]')
    except Exception as e:
        log_exception(e, logger)

def get_conf() -> Dict[str, Any]:
    """
    Returns rinbot's config file

    Returns:
        Dict[str, Any]: The config file as a dict
    """
    
    conf = read(Path.config, silent=True)
    
    if not conf:
        logger.critical('Could not load config, check your rinbot instance as it might be corrupted.')
        sys.exit(1)
    
    return conf

def get_locale(locale: str) -> Optional[Dict[str, Union[str, List]]]:
    return read(os.path.join(Path.locale, f'{locale}.json'), silent=True)
