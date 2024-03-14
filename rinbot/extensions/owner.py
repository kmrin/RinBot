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

import os, discord, asyncio
from discord import app_commands
from discord.ext.commands import Cog
from discord.app_commands.models import Choice
from rinbot.base.helpers import load_config, load_lang, format_exception
from rinbot.base.interface import ZeroOwnersView
from rinbot.base.events import EventHandler
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

config = load_config()
text = load_lang()
ext_list = []

class Owner(Cog, name="owner"):
    def __init__(self, bot: RinBot):
        self.bot = bot
        self.selected_user = None

    # Command groups
    extension = app_commands.Group(name=text["OWNER_EXTENSION_NAME"],
                                   description=text["OWNER_EXTENSION_DESC"])
    owners    = app_commands.Group(name=text["OWNER_OWNERS_NAME"],
                                   description=text["OWNER_OWNERS_DESC"])

    @extension.command(
        name=text["OWNER_EXTENSION_LOAD_NAME"],
        description=text["OWNER_EXTENSION_LOAD_DESC"])
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    # @is_admin()
    @is_owner()
    async def _extension_load(self, interaction: Interaction, extension:Choice[str]) -> None:
        if not extension:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        try:
            await self.bot.load_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_LOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_LOADING']} {extension.value} `{e}`",
                color=RED)

        await respond(interaction, message=embed)

        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)

    @extension.command(
        name=f"{text['OWNER_EXTENSION_UNLOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_UNLOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    # @is_admin()
    @is_owner()
    async def _extension_unload(self, interaction: discord.Interaction, extension: Choice[str] = None) -> None:
        if not extension:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        if extension.value == "owner":
            return await respond(interaction, RED, message=text['OWNER_EXTENSION_EXT_IS_OWNER'])

        try:
            await self.bot.unload_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_UNLOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_UNLOADING']} {extension.value}: `{e}`",
                color=RED)

        await respond(interaction, message=embed)

        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)

    @extension.command(
        name=f"{text['OWNER_EXTENSION_RELOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_RELOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    # @is_admin()
    @is_owner()
    async def _extension_reload(self, interaction: discord.Interaction, extension: Choice[str] = None) -> None:
        if not extension:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        try:
            await self.bot.reload_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_RELOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_RELOADING']} {extension.value}: `{e}`",
                color=RED)

        await respond(interaction, message=embed)

        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)

    @owners.command(
        name=text['OWNER_OWNERS_ADD_NAME'],
        description=text['OWNER_OWNERS_ADD_DESC'])
    @not_blacklisted()
    # @is_admin()
    @is_owner()
    async def _owners_add(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        owners = await self.bot.db.get("owners")

        if str(member.id) not in owners:
            owners.append(str(member.id))
        else:
            return await respond(interaction, RED, message=text['OWNER_OWNERS_ALREADY_OWNER'])

        await self.bot.db.update("owners", owners)
        await respond(interaction, GREEN, message=f"{text['OWNER_OWNERS_USER_ADDED']} {member.name}")

    @owners.command(
        name=text['OWNER_OWNERS_REM_NAME'],
        description=text['OWNER_OWNERS_REM_DESC'])
    @not_blacklisted()
    # @is_admin()
    @is_owner()
    async def _owners_remove(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        owners = await self.bot.db.get("owners")

        if not str(member.id) in owners:
            return await respond(interaction, RED, message=f"{member.name} {text['OWNER_OWNERS_NOT_OWNER']}")

        owners.remove(str(member.id))

        await interaction.response.defer()

        await self.bot.db.update("owners", owners)
        await respond(interaction, GREEN, message=f"{member.name} {text['OWNER_OWNERS_REMOVED']}", response_type=1)

        # If no owners are left
        if len(owners) < 1 or not owners:
            # Grab member names and IDs
            members = [m for m in interaction.guild.members if not m.bot]
            unames = [m.global_name for m in members]
            uids = [str(m.id) for m in members]

            # Run view and wait for response
            view = ZeroOwnersView(unames, self, interaction.user.id)

            msg = await interaction.channel.send(text["OWNER_OWNERS_EMPTY_WARNING"], view=view)

            while not self.selected_user:
                await asyncio.sleep(0.5)

            view.stop()

            await msg.delete()

            # Grab ID of selected user
            if str(self.selected_user) in unames:
                id = uids[int(unames.index(str(self.selected_user)))]

                # Add user to owners
                owners.append(str(id))

                await self.bot.db.update("owners", owners)

                await respond(
                    interaction, color=GREEN, message=f"{text['OWNER_OWNERS_USER_ADDED']} {self.selected_user}",
                    response_type=1)

                self.selected_user = None

    @app_commands.command(
        name=text["OWNER_RELOAD_EVENT_HANDLER_NAME"],
        description=text["OWNER_RELOAD_EVENT_HANDLER_DESC"])
    async def _reload_event_handler(self, interaction: Interaction) -> None:
        await self.bot.add_cog(EventHandler(self.bot), override=True)
        await respond(interaction, color=YELLOW, message=text["OWNER_RELOAD_EVENT_HANDLER_TEXT"])

    @app_commands.command(
        name=text["OWNER_SHUTDOWN_NAME"],
        description=text["OWNER_SHUTDOWN_DESC"])
    async def _shutdown(self, interaction: Interaction) -> None:
        await respond(interaction, YELLOW, text["OWNER_SHUTDOWN_EMBED_DESC"])
        await self.bot.stop()

# SETUP
async def setup(bot: RinBot):
    ai_ext = ["imagecaption", "languagemodel", "message_handler", "stablediffusion"]
    booru_ext = ["booru"]
    rule34_ext = ["rule34"]

    sum = ai_ext + booru_ext + rule34_ext

    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/"):
        if file.endswith(".py"):
            extension = file[:-3]

            if config["AI_ENABLED"] and extension in ai_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif config["BOORU_ENABLED"] and extension in booru_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif config["RULE34_ENABLED"] and extension in rule34_ext:
                ext_list.append(Choice(name=extension, value=extension))

            is_general = all(extension not in sl for sl in sum)
            if is_general:
                ext_list.append(Choice(name=extension, value=extension))

    await bot.add_cog(Owner(bot))