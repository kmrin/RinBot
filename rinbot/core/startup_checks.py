import os
import re
import sys
import nextcord
import subprocess

from .paths import get_os_path
from .loggers import Loggers, log_exception

logger = Loggers.STARTUP_CHECKS

def check_cache() -> None:
    logger.info('Checking cache dirs')
    
    folders = [
        '../instance',
        '../instance/database',
        '../instance/cache/fun',
        '../instance/cache/fortnite',
        '../instance/cache/fortnite/downloads',
        '../instance/cache/fortnite/composites',
        '../instance/cache/fortnite/stats',
        '../instance/cache/valorant',
        '../instance/cache/stickbug',
        '../instance/logs',
        '../instance/logs/tracebacks',
        '../instance/logs/lavalink',
        '../instance/logs/client',
        '../instance/tts'
    ]
    
    for folder in folders:
        path = get_os_path(folder)
        folder_name = folder.split('..')[1]
        
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                logger.info(f"Created directory '{folder_name}'")
        except PermissionError:
            logger.critical(f"Insufficient permissions to create folder '{folder}'")
        except OSError as e:
            log_exception(e, logger, True)
    
    logger.info('Checked cache dirs')

def check_java() -> None:
    logger.info('Checking java')
    
    try:
        output = subprocess.check_output(
            ['java', '-version'],
            stderr=subprocess.STDOUT, text=True
        )
    except FileNotFoundError:
        logger.critical(
            'Java was not found on your system, please install Java 17 or higher and try again.'
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.critical('Failed to check java version')
        log_exception(e, logger, True)
        sys.exit(1)
    
    match = re.search(r'version "(\d+)\.', output)
    if not match:
        logger.critical('Could not parse java version from output')
        sys.exit(1)
    
    ver = int(match.group(1))
    if ver < 17:
        logger.critical(f'Invalid java version found: {ver}. RinBot needs 17 or higher')
        sys.exit(1)
    
    logger.info(f'Checked java, version {ver} found')

async def check_token(token: str) -> bool:
    logger.info('Checking token')
    
    dummy = nextcord.Client(intents=nextcord.Intents.default())
    
    try:
        @dummy.event
        async def on_ready() -> None:
            await dummy.close()
        
        await dummy.start(token)
        
        logger.info('Token is valid')
        return True
    except nextcord.LoginFailure:
        await dummy.close()
        logger.error('Token is invalid')
        return False
    except Exception as e:
        log_exception(e, logger, critical=True)
        sys.exit(1)
