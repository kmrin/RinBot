"""
RinBot v1.7.1 (GitHub release)
made by rin
"""

# Imports
import json, os
from typing import Callable, TypeVar
from discord.ext import commands
from exceptions import *
from program import db_manager

# Typevar
T = TypeVar("T")

# Checks if a user is in the 'owner' class
def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_owner(context.author.id):
            raise UserNotOwner
        return True
    return commands.check(predicate)

# Checks if a user is in the 'admins' class
def is_admin() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_admin(context.author.id):
            raise UserNotAdmin
        return True
    return commands.check(predicate)

# Checks if a user is not blacklisted
def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise UserBlacklisted
        return True
    return commands.check(predicate)