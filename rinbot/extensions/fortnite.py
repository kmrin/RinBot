"""
RinBot's fortnite command cog
- Commands:
    * /fortnite daily-shop `Manually shows the fortnite daily shop on the channel`
    * /fortnite stats `Shows the player's ingame stats as an image on the channel`
"""

from discord import File, Interaction, app_commands
from discord.ext.commands import Cog
from discord.app_commands import Choice

from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Fortnite(Cog, name='fortnite'):
    def __init__(self, bot: RinBot):
        self.bot = bot

    fortnite_group = app_commands.Group(name=text["FORTNITE_GROUP_NAME"], description=text["FORTNITE_GROUP_DESC"])

    @fortnite_group.command(
        name=text['FORTNITE_DAILY_SHOP_NAME'],
        description=text['FORTNITE_DAILY_SHOP_DESC'])
    @not_blacklisted()
    async def daily_shop(self, interaction: Interaction) -> None:
        await interaction.response.defer(thinking=True)
        await show_fn_daily_shop(self.bot, interaction)
    
    @fortnite_group.command(
        name=text['FORTNITE_STATS_NAME'],
        description=text['FORTNITE_STATS_DESC'])
    @app_commands.choices(
        season=[
            Choice(name=text['YES'], value=1)])
    @not_blacklisted()
    async def stats(self, interaction: Interaction, player: str, season: Choice[int]=0) -> None:
        await interaction.response.defer()
        
        data = await self.bot.fortnite_api.get_stats(player, True if season == 0 else False)
        
        stats = data[0]
        img_path = data[1]
        
        if 'error' in stats.keys():
            errors = {
                401: text['FORTNITE_STATS_ERROR_401'],
                404: text['FORTNITE_STATS_ERROR_404'].format(
                    name=f'`{player}`'
                )
            }
            
            return await respond(interaction, Colour.RED, errors[stats['status']], response_type=1)
        
        if not img_path:
            return await respond(interaction, Colour.RED, text['FORTNITE_STATS_ERORR_IMG'], response_type=1)
        
        img = File(img_path, filename=f'{player}.png')
        
        await interaction.followup.send(file=img)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Fortnite(bot))
