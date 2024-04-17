"""
RinBot's owner command cog
- commands:
    * /extension load `Loads a bot extension`
    * /extension unload `Unloads a bot extension`
    * /extension reload `Reloads a bot extension`
    * /owners add `Adds a user to the owners list`
    * /owners remove `Removes a user from the owners list`
    * /reload-event-handler `Reloads the event handler Cog`
    * /shutdown `Shuts the bot down`
"""

import os
import discord

from discord import Interaction, app_commands
from discord.app_commands.models import Choice
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionNotLoaded
from discord.ext.commands import Cog

from rinbot.base import log_exception
from rinbot.base import EventHandler
from rinbot.base import respond
from rinbot.base import DBTable
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import Path
from rinbot.base import text
from rinbot.base import conf

from rinbot.base import is_owner
# from rinbot.base import is_admin
# from rinbot.base import not_blacklisted

ext_list = []

class Owner(Cog, name='owner'):
    def __init__(self, bot: RinBot):
        self.bot = bot
    
    extension = app_commands.Group(
        name=text["OWNER_EXTENSION_NAME"],
        description=text["OWNER_EXTENSION_DESC"])
    owners = app_commands.Group(
        name=text["OWNER_OWNERS_NAME"],
        description=text["OWNER_OWNERS_DESC"])
    
    @extension.command(
        name=text['OWNER_EXT_LOAD_NAME'],
        description=text['OWNER_EXT_LOAD_DESC'])
    @app_commands.choices(extension=ext_list)
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _extension_load(self, interaction: Interaction, extension: Choice[str]) -> None:
        try:
            await self.bot.load_extension(f'rinbot.extensions.{extension.value}')
            desc = text['OWNER_EXT_LOAD_LOADED'].format(ext=extension.value)
            colour = Colour.GREEN
        except ExtensionAlreadyLoaded:
            desc = text['OWNER_EXT_LOAD_ALREADY_LOADED'].format(ext=extension.value)
            colour = Colour.RED
        except Exception as e:
            log_exception(e)
            desc = text['OWNER_EXT_LOAD_FAILED'].format(ext=extension.value)
            colour = Colour.RED
        
        await respond(interaction, colour, desc)
        
        await self.bot.tree.sync()
        
        if interaction.guild:
            await self.bot.tree.sync(guild=interaction.guild)
    
    @extension.command(
        name=text['OWNER_EXT_UNLOAD_NAME'],
        description=text['OWNER_EXT_UNLOAD_DESC'])
    @app_commands.choices(extension=ext_list)
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _extension_unload(self, interaction: Interaction, extension: Choice[str]) -> None:
        if extension.value == 'owner':
            return await respond(interaction, Colour.RED, text['OWNER_EXT_UNLOAD_IS_OWNER'])
        
        try:
            await self.bot.unload_extension(f'rinbot.extensions.{extension.value}')
            desc = text['OWNER_EXT_UNLOAD_UNLOADED'].format(ext=extension.value)
            colour = Colour.GREEN
        except ExtensionNotLoaded:
            desc = text['OWNER_EXT_UNLOAD_ALREADY_UNLOADED'].format(ext=extension.value)
            colour = Colour.RED
        except Exception as e:
            log_exception(e)
            desc = text['OWNER_EXT_UNLOAD_FAILED'].format(ext=extension.value)
            colour = Colour.RED
        
        await respond(interaction, colour, desc)
        
        await self.bot.tree.sync()
        
        if interaction.guild:
            await self.bot.tree.sync(guild=interaction.guild)
    
    @extension.command(
        name=text['OWNER_EXT_RELOAD_NAME'],
        description=text['OWNER_EXT_RELOAD_DESC'])
    @app_commands.choices(extension=ext_list)
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _extension_reload(self, interaction: Interaction, extension: Choice[str]) -> None:        
        try:
            await self.bot.reload_extension(f'rinbot.extensions.{extension.value}')
            desc = text['OWNER_EXT_RELOAD_RELOADED'].format(ext=extension.value)
            colour = Colour.GREEN
        except Exception as e:
            log_exception(e)
            desc = text['OWNER_EXT_RELOAD_FAILED'].format(ext=extension.value)
            colour = Colour.RED
        
        await respond(interaction, colour, desc)
        
        await self.bot.tree.sync()
        
        if interaction.guild:
            await self.bot.tree.sync(guild=interaction.guild)
    
    @owners.command(
        name=text['OWNER_OWNERS_ADD_NAME'],
        description=text['OWNER_OWNERS_ADD_DESC'])
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _owners_add(self, interaction: Interaction, member: discord.Member) -> None:        
        owners = await self.bot.db.get(DBTable.OWNERS)
        owner_ids = [row[0] for row in owners]
        
        if member.id in owner_ids:
            return await respond(interaction, Colour.RED, text['OWNER_OWNERS_ADD_ALREADY_OWNER'].format(user=member.name))
        
        await self.bot.db.put(DBTable.OWNERS, {'user_id': member.id})
        
        await respond(interaction, Colour.GREEN, text['OWNER_OWNERS_ADD_USER_ADDED'].format(user=member.name))
    
    @owners.command(
        name=text['OWNER_OWNERS_REM_NAME'],
        description=text['OWNER_OWNERS_REM_DESC'])
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _owners_remove(self, interaction: Interaction, member: discord.Member) -> None:        
        owners = await self.bot.db.get(DBTable.OWNERS)
        owner_ids = [row[0] for row in owners]
        
        if not member.id in owner_ids:
            return await respond(interaction, Colour.RED, text['OWNER_OWNERS_REM_NOT_OWNER'].format(user=member.name))
        
        await self.bot.db.delete(DBTable.OWNERS, f'user_id={member.id}')
        
        await respond(interaction, Colour.GREEN, text['OWNER_OWNERS_REM_REMOVED'].format(user=member.name))
        
        owners = await self.bot.db.get(DBTable.OWNERS)
        
        if not owners:
            await respond(interaction, Colour.RED, text['OWNER_OWNERS_EMPTY_WARNING'], hidden=True, response_type=1)
    
    @app_commands.command(
        name=text['OWNER_RELOAD_EVENT_HANDLER_NAME'],
        description=text['OWNER_RELOAD_EVENT_HANDLER_DESC'])
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _reload_event_handler(self, interaction: Interaction) -> None:
        await self.bot.add_cog(EventHandler(self.bot), override=True)
        await respond(interaction, Colour.YELLOW, text['OWNER_RELOAD_EVENT_HANDLER_TEXT'])
    
    @app_commands.command(
        name=text['OWNER_SHUTDOWN_NAME'],
        description=text['OWNER_SHUTDOWN_DESC'])
    @is_owner()
    # @is_admin()
    # @not_blacklisted()
    async def _shutdown(self, interaction: Interaction) -> None:
        await respond(interaction, Colour.YELLOW, text['OWNER_SHUTDOWN_EMBED'])
        await self.bot.stop()

async def setup(bot: RinBot):
    ai_ext = ["imagecaption", "languagemodel", "message_handler", "stablediffusion"]
    booru_ext = ["booru"]
    rule34_ext = ["rule34"]

    everything = ai_ext + booru_ext + rule34_ext

    for file in os.listdir(Path.extensions):
        if file.endswith(".py"):
            extension = file[:-3]

            if conf["AI_ENABLED"] and extension in ai_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif conf["BOORU_ENABLED"] and extension in booru_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif conf["RULE34_ENABLED"] and extension in rule34_ext:
                ext_list.append(Choice(name=extension, value=extension))

            is_general = all(extension not in sl for sl in everything)
            if is_general:
                ext_list.append(Choice(name=extension, value=extension))
    
    await bot.add_cog(Owner(bot))
