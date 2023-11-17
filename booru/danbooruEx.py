"""
RinBot v1.9.0 (GitHub release)
made by rin
"""

# Imports
from __future__ import unicode_literals
import discord, random, os
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from discord.app_commands.models import Choice
from program.checks import *
from booru import Danbooru
from random import randint
from dotenv import load_dotenv
from program.helpers import strtobool

# Load env vars
load_dotenv()
BOORU_USERNAME=os.getenv("BOORU_USERNAME")
BOORU_API_KEY=os.getenv("BOORU_API_KEY")
BOORU_IS_GOLD=strtobool(os.getenv("BOORU_IS_GOLD"))

# 'booru' command block
class Booru(commands.Cog, name='booru'):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(
        name='booru-random',
        description='Gives you a random danbooru image from your given tags and rating!')
    @app_commands.describe(rating='The rating of your image')
    @app_commands.describe(tags='Your tags')
    @app_commands.choices(
        rating=[
            Choice(name='G - general', value='g'),
            Choice(name='S - sensitive', value='s'),
            Choice(name='Q - questionable', value='q')])
    @not_blacklisted()
    async def booru_random(self, ctx:Context, rating:Choice[str]=None, tags:str=None) -> None:
        await ctx.defer()
        if not rating:
            embed = discord.Embed(
                description=" ❌  'rating' attribute empty.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        tag_count = tags.split(" ")
        if len(tag_count) >= 3 and not BOORU_IS_GOLD:
            embed = discord.Embed(
                description=" ❌  Due to API limitations, provide only a max. of 2 tags.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        elif len(tag_count) >= 6:
            embed = discord.Embed(
                description=" ❌  Due to API limitations, provide only a max. of 6 tags.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
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
            embed = discord.Embed(
                title=' ❌  Error on DanbooruAPI',
                description=f"{e}",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(color=0x9f17d1)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Booru(bot))