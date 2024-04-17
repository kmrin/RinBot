"""
RinBot's booru command cog
- Commands:
    * /booru-random `Shows a random picture from danbooru with the given tags and rating`
"""

import random
import discord

from discord import app_commands, Interaction
from discord.ext.commands import Cog
from discord.app_commands import Choice

from rinbot.booru import Danbooru
from rinbot.base import log_exception
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import conf
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

UNAME = conf['BOORU_USERNAME']
API = conf['BOORU_KEY']
IS_GOLD = conf['BOORU_IS_GOLD']

class Booru(Cog, name="booru"):
    def __init__(self, bot: RinBot):
        self.bot = bot
        self.client = Danbooru("danbooru", username=UNAME, api_key=API)
    
    booru = app_commands.Group(name=text['BOORU_NAME'], description=text['BOORU_DESC'])

    @booru.command(
        name=text['BOORU_RANDOM_NAME'],
        description=text['BOORU_RANDOM_DESC'])
    @app_commands.choices(
        rating=[
            Choice(name=f"{text['BOORU_RANDOM_RATING_G']}", value="g"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_S']}", value="s"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_Q']}", value="q")])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _booru_random(self, interaction: Interaction, rating: Choice[str], tags: str=None) -> None:
        request_tags = f'rating:{rating.value}'
        
        if tags:
            chars = [',', '.', '|', '  ']
            for char in chars:
                if char in tags:
                    return await respond(interaction, Colour.RED, text['BOORU_RANDOM_INVALID_TAGS'])
            
            tag_count = tags.split(' ')
        
            if len(tag_count) >= 3 and not IS_GOLD:
                return await respond(interaction, Colour.RED, text['BOORU_RANDOM_MAX_API'])
            elif len(tag_count) >= 6:
                return await respond(interaction, Colour.RED, text['BOORU_RANDOM_MAX_API_GOLD'])

            request_tags = request_tags + ' ' + tags
        
        await interaction.response.defer()
        
        try:
            posts = self.client.post_list(
                limit=100,
                tags=request_tags
            )
            
            post = random.choice(posts)
            
            try:
                url = post['file_url']
            except:
                url = post['source']
            
            embed = discord.Embed(colour=Colour.PURPLE)
            embed.set_image(url=url)
            
            await respond(interaction, message=embed, response_type=1)
        except IndexError:
            await respond(interaction, Colour.RED, text['BOORU_RANDOM_NO_RESULTS'], response_type=1)
        except Exception as e:
            e = log_exception(e)
            return await respond(interaction, Colour.RED, text['BOORU_RANDOM_API_ERROR'].format(e=e), response_type=1)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Booru(bot))
