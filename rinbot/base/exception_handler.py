"""
Contains a function that logs a raised exception and saves the entire traceback as a file
"""

import os
import traceback

from datetime import datetime

from .logger import logger
from .paths import Path

def log_exception(e: Exception, critical: bool=False, log_trace: bool=True) -> str:
    """
    Formats an exception into a understandable string and logs it

    Args:
        e (Exception): The exception
        critical (bool, optional): If the log state should be critical instead of error. Defaults to False.
        log_trace (bool, optional): Log the entire traceback as a separate file. Defaults to True.

    Returns:
        str: The formatted exception as '<exception_name> [<path> | <line>] -> <message>'
    """
    
    path, line, _, _ = traceback.extract_tb(e.__traceback__)[-1]
    path = os.path.basename(path)
    
    formatted = f'{type(e).__name__} [{path} | {line}] -> {str(e)}'
    
    if critical:
        logger.critical(formatted)
    else:
        logger.error(formatted)
    
    # Log entire traceback
    if not log_trace:
        return formatted
    
    trace = traceback.format_exception(type(e), e, e.__traceback__)
    trace = ''.join(trace)
    
    now = datetime.now().strftime('%y.%m.%d-%H%M%S')
    
    filename = f'{type(e).__name__}_{now.replace(":", "-")}.txt'
    filepath = os.path.join(Path.tracebacks, filename)
    filedir = os.path.dirname(filepath)
    
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(trace)
    
    return formatted

# TEST
if __name__ == '__main__':
    try:
        with open('crabby_patty_secret_formula.txt') as f:
            f.read()
    except Exception as e:
        log_exception(e)
