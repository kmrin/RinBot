"""
RinBot's gemini command cog
- Commands:
    * /gemini talk - `Begin a conversation with google's gemini`
    * /gemini reset - `Resets your conversation`
"""

import discord
from discord import app_commands
from discord.ext.commands import Cog
from discord.app_commands.models import Choice
from rinbot.gemini.conversation import message, reset
from rinbot.base.helpers import load_lang, load_config
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

text = load_lang()
conf = load_config()

class Gemini(Cog, name="gemini"):
    def __init__(self, bot: RinBot):
        self.bot = bot

    # command groups
    gemini = app_commands.Group(name=text["GEMINI_NAME"], description=text["GEMINI_DESC"])

    @gemini.command(
        name=text["GEMINI_TALK_NAME"],
        description=text["GEMINI_TALK_DESC"])
    @app_commands.describe(prompt=text["GEMINI_TALK_PROMPT_DESC"])
    @app_commands.describe(private=text["GEMINI_TALK_PRIVATE_DESC"])
    @app_commands.choices(
        private=[Choice(name=text["YES"], value=1)])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _gemini_talk(self, interaction: discord.Interaction, prompt: str=None, private: Choice[int]=0) -> None:
        if not prompt:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])
        
        ephemeral = False if private == 0 else True
        await interaction.response.defer(thinking=True, ephemeral=ephemeral)
        text = message(interaction.user.name, prompt)
        await interaction.followup.send(text, ephemeral=ephemeral)

    @gemini.command(
        name=text["GEMINI_RESET_NAME"],
        description=text["GEMINI_RESET_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _gemini_reset(self, interaction: discord.Interaction) -> None:
        reset(interaction.user.name)
        await respond(interaction, GREEN, message=text["GEMINI_RESET_SUCCESS"])

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Gemini(bot))