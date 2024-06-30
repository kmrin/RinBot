import sys
import pytz
import nextcord

from nextcord.ext.commands import Bot
from typing import Dict, TYPE_CHECKING

from rinbot.gemini.conversation import GeminiClient
from rinbot.fortnite.api import FortniteAPI
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.valorant.db import DATABASE

from .commands import Core
from .db import DBTable, DBManager
from .events import EventHandler
from .loggers import Loggers, log_exception
from .loader import load_extensions
from .paths import get_os_path
from .helpers import gen_intents
from .json_manager import get_conf
from .startup_checks import check_cache, check_java
from .programs import ProgramHandler
from .tasks import TaskHandler
from .types import TTSClient

if TYPE_CHECKING:
    from rinbot.music.player import Player

logger = Loggers.CLIENT
conf = get_conf()

class RinBot(Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=conf['PREFIX'],
            intents=gen_intents(conf['INTENTS']),
            help_command=None
        )
        
        self.tts_clients: Dict[int, TTSClient] = {}
        self.music_clients: Dict[int, 'Player'] = {}
        self.utc = pytz.utc
        self.db = DBManager()
        self.task_handler = TaskHandler(self)
        self.program_handler = ProgramHandler()
        
        self.fn_key = conf['FORTNITE_KEY']
        self.fn_lang = conf['FORTNITE_DAILY_SHOP_LANG']
        if self.fn_lang not in [
            "ar", "de", "en", "es", "es-419", "fr", "it", 
            "ja", "ko", "pl", "pt-BR", "ru", "tr","zh-CN", 
            "zh-Hant"
        ]:
            logger.warning('Invalid fortnite daily shop language selected, defaulting to english')
            self.fn_lang = 'en'
        
        self.fortnite_api = FortniteAPI(self.fn_lang, self.fn_key)
        
        self.val_db = DATABASE()
        self.val_endpoint = API_ENDPOINT()
        
        self.gemini: GeminiClient = None
        if conf['GEMINI_KEY']:
            self.gemini = GeminiClient(conf['GEMINI_KEY'])
                
        # Will I use AI?
        if conf['USE_LOCAL_KOBOLD'] and conf['KOBOLD_CHANNEL']:
            from langchain_community.llms.koboldai import KoboldApiLLM
            
            self.kb_endpoint: str = conf['KOBOLD_ENDPOINT']
            if len(self.kb_endpoint.split('/api')) > 0:
                self.kb_endpoint = self.kb_endpoint.split('/api')[0]
            
            self.kb_chatlog_dir = get_os_path('../instance/cache/chatlog')
            self.kb_endpoint_conn = False
            self.kb_channel_id = conf['KOBOLD_CHANNEL']
            self.kb_num_lines_to_keep = 15
            self.kb_guild_ids = [int(x) for x in conf['AI_CHANNEL'].split(',')]
            self.kb_debug = True
            self.kb_char_name = conf['KOBOLD_AI_NAME']
            self.kb_endpoint_type = 'Kobold'
            self.kb_llm = KoboldApiLLM(endpoint=self.kb_endpoint, max_length=800)
    
    async def __recovery_loop(self) -> None:
        logger.critical('RinBot failed to login due to an invalid token, would you like to replace it?')
        
        reset = input('Y / N: ').lower()
        if reset == 'y' or reset == 'yes':
            logger.info('Deleting old token from database')
            
            await self.db.delete(DBTable.BOT)
            await self.db.setup()
            
            logger.info('Recovery complete')
            
            await self.init(from_recovery=True)
        elif reset == 'n' or reset == 'no':
            logger.info('Understood, shutting down')
            
            await self.stop()
            sys.exit(1)
        else:
            logger.error('Invalid input, try again')
            
            await self.__recovery_loop()
    
    async def init(self, from_recovery: bool = False) -> None:
        """
        Startup sequence
        """
        
        if not from_recovery:
            # Checks
            check_cache()
            check_java()
            
            # Start db
            await self.db.setup()
            
            # Load core cogs
            self.add_cog(EventHandler(self))
            self.add_cog(Core(self))
            logger.info('Loaded internal extensions')
            
            # Load all extensions
            load_extensions(self)
            
            # Run necessary programs
            for program in conf['EXTERNAL_PROGRAMS']:
                if program == 'lavalink' and not conf['USE_BUILTIN_LAVALINK_SERVER']:
                    continue
                
                await self.program_handler.start(program)
        
        # Log in to discord and build internal cache
        try:
            query = await self.db.get(DBTable.BOT)
            
            if not query:
                logger.critical('Could not query database and fetch token')
                sys.exit(1)
            
            await self.start(query[0][0])
        except nextcord.LoginFailure:
            await self.__recovery_loop()
        except (KeyboardInterrupt, SystemExit):
            await self.stop()
        except Exception as e:
            log_exception(e, logger)

    async def stop(self) -> None:
        """
        Stop sequence
        """
        
        # Check for voice states and disconnect them
        """ for player in self.music_clients.values():
            await player.dc(force=True) """
        for tts in self.tts_clients.values():
            await tts.client.disconnect(force=True)
        
        # Kill all running programs
        await self.program_handler.stop_all()
        
        # Close the client
        await self.close()
