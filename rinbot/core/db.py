import os
import sys
import aiosqlite

from enum import Enum
from sqlite3 import OperationalError
from typing import TYPE_CHECKING, Optional, Iterable, Union, Dict

from .paths import Path
from .loggers import Loggers, log_exception
from .startup_checks import check_cache, check_token

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.DB

class DBTable(Enum):
    ADMINS = 'admins'
    BLACKLIST = 'blacklist'
    BOT = 'bot'
    CURRENCY = 'currency'
    DAILY_SHOP_CHANNELS = 'daily_shop_channels'
    FAV_TRACKS = 'fav_tracks'
    FAV_PLAYLISTS = 'fav_playlists'
    GUILDS = 'guilds'
    HISTORY_GUILDS = 'history_guilds'
    HISTORY_INDIVIDUAL = 'history_individual'
    OWNERS = 'owners'
    STORE = 'store'
    TTS = 'tts'
    WARNS = 'warns'
    WELCOME_CHANNELS = 'welcome_channels'

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
        # Make sure cache dirs exist in case of db usage in odd places
        check_cache()
        
        if not os.path.isfile(Path.schema):
            logger.critical('Database schema file not found. Check your RinBot instance')
            sys.exit(1)
    
    @staticmethod
    async def _connect() -> Optional[aiosqlite.core.Connection]:
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
        except (OSError, UnicodeDecodeError) as e:
            log_exception(e, logger, True)
            sys.exit(1)
        except aiosqlite.DatabaseError as e:
            log_exception(e, logger)
        
        # Return None if there are connection errors
        return None
    
    async def get(self, table: DBTable, condition: str = None, silent: bool = False) -> Optional[Iterable[aiosqlite.Row]]:
        """
        Retrieves data from the database

        Args:
            table (DBTable): The database table
            condition (str, optional): SQL query condition (if any). Defaults to None.

        Returns:
            Iterable[aiosqlite.Row]: Example of 'bot' table: '[("token",)]'
        """
        
        if not silent:
            logger.info(f'GET database operation: [T: {table} | C: {condition}]')
        
        conn = await self._connect()
        if conn is None:
            return None
        
        try:
            async with conn.execute(
                f'SELECT * FROM {table.value} WHERE {condition}'
                if condition else
                f'SELECT * FROM {table.value}'
            ) as cursor:
                rows = await cursor.fetchall()
            
            if not silent:
                logger.info('GET operation successful')
            
            return rows
        except (aiosqlite.ProgrammingError, TypeError) as e:
            log_exception(e, logger)
        except AttributeError as e:
            logger.error(f'Invalid table or connection error: {e}')
        except OperationalError:
            return None
        finally:
            await conn.close()
        
        return None
    
    async def put(self, table: DBTable, data: Dict[str, Union[str, int]], silent: bool = False) -> bool:
        """
        Inserts data into the database

        Args:
            table (DBTable): The database table
            data (Dict[str, Union[str, int]]): Data as a dict, keys are columns, values are rows

        Returns:
            bool: True if successful, otherwise False
        """
        
        if not silent:
            logger.info(f'PUT database operation: [T: {table}]')
        
        conn = await self._connect()
        if conn is None:
            return False
        
        try:
            async with conn.cursor() as cursor:
                placeholders = ', '.join(['?'] * len(data))
                columns = ', '.join(data.keys())
                values = tuple(data.values())
                
                await cursor.execute(
                    f'INSERT INTO {table.value} ({columns}) VALUES ({placeholders})',
                    values
                )
                
                await conn.commit()
                
                await cursor.execute(
                    f'SELECT * FROM {table.value} WHERE rowid=last_insert_rowid()'
                )
                
                inserted = await cursor.fetchone()
                
                if not silent:
                    logger.info('PUT operation successful')
                
                return inserted == values
        except aiosqlite.IntegrityError as e:
            log_exception(e, logger)
        except Exception as e:
            log_exception(e, logger)
        finally:
            await conn.close()
        
        return False
    
    async def update(self, table: DBTable, data: Dict[str, Union[str, int]], condition: str = None, silent: bool = False) -> bool:
        """
        Updates an existing row in the database.

        Args:
            table (DBTable): The database table.
            data (Dict[str, Union[str, int]]): Data as a dict, keys are columns, values are rows.
            condition (str, optional): SQL query condition (if any). Defaults to None.
            from_msg_event (bool, optional): If the update is from the on_message() bot event. Defaults to False.

        Returns:
            bool: True if successful, False otherwise.
        """
        
        if not silent:
            logger.info(f'UPDATE database operation: [T: {table} | C: {condition}]')
        
        conn = await self._connect()
        if not conn:
            return False
        
        try:
            async with conn.cursor() as cursor:
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
                    if not silent:
                        logger.warning('UPDATE operation failure, no rows were updated')
                    
                    return False
                
                if not silent:
                    logger.info('UPDATE operation successful')
                
                return True
        except aiosqlite.IntegrityError as e:
            log_exception(e, logger)
            
            # Rollback the transaction if it explicitly fails
            await conn.rollback()
        except Exception as e:
            log_exception(e, logger)
        finally:
            await conn.close()
        
        return False
    
    async def delete(self, table: DBTable, condition: str = None, silent: bool = False) -> bool:
        """
        Deletes rows from the database based on a condition.

        Args:
            table (DBTable): The database table.
            condition (str, optional): The condition to identify rows to be deleted. Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
        
        if not silent:
            logger.info(f'DELETE database operation: [T: {table} | C: {condition}]')
        
        conn = await self._connect()
        if not conn:
            return False
        
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    f'DELETE FROM {table.value} WHERE {condition}'
                    if condition else
                    f'DELETE FROM {table.value}'
                )
                
                await conn.commit()
                
                if not cursor.rowcount > 0:
                    if not silent:
                        logger.error('DELETE operation failed, check condition or if table was already empty')
                    
                    return False
                
                if not silent:
                    logger.info('DELETE operation successful')
                
                return True
        except aiosqlite.IntegrityError as e:
            log_exception(e, logger)
            
            # Rollback the transaction if it explicitly fails
            await conn.rollback()
        except Exception as e:
            log_exception(e, logger)
        finally:
            await conn.close()
        
        return False
    
    async def setup(self) -> None:
        """
        Goes through rinbot's initial setup
        
        Can be triggered once by a fresh database start
        
        Inserts the following data into the "bot" table:
            "token" = <bot token>
        Inserts the following data into the "owners" table:
            "user_id" = <owner id>
        """
        
        def _ohoh() -> None:
            logger.critical('Something bad happened X(')
            sys.exit(1)
        
        logger.info('Checking database status')
        
        owners = await self.get(DBTable.OWNERS, silent=True)
        if not owners:            
            logger.warning('No owners registered on the database!')
            logger.info('Please insert your discord user ID below so I can register you as my owner :)')
            
            while True:
                user_id = input('User ID: ')
                if user_id.isnumeric():
                    query = await self.put(DBTable.OWNERS, {'user_id': int(user_id)}, silent=True)
                    if not query:
                        _ohoh()
                    
                    break
                    
                logger.error('Invalid ID! Make sure it only contains numbers!')
        
        bot = await self.get(DBTable.BOT, silent=True)
        if not bot:            
            while True:
                logger.warning('No token registered on the database!')
                logger.info('Please insert your discord app token below!')
                
                token = input('App token: ')
                
                logger.info('Checking provided token')
                
                if await check_token(token):
                    query = await self.put(DBTable.BOT, {'token': token}, silent=True)
                    if not query:
                        _ohoh()
                    
                    break
                
                logger.error('Invalid token! Make sure you copied it right.')
    
    async def check_guilds(self, bot: 'RinBot') -> None:
        logger.info('Checking guilds')
        
        query = await self.get(DBTable.GUILDS, silent=True)
        
        db_joined = {row[0] for row in query}
        bot_joined = {guild.id for guild in bot.guilds}
        
        missing = bot_joined - db_joined
        extra = db_joined - bot_joined
        
        for guild in missing:
            await self.put(DBTable.GUILDS, {'guild_id': guild}, silent=True)
        for guild in extra:
            await self.delete(DBTable.GUILDS, f'guild_id={guild}', silent=True)
        
        logger.info('Checked guilds')
    
    async def check_welcome_channels(self, bot: 'RinBot') -> None:
        logger.info('Checking welcome channels')
        
        query = await self.get(DBTable.WELCOME_CHANNELS, silent=True)
        in_db = {row[0] for row in query}
        
        for guild in bot.guilds:
            if guild.id not in in_db:
                await self.put(DBTable.WELCOME_CHANNELS, {'guild_id': guild.id}, silent=True)
        
        logger.info('Checked welcome channels')
    
    async def check_economy(self, bot: 'RinBot') -> None:
        logger.info('Checking economy')
        
        for guild in bot.guilds:
            member_ids = [member.id for member in guild.members]
            
            for member_id in member_ids:
                query = await self.get(DBTable.CURRENCY, f'guild_id={guild.id} AND user_id={member_id}', silent=True)
                
                if not query:
                    await self.put(DBTable.CURRENCY, {'guild_id': guild.id, 'user_id': member_id}, silent=True)
        
        logger.info('Checked economy')
    
    async def check_daily_shop(self, bot: 'RinBot') -> None:
        logger.info('Checking daily shop')
        
        for guild in bot.guilds:
            query = await self.get(DBTable.DAILY_SHOP_CHANNELS, f'guild_id={guild.id}', silent=True)
            
            if not query:
                await self.put(DBTable.DAILY_SHOP_CHANNELS, {'guild_id': guild.id}, silent=True)
        
        logger.info('Checked daily shop')
    
    async def check_all(self, bot: 'RinBot'):
        await self.check_guilds(bot)
        await self.check_welcome_channels(bot)
        await self.check_economy(bot)
        await self.check_daily_shop(bot)
