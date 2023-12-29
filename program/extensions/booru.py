# Imports
from __future__ import unicode_literals
import discord, random, os
from discord import Interaction
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Group
from discord.app_commands.models import Choice
from program.base.checks import *
from program.booru import Danbooru
from random import randint
from dotenv import load_dotenv
from program.base.helpers import strtobool, load_lang, format_exception
from program.base.colors import *

# Verbose
text = load_lang()

# Load env vars
load_dotenv()
BOORU_USERNAME=os.getenv("BOORU_USERNAME")
BOORU_API_KEY=os.getenv("BOORU_API_KEY")
BOORU_IS_GOLD=strtobool(os.getenv("BOORU_IS_GOLD"))

# 'booru' command block
class Booru(commands.Cog, name='booru'):
    def __init__(self, bot):
        self.bot = bot
    
    booru_group = Group(name=f"{text['BOORU_NAME']}", description=f"{text['BOORU_DESC']}")
    
    @booru_group.command(
        name=f"{text['BOORU_RANDOM_NAME']}",
        description=f"{text['BOORU_RANDOM_DESC']}")
    @app_commands.choices(
        rating=[
            Choice(name=f"{text['BOORU_RANDOM_RATING_G']}", value="g"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_S']}", value="s"),
            Choice(name=f"{text['BOORU_RANDOM_RATING_Q']}", value="q")])
    @not_blacklisted()
    async def booru_random(self, interaction:Interaction, rating:Choice[str]=None, tags:str=None) -> None:
        if not rating:
            embed = discord.Embed(
                description=f"{text['BOORU_RANDOM_NO_RAT']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        tag_count = tags.split(" ")
        if len(tag_count) >= 3 and not BOORU_IS_GOLD:
            embed = discord.Embed(
                description=f"{text['BOORU_RANDOM_MAX_API']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        elif len(tag_count) >= 6:
            embed = discord.Embed(
                description=f"{text['BOORU_RANDOM_MAX_API_GOLD']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        await interaction.response.defer()
        try:
            client = Danbooru('danbooru', username=BOORU_USERNAME, api_key=BOORU_API_KEY)
            posts = client.post_list(tags=f'rating:{rating.value}'
                                     if not tags else tags, pages=randint(1, 1000), limit=1000)
            post = random.choice(posts)
            try:
                url = post['file_url']
            except:
                url = post['source']
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                title=f"{text['BOORU_RANDOM_API_ERROR']}",
                description=f"{e}",
                color=0xd91313)
            return await interaction.followup.send(embed=embed)
        embed = discord.Embed(color=0x9f17d1)
        embed.set_image(url=url)
        await interaction.followup.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Booru(bot))