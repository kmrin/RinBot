import asyncio

from nextcord import application_command, Interaction
from nextcord.ext.commands import Context
from nextcord.colour import Colour
from typing import Union

from .loggers import Loggers
from .responder import respond
from .helpers import get_interaction_locale, get_localized_string

logger = Loggers.ERRORS

class InteractionTimedOut(Exception):
    def __init__(self, interaction: Union[Context, Interaction]) -> None:
        asyncio.create_task(self.__do_action(interaction))
    
    def __str__(self) -> None:
        return 'An interaction timed out'

    @staticmethod
    async def __do_action(interaction: Union[Context, Interaction]) -> None:
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'INTERFACE_TIMEOUT_EMBED')
        await respond(interaction, Colour.yellow(), msg, hidden=True)

class RinBotInteractionError(Exception):
    def __init__(self, interaction: Union[Context, Interaction]) -> None:
        asyncio.create_task(self.__do_action(interaction))
    
    def __str__(self) -> None:
        return 'Something went no-no in the code somewhere!'

    @staticmethod
    async def __do_action(interaction: Union[Context, Interaction]) -> None:
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'INTERACTION_ERROR')
        await respond(interaction, Colour.red(), msg, hidden=True)

class UserNotOwner(application_command.ApplicationCheckFailure):
    def __init__(self, interaction: Interaction) -> None:
        asyncio.create_task(self.__do_action(interaction))

    @staticmethod
    async def __do_action(interaction: Interaction) -> None:
        author = interaction.user
        guild = interaction.guild if interaction.guild else None
        channel = interaction.channel or None
                
        logger.info(
            f'Someone tried running a command of class "owner" but they are not in this class: '
            f'[Who: {author.name} | Where: {guild.name if guild else "DMs"} {f"(ID: {guild.id}, In channel: {channel} (ID: {channel.id}))" if guild else ""}]'
        )
        
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'CHECKS_NOT_OWNER')
        await respond(interaction, Colour.red(), msg, hidden=True)

class UserNotAdmin(application_command.ApplicationCheckFailure):
    def __init__(self, interaction: Interaction) -> None:
        asyncio.create_task(self.__do_action(interaction))

    @staticmethod
    async def __do_action(interaction: Interaction) -> None:
        author = interaction.user
        guild = interaction.guild if interaction.guild else None
        channel = interaction.channel or None
                
        logger.info(
            f'Someone tried running a command of class "admin" but they are not in this class: '
            f'[Who: {author.name} | Where: {guild.name if guild else "DMs"} {f"(ID: {guild.id}, In channel: {channel} (ID: {channel.id}))" if guild else ""}]'
        )
        
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'CHECKS_NOT_ADMIN')
        await respond(interaction, Colour.red(), msg, hidden=True)

class UserBlacklisted(application_command.ApplicationCheckFailure):
    def __init__(self, interaction: Interaction) -> None:
        asyncio.create_task(self.__do_action(interaction))

    @staticmethod
    async def __do_action(interaction: Interaction) -> None:
        author = interaction.user
        guild = interaction.guild
        channel = interaction.channel or None
                
        logger.info(
            f'Someone tried running a command but they are blacklisted: '
            f'[Who: {author.name} | Where: {guild.name} (ID: {guild.id}, In channel: {channel} (ID: {channel.id}))]'
        )
        
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'CHECKS_BLACKLISTED')
        await respond(interaction, Colour.red(), msg, hidden=True)

class UserNotInGuild(application_command.ApplicationCheckFailure):
    def __init__(self, interaction: Union[Context, Interaction]) -> None:
        asyncio.create_task(self.__do_action(interaction))
    
    @staticmethod
    async def __do_action(interaction: Union[Context, Interaction]) -> None:
        author = interaction.user or interaction.author
        
        logger.info(
            f'Someone tried running a guild command in my DMs: '
            f'[Who: {author.name}]'
        )
        
        locale = get_interaction_locale(interaction)
        msg = get_localized_string(locale, 'CHECKS_NOT_GUILD')
        await respond(interaction, Colour.red(), msg, hidden=True)
