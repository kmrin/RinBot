"""
RinBot v1.6.0 (GitHub release)
made by rin
"""

# Imports
import os
import aiosqlite

# Database path
DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

# Returns a list with users on the blacklist
async def get_blacklisted_users() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Returns a list with users on the 'admin' class
async def get_admin_users() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM admins"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Checks if a user is in the blacklist
async def is_blacklisted(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM blacklist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# Checks if a user is in the 'admins' class
async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM admins WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# Adds a user to the blacklist
async def add_user_to_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO blacklist(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Removes a user from the blacklist
async def remove_user_from_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Adds a user to the 'admins' class
async def add_user_to_admins(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO admins(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM admins")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Removes a user from the 'admins' class
async def remove_user_from_admins(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM admins")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Adds a user to the owners class
async def add_user_to_owners(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO owners(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM owners")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Removes a user from the owners class
async def remove_user_from_owners(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM owners WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT (*) FROM owners")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Returns the list of owners
async def get_owners() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM owners"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Checks if the user is a owner
async def is_owner(user_id:int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM owners WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# Adds a guild ID to the database
async def add_guild_id(guild_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO guild_ids(guild_id) VALUES (?)", (guild_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM guild_ids")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Returns the guild IDs from the database
async def get_guild_ids() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT guild_id FROM guild_ids"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Adds the IDs of joined servers to the database
async def add_joined_on(joined_on: str) -> str:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO joined_on(joined_on) VALUES (?)", (joined_on,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM joined_on")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Returns the IDs of all joined servers from the database
async def get_joined_ids() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT joined_on FROM joined_on"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Adds a warning to a user
async def add_warn(user_id: int, server_id: int, moderator_id: int, reason: str) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",(
                user_id,
                server_id,),)
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await db.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",(
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,),)
            await db.commit()
            return warn_id

# Removes a warning from a user
async def remove_warn(warn_id: int, user_id: int, server_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,),)
        await db.commit()
        rows = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),)
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Returns the total warnings a user has as a list
async def get_warnings(user_id: int, server_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,),)
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list