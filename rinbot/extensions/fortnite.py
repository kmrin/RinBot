"""
RinBot's fortnite command cog
- Commands:
    * /fortnite daily-shop `Manually shows the fortnite daily shop on the channel`
    * /fortnite stats `Shows the player's ingame stats as an image on the channel`
"""

import discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import Cog
from discord.app_commands.models import Choice
from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.base.helpers import load_lang
from rinbot.base.responder import respond
from rinbot.base.checks import *
from rinbot.base.colors import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

text = load_lang()

class Fortnite(Cog, name="fortnite"):
    def __init__(self, bot: "RinBot"):
        self.bot = bot
    
    # Command groups
    fortnite_group = app_commands.Group(name=text["FORTNITE_GROUP_NAME"], description=text["FORTNITE_GROUP_DESC"])
    
    @fortnite_group.command(
        name=text['FORTNITE_DAILY_SHOP_NAME'],
        description=text['FORTNITE_DAILY_SHOP_DESC'])
    @not_blacklisted()
    async def daily_shop(self, interaction:Interaction) -> None:
        await interaction.response.defer(thinking=True)
        await show_fn_daily_shop(self.bot, interaction)
    
    @fortnite_group.command(
        name=text['FORTNITE_STATS_NAME'],
        description=text['FORTNITE_STATS_DESC'])
    @app_commands.choices(season=[Choice(name=text["YES"], value="yes")])
    @not_blacklisted()
    async def player_stats(self, interaction:Interaction, player:str=None, season:Choice[str]="no") -> None:
        await interaction.response.defer()
        
        if not player:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'], response_type=1)
        
        data = await self.bot.fortnite_api.get_stats(player, False if season == "no" else True)
        
        stats = data[0]
        img_path = data[1]
        
        if "error" in stats.keys():
            errors = {
                401: text['FORTNITE_STATS_ERROR_401'],
                404: f"{text['FORTNITE_STATS_ERROR_404'][0]} `'{player}'` {text['FORTNITE_STATS_ERROR_404'][1]}"}
            
            return await respond(interaction, RED, message=errors[stats["status"]], response_type=1)
                
        if not img_path:
            return await respond(interaction, RED, message=text['FORTNITE_STATS_ERROR_IMG'], response_type=1)
        
        img = discord.File(img_path, filename=f"{player}.png")
        
        await interaction.followup.send(file=img)

# SETUP
async def setup(bot: "RinBot"):
    await bot.add_cog(Fortnite(bot))