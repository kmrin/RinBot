"""
RinBot v1.9.0
made by rin
"""

# Imports
import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from program.checks import *
from rule34 import rule34Api

# Command cog 'rule34'
class Rule34(commands.Cog, name='rule34'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name='rule34-icame',
        description='Shows the top 10 characters on the i came list')
    @not_blacklisted()
    async def r34_icame(self, ctx:Context) -> None:
        await ctx.defer()
        r34 = rule34Api()
        result = r34.icame(limit=10)
        chars = []
        for char in result:
            char_name = char._character_name.split(" ")
            char_name = [name.capitalize() for name in char_name]
            char_name = ' '.join(char_name)
            chars.append(char_name)
        result = [f"**{i+1}.** {r}" for i, r in enumerate(chars)]
        result = '\n'.join(result)
        embed = discord.Embed(
            title=' 📋  Top 10 I Came',
            description=result,
            color=0x9f17d1)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name='rule34-random',
        description='Shows a random image or gif from rule34 with the given tags')
    @app_commands.describe(tags='The tags of your choice')
    @not_blacklisted()
    async def rule34_random(self, ctx:Context, tags:str=None) -> None:
        await ctx.defer()
        if not tags:
            embed = discord.Embed(
                description=" ❌  'tags' attribute empty.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        r34 = rule34Api()
        tags = tags.split(" ")
        post = r34.random_post(tags)
        embed = discord.Embed(color=0x9f17d1)
        embed.set_image(url=post._image)
        embed.add_field(
            name='Open on browser',
            value=f'[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})',
            inline=False)
        await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Rule34(bot))