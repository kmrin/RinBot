"""
Check functions ran at launch
"""

import os
import sys
import discord
import subprocess

from .exception_handler import log_exception
from .get_os_path import get_os_path
from .json_loader import get_lang
from .logger import logger

text = get_lang()

def check_cache() -> None:
    """
    A check ran at startup to make sure all cache dirs exits
    """

    folders = [
        '../instance',
        '../instance/database',
        '../instance/cache/fun',
        '../instance/cache/chatlog',
        '../instance/cache/stablediffusion',
        '../instance/cache/fortnite',
        '../instance/cache/fortnite/downloads',
        '../instance/cache/fortnite/composites',
        '../instance/cache/fortnite/stats',
        '../instance/cache/valorant',
        '../instance/cache/stickbug',
        '../instance/logs',
        '../instance/logs/tracebacks',
        '../instance/logs/lavalink',
        '../instance/logs/bot',
        '../instance/tts'
    ]
    
    for folder in folders:
        path = get_os_path(folder)
        folder_name = folder.split('..')[1]
        
        try:
            if not os.path.exists(path):
                os.makedirs(path)
                logger.info(text['CREATED_DIR'].format(dir=folder_name))
        except Exception as e:
            logger.critical(text['ERROR_CREATING_DIR'].format(dir=folder_name, error=e))

def check_java():
    """
    A check ran at startup to make sure the correct version of java is installed
    """
    
    def __quit():
        logger.critical(text['JAVA_NOT_FOUND'])
        sys.exit()
    
    logger.info(text['JAVA_CHECKING'])
    ver_line = ''
    
    try:
        output = subprocess.check_output('java -version',
            stderr=subprocess.STDOUT, shell=True, text=True)
        
        lines = output.split('\n')
        
        for line in lines:
            if 'version' in line.lower():
                ver_line = line
                
                break
            else:
                __quit()
        
        ver = ver_line.split()[2]
        ver = int(''.join(c for c in ver if c.isdigit() or c == '.').split('.')[0])
        
        try:
            if not ver >= 17:
                logger.error(text["JAVA_INVALID_VERSION"].format(ver=f':{ver}'))
                sys.exit()
        except:
            logger.error(text['JAVA_INVALID_VERSION'])
            sys.exit()
        
        logger.info(text['JAVA_FOUND'].format(ver=ver))
    except:
        __quit()

async def check_token(token: str) -> bool:
    """
    A check ran at startup to verify is the user provided token is valid or not

    Args:
        token (str): Your discord bot token

    Returns:
        bool: True if valid, else False
    """
    
    dummy = discord.Client(intents=discord.Intents.default())
    
    try:
        @dummy.event
        async def on_ready() -> None:
            await dummy.close()
        
        await dummy.start(token)
        
        return True
    except discord.LoginFailure:
        await dummy.close()
        
        return False
    except Exception as e:
        log_exception(e, critical=True)
        sys.exit()

# TEST
if __name__ == '__main__':
    import time
    import asyncio
        
    print("Checking cache")
    check_cache()
    time.sleep(1.5)
    
    print("Checking java")
    check_java()
    time.sleep(1.5)
    
    print("Checking token")
    result = asyncio.run(check_token(input("Provide a token for testing: ")))
    print(result)
