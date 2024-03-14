"""
#### Program Handler\n
Handles the opening and closing of external programs used by rinbot
"""

import os, json, asyncio, subprocess
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang, format_exception, get_path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

text = load_lang()

class ProgramHandler:
    def __init__(self, bot: "RinBot"):
        self.base_path = get_path("programs")
        self.programs = {}
        self.bot = bot
    
    async def run(self, program: str):
        if not os.path.exists(os.path.join(self.base_path, program)):
            logger.error(text["PG_HANDLER_PATH_NOT_EXISTS"])
            return
        
        try:
            with open(f"rinbot/programs/{program}/args.json", encoding="utf-8") as f:
                args = json.load(f)
        except FileNotFoundError:
            logger.error(text["PG_HANDLER_ARGS_NOT_EXISTS"])
            return
        
        try:
            process = await asyncio.to_thread(subprocess.Popen, args, cwd=f"rinbot/programs/{program}",
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.programs[program] = process
            logger.info(f"{text['PG_HANDLER_STARTED']} '{program}'")
        except Exception as e:
            logger.error(f"{text['PG_HANDLER_ERROR_RUNNING']} '{program}': {format_exception(e)}")
    
    async def stop(self, program: str):
        try:
            process: subprocess.Popen = self.programs.pop(program)
            process.terminate()
            logger.info(f"{text['PG_HANDLER_STOPPED']} '{program}'")
        except KeyError:
            logger.error(
                f"{text['PG_HANDLER_NOT_RUNNING'][0]} '{program}' {text['PG_HANDLER_NOT_RUNNING'][1]}")
        except Exception as e:
            logger.error(
                f"{text['PG_HANDLER_ERROR_STOPPING']} '{program}': {format_exception(e)}")

    async def stop_all(self):
        for name, program in self.programs.items():
            try:
                program.terminate()
                self.programs.pop(name)
                logger.info(f"{text['PG_HANDLER_STOPPED']} '{name}'")
                if not self.programs:
                    break
            except KeyError:
                logger.error(
                    f"{text['PG_HANDLER_NOT_RUNNING'][0]} '{name}' {text['PG_HANDLER_NOT_RUNNING'][1]}")
            except Exception as e:
                logger.error(
                    f"{text['PG_HANDLER_ERROR_STOPPING']} '{name}': {format_exception(e)}")