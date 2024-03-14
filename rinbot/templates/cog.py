"""
#### Template of a command Cog for rinbot
"""

import asyncio, discord
from discord import app_commands
from discord.ext.commands import Cog
from rinbot.base.helpers import load_lang
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

text = load_lang()

class MyCog(Cog, name="mycog"):
    def __init__(self, bot: RinBot):
        self.bot = bot

    @app_commands.command(
        name="example-command",
        description="example-command-description")
    @not_blacklisted()
    @is_admin()
    @is_owner()
    async def _example_command(self, interaction: discord.Interaction) -> None:
        await respond(interaction, color=YELLOW, message="This is an example command!")

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(MyCog(bot))