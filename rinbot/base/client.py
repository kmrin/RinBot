"""
RinBot's client (discord.ext.commands.Bot)
"""

import sys
import pytz
import discord
import wavelink

from discord.ext.commands import Bot
from typing import Dict

from rinbot.fortnite.api import FortniteAPI
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.valorant.db import DATABASE
from rinbot.music.player import Player

from .db import DBTable, DBManager
from .events import EventHandler
from .exception_handler import log_exception
from .extension_loader import load_extensions
from .get_os_path import get_os_path
from .intents import gen_intents
from .json_loader import get_conf, get_lang
from .launch_checks import check_cache, check_java
from .logger import logger
from .program_handler import ProgramHandler
from .tasks import TaskHandler

conf = get_conf()
text = get_lang()

class RinBot(Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=conf['PREFIX'],
            intents=gen_intents(),
            help_command=None
        )
        
        self.tts_clients: Dict[int, discord.VoiceClient] = {}
        self.music_clients: Dict[int, Player] = {}
        self.utc = pytz.utc
        self.db = DBManager()
        self.task_handler = TaskHandler(self)
        self.program_handler = ProgramHandler()

        self.fn_key = conf["FORTNITE_API_KEY"]
        self.fn_language = conf["FORTNITE_DAILY_SHOP_LANGUAGE"]
        if self.fn_language not in [
            "ar", "de", "en", "es", "es-419", "fr", "it", 
            "ja", "ko", "pl", "pt-BR", "ru", "tr","zh-CN", 
            "zh-Hant"
        ]:
            logger.warning(text['CLIENT_INVALID_FORTNITE_LANGUAGE'])
            self.fn_language = 'en'
        
        self.fortnite_api = FortniteAPI(self.fn_language, self.fn_key)
        
        self.val_db = DATABASE()
        self.val_endpoint = API_ENDPOINT()
        
        # Will I use AI?
        if conf['AI_ENABLED'] and conf['AI_CHANNELS']:
            from langchain.llms.koboldai import KoboldApiLLM

            self.endpoint = str(conf['AI_ENDPOINT_KOBOLD'])
            
            if len(self.endpoint.split('/api')) > 0:
                self.endpoint = self.endpoint.split('/api')[0]
            
            self.chatlog_dir = get_os_path('../instance/cache/chatlog')
            self.endpoint_connected = False
            self.channel_id = conf['AI_CHANNEL']
            self.num_lines_to_keep = 15
            self.guild_ids = [int(x) for x in conf['AI_CHANNELS'].split(',')]
            self.debug = True
            self.char_name = 'RinBot'
            self.endpoint_type = 'Kobold'
            self.llm = KoboldApiLLM(endpoint=self.endpoint, max_length=800)
    
    async def __recovery_loop(self):
        reset = input(text['FAILURE_LOGIN_INST'])
        
        if reset.lower() == 'y' or reset.lower() == 'yes':
            logger.info(text['FAILURE_LOGIN_YES'])
            
            await self.db.delete(DBTable.BOT)
            await self.db.setup()
            
            logger.info(text['FAILURE_LOGIN_SETUP_COMPLETE'])
            await self.init(from_recovery=True)
        
        elif reset.lower() == 'n' or reset.lower() == 'no':
            logger.info(text['FAILURE_LOGIN_NO'])
            await self.stop()
            
            sys.exit()
        else:
            await self.__recovery_loop()
    
    async def init(self, from_recovery: bool=False):
        """
        Startup sequence
        """
        
        if not from_recovery:
            # Checks
            check_cache()
            check_java()
            
            # Start db
            await self.db.setup()
            
            # Load events cog
            await self.add_cog(EventHandler(self))
            
            # Load all extensions
            await load_extensions(self)
            
            # Run necessary programs
            for program in conf['PROGRAMS']:
                if program == 'lavalink' and not conf['LAVALINK_USE_BUILTIN']:
                    continue
                
                await self.program_handler.start(program)
        
        # Log in to discord and build internal cache
        try:
            query = await self.db.get(DBTable.BOT)
            token = ''
            
            if not query:
                logger.critical(text['FAILURE_NO_TOKEN'])
                sys.exit()
            
            for row in query:
                token = row[0]
                break
            
            await self.start(token)
            
        except discord.LoginFailure:
            logger.critical(text['FAILURE_LOGIN'])
            await self.__recovery_loop()
            
        except (KeyboardInterrupt, SystemExit):
            await self.stop()
            
        except Exception as e:
            log_exception(e)

    async def stop(self):
        """
        Stop sequence
        """
        
        # Check for voice states and disconnect them
        for player in self.music_clients.values():
            await player.disconnect()
        
        for tts in self.tts_clients.values():
            await tts.disconnect()
        
        # Kill all running programs
        await self.program_handler.stop_all()
        
        # Close the bot
        await self.close()
    
    async def setup_hook(self) -> None:
        nodes = [
            wavelink.Node(
                uri=conf['LAVALINK_ENDPOINT'],
                password=conf['LAVALINK_PASSWORD']
            )
        ]
        
        await wavelink.Pool.connect(nodes=nodes, client=self)
