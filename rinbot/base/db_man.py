"""
#### Database Manager
Contains functions that add, remove, or modify contents inside RinBot's database
"""

# Imports
import os, sys, json, aiosqlite
from rinbot.base.helpers import load_lang, format_exception, check_token
from rinbot.base.logger import logger

# Load text
text = load_lang()

# DB dirs
DB_DIR = f"{os.path.realpath(os.path.dirname(__file__))}/../database/"
DB_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/sqlite.db"

# Check if the schema file is present
if not os.path.isfile(f"{DB_DIR}/schema.sql"):
    logger.error(text['DBMAN_SCHEMA_NOT_FOUND'])

async def init_db() -> aiosqlite.core.Connection:
    """
    Starts a connection with the database and returns a aiosqlite connection object
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        with open(f"{DB_DIR}/schema.sql") as sc:
            await db.executescript(sc.read())
            return db
    except Exception as e: logger.error(f"{format_exception(e)}")

async def do_setup():
    """
    #### Goes through RinBot's initial setup
    Can only be triggered once by a fresh database start\n
    Inserts the following data into the "bot" table:\n
        data:dict = `{"token"}`
    
    Inserts the following data into the "owners" table:\n
        data:list = `[user_id]`
    """
    try:
        logger.info(text['DBMAN_CHECK_START'])
        conn = await init_db()
        query = await conn.execute("SELECT data FROM owners")
        result = await query.fetchone()
        owners = json.loads(result[0])
        if not owners:
            valid_id = False
            logger.warning(text['DBMAN_NO_OWNERS'])
            logger.info(text['DBMAN_NO_OWNERS_INST'])
            while not valid_id:
                id = input(text['DBMAN_ASK_ID'])
                if id.isnumeric():
                    query = await update_table("owners", [str(id)])
                    if not query:
                        logger.critical(text['DBMAN_DB_ERROR'])
                        sys.exit()
                    else: valid_id = True
                else: logger.error(text['DBMAN_INVALID_ID'])
        query = await conn.execute("SELECT data FROM bot")
        result = await query.fetchone()
        bot = json.loads(result[0])
        if not bot["token"]:
            valid_token = False
            while not valid_token:
                logger.warning(text['DBMAN_NO_TOKEN'])
                logger.info(text['DBMAN_NO_TOKEN_INST'])
                token = input(text['DBMAN_ASK_TOKEN'])
                logger.info(text['DBMAN_CHECKING_TOKEN'])
                if await check_token(token):
                    bot["token"] = token
                    query = await update_table("bot", bot)
                    if not query:
                        logger.critical(text['DBMAN_DB_ERROR'])
                        sys.exit()
                    else: valid_token = True
                else: logger.error(text['DBMAN_INVALID_TOKEN'])
        logger.info(text['DBMAN_CHECK_DONE'])
    except Exception as e: logger.error(f"{format_exception(e)}")
    finally: await conn.close()

async def populate():
    """
    Populates RinBot's DB with base data
    """
    try:
        conn = await init_db()
        base = {
            "bot": {"token": False}, "owners": [], "admins": {}, "blacklist": {}, 
            "guilds": [], "warns": {}, "currency": {}, "histories": {}, 
            "welcome_channels": {}, "daily_shop_channels": {}, "store": {}}
        for table, data in base.items():
            query = await conn.execute(f"SELECT data FROM {table}")
            is_present = await query.fetchone()
            if not is_present:
                await conn.execute(f"INSERT INTO {table}(data) VALUES(?)", (json.dumps(data, ensure_ascii=False, indent=4),))
                await conn.commit()
    except Exception as e: logger.error(f"{format_exception(e)}")
    finally: await conn.close()

async def get_table(table:str) -> dict | list:
    """
    #### Reads a table on the database and returns it's data
    RinBot's database consists of the following tables:
    - bot `{"token"}`
    - owners `[user_ids]`
    - admins `{guild_id: [user_id]}`
    - blacklist `{guild_id: [user_id]}`
    - guilds `[guild_ids]`
    - warns `{"guild_id": "user_id": [{"id", "moderator_id", "reason"}]}`
    - currency `[{user_id, guild_id, wallet, messages}]`
    - histories `{guild_id}`
    - welcome_channels `{guild_id}`
    - daily_shop_channels `{guild_id}`
    - store `{guild_id}`
    """
    try:
        conn = await init_db()
        async with conn.execute(f"SELECT data FROM {table}") as cursor:
            result = await cursor.fetchone()
            if result: return json.loads(result[0])
            else: return None
    except Exception as e: logger.error(f"{format_exception(e)}")
    finally: await conn.close()

async def update_table(table:str, data) -> bool:
    """
    #### Updates a table on the database with the provided data
    The data needs to be in JSON format, either a dict or a list\n
    This function will then make a comparison to see if the data on the db
    equals to the data provided, if so, the data was updated successfully and
    we return True, else, the data was not updated and we return False
    
    RinBot's database consists of the following tables:
    - bot `{"token"}`
    - owners `[user_ids]`
    - admins `{guild_id: [user_id]}`
    - blacklist `{guild_id: [user_id]}`
    - guilds `[guild_ids]`
    - warns `{"guild_id": "user_id": [{"id", "moderator_id", "reason"}]}`
    - currency `[{user_id, guild_id, wallet, messages}]`
    - histories `{guild_id}`
    - welcome_channels `{guild_id}`
    - daily_shop_channels `{guild_id}`
    - store `{guild_id}`
    """
    try:
        conn = await init_db()
        await conn.execute(f"UPDATE {table} SET data=?",
                            (json.dumps(data, ensure_ascii=False, indent=4),))
        await conn.commit()
        current = await get_table(table)
        if current == data:
            logger.info(f"{text['DBMAN_TABLE_UPDATED']} {table}")
            return True
        else:
            logger.error(f"{text['DBMAN_ERROR_UPDATING_TABLE']} {table}")
            return False
    except Exception as e: logger.error(f"{format_exception(e)}")
    finally: await conn.close()

async def startup():
    """
    #### Executes the necessary db functions to ready-up the database
    """
    await do_setup()
    await populate()