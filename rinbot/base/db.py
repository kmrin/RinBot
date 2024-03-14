"""
#### Database manager\n
Contains functions that add, remove or modify contents inside RinBot's database
"""

import os, sys, json, aiosqlite
from typing import Literal
from rinbot.base.helpers import load_lang, check_token, format_exception, get_path
from rinbot.base.logger import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

text = load_lang()

DB_DIR = get_path("database")
DB_PATH = get_path("database/sqlite.db")

# Check if schema file is present
if not os.path.isfile(f"{DB_DIR}/schema.sql"):
    logger.critical(text["DBMAN_SCHEMA_NOT_FOUND"])
    sys.exit()

class DBManager:
    def __init__(self, bot: "RinBot"):
        self.bot = bot
    
    async def connect(self) -> aiosqlite.core.Connection:
        """
        #### Starts a connection with the database
        - returns:
            * aiosqlite.core.Connection
        """
        
        try:
            db = await aiosqlite.connect(DB_PATH)
            with open(f"{DB_DIR}/schema.sql") as sc:
                await db.executescript(sc.read())
                return db
        except Exception as e:
            logger.error(format_exception(e))
    
    async def setup(self):
        """
        #### Goes through rinbot's initial setup\n

        Can be triggered once by a fresh database start\n

        Inserts the following data into the "bot" table:
            data: dict = `{"token": <bot token>}`

        Inserts the following data into the "owners" table:
            data: list = `[<owner id>]`
        :return:
        """
        
        conn = await self.connect()
        
        try:
            logger.info(text["DBMAN_CHECK_START"])

            query = await conn.execute("SELECT data FROM owners")
            result = await query.fetchone()

            owners = json.loads(result[0])

            if not owners:
                valid_id = False

                logger.warning(text["DBMAN_NO_OWNERS"])
                logger.info(text["DBMAN_NO_OWNERS_INST"])

                while not valid_id:
                    id = input(text["DBMAN_ASK_ID"])
                    if id.isnumeric():
                        query = await self.update("owners", [str(id)])
                        if not query:
                            logger.critical(text["DBMAN_DB_ERROR"])
                            sys.exit()
                        else:
                            valid_id = True
                    else:
                        logger.error(text["DBMAN_INVALID_ID"])

            query = await conn.execute("SELECT data FROM bot")
            result = await query.fetchone()

            bot = json.loads(result[0])

            if not bot["token"]:
                valid_token = False
                while not valid_token:
                    logger.warning(text["DBMAN_NO_TOKEN"])
                    logger.info(text["DBMAN_NO_TOKEN_INST"])

                    token = input(text['DBMAN_ASK_TOKEN'])

                    logger.info(text["DBMAN_CHECKING_TOKEN"])
                    if await check_token(token):
                        bot["token"] = token
                        query = await self.update("bot", bot)
                        if not query:
                            logger.critical(text["DBMAN_DB_ERROR"])
                            sys.exit()
                        else:
                            valid_token = True
                    else:
                        logger.error(text["DBMAN_INVALID_TOKEN"])
            logger.info(text["DBMAN_CHECK_DONE"])
        except Exception as e:
            logger.error(f"{format_exception(e)}")
        finally:
            await conn.close()
    
    async def populate(self):
        """
        #### Populates RinBot's DB with base data 
        """
        
        conn = await self.connect()
        base = {
            "bot": {"token": False}, "owners": [], "admins": {}, "blacklist": {},
            "guilds": [], "warns": {}, "currency": {}, "histories": {},
            "welcome_channels": {}, "daily_shop_channels": {}, "store": {}, "valorant": {}}

        try:
            for table, data in base.items():
                query = await conn.execute(f"SELECT data FROM {table}")
                is_present = await query.fetchone()
                if not is_present:
                    await conn.execute(f"INSERT INTO {table}(DATA) VALUES(?)",
                                       (json.dumps(data, ensure_ascii=False, indent=4),))
                    await conn.commit()
        except Exception as e:
            logger.error(format_exception(e))
        finally:
            await conn.close()
    
    async def get(self, table: Literal[
        "bot", "owners", "admins", "blacklist", "guilds", "warns", "currency",
        "histories", "welcome_channels", "daily_shop_channels", "store", "valorant"
    ]) -> dict | list | None:
        """
        #### Reads a table on the database and returns it's data\n
        """
        
        conn = await self.connect()

        try:
            async with conn.execute(f"SELECT data FROM {table}") as cursor:
                result = await cursor.fetchone()
                if result:
                    return json.loads(result[0])
                else:
                    return None
        except Exception as e:
            logger.error(format_exception(e))
        finally:
            await conn.close()
    
    async def update(self, table: Literal[
        "bot", "owners", "admins", "blacklist", "guilds", "warns", "currency",
        "histories", "welcome_channels", "daily_shop_channels", "store", "valorant"
    ], data: dict | list, from_msg: bool=False) -> bool:
        """
        Updates a table on the database with the provided data\n
        The data needs to be in JSON format, either a dict or a list\n
        This function will then make a comparison to see if the data on the db\n
        equals the data provided, if so, the data was updated successfully (True) else False
        :return: bool
        """
        
        conn = await self.connect()

        try:
            await conn.execute(f"UPDATE {table} SET data=?",
                               (json.dumps(data, ensure_ascii=False, indent=4),))
            await conn.commit()

            current = await self.get(table)
            if current == data:
                if not from_msg:
                    logger.info(f"{text['DBMAN_TABLE_UPDATED']} '{table}'")
                return True
            else:
                logger.error(f"{text['DBMAN_ERROR_UPDATING_TABLE']} '{table}'")
                return False
        except Exception as e:
            logger.error(format_exception(e))
        finally:
            await conn.close()
    
    async def startup(self):
        """
        #### Executes the necessary functions to get the db ready
        """
        
        await self.populate()
        await self.setup()
    
    async def check_guilds(self):
        logger.info(text["INIT_CHECKING_GUILDS"])

        joined = await self.get("guilds")

        for guild in self.bot.guilds:
            if str(guild.id) not in joined:
                joined.append(str(guild.id))

        update = await self.update("guilds", joined)
        if update:
            logger.info(text["INIT_CHECKED_GUILDS"])
        else:
            logger.error(text["INIT_ERROR_CHECKING_GUILDS"])

    async def check_economy(self):
        logger.info(text["INIT_CHECKING_ECONOMY"])

        economy = await self.get("currency")

        for guild in self.bot.guilds:
            if str(guild.id) not in economy.keys():
                economy[str(guild.id)] = {}

            for member in guild.members:
                if str(member.id) not in economy[str(guild.id)]:
                    economy[str(guild.id)][str(member.id)] = {"wallet": 500, "messages": 0}

            logger.info(f"{text['INIT_CURR_GUILD'][0]} {guild.member_count} {text['INIT_CURR_GUILD'][1]} {guild.name} (ID: {guild.id})")

            update = await self.update("currency", economy)
            if update:
                logger.info(text["INIT_CHECKED_ECONOMY"])
            else:
                logger.error(text["INIT_ERROR_CHECKING_ECONOMY"])

    async def check_valorant(self):
        logger.info(text["INIT_CHECKING_VALORANT"])

        val = await self.get("valorant")

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in val.keys():
                val[guild_id] = {"active": False, "channel_id": 0, "members": {}}

            for member in guild.members:
                member_id = str(member.id)
                if member_id not in val[guild_id]["members"].keys():
                    val[guild_id]["members"][member_id] = {"active": False, "type": 0}

        update = await self.update("valorant", val)
        if update:
            logger.info(text['INIT_CHECKED_VALORANT'])
        else:
            logger.error(text['INIT_ERROR_CHECKING_VALORANT'])
    
    async def check_all(self):
        await self.check_economy()
        await self.check_guilds()
        await self.check_valorant()

class OfflineDB:
    def __init__(self):
        pass
    
    async def connect(self) -> aiosqlite.core.Connection:
        try:
            db = await aiosqlite.connect(DB_PATH)
            with open(f"{DB_DIR}/schema.sql") as sc:
                await db.executescript(sc.read())
                return db
        except Exception as e:
            logger.error(format_exception(e))
    
    async def get(self, table: Literal[
        "bot", "owners", "admins", "blacklist", "guilds", "warns", "currency",
        "histories", "welcome_channels", "daily_shop_channels", "store", "valorant"
    ]) -> dict | list | None:
        """
        #### Reads a table on the database and returns it's data\n
        """
        
        conn = await self.connect()

        try:
            async with conn.execute(f"SELECT data FROM {table}") as cursor:
                result = await cursor.fetchone()
                if result:
                    return json.loads(result[0])
                else:
                    return None
        except Exception as e:
            logger.error(format_exception(e))
        finally:
            await conn.close()