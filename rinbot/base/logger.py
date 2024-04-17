"""
Logger

- Log states:
    * logger.info
    * logger.warning
    * logger.error
    * logger.critical
"""

import os
import logging
import datetime

from .get_os_path import get_os_path

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

timestamp = datetime.datetime.now().strftime('%y.%m.%d-%H%M%S')
log_filename = get_os_path(f'../instance/logs/bot/rinbot-{timestamp}.log')
log_dirname = os.path.dirname(log_filename)

if not os.path.exists(log_dirname):
    os.makedirs(log_dirname)

logger = logging.getLogger('rinbot')
logger.setLevel(logging.INFO)

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

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# TEST
if __name__ == '__main__':
    logger.info('This is an info message')
    logger.warning('This is a warning message')
    logger.error('This is an error message')
    logger.critical('This is a critical message')
