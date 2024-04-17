"""
RinBot's rule34 command cog
- commands:
    * /rule34 icame `Shows the top 10 leaderboard of rule34's iCame character list`
    * /rule34 random `Shows a random image from rule34 with the given tags`
"""

import aiohttp
import discord

from io import BytesIO
from PIL import Image
from typing import Union
from discord import app_commands, Interaction
from discord.ext.commands import Cog

from rinbot.rule34.post import Post
from rinbot.rule34 import rule34Api
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Rule34(Cog, name="rule34"):
    def __init__(self, bot: RinBot):
        self.bot = bot
        self.api = rule34Api()

    rule34 = app_commands.Group(name=text['RULE34_NAME'], description=text['RULE34_DESC'])
    
    @staticmethod
    async def __convert_png(url) -> Union[discord.File, None]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status!= 200:
                    return None
                
                img_b = await response.read()
                img = Image.open(BytesIO(img_b))
                out = BytesIO()
                img.save(out, format='PNG')
                out.seek(0)
                
                return discord.File(out, filename='r34_result.png')
    
    async def __get_random_post(self, tags) -> Union[list, Post, None]:
        post = self.api.random_post(tags)
        
        if not post:
            return None
        
        if post._video:
            if post._video != '':
                post = await self.__get_random_post(tags)
        
        if not '.png' in post._image:
            post._image = await self.__convert_png(post._image)
        
        return post
    
    @rule34.command(
        name=text["RULE34_RANDOM_NAME"],
        description=text["RULE34_RANDOM_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rule34_random(self, interaction: Interaction, tags: str) -> None:
        chars = [',', '.', '|', '  ']
        for char in chars:
            if char in tags:
                return await respond(interaction, Colour.RED, text['RULE34_RANDOM_INVALID_TAGS'])
        
        await interaction.response.defer()
        
        tags = tags.split(' ')
        post = await self.__get_random_post(tags)
        
        if not post:
            return await respond(interaction, Colour.RED, text['RULE34_RANDOM_NO_RESULTS'], response_type=1)
        
        if isinstance(post._image, discord.File):
            await interaction.followup.send(
                f'{text["RULE34_RANDOM_LINK_TEXT"]}[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})',
                file=post._image
            )
        else:
            await interaction.followup.send(
                f'{text["RULE34_RANDOM_LINK_TEXT"]}[Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})'
            )
    
    @rule34.command(
        name=text["RULE34_ICAME_NAME"],
        description=text["RULE34_ICAME_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rule34_icame(self, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        result = self.api.icame(limit=10)
        chars = []
        
        for char in result:
            char_name = char._character_name.split(" ")
            char_name = [name.capitalize() for name in char_name]
            char_name = " ".join(char_name)
            chars.append(char_name)

        result = [f"**{i + 1}.** {r}" for i, r in enumerate(chars)]
        result = "\n".join(result)
        
        await respond(interaction, Colour.PURPLE, result, text['RULE34_ICAME_TITLE'], response_type=1)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Rule34(bot))
