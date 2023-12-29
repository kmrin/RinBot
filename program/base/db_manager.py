# Imports
import os, sys, json, aiosqlite, discord
from discord.ext.commands import Bot
from program.base.helpers import load_lang, format_exception

# Load verbose
text = load_lang()

# Database values
DATABASE_DIR = f"{os.path.realpath(os.path.dirname(__file__))}/../../database/"
DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../../database/sqlite.db"

# Check if the schema file is present
if not os.path.isfile(f"{DATABASE_DIR}/schema.sql"):
    sys.exit(f"{text['DB_MANAGER_ERROR_SCHEMA_NOT_FOUND']}")

# Define global bot object
bot:Bot = None
def declare_bot(b):
    global bot
    bot = b

# Initializes a connection with the database or creates it if innexistant
async def init_db() -> aiosqlite.core.Connection:
    try:
        db = await aiosqlite.connect(f"{DATABASE_PATH}")
        with open(f"{DATABASE_DIR}/schema.sql") as sc:
            await db.executescript(sc.read())
            return db
    except Exception as e:
        e = format_exception(e)
        sys.exit(f"{text['DB_MANAGER_ERROR_BASE']} {e}")

# Template funcion
async def change_me():
    try:
        conn = await init_db()
        async with conn.execute(
            ""
        ) as cursor:
            pass
    except Exception as e:
        e = format_exception(e)
        sys.exit(f"{text['DB_MANAGER_ERROR_BASE']} {e}")
    finally:
        await conn.close()

# Checks if there are owners present, if not, run through the "setup process"
async def check_owners():
    try:
        conn = await init_db()
        result = await conn.execute("SELECT user_id FROM owners")
        owners = await result.fetchall()
        if len(owners) == 0:
            valid = False
            bot.logger.info(f"{text['DB_MANAGER_FRESH_DB']}")
            bot.logger.info(f"{text['DB_MANAGER_INSTRUCTIONS']}")
            while not valid:
                id = input('Your ID: ')
                if id.isnumeric():
                    add_owner = await add_user_to_owners(id)
                    add_admin = await add_user_to_admins(id)
                    if not add_owner or not add_admin:
                        bot.logger.error(f"{text['DB_MANAGER_USER_NOT_ADDED']}")
                    else:
                        valid = True
                        bot.logger.info(f"{text['DB_MANAGER_THANKING']}")
                else:
                    bot.logger.info(f"{text['DB_MANAGER_INVALID_ID']}")
    except Exception as e:
        e = format_exception(e)
        sys.exit(f"{text['DB_MANAGER_ERROR_BASE']} {e}")
    finally:
        await conn.close()

# Checks if the user is a owner
async def is_owner(user_id:int) -> bool:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM owners WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns the list of owners
async def get_owners() -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM owners"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a user to the owners class
async def add_user_to_owners(user_id:int) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO owners(user_id) VALUES(?)", (user_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT user_id FROM owners WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True 
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes a user from the owners class
async def remove_user_from_owners(user_id:int) -> bool:
    try:
        owner = await is_owner(user_id)
        if owner:
            conn = await init_db()
            await conn.execute("DELETE FROM owners WHERE user_id=?", (user_id,))
            await conn.commit()
            async with conn.execute("SELECT COUNT (*) FROM owners") as cursor:
                rows = await cursor.fetchone()
            if len(rows) < 1: return None
            else: return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Checks if the user is a admin
async def is_admin(user_id:int) -> bool:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM admins WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns the list of admins
async def get_admins() -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM admins"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a user to the admins class
async def add_user_to_admins(user_id:int) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO admins(user_id) VALUES(?)", (user_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT user_id FROM admins WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True 
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes a user from the admins class
async def remove_user_from_admins(user_id:int) -> bool:
    try:
        admin = await is_admin(user_id)
        if admin:
            conn = await init_db()
            await conn.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
            await conn.commit()
            async with conn.execute("SELECT COUNT (*) FROM admins") as cursor:
                rows = await cursor.fetchone()
            if len(rows) < 1: return None
            else: return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Checks if the user is on the blacklist
