"""
RinBot v1.4.3
feita por rin
"""

# Imports
import json, os
from typing import Callable, TypeVar
from discord.ext import commands
from exceptions import *
from program import db_manager

# Typevar
T = TypeVar("T")

# Verifica se um usuário está na classe 'owner'
def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        with open(
            f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
        ) as file:
            data = json.load(file)
        if str(context.author.id) not in data["owners"]:
            raise UserNotOwner
        return True
    return commands.check(predicate)

# Verifica se um usuário está na classe 'admins'
def is_admin() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_admin(context.author.id):
            raise UserNotAdmin
        return True
    return commands.check(predicate)

# Verifica se um usuário não está na lista negra
def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise UserBlacklisted
        return True
    return commands.check(predicate)