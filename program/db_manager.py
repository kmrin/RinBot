"""
RinBot v1.9.0 (GitHub release)
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

# Adiciona um usuário aos participantes da economia
async def add_user_to_currency(user_id:int, server_id:int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM currency WHERE user_id=? AND server_id=?", 
            (user_id, server_id)
        ) as cursor:
            result = await cursor.fetchone()
            if not result:
                await db.execute("INSERT INTO currency(user_id,server_id) VALUES (?,?)",
                                 (user_id,server_id))
                await db.commit()
                
# Retorna quantas laranjas o usuário tem
async def get_user_currency(user_id, server_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT wallet FROM currency WHERE user_id=? AND server_id=?", 
            (user_id, server_id)
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
            
# Retorna quantas mensagens o usuário já enviou
async def get_user_message_count(user_id, server_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT messages FROM currency WHERE user_id=? AND server_id=?",
            (user_id, server_id)
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
            
# Atualiza a quantia de mensagens enviada por um usuário e premia caso atinja o limite
async def update_message_count(user_id, server_id, punish=False):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE currency SET messages=messages+1 WHERE user_id=? AND server_id=?",
            (user_id, server_id))
        await db.commit()
        current = await get_user_message_count(user_id, server_id)
        if punish:
            await db.execute(
                "UPDATE currency SET messages=0 WHERE user_id=? AND server_id=?",
                (user_id, server_id))
            await db.commit()
        if current == 50:
            await db.execute(
                "UPDATE currency SET messages=0 WHERE user_id=? AND server_id=?",
                (user_id, server_id))
            await db.commit()
            await add_currency(user_id, server_id, 25)
            
# Adiciona laranjas a um usuário
async def add_currency(user_id, server_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE currency SET wallet=wallet+? WHERE user_id=? AND server_id=?",
                         (amount, user_id, server_id))
        await db.commit()
        
# Remove laranjas de um usuário
async def remove_currency(user_id, server_id, amount):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        current_amount = await get_user_currency(user_id, server_id)
        if int(current_amount) < amount:
            return None
        else:
            await db.execute("UPDATE currency SET wallet=wallet-? WHERE user_id=? AND server_id=?",
                            (amount, user_id, server_id))
            await db.commit()
            return True
        
# Transfere laranjas de um usuário pra outro
async def move_currency(from_user, to_user, server_id, amount):
    from_user_amount = await get_user_currency(from_user, server_id)
    if int(from_user_amount) < amount:
        return None
    else:
        await remove_currency(from_user, server_id, amount)
        await add_currency(to_user, server_id, amount)
        return True
    
# Retorna a lista dos usuários com mais laranjas (top 10)
async def get_leaderboard(server_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, wallet FROM currency WHERE server_id=? ORDER BY wallet DESC LIMIT 10", 
            (server_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [(row[0],row[1]) for row in rows]