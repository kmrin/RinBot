"""
RinBot's general command cog
- Commands:
    * /help `Shows a help paginated embed with all commands`
    * /translate `Translates a string to another language (Auto -> PT-BR by default)`
    * /specs `Shows the system specs of the computer running the bot`
    * /rininfo `Shows info about the bot`
    * /ping `Sends back a ping-pong response with the bot's network latency`
"""

import os, discord, platform
from discord import app_commands
from discord.ext.commands import Cog
from rinbot.base.helpers import load_config, load_lang, remove_nl, get_specs, translate, format_exception
from rinbot.base.interface import Paginator
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

config = load_config()
text = load_lang()

class General(Cog, name="general"):
    def __init__(self, bot: RinBot):
        self.bot = bot

    @app_commands.command(
        name=text["GENERAL_HELP_NAME"],
        description=text["GENERAL_HELP_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _help(self, interaction: Interaction) -> None:
        try:
            with open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/text/help-{config['LANGUAGE']}.md",
                      "r", encoding="utf-8") as f:

                lines = f.readlines()
                lines = "\n".join(remove_nl(lines)).split("\n")

                chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]

                embed = discord.Embed(title=text["GENERAL_HELP_TITLE"], color=YELLOW)
                embed.description="\n".join(chunks[0])

                view = Paginator(embed, chunks)

                await respond(interaction, message=embed, view=view)
        except FileNotFoundError:
            await respond(interaction, RED, message=text["ERROR_FILE_NOT_FOUND"])
        except Exception as e:
            await self.bot.log("erro'r", format_exception(e))

    @app_commands.command(
        name=text['GENERAL_TRANSLATE_NAME'],
        description=text['GENERAL_TRANSLATE_DESC'])
    @app_commands.describe(from_lang=text['GENERAL_TRANSLATE_FROM_LANG'])
    @app_commands.describe(to_lang=text['GENERAL_TRANSLATE_TO_LANG'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _translate(self, interaction: Interaction, text: str=None, from_lang: str=None, to_lang: str="pt-br") -> None:
        lang = load_lang()
        if not text or not from_lang:
            return await respond(interaction, RED, message=lang['ERROR_INVALID_PARAMETERS'])

        await interaction.response.defer()

        text = translate(text, from_lang=from_lang, to_lang=to_lang)

        await respond(interaction, YELLOW, message=text, response_type=1)

    @app_commands.command(
        name=text['GENERAL_SPECS_NAME'],
        description=text['GENERAL_SPECS_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _specs(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        specs = get_specs()
        
        embed = discord.Embed(title=text['GENERAL_SPECS_TITLE'], color=BLUE)
        
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)
        
        embed.add_field(name=text['GENERAL_SPECS_SYSTEM'], value=specs['os'], inline=False)
        embed.add_field(name="CPU", value=specs['cpu'], inline=False)
        embed.add_field(name="RAM", value=specs['ram'], inline=False)
        embed.add_field(name="GPU", value=specs['gpu'], inline=False)
        
        try:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {interaction.user.global_name}",
                             icon_url=interaction.user.avatar.url)
        except AttributeError:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {interaction.user.global_name}",
                             icon_url=interaction.user.default_avatar.url)
        
        await respond(interaction, message=embed, response_type=1)

    @app_commands.command(
        name=text['GENERAL_RININFO_NAME'],
        description=text['GENERAL_RININFO_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rininfo(self, interaction: Interaction) -> None:
        embed = discord.Embed(title=f"{text['GENERAL_RININFO_EMBED_TITLE']}", color=YELLOW)

        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)

        embed.add_field(name=f"{text['GENERAL_RININFO_CREATED_IN'][0]}",
                        value=f"{text['GENERAL_RININFO_CREATED_IN'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_VERSION'][0]}", value=f"{text['GENERAL_RININFO_VERSION'][1]}",
                        inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_PROGRAMMER'][0]}",
                        value=f"{text['GENERAL_RININFO_PROGRAMMER'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_BUGFINDER'][0]}", value=f"{text['GENERAL_RININFO_BUGFINDER'][1]}",
                        inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_PY_VER']}", value=f"{platform.python_version()}", inline=True)

        try:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {interaction.user}",
                             icon_url=f"{interaction.user.avatar.url}")
        except AttributeError:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {interaction.user}",
                             icon_url=f"{interaction.user.default_avatar.url}")

        await respond(interaction, message=embed)

    @app_commands.command(
        name=text['GENERAL_PING_NAME'], description=text['GENERAL_PING_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _ping(self, interaction: Interaction) -> None:
        await respond(interaction, YELLOW, "🏓 Pong!",
                      f"{text['GENERAL_PING_EMBED']} {round(self.bot.latency * 1000)}ms")

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(General(bot))