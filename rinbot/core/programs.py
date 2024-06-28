import os
import asyncio
import subprocess

from typing import Dict

from .json_manager import read
from .loggers import Loggers, log_exception
from .paths import Path

logger = Loggers.PROGRAMS

class ProgramHandler:
    def __init__(self) -> None:
        self._base_path = Path.programs
        self._programs: Dict[str, subprocess.Popen] = {}
        self._program_restart_sleep_time = 5
    
    async def start(self, program: str) -> None:
        logger.info(f"Starting '{program}'")
        
        program_path = os.path.join(self._base_path, program)
        if not os.path.exists(program_path):
            logger.error(f"Path to program '{program}' does not exist")
            return
        
        args = read(os.path.join(program_path, 'args.json'))
        if not args:
            logger.error(f"Args file not found for program '{program}'")
            return
        
        try:
            process = await asyncio.to_thread(
                subprocess.Popen,
                args, cwd=program_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._programs[program] = process
            
            logger.info(f"Started '{program}'")
        except Exception as e:
            log_exception(e, logger)
    
    async def stop(self, program: str) -> None:
        logger.info(f"Stopping '{program}'")
        
        try:
            process = self._programs.pop(program)
            process.terminate()
            
            logger.info(f"Stopped '{program}'")
        except KeyError:
            logger.error(f"Program '{program}' is not running")
        except Exception as e:
            log_exception(e, logger)
    
    async def stop_all(self) -> None:
        logger.info('Stopping all programs')
        
        for program in self._programs.keys():
            await self.stop(program)
            
            # Prevent looping (idk why it does that)
            if not self._programs:
                break
        
        logger.info('All programs stopped')
    
    async def restart(self, program: str) -> None:
        await self.stop(program)
        await asyncio.sleep(self._program_restart_sleep_time)
        await self.start(program)
