import os
import logging
import datetime
import traceback

from logging import ERROR
from typing import Optional

from .paths import Path, get_os_path

class LoggingFormatter(logging.Formatter):
    black = '\x1b[30m'
    red = '\x1b[31m'
    green = '\x1b[32m'
    yellow = '\x1b[33m'
    blue = '\x1b[34m'
    gray = '\x1b[38m'
    reset = '\x1b[0m'
    bold = '\x1b[1m'

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno)

        format_str = '(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}'
        format_str = format_str.replace('(black)', self.black + self.bold)
        format_str = format_str.replace('(reset)', self.reset)
        format_str = format_str.replace('(levelcolor)', log_color)
        format_str = format_str.replace('(green)', self.green + self.bold)

        formatter = logging.Formatter(format_str, '%Y-%m-%d %H:%M:%S', style='{')

        return formatter.format(record)

timestamp = datetime.datetime.now().strftime('%d.%m.%y-%H%M%S')
log_filename = get_os_path(f'../instance/logs/client/rin-{timestamp}.log')
log_dirname = os.path.dirname(log_filename)

os.makedirs(log_dirname, exist_ok=True)

root_logger = logging.getLogger('rinbot')
root_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())

file_handler = logging.FileHandler(
    filename=log_filename,
    mode='a',
    encoding='utf-8',
    delay=False
)

file_handler.setFormatter(
    logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S",
        style="{"
    )
)

root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

class Loggers:
    ROOT: logging.Logger            = root_logger
    COMMAND_CHECKS: logging.Logger  = logging.getLogger('Command Checks')
    CLIENT: logging.Logger          = logging.getLogger('Client')
    COMMANDS: logging.Logger        = logging.getLogger('Commands')
    DB: logging.Logger              = logging.getLogger('DB')
    EVENTS: logging.Logger          = logging.getLogger('Events')
    EXTENSIONS: logging.Logger      = logging.getLogger('Extensions')
    ERRORS: logging.Logger          = logging.getLogger('Errors')
    FORTNITE: logging.Logger        = logging.getLogger('Fortnite')
    HELPERS: logging.Logger         = logging.getLogger('Helpers')
    INTERFACE: logging.Logger       = logging.getLogger('Interface')
    PROGRAMS: logging.Logger        = logging.getLogger('Programs')
    STARTUP_CHECKS: logging.Logger  = logging.getLogger('Startup Checks')
    TASKS: logging.Logger           = logging.getLogger('Tasks')
    LOADER: logging.Logger          = logging.getLogger('Loader')
    JSON: logging.Logger            = logging.getLogger('Json')
    RESPONDER: logging.Logger       = logging.getLogger('Responder')
    VALORANT: logging.Logger        = logging.getLogger('Valorant')

for logger_name, logger in vars(Loggers).items():
    if isinstance(logger, logging.Logger) and logger_name != 'ROOT':
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

def log(msg: str, logger: Optional[logging.Logger], level: int = logging.INFO) -> None:
    """
    Log a message

    Args:
        msg (str): The message
        logger (logging.Logger): Desired logger. Defaults to the root logger
        level (int, optional): Logging level. Defaults to logging.INFO.
    """
    
    if not logger:
        logger = root_logger
    
    logger.log(level, msg)

def log_exception(e: Exception, logger: Optional[logging.Logger] = None, critical: bool = False, log_trace: bool = True) -> str:
    """
    Formats an exception into a understandable string and logs it to the provided logger

    Args:
        e (Exception): The exception
        logger (Optional[logging.Logger], optional): The logger. Defaults to None.
        critical (bool, optional): If the log state should be critical instead of error. Defaults to False.
        log_trace (bool, optional): Log the entire traceback in a separate file. Defaults to True.

    Returns:
        str: The formatted exception as '<ex_name> [<path> | <line>] -> <msg>'
    """
    
    path, line, _, _ = traceback.extract_tb(e.__traceback__)[-1]
    path = os.path.basename(path)

    formatted = f'{type(e).__name__} [{path} | {line}] -> {str(e)}'

    level = ERROR if not critical else ERROR

    if not logger:
        logger = root_logger

    logger.log(level, formatted)

    # Log entire traceback
    if not log_trace:
        return formatted

    trace = traceback.format_exception(type(e), e, e.__traceback__)
    trace = ''.join(trace)

    now = datetime.datetime.now().strftime('%d.%m.%y-%H%M%S')

    filename = f'{type(e).__name__}_{now.replace(":", "-")}.txt'
    filepath = os.path.join(Path.tracebacks, filename)
    filedir = os.path.dirname(filepath)

    os.makedirs(filedir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(trace)

    return formatted
