"""
RinBot v1.4.3
feita por rin
"""

# Imports
import os
import aiosqlite

# Caminho do arquivo SQL
DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

# Retorna uma lista com os usuários na lista negra
async def get_blacklisted_users() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Retorna uma lista com os usuários da classe 'admin'
async def get_admin_users() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM admins"
        ) as cursor:
            result = await cursor.fetchall()
            return result

# Verifica se um usuário está na lista negra
async def is_blacklisted(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM blacklist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# Verifica se um usuário está na classe 'admins'
async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM admins WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

# Adiciona um usuário a lista negra
async def add_user_to_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO blacklist(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Remove um usuário da lista negra
async def remove_user_from_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Adiciona um usuário na classe 'admins'
async def add_user_to_admins(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO admins(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM admins")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Remove um usuário da classe 'admins'
async def remove_user_from_admins(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM admins")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

# Adiciona um aviso a um usuário
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

# Remove um aviso de um usuário
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

# Retorna a lista de avisos de um usuário
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