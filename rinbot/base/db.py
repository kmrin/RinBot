"""
Database Manager
"""

import os
import sys
import aiosqlite

from typing import Union, Iterable, Dict, TYPE_CHECKING
from aiosqlite.cursor import Cursor
from sqlite3 import Row
from enum import Enum

from .exception_handler import log_exception
from .json_loader import get_lang
from .launch_checks import check_cache, check_token
from .logger import logger
from .paths import Path

if TYPE_CHECKING:
    from client import RinBot

text = get_lang()

class DBTable(Enum):
    ADMINS = 'admins'
    BLACKLIST = 'blacklist'
    BOT = 'bot'
    CURRENCY = 'currency'
    DAILY_SHOP_CHANNELS = 'daily_shop_channels'
    GUILDS = 'guilds'
    HISTORY_GUILDS = 'history_guilds'
    HISTORY_INDIVIDUAL = 'history_individual'
    OWNERS = 'owners'
    STORE = 'store'
    TTS = 'tts'
    VALORANT = 'valorant'
    WARNS = 'warns'
    WELCOME_CHANNELS = 'welcome_channels'

class DBColumns(Enum):
    class admins():
        GUILD_ID = "guild_id"
        USER_ID = "user_id"
    
    class blacklist():
        GUILD_ID = "guild_id"
        USER_ID = "user_id"

    class bot():
        TOKEN = "token"
    
    class currency():
        GUILD_ID = "guild_id"
        USER_ID = "user_id"
        WALLET = "wallet"
        MESSAGES = "messages"

    class daily_shop_channels():
        GUILD_ID = "guild_id"
        FORTNITE_ACTIVE = "fortnite_active"
        FORTNITE_CHANNEL_ID = "fortnite_channel_id"
        VALORANT_ACTIVE = "valorant_active"
        VALORANT_CHANNEL_ID = "valorant_channel_id"
    
    class guilds():
        GUILD_ID = "guild_id"
    
    class history_guilds():
        GUILD_ID = "guild_id"
        TITLE = "title"
        URL = "url"
    
    class history_individual():
        USER_ID = "user_id"
        TITLE = "title"
        URL = "url"
    
    class owners():
        USER_ID = "user_id"
    
    class sqlite_sequence():
        NAME = "name"
        SEQ = "seq"
    
    class store():
        GUILD_ID = "guild_id"
        ID = "id"
        NAME = "name"
        PRICE = "price"
        TYPE = "type"
    
    class tts():
        GUILD_ID = "guild_id"
        ACTIVE = "active"
        CHANNEL_ID = "channel_id"
        SAY_USER = "say_user"
        LANGUAGE = "language"

    class valorant():
        USER_ID = "user_id"
        ACTIVE = "active"
        TYPE = "type"
        TARGET_GUILD = "target_guild"

    class warns():
        GUILD_ID = "guild_id"
        USER_ID = "user_id"
        MODERATOR_ID = "moderator_id"
        WARN = "warn"
        ID = "id"
    
    class welcome_channels():
        GUILD_ID = "guild_id"
        ACTIVE = "active"
        CHANNEL_ID = "channel_id"
        CUSTOM_MSG = "custom_msg"