async def is_blacklisted(user_id:int) -> bool:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM blacklist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns the list of blacklisted users
async def get_blacklisted() -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id, strftime('%s', created_at) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a user to the blacklist
async def add_user_to_blacklist(user_id:int) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO blacklist(user_id) VALUES(?)", (user_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT COUNT(*) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes a user from the blacklist
async def remove_user_from_blacklist(user_id:int) -> bool:
    try:
        blacklisted = await is_blacklisted(user_id)
        if blacklisted:
            conn = await init_db()
            await conn.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
            await conn.commit()
            async with conn.execute(
                "SELECT COUNT(*) FROM blacklist"
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result is not None else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds the ID of a joined server to the database
async def add_joined_on(guild_id:int) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO joined_on(guild_id) VALUES(?)", (guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM joined_on WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns the IDs of all joined servers
async def get_joined_ids() -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT guild_id FROM joined_on"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a warning to the user
async def add_warn(user_id:int, server_id:int, moderator_id:int, reason:str) -> int:
    try:
        conn = await init_db()
        rows = await conn.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1"
        , (user_id, server_id,),)
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await conn.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)"
            , (warn_id, user_id, server_id, moderator_id, reason,),)
            await conn.commit()
            return warn_id
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes a warning from a user
async def remove_warn(warn_id:int, user_id:int, server_id:int) -> int:
    try:
        conn = await init_db()
        await conn.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?"
        , (warn_id, user_id, server_id,),)
        await conn.commit()
        rows = await conn.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?"
        , (user_id, server_id,),)
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns the total warnings a user has as a list
async def get_warnings(user_id:int, server_id:int) -> list:
    try:
        conn = await init_db()
        rows = await conn.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (user_id,server_id,),)
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a user to the economy
async def add_user_to_currency(user_id:int, server_id:int):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM currency WHERE user_id=? AND server_id=?"
        , (user_id, server_id)) as cursor:
            result = await cursor.fetchone()
            if not result:
                await conn.execute("INSERT INTO currency(user_id, server_id) VALUES (?, ?)",
                                   (user_id, server_id))
                await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns how much currency a user has
async def get_user_currency(user_id, server_id):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT wallet FROM currency WHERE user_id=? AND server_id=?"
        , (user_id, server_id)) as cursor:
            result = await cursor.fetchone()
            if result: return result[0]
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Returns how many messages the user has sent
async def get_user_message_count(user_id, server_id):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT messages FROM currency WHERE user_id=? AND server_id=?"
        , (user_id, server_id)) as cursor:
            result = await cursor.fetchone()
            if result: return result[0]
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Updates how many messages a user has sent and gives an award uppon reaching the limit
async def update_message_count(user_id, server_id):
    try:
        conn = await init_db()
        await conn.execute("UPDATE currency SET messages=messages+1 WHERE user_id=? AND server_id=?",
                           (user_id, server_id))
        await conn.commit()
        current = await get_user_message_count(user_id, server_id)
        if current == 50:
            await conn.execute("UPDATE currency SET messages=0 WHERE user_id=? AND server_id=?",
                               (user_id, server_id))
            await conn.commit()
            await add_currency(user_id, server_id, 25)
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Rewards a user with oranges
async def add_currency(user_id, server_id, amount):
    try:
        conn = await init_db()
        await conn.execute("UPDATE currency SET wallet=wallet+? WHERE user_id=? AND server_id=?",
                           (amount, user_id, server_id))
        await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes oranges from a user
async def remove_currency(user_id, server_id, amount):
    try:
        current = await get_user_currency(user_id, server_id)
        if int(current) < amount:
            return None
        else:
            conn = await init_db()
            await conn.execute("UPDATE currency SET wallet=wallet-? WHERE user_id=? AND server_id=?",
                               (amount, user_id, server_id))
            await conn.commit()
            return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Moves currency between users
