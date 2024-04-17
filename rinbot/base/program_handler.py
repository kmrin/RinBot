"""
Handles the opening and closing of external programs used by rinbot
"""

import os
import json
import asyncio
import subprocess

from typing import Dict

from .exception_handler import log_exception
from .get_os_path import get_os_path
from .json_loader import get_lang
from .logger import logger

text = get_lang()

class ProgramHandler:
    def __init__(self) -> None:
        self.__base_path = get_os_path('programs')
        self.__programs: Dict[str, subprocess.Popen] = {}
        self.__program_restart_sleep_time = 5
    
    async def start(self, program: str) -> None:
        logger.info(text['PG_HANDLER_STARTING'].format(pg=program))
        
        program_path = os.path.join(self.__base_path, program)
        
        if not os.path.exists(program_path):
            logger.error(text['PG_HANDLER_PATH_NOT_EXIST'].format(pg=program_path))
            return
        
        try:
            with open(os.path.join(program_path, 'args.json'), 'r', encoding='utf-8') as f:
                args = json.load(f)
        except FileNotFoundError:
            logger.error(text['PG_HANDLER_ARGS_NOT_EXIST'].format(pg=program))
            return
        
        try:
            process = await asyncio.to_thread(
                subprocess.Popen,
                args,
                cwd=program_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.__programs[program] = process
            
            logger.info(text['PG_HANDLER_STARTED'].format(pg=program))
        except Exception as e:
            log_exception(e)
    
    async def stop(self, program: str) -> None:
        logger.info(text['PG_HANDLER_STOPPING'].format(pg=program))
        
        try:
            process = self.__programs.pop(program)
            process.terminate()
            
            logger.info(text['PG_HANDLER_STOPPED'].format(pg=program))
        except KeyError:
            logger.error(text['PG_HANDLER_NOT_RUNNING'].format(pg=program))
        except Exception as e:
            log_exception(e)

    async def stop_all(self) -> None:
        logger.info(text['PG_HANDLER_STOPPING_ALL'])
        
        for program in self.__programs.keys():
            await self.stop(program)
            
            # Prevent looping (idk why it does that)
            if not self.__programs:
                break
        
        logger.info(text['PG_HANDLER_STOPPING_ALL_DONE'])
    
    async def restart(self, program: str) -> None:
        await self.stop(program)
        await asyncio.sleep(self.__program_restart_sleep_time)
        await self.start(program)

# TEST
async def do_test():    
    handler = ProgramHandler()
    
    await handler.start('lavalink')
    await asyncio.sleep(5)
    
    await handler.restart('lavalink')
    await asyncio.sleep(5)
    
    await handler.stop('lavalink')
    await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(do_test())
