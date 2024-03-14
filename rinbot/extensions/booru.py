"""
RinBot's booru command cog
- Commands:
    * /booru-random `Shows a random picture from danbooru with the given tags and rating`
"""

from __future__ import unicode_literals
import random, discord
from random import randint
from discord import app_commands
from discord.ext.commands import Cog
from discord.app_commands.models import Choice
from rinbot.booru import Danbooru
from rinbot.base.helpers import load_config, load_lang, format_exception
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

config = load_config()
text = load_lang()

UNAME = config["BOORU_USERNAME"]
API = config["BOORU_KEY"]
IS_GOLD = config["BOORU_IS_GOLD"]

class Booru(Cog, name="booru"):
    def __init__(self, bot: RinBot):
        self.bot = bot
    
    # Command groups
    booru = app_commands.Group(name=text["BOORU_NAME"], description=text["BOORU_DESC"])
    
    @booru.command(
        name=text["BOORU_RANDOM_NAME"],
        description=text["BOORU_RANDOM_DESC"])
    @app_commands.choices(
        rating=[
            Choice(name=f"{text['BOORU_RANDOM_RATING_G']}", value="g"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_S']}", value="s"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_Q']}", value="q")])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _booru_random(self, interaction: discord.Interaction, rating: Choice[str]=None, tags: str=None) -> None:
        # If a rating is not provided
        if not rating:
            return await respond(interaction, RED, message=text["BOORU_RANDOM_NO_RAT"])
        
        # Split tags and check how many are there
        tag_count = tags.split(" ")
        if len(tag_count) >=3 and not IS_GOLD:
            return await respond(interaction, RED, message=text["BOORU_RANDOM_MAX_API"])
        elif len(tag_count) >= 6:
            return await respond(interaction, RED, text["BOORU_RANDOM_MAX_API_GOLD"])
        
        # Do the thing
        await interaction.response.defer()
        
        try:
            try:
                client = Danbooru("danbooru", username=UNAME, api_key=API)
                posts = client.post_list(tags=f"rating:{rating.value}"
                                         if not tags else tags, pages=randint(1, 1000), limit=1000)
                post = random.choice(posts)
                
                try:
                    url = post["file_url"]
                except:
                    url = post["source"]
                
                embed = discord.Embed(color=PURPLE)
                embed.set_image(url=url)
                
                await respond(interaction, message=embed, response_type=1)
            except IndexError:
                return await respond(interaction, RED, message=text["BOORU_RANDOM_EMPTY_RESPONSE"], response_type=1)
        except Exception as e:
           e = format_exception(e)
           return await respond(interaction, RED, text["BOORU_RANDOM_API_ERROR"], e, response_type=1)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Booru(bot))