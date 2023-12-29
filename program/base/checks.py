# Imports
from typing import Callable, TypeVar
from discord.ext import commands
from program.base.exceptions import Exceptions as E
from program.base import db_manager

# Typevar
T = TypeVar("T")

# Checks if a user is in the 'owner' class
def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_owner(context.author.id):
            raise E.UserNotOwner
        return True
    return commands.check(predicate)

# Checks if a user is in the 'admins' class
def is_admin() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_admin(context.author.id):
            raise E.UserNotAdmin
        return True
    return commands.check(predicate)

# Checks if a user is not blacklisted
def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise E.UserBlacklisted
        return True
    return commands.check(predicate)