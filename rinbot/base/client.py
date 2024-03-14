"""
#### RinBot's client (discord.ext.commands.Bot)
"""

import sys, pytz, discord, wavelink
# from typing import Literal
# from discord.channel import TextChannel
from discord.ext.commands import Bot
from rinbot.fortnite.api import FortniteAPI
from rinbot.valorant.db import DATABASE
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.base.helpers import load_lang, load_config, gen_intents, format_exception, check_cache, check_java
from rinbot.base.loader import load_extensions
from rinbot.base.programs import ProgramHandler
from rinbot.base.events import EventHandler
from rinbot.base.tasks import TaskHandler
from rinbot.base.db import DBManager
from rinbot.base.logger import logger
from rinbot.base.colors import *

config = load_config()
text = load_lang()

class RinBot(Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=gen_intents())
        
        self.utc = pytz.utc
        
        self.db = DBManager(self)
        self.task_handler = TaskHandler(self)
        self.program_handler = ProgramHandler(self)
        
        self.fn_language = config["FORTNITE_DAILY_SHOP_LANGUAGE"]
        if self.fn_language not in ["ar", "de", "en", "es", "es-419", "fr", "it", "ja", "ko", "pl", "pt-BR", "ru", "tr", "zh-CN", "zh-Hant"]:
            logger.error(f"{text['INIT_INVALID_FN_LANGUAGE'][0]}{self.fn_language}{text['INIT_INVALID_FN_LANGUAGE'][1]}")
            sys.exit()
        self.fortnite_api = FortniteAPI(self.fn_language, config["FORTNITE_API_KEY"])
        
        self.val_db = DATABASE()
        self.val_endpoint = API_ENDPOINT()
        
        # Will I use AI?
        if config["AI_ENABLED"] and config["AI_CHANNELS"]:
            from langchain.llms.koboldai import KoboldApiLLM
            
            # AI specific settings
            self.endpoint = str(config["AI_ENDPOINT_KOBOLD"])
            if len(self.endpoint.split("/api")) > 0:
                self.endpoint = self.endpoint.split("/api")[0]
            self.chatlog_dir = "cache/chatlog"
            self.endpoint_connected = False
            self.channel_id = config["AI_CHANNEL"]
            self.num_lines_to_keep = 15
            self.guild_ids = [int(x) for x in config["AI_CHANNEL"].split(",")]
            self.debug = True
            self.char_name = "RinBot"
            self.endpoint_type = "Kobold"
            self.llm = KoboldApiLLM(endpoint=self.endpoint, max_length=800)
    
    async def init(self):
        """
        #### Bot startup sequence
        """
        
        # Checks
        check_cache()
        check_java()
        
        # Load events cog
        await self.add_cog(EventHandler(self))
        
        # Initialise db
        await self.db.startup()
        
        # Load all extensions
        await load_extensions(self)
        
        # Run lavalink
        if config["LAVALINK_USE_BUILTIN"]:
            await self.program_handler.run("lavalink")
        
        # Log in to discord and build internal cache
        try:
            bot = await self.db.get("bot")
            await self.start(token=bot["token"], reconnect=True)
        except (KeyboardInterrupt, SystemExit):
            if config["LAVALINK_USE_BUILTIN"]:
                await self.program_handler.stop("lavalink")
        except Exception as e:
            logger.error(format_exception(e))
    
    async def stop(self):
        """
        #### Bot stop sequence
        """
        
        # Kill all running programs
        await self.program_handler.stop_all()
        
        # Close the bot
        await self.close()
    
    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri=config["LAVALINK_ENDPOINT"], password=config["LAVALINK_PASSWORD"])]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=None)
    
    """ async def log(self, type: Literal["info", "warning", "error", "critical"], message:str):        
        colors = {"info": GREEN, "warning": YELLOW, "error": RED, "critical": PURPLE}

        if type == "info": logger.info(message)
        elif type == "warning": logger.warning(message)
        elif type == "error": logger.error(message)
        elif type == "critical": logger.critical(message)

        if not self.is_ready():
            return

        channel = self.get_channel(int(config["LOG_CHANNEL"])) or await self.fetch_channel(int(config["LOG_CHANNEL"]))

        if not channel:
            return

        if not isinstance(channel, TextChannel):
            logger.error(text["CLIENT_CHANNEL_NOT_TEXT"])
            return

        embed = discord.Embed(description=f"> {message}", color=colors[type])
        await channel.send(embed=embed) """