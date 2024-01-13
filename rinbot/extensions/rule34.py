"""
#### RinBot's rule34 command cog
- commands:
    * /rule34 icame `Shows the top 10 leaderboard of rule34's iCame character list`
    * /rule34 random `Shows a random image from rule34 with the given tags`
"""

# Imports
import discord, aiohttp
from discord.ext.commands import Bot, Cog
from discord.app_commands import Group
from rinbot.base.checks import *
from rinbot.rule34 import rule34Api
from rinbot.base.helpers import load_lang
from rinbot.base.colors import *
from io import BytesIO
from PIL import Image

# Verbose
text = load_lang()

# Command cog 'rule34'
class Rule34(Cog, name="rule34"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    rule34_group = Group(name=f"{text['RULE34_NAME']}", description=f"{text['RULE34_DESC']}")
    
    async def convert_png(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    bytes = await response.read()
                    img = Image.open(BytesIO(bytes))
                    out = BytesIO()
                    img.save(out, format="PNG")
                    out.seek(0)
                    return discord.File(out, filename="r34.png")
    
    async def get_random_post(self, tags):
        r34 = rule34Api()
        post = r34.random_post(tags)
        if post._video:
            if post._video != "":
                post = await self.get_random_post(tags)
        if not ".png" in post._image:
            post._image = await self.convert_png(post._image)
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
            return await interaction.followup.send(embed=embed)
        if "," in tags:
            embed = discord.Embed(
                description=f"{text['RULE34_ERROR_COMMA_ON_TAG']}",
                color=PURPLE)
            return await interaction.followup.send(embed=embed)
        tags = tags.split(" ")
        post = await self.get_random_post(tags)
        if isinstance(post._image, discord.File):
            await interaction.channel.send(content=f"{text['RULE34_RANDOM_LINK_TEXT']}[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})", file=post._image)
        else:
            await interaction.channel.send(content=f"{text['RULE34_RANDOM_LINK_TEXT']}[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})")

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Rule34(bot))