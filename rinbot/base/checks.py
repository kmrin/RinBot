"""
#### Checks\n
Verification steps executed before a command
"""

from discord import Interaction
from discord.app_commands import check
from typing import Callable, TypeVar
from rinbot.base.errors import Exceptions as E
from rinbot.base.db import OfflineDB

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

T = TypeVar("T")

db = OfflineDB()

def is_owner() -> Callable[[T], T]:
    async def predicate(interaction:Interaction) -> bool:
        query = await db.get("owners")
        if not str(interaction.user.id) in query:
            raise E.UserNotOwner
        return True
    return check(predicate)

def is_admin() -> Callable[[T], T]:
    async def predicate(interaction:Interaction) -> bool:
        query = await db.get("admins")
        if interaction.guild:
            if str(interaction.guild.id) in query.keys():
                if not str(interaction.user.id) in query[str(interaction.guild.id)]:
                    raise E.UserNotAdmin
            else:
                raise E.UserNotAdmin
        else:
            raise E.UserNotInGuild
        return True
    return check(predicate)

def not_blacklisted() -> Callable[[T], T]:
    async def predicate(interaction:Interaction) -> bool:
        query = await db.get("blacklist")
        if interaction.guild:
            if str(interaction.guild.id) in query.keys():
                if str(interaction.user.id) in query[str(interaction.guild.id)]:
                    raise E.UserBlacklisted
        return True
    return check(predicate)