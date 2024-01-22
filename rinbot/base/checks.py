"""
#### Checks
Checks that run before a command is executed
"""

# Imports
from discord import Interaction
from discord.app_commands import check
from typing import Callable, TypeVar
from rinbot.base.db_man import *
from rinbot.base.errors import Exceptions as E

T = TypeVar("T")

# app_commands checks
def is_owner() -> Callable[[T], T]:
    async def predicate(interaction:Interaction) -> bool:
        query = await get_table("owners")
        if not str(interaction.user.id) in query:
            raise E.UserNotOwner
        return True
    return check(predicate)

def is_admin() -> Callable[[T], T]:
    async def predicate(interaction:Interaction) -> bool:
        query = await get_table("admins")
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
        query = await get_table("blacklist")
        if interaction.guild:
            if str(interaction.guild.id) in query.keys():
                if str(interaction.user.id) in query[str(interaction.guild.id)]:
                    raise E.UserBlacklisted
        return True
    return check(predicate)