class DBManager:
    """
    Database Manager
    
    - Data manipulation functions:
        * get
        * put
        * update
        * delete
    """
    
    def __init__(self) -> None:
        # Make sure cache dirs exists in case of db usage in odd places
        check_cache()
        
        if not os.path.isfile(Path.schema):
            logger.critical(text['DB_ERROR_NO_SCHEMA'])
            sys.exit()
    
    @staticmethod
    async def __connect() -> aiosqlite.core.Connection:
        """
        Attempts a connection to the database and returns it

        Returns:
            aiosqlite.core.Connection: Connection
        """
        
        try:
            db = await aiosqlite.connect(Path.database)
            with open(Path.schema) as sc:
                await db.executescript(sc.read())
                return db
        except Exception as e:
            log_exception(e)
    
    async def get(self, table: DBTable, condition: str=None) -> Iterable[Row]:
        """
        Retrieves data from the database

        Args:
            table (DBTable): The database table
            condition (str, optional): SQL query condition (if any). Defaults to None.

        Returns:
            Iterable[Row]: Example of "bot" table: "[('token',)]"
        """

        conn = await self.__connect()

        try:
            cursor: Cursor = await conn.cursor()

            await cursor.execute(
                f'SELECT * FROM {table.value} WHERE {condition}'
                if condition else
                f'SELECT * FROM {table.value}'
            )

            rows = await cursor.fetchall()
            return rows
        except Exception as e:
            log_exception(e)
        finally:
            await conn.close()
    
    async def put(self, table: DBTable, data: Dict[str, Union[str, int]]) -> bool:
        """
        Puts data into the database

        Args:
            table (DBTable): The database table
            data (Dict[str, Union[str, int]]): The data as a dict where the keys are the columns and the values are the rows
        
        Returns:
            bool: True if successful else False
        """

        conn = await self.__connect()

        try:
            cursor: Cursor = await conn.cursor()

            placeholders = ", ".join(['?'] * len(data))
            columns = ", ".join(data.keys())
            values = tuple(data.values())

            await cursor.execute(
                f"INSERT INTO {table.value} ({columns}) VALUES ({placeholders})",
                values
            )

            await conn.commit()

            await cursor.execute(
                f"SELECT * FROM {table.value} WHERE rowid=last_insert_rowid()"
            )

            inserted = await cursor.fetchone()

            if inserted != values:
                return False

            return True
        except Exception as e:
            log_exception(e)
        finally:
            await conn.close()
    
    async def update(self, table: DBTable, data: Dict[str, Union[str, int]], condition: str=None, from_msg_event: bool=False) -> bool:
        """
        Updates an existing row on the database

        Args:
            table (DBTable): The database table
            data (Dict[str, Union[str, int]]):The data as a dict where the keys are the columns and the values are the rows
            condition (str, optional): SQL query condition (if any). Defaults to None.
            from_msg_event (bool, optional): If the update is coming from the on_message() bot event. Defaults to False.

        Returns:
            bool: True if the transaction was a success, else False
        """

        conn = await self.__connect()

        try:
            cursor: Cursor = await conn.cursor()

            set_clause = ", ".join([f'{key} = ?' for key in data.keys()])
            values = tuple(data.values())

            await cursor.execute(
                f'UPDATE {table.value} SET {set_clause} WHERE {condition}'
                if condition else
                f'UPDATE {table.value} SET {set_clause}',
                values
            )

            await conn.commit()

            if not cursor.rowcount > 0:
                if not from_msg_event:
                    logger.error(text['DB_ERROR_UPDATING'].format(tb=table.value))
                return False

            if not from_msg_event:
                logger.info(text['DB_UPDATED'].format(tb=table.value))

            return True
        except Exception as e:
            log_exception(e)
        finally:
            await conn.close()
    
    async def delete(self, table: DBTable, condition: str=None) -> bool:
        """
        Deletes rows from the database based on a condition

        Args:
            table (DBTable): The database table
            condition (str, optional): The condition to identify the rows to be deleted. Defaults to None.

        Returns:
            bool: True if the transaction was successful, else False
        """

        conn = await self.__connect()

        try:
            cursor: Cursor = await conn.cursor()

            await cursor.execute(
                f'DELETE FROM {table.value} WHERE {condition}'
                if condition else
                f'DELETE FROM {table.value}'
            )

            await conn.commit()

            if not cursor.rowcount > 0:
                return False

            return True
        except Exception as e:
            log_exception(e)
        finally:
            await conn.close()
    
    async def setup(self):
        """
        Goes through rinbot's initial setup

        Can be triggered once by a fresh database start

        Inserts the following data into the "bot" table:
            "token" = <bot token>
        Inserts the following data into the "owners" table:
            "user_id" = <owner id>
        """

        try:
            logger.info(text['DB_CHECK_START'])

            owners = await self.get(DBTable.OWNERS)

            if not owners:
                valid_id = False

                logger.warning(text['DB_NO_OWNERS'])
                logger.info(text['DB_NO_OWNERS_INST'])

                while not valid_id:
                    user_id = input(text['DB_ASK_ID'])

                    if user_id.isnumeric():
                        query = await self.put(DBTable.OWNERS, {'user_id': int(user_id)})

                        if not query:
                            logger.critical(text['DB_DB_ERROR'])
                            sys.exit()

                        valid_id = True
                    else:
                        logger.error(text['DB_INVALID_ID'])

            bot = await self.get(DBTable.BOT)

            if not bot:
                valid_token = False

                while not valid_token:
                    logger.warning(text['DB_NO_TOKEN'])
                    logger.info(text['DB_NO_TOKEN_INST'])

                    token = input(text['DB_ASK_TOKEN'])

                    logger.info(text['DB_CHECKING_TOKEN'])

                    if await check_token(token):
                        query = await self.put(DBTable.BOT, {'token': token})

                        if not query:
                            logger.critical(text['DB_DB_ERROR'])
                            sys.exit()

                        valid_token = True
                    else:
                        logger.error(text['DB_INVALID_TOKEN'])
        except Exception as e:
            log_exception(e)
    
    async def check_guilds(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_GUILDS'])

            query = await self.get(DBTable.GUILDS)

            db_joined = {row[0] for row in query}
            bot_joined = {guild.id for guild in bot.guilds}

            missing = bot_joined - db_joined
            extra = db_joined - bot_joined

            for guild in missing:
                await self.put(DBTable.GUILDS, {'guild_id': guild})
            for guild in extra:
                await self.delete(DBTable.GUILDS, condition=f'guild_id={guild}')

            logger.info(text['CHECKED_GUILDS'])
        except Exception as e:
            log_exception(e)

    async def check_welcome_channels(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_WELCOME_CHANNELS'])

            query = await self.get(DBTable.WELCOME_CHANNELS)
            in_db = {row[0] for row in query}

            for guild in bot.guilds:
                if guild.id not in in_db:
                    await self.put(DBTable.WELCOME_CHANNELS, {'guild_id': guild.id})

            logger.info(text['CHECKED_WELCOME_CHANNELS'])
        except Exception as e:
            log_exception(e)

    async def check_economy(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_ECONOMY'])

            for guild in bot.guilds:
                member_ids = [member.id for member in guild.members]

                for member_id in member_ids:
                    query = await self.get(DBTable.CURRENCY, condition=f'guild_id={guild.id} AND user_id={member_id}')

                    if not query:
                        await self.put(DBTable.CURRENCY, {'guild_id': guild.id, 'user_id': member_id})

            logger.info(text['CHECKED_ECONOMY'])
        except Exception as e:
            log_exception(e)

    async def check_daily_shop(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_DAILY'])

            for guild in bot.guilds:
                query = await self.get(DBTable.DAILY_SHOP_CHANNELS, condition=f'guild_id={guild.id}')
                if not query:
                    await self.put(DBTable.DAILY_SHOP_CHANNELS, {'guild_id': guild.id})

            logger.info(text['CHECKED_DAILY'])
        except Exception as e:
            log_exception(e)

    async def check_valorant(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_VALORANT'])

            for guild in bot.guilds:
                member_ids = [member.id for member in guild.members]

                for member_id in member_ids:
                    query = await self.get(DBTable.VALORANT, condition=f'user_id={member_id}')

                    if not query:
                        await self.put(DBTable.VALORANT, {'user_id': member_id})

            logger.info(text['CHECKED_VALORANT'])
        except Exception as e:
            log_exception(e)

    async def check_tts(self, bot: 'RinBot'):
        try:
            logger.info(text['CHECKING_TTS'])
            
            for guild in bot.guilds:
                query = await self.get(DBTable.TTS, condition=f'guild_id={guild.id}')
                
                if not query:
                    await self.put(
                        DBTable.TTS,
                        {
                            'guild_id': guild.id,
                            'language': 'en'
                        }
                    )
            
            logger.info(text['CHECKED_TTS'])
        except Exception as e:
            log_exception(e)

    async def check_all(self, bot: 'RinBot'):
        await self.check_guilds(bot)
        await self.check_welcome_channels(bot)
        await self.check_economy(bot)
        await self.check_daily_shop(bot)
        await self.check_valorant(bot)
        await self.check_tts(bot)

# TEST
async def do_test():
    db = DBManager()
    
    await db.setup()
    
    print("\nAdding admins")
    await db.put(DBTable.ADMINS, {
        'guild_id': 1234, 'user_id': 1234})
    await db.put(DBTable.ADMINS, {
        'guild_id': 5678, 'user_id': 1234})
    await db.put(DBTable.ADMINS, {
        'guild_id': 1234, 'user_id': 5678})
    
    print("\nShowing current admins")
    admins = await db.get(DBTable.ADMINS)
    print(admins)

    print("\nRemoving an admin")
    await db.delete(DBTable.ADMINS, "guild_id=1234 AND user_id=5678")

    print("\nShowing current admins")
    admins = await db.get(DBTable.ADMINS)
    print(admins)

    print("\nUpdating an admin's ID")
    await db.update(DBTable.ADMINS, data={'user_id': 9012}, condition='guild_id=5678')

    print("\nShowing current admins")
    admins = await db.get(DBTable.ADMINS)
    print(admins)

if __name__ == '__main__':
    import asyncio
    
    asyncio.run(do_test())
