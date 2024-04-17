"""
Errors
"""

import asyncio

from discord import app_commands, Interaction

from .colours import Colour
from .exception_handler import log_exception
from .json_loader import get_lang
from .logger import logger
from .responder import respond

text = get_lang()

class Exceptions:
    class UserNotOwner(app_commands.CheckFailure):
        def __init__(self, interaction: Interaction):
            asyncio.create_task(self.__do_action(interaction))
        
        @staticmethod
        async def __do_action(interaction: Interaction):
            try:
                await respond(
                    interaction,
                    message=text['CHECKS_NOT_OWNER'],
                    colour=Colour.RED
                )

                logger.warning(
                    text['CHECKS_NOT_OWNER_LOG'].format(
                        user=interaction.user,
                        user_id=interaction.user.id,
                        guild=interaction.guild if interaction.guild else None,
                        guild_id=interaction.guild.id if interaction.guild else None
                    )
                )
            except Exception as e:
                log_exception(e)
    
    class UserNotAdmin(app_commands.CheckFailure):
        def __init__(self, interaction: Interaction):
            asyncio.create_task(self.__do_action(interaction))
        
        @staticmethod
        async def __do_action(interaction: Interaction):
            try:
                await respond(
                    interaction,
                    message=text['CHECKS_NOT_ADMIN'],
                    colour=Colour.RED
                )

                logger.warning(
                    text['CHECKS_NOT_ADMIN_LOG'].format(
                        user=interaction.user,
                        user_id=interaction.user.id,
                        guild=interaction.guild if interaction.guild else None,
                        guild_id=interaction.guild.id if interaction.guild else None
                    )
                )
            except Exception as e:
                log_exception(e)
    
    class UserBlacklisted(app_commands.CheckFailure):
        def __init__(self, interaction: Interaction):
            asyncio.create_task(self.__do_action(interaction))
        
        @staticmethod
        async def __do_action(interaction: Interaction):
            try:
                await respond(
                    interaction,
                    message=text['CHECKS_BLACKLISTED'],
                    colour=Colour.RED
                )

                logger.warning(
                    text['CHECKS_BLACKLISTED_LOG'].format(
                        user=interaction.user,
                        user_id=interaction.user.id,
                        guild=interaction.guild,
                        guild_id=interaction.guild.id
                    )
                )
            except Exception as e:
                log_exception(e)
    
    class UserNotInGuild(app_commands.CheckFailure):
        def __init__(self, interaction: Interaction):
            asyncio.create_task(self.__do_action(interaction))
        
        @staticmethod
        async def __do_action(interaction: Interaction):
            try:
                await respond(
                    interaction,
                    message=text['CHECKS_NOT_GUILD'],
                    colour=Colour.RED
                )

                logger.warning(
                    text['CHECKS_NOT_GUILD_LOG'].format(
                        user=interaction.user,
                        user_id=interaction.user.id
                    )
                )
            except Exception as e:
                log_exception(e)
