import discord
from discord import app_commands
from typing import Callable, TypeVar
from discord.ext import commands
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang
from rinbot.base.exceptions import Exceptions as E
from rinbot.base import db_manager

T = TypeVar("T")

text = load_lang()

# Checks to be used in hybrid and normal commands
def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_owner(context.author.id):
            raise E.UserNotOwner
        return True
    return commands.check(predicate)
def is_admin() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if not await db_manager.is_admin(context.author.id, context.guild.id):
            raise E.UserNotAdmin
        return True
    return commands.check(predicate)
def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id, context.guild.id):
            raise E.UserBlacklisted
        return True
    return commands.check(predicate)

# Checks to be used in app commands (command groups etc)
def is_owner_ac():
    async def predicate(interaction:discord.Interaction) -> bool:
        if not await db_manager.is_owner(interaction.user.id):
            raise E.AC_UserNotOwner
        return True
    return app_commands.check(predicate)
def is_admin_ac():
    async def predicate(interaction:discord.Interaction) -> bool:
        if not await db_manager.is_admin(interaction.user.id, interaction.guild.id):
            raise E.AC_UserNotAdmin
        return True
    return app_commands.check(predicate)
def not_blacklisted_ac():
    async def predicate(interaction:discord.Interaction) -> bool:
        if await db_manager.is_blacklisted(interaction.user.id, interaction.guild.id):
            raise E.AC_UserBlacklisted
        return True
    return app_commands.check(predicate)