# Imports
import discord
from discord.ext.commands import Bot, Cog
from discord.app_commands import Group
from program.base.checks import *
from program.rule34 import rule34Api
from program.base.helpers import load_lang
from program.base.colors import *

# Verbose
text = load_lang()

# Command cog 'rule34'
class Rule34(Cog, name="rule34"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    rule34_group = Group(name=f"{text['RULE34_NAME']}", description=f"{text['RULE34_DESC']}")
    
    async def get_random_post(self, tags):
        r34 = rule34Api()
        post = r34.random_post(tags)
        if post._video != "":
            post = await self.get_random_post(tags)
        return post
    
    @rule34_group.command(
        name=f"{text['RULE34_ICAME_NAME']}",
        description=f"{text['RULE34_ICAME_DESC']}")
    @not_blacklisted()
    async def rule34_icame(self, interaction:discord.Interaction) -> None:
        await interaction.response.defer()
        r34 = rule34Api()
        result = r34.icame(limit=10)
        chars = []
        for char in result:
            char_name = char._character_name.split(" ")
            char_name = [name.capitalize() for name in char_name]
            char_name = " ".join(char_name)
            chars.append(char_name)
        result = [f"**{i+1}.** {r}" for i, r in enumerate(chars)]
        result = "\n".join(result)
        embed = discord.Embed(
            title=f"{text['RULE34_ICAME_TITLE']}",
            description=result,
            color=PURPLE)
        await interaction.followup.send(embed=embed)
    
    @rule34_group.command(
        name=f"{text['RULE34_RANDOM_NAME']}",
        description=f"{text['RULE34_RANDOM_DESC']}")
    @not_blacklisted()
    async def rule34_random(self, interaction:discord.Interaction, tags:str=None) -> None:
        await interaction.response.defer()
        if not tags:
            embed = discord.Embed(
                description=f"{text['RULE34_RANDOM_NO_TAG']}",
                color=PURPLE)
            await interaction.followup.send(embed=embed)
            return
        tags = tags.split(" ")
        post = await self.get_random_post(tags)
        embed = discord.Embed(color=0x9f17d1)
        embed.set_image(url=post._image)
        embed.add_field(
            name=f"{text['RULE34_RANDOM_LINK_TEXT']}",
            value=f'[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})',
            inline=False)
        await interaction.followup.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Rule34(bot))