"""
RinBot's gemini command cog
- Commands:
    * /gemini talk - `Begin a conversation with google's gemini`
    * /gemini reset - `Resets your conversation`
"""

import discord

from discord import app_commands, Interaction
from discord.ext.commands import Cog
from discord.app_commands import Choice

from rinbot.gemini.conversation import message, reset
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Gemini(Cog, name='gemini'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    gemini = app_commands.Group(name=text['GEMINI_NAME'], description=text['GEMINI_DESC'])
    
    @gemini.command(
        name=text['GEMINI_TALK_NAME'],
        description=text['GEMINI_TALK_DESC'])
    @app_commands.describe(prompt=text['GEMINI_TALK_PROMPT_DESC'])
    @app_commands.describe(private=text['GEMINI_TALK_PRIVATE_DESC'])
    @app_commands.choices(
        private=[Choice(name=text['YES'], value=1)])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _gemini_talk(self, interaction: Interaction, prompt: str, private: Choice[int] = 0) -> None:
        ephemeral = False if private == 0 else True
        await interaction.response.defer(thinking=True, ephemeral=ephemeral)
        msg = message(interaction.user.name, prompt)
        await interaction.followup.send(msg, ephemeral=ephemeral)
    
    @gemini.command(
        name=text['GEMINI_RESET_NAME'],
        description=text['GEMINI_RESET_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _gemini_reset(self, interaction: Interaction) -> None:
        reset(interaction.user.name)
        await respond(interaction, Colour.GREEN, text['GEMINI_RESET_SUCCESS'])

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Gemini(bot))
