import os, sys, json, aiosqlite, discord
from discord.ext.commands import Bot
from rinbot.base.helpers import load_lang, format_exception

text = load_lang()

DATABASE_DIR = f"{os.path.realpath(os.path.dirname(__file__))}/../database/"
DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/sqlite.db"

# Check if the schema file is present
if not os.path.isfile(f"{DATABASE_DIR}/schema.sql"):
    sys.exit(f"{text['DBMAN_SCHEMA_NOT_FOUND']}")

# Define global bot obj
bot:Bot = None
def declare_bot(b):
    global bot
    bot = b

"""
Template function:

async def func():
    try:
        conn = await init_db()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
"""

##############################
# STARTUP SECTION START
##############################
async def init_db() -> aiosqlite.core.Connection:
    """Starts a connection with the database and returns a aiosqlite connection object"""
    try:
        db = await aiosqlite.connect(f"{DATABASE_PATH}")
        with open(f"{DATABASE_DIR}/schema.sql") as sc:
            await db.executescript(sc.read())
            return db
    except Exception as e:
        e = format_exception(e)
        sys.exit(f"{text['DBMAN_ERROR']} {e}")

async def check_owners():
    """Checks if there are owners present in the db, if not, runs through the bot setup process"""
    try:
        conn = await init_db()
        result = await conn.execute("SELECT user_id FROM owners")
        owners = await result.fetchall()
        if len(owners) == 0:
            valid = False
            bot.logger.info(f"{text['DBMAN_FRESH_DB']}")
            bot.logger.info(f"{text['DBMAN_INSTRUCTIONS']}")
            while not valid:
                id = input(f"{text['DBMAN_ASKING_ID']}")
                if id.isnumeric():
                    add_owner = await add_user_to_owners(id)
                    if not add_owner:
                        bot.logger.error(f"{text['DBMAN_USER_NOT_ADDED']}")
                        await check_owners()
                    else:
                        valid = True
                        bot.logger.info(f"{text['DBMAN_THANKING']}")
                else:
                    bot.logger.error(f"{text['DBMAN_INVALID_ID']}")
    except Exception as e:
        e = format_exception(e)
        sys.exit(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# STARTUP SECTION END
##############################

##############################
# CHECKS SECTION START
##############################
async def is_owner(user_id:int) -> bool:
    """Checks if a user with a given ID is a owner"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM owners WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def is_admin(user_id:int, guild_id:int) -> bool:
    """Checks if a user with a given ID and guild is a admin of that guild"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM admins WHERE user_id=? AND guild_id=?", (user_id, guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def is_blacklisted(user_id:int, guild_id:int) -> bool:
    """Checks if the user with a given ID and guild is blacklisted from using the bot on that guild"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT * FROM blacklist WHERE user_id=? AND guild_id=?", (user_id, guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# CHECKS SECTION END
##############################

##############################
# GET SECTION START
##############################
async def get_owners() -> list:
    """Returns the list of owners of the bot"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM owners"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_admins(guild_id:int) -> list:
    """Returns the list of admins of a guild"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM admins WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_blacklisted(guild_id:int) -> list:
    """Returns the list of blacklisted users of a guild"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id FROM blacklist WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_joined_ids() -> list:
    """Returns the list of all guilds the bot has joined"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT guild_id FROM joined_on"
        ) as cursor:
            result = await cursor.fetchall()
            return result
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_warnings(user_id:int, server_id:int) -> list:
    """Returns the list of a user's warnings (if any)"""
    try:
        conn = await init_db()
        rows = await conn.execute(
            "SELECT user_id, server_id, moderator_id, reason, id FROM warns WHERE user_id=? AND server_id=?",
            (user_id,server_id,),)
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_user_currency(user_id, server_id):
    """Returns how much currency a user has on a server"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_user_message_count(user_id, server_id):
    """Returns how many messages a user has sent between currency updates"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_currency_leaderboard(server_id):
    """Returns the currency leaderboard of a server"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT user_id, wallet FROM currency WHERE server_id=? ORDER BY wallet DESC LIMIT 10",
        (server_id,)) as cursor:
            return [(row[0],row[1]) for row in await cursor.fetchall()]
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_store() -> dict:
    """Returns the bot's item store"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_history(server_id) -> list:
    """Returns the song history of a server"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_favorites(user_id) -> list:
    """Returns the favorites of a user"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_welcome_channel(guild_id:int) -> list:
    """Returns the settings of the welcome channel for a guild"""
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT active, channel_id, custom_message FROM welcome_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return result
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def get_daily_shop_channel(guild_id:int) -> list:
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT active, channel_id FROM daily_shop_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return result
            else: return None
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# GET SECTION END
##############################

##############################
# ADD SECTION START
##############################
async def add_welcome_channel(channel_id, guild_id, custom_msg) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO welcome_channels(channel_id, guild_id, custom_message) VALUES (?,?,?)", (channel_id, guild_id, custom_msg))
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM welcome_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_daily_shop_channel(channel_id, guild_id) -> bool:
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO daily_shop_channels(channel_id, guild_id) VALUES (?,?)", (channel_id, guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM daily_shop_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_user_to_owners(user_id:int) -> bool:
    """Adds a user to the owners class"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_user_to_admins(user_id:int, guild_id:int) -> bool:
    """Adds a user to the admins class of a server"""
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO admins(user_id,guild_id) VALUES(?,?)", (user_id,guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT user_id FROM admins WHERE user_id=? AND guild_id=?", (user_id,guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            if result: return True 
            else: return False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_user_to_blacklist(user_id:int, guild_id:int) -> bool:
    """Adds a user to a server's blacklist"""
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO blacklist(user_id,guild_id) VALUES(?,?)", (user_id,guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT COUNT(*) FROM blacklist WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_joined_on(guild_id:int) -> bool:
    """Register a joined guild when the bot joins it"""
    try:
        conn = await init_db()
        await conn.execute("INSERT INTO joined_on(guild_id) VALUES(?)", (guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM joined_on WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return True if result else False
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_warn(user_id:int, server_id:int, moderator_id:int, reason:str) -> int:
    """Adds a warning to a user on a server"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_user_to_currency(user_id:int, server_id:int):
    """Add a user to a guild's currency"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_currency(user_id, server_id, amount):
    """Give currency to a user on a guild"""
    try:
        conn = await init_db()
        await conn.execute("UPDATE currency SET wallet=wallet+? WHERE user_id=? AND server_id=?",
                           (amount, user_id, server_id))
        await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def add_to_favorites(user_id, data):
    """Add something to a user's favorites"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# ADD SECTION END
##############################

##############################
# REMOVE SECTION START
##############################
async def remove_user_from_owners(user_id:int) -> bool:
    """Removes a user from the owners class"""
    try:
        if await is_owner(user_id):
            conn = await init_db()
            await conn.execute("DELETE FROM owners WHERE user_id=?", (user_id,))
            await conn.commit()
            async with conn.execute("SELECT COUNT (*) FROM owners") as cursor:
                rows = await cursor.fetchone()
            if len(rows) < 1: return None
            else: return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def remove_user_from_admins(user_id:int, guild_id:int) -> bool:
    """Removes a user from the admins class"""
    try:
        admin = await is_admin(user_id, guild_id)
        if admin:
            conn = await init_db()
            await conn.execute("DELETE FROM admins WHERE user_id=? AND guild_id=?", (user_id,guild_id,))
            await conn.commit()
            async with conn.execute("SELECT COUNT (*) FROM admins") as cursor:
                rows = await cursor.fetchone()
            if len(rows) < 1: return None
            else: return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def remove_user_from_blacklist(user_id:int, guild_id:int) -> bool:
    """Removes a user from a server's blacklist"""
    try:
        blacklisted = await is_blacklisted(user_id, guild_id)
        if blacklisted:
            conn = await init_db()
            await conn.execute("DELETE FROM blacklist WHERE user_id=? AND guild_id=?", (user_id,guild_id,))
            await conn.commit()
            async with conn.execute(
                "SELECT COUNT(*) FROM blacklist WHERE guild_id=?", (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result is not None else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def remove_joined_on(guild_id:int) -> bool:
    """Removes a guild from the database after the bot leaves it"""
    try:
        conn = await init_db()
        await conn.execute("DELETE FROM joined_on WHERE guild_id=?", (guild_id,))
        await conn.commit()
        async with conn.execute(
            "SELECT * FROM joined_on WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return False if result else True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")

async def remove_warn(warn_id:int, user_id:int, server_id:int) -> int:
    """'Remove a warn from a user in a guild"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def remove_currency(user_id, server_id, amount):
    """Removes currency from a user in a guild"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def remove_from_favorites(user_id, pl_id):
    """Removes an entry on a user's favorites"""
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
                description=f"{text['DB_MANAGER_REM_FAV_REMOVED'][0]}  `{item['title']}` {text['DB_MANAGER_REM_FAV_REMOVED'][1]}",
                color=0x25d917)
        except IndexError:
            return discord.Embed(
                description = f"{text['DB_MANAGER_REM_FAV_NO_RANGE']}",
                color=0xd91313)
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
##############################
# REMOVE SECTION END
##############################

##############################
# UPDATE SECTION START
##############################
async def update_welcome_channel(channel_id, guild_id):
    try:
        conn = await init_db()
        await conn.execute("UPDATE welcome_channels SET channel_id=? WHERE guild_id=?", (channel_id, guild_id,))
        await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def update_daily_shop_channel(channel_id, guild_id):
    try:
        conn = await init_db()
        await conn.execute("UPDATE daily_shop_channels SET channel_id=? WHERE guild_id=?", (channel_id, guild_id,))
        await conn.commit()
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def toggle_welcome_channel(guild_id):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT active FROM welcome_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            await conn.execute("UPDATE welcome_channels SET active=? WHERE guild_id=?", 
                              (1 if result[0] == 0 else 0, guild_id,))
            await conn.commit()
            return 1 if result[0] == 0 else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def toggle_daily_shop_channel(guild_id):
    try:
        conn = await init_db()
        async with conn.execute(
            "SELECT active FROM daily_shop_channels WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            await conn.execute("UPDATE daily_shop_channels SET active=? WHERE guild_id=?", 
                              (1 if result[0] == 0 else 0, guild_id,))
            await conn.commit()
            return 1 if result[0] == 0 else 0
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def update_message_count(user_id, server_id):
    """Adds 1 to a user's message count and rewards users for reaching the specified limit"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def move_currency(from_user, to_user, server_id, amount):
    """Moves currency between users"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")

async def update_store(data) -> bool:
    """Updates the bot's store items"""
    try:
        conn = await init_db()
        await conn.execute("UPDATE store SET data=? WHERE id=?", (json.dumps(data), 1))
        await conn.commit()
        return True
    except Exception as e:
        e = format_exception(e)
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
        return False
    finally:
        await conn.close()

async def update_history(server_id, data):
    """Updates a server's song history"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# UPDATE SECTION END
##############################

##############################
# CLEAR SECTION START
##############################
async def clear_history(server_id) -> bool:
    """Clears a server's song history"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()

async def clear_favorites(user_id) -> bool:
    """Clears someone's favorites"""
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
        bot.logger.error(f"{text['DBMAN_ERROR']} {e}")
    finally:
        await conn.close()
##############################
# CLEAR SECTION END
##############################