async def move_currency(from_user, to_user, server_id, amount):
    try:
        from_user_amount = await get_user_currency(from_user, server_id)
        if int(from_user_amount) < amount:
            return None
        else:
            await remove_currency(from_user, server_id, amount)
            await add_currency(to_user, server_id, amount)
            return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")

# Returns the list of top 10 users with the most currency
async def get_currency_leaderboard(server_id):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id, wallet FROM currency WHERE server_id=? ORDER BY wallet DESC LIMIT 10",
        (server_id,)) as cursor:
            return [(row[0],row[1]) for row in await cursor.fetchall()]
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Retrieves the item store of a server
async def get_store() -> dict:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT data FROM store") as cursor:
            result = await cursor.fetchone()
            if result:
                data = json.loads(result[0])
                return data
            else:
                await conn.execute("INSERT INTO store(id, data) VALUES(?,?)",
                             (1, json.dumps({})))
                await conn.commit()
                return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Updates the store
async def update_store(data) -> bool:
    try:
        conn = await init_db()
        await conn.execute("UPDATE store SET data=? WHERE id=?", (json.dumps(data), 1))
        await conn.commit()
        return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
        return False
    finally:
        await conn.close()

# Retrieves the song history of a server
async def get_history(server_id) -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT data FROM histories WHERE server_id=?"
        , (server_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                data = json.loads(result[0])
                return data
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Updates the song history of a server
async def update_history(server_id, data):
    try:
        current:list = await get_history(server_id)
        conn = await init_db()
        if current:
            await conn.execute(
            "UPDATE histories SET data=? WHERE server_id=?"
            , (json.dumps(data, ensure_ascii=False), server_id))
            await conn.commit()
        else:
            await conn.execute(
                "INSERT INTO histories(server_id, data) VALUES(?, ?)"
            , (server_id, (json.dumps(data, ensure_ascii=False))))
            await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Clears the song history of a server
async def clear_history(server_id) -> bool:
    try:
        current:list = await get_history(server_id)
        conn = await init_db()
        if current:
            await conn.execute(
                "DELETE FROM histories WHERE server_id=?", (server_id,))
            await conn.commit()
            return True
        else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Retrieves the favorites of a user
async def get_favorites(user_id) -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT data FROM favorites WHERE user_id=?"
        , (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                data = json.loads(result[0])
                return data
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Adds a playlist to someone's favorites
async def add_to_favorites(user_id, data):
    try:
        current:list = await get_favorites(user_id)
        conn = await init_db()
        if isinstance(current, list):
            current.append(data)
            await conn.execute(
            "UPDATE favorites SET data=? WHERE user_id=?"
            , (json.dumps(current), user_id))
            await conn.commit()
        else:
            current = []
            current.append(data)
            await conn.execute(
                "INSERT INTO favorites(user_id, data) VALUES(?, ?)"
            , (user_id, json.dumps(current)))
            await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()

# Removes a playlist from someone's favorites
async def remove_from_favorites(user_id, pl_id):
    try:
        current:list = await get_favorites(user_id)
        conn = await init_db()
        if not current:
            return None
        try:
            item = current[pl_id]
            current.pop(pl_id)
            await conn.execute(
                "UPDATE favorites SET data=? WHERE user_id=?"
                ,(json.dumps(current), user_id))
            await conn.commit()
            return discord.Embed(
                description=f" {text['DB_MANAGER_REM_FAV_REMOVED'][0]}  `{item['title']}` {text['DB_MANAGER_REM_FAV_REMOVED'][1]}",
                color=0x25d917)
        except IndexError:
            return discord.Embed(
                description = f"{text['DB_MANAGER_REM_FAV_NO_RANGE']}",
                color=0xd91313)
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")

# Clears the song favorites of a server
async def clear_favorites(user_id) -> bool:
    try:
        current:list = await get_favorites(user_id)
        conn = await init_db()
        if current:
            await conn.execute(
                "DELETE FROM favorites WHERE user_id=?", (user_id,))
            await conn.commit()
            return True
        else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"[db_manager.py]: {e}")
    finally:
        await conn.close()