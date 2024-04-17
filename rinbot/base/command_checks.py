"""
Security checks ran before commands are executed
"""

from discord import Interaction
from discord.app_commands import check
from typing import Callable, TypeVar

from .db import DBTable, DBManager
from .errors import Exceptions as E
from .exception_handler import log_exception
from .json_loader import get_lang

text = get_lang()
db = DBManager()

T = TypeVar('T')

def is_owner() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        try:
            query = await db.get(DBTable.OWNERS)

            if not query:
                raise E.UserNotOwner(interaction)

            ids = [row[0] for row in query]

            if not interaction.user.id in ids:
                raise E.UserNotOwner(interaction)

            return True
        except Exception as e:
            log_exception(e)

    return check(predicate)

def is_admin() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        try:
            if not interaction.guild:
                raise E.UserNotInGuild(interaction)

            query = await db.get(DBTable.ADMINS, condition=f"guild_id={interaction.guild.id}")

            if not query:
                raise E.UserNotAdmin(interaction)

            ids = [row[1] for row in query]

            if not interaction.user.id in ids:
                raise E.UserNotAdmin(interaction)

            return True
        except Exception as e:
            log_exception(e)

    return check(predicate)

def not_blacklisted() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        try:
            if not interaction.guild:
                return True

            query = await db.get(DBTable.BLACKLIST,
                condition=f"guild_id={interaction.guild.id} AND user_id={interaction.user.id}")

            if not query:
                return True

            raise E.UserBlacklisted(interaction)
        except Exception as e:
            log_exception(e)

    return check(predicate)
