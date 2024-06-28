from nextcord import Interaction
from nextcord.ext.application_checks import check
from typing import Callable, TypeVar

from .loggers import Loggers
from .db import DBTable, DBManager
from .errors import UserNotOwner, UserNotAdmin, UserNotInGuild, UserBlacklisted

logger = Loggers.COMMAND_CHECKS
db = DBManager()

T = TypeVar('T')

def is_guild() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        if not interaction.guild:
            raise UserNotInGuild(interaction)
        
        return True
    return check(predicate)

def is_owner() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        query = await db.get(DBTable.OWNERS)
        if not query:
            raise UserNotOwner(interaction)
        
        ids = [row[0] for row in query]
        if not interaction.user.id in ids:
            raise UserNotOwner(interaction)
        
        return True
    return check(predicate)

def is_admin() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        if not interaction.guild:
            raise UserNotInGuild(interaction)
        
        query = await db.get(DBTable.ADMINS, f'guild_id={interaction.guild.id}')
        if not query:
            raise UserNotAdmin(interaction)
        
        ids = [row[1] for row in query]
        if not interaction.user.id in ids:
            raise UserNotAdmin(interaction)
        
        return True
    return check(predicate)

def not_blacklisted() -> Callable[[T], T]:
    async def predicate(interaction: Interaction) -> bool:
        if not interaction.guild:
            return True
        
        query = await db.get(DBTable.BLACKLIST, f'guild_id={interaction.guild.id} AND user_id={interaction.user.id}')
        if not query:
            return True
        
        raise UserBlacklisted(interaction)
    return check(predicate)
