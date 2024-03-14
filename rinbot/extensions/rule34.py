"""
#### RinBot's rule34 command cog
- commands:
    * /rule34 icame `Shows the top 10 leaderboard of rule34's iCame character list`
    * /rule34 random `Shows a random image from rule34 with the given tags`
"""

import discord, aiohttp
from io import BytesIO
from PIL import Image
from discord import app_commands
from discord.ext.commands import Cog
from rinbot.rule34.post import Post
from rinbot.rule34 import rule34Api
from rinbot.base.helpers import load_lang
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

text = load_lang()

# noinspection PyUnresolvedReferences,PyBroadException,PyProtectedMember
class Rule34(Cog, name="rule34"):
    def __init__(self, bot: RinBot):
        self.bot = bot

    # Command groups
    rule34 = app_commands.Group(name=text["RULE34_NAME"], description=text["RULE34_DESC"])

    @staticmethod
    async def __convert_png(url) -> discord.File | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    bytes = await response.read()
                    img = Image.open(BytesIO(bytes))
                    out = BytesIO()
                    img.save(out, format="PNG")
                    out.seek(0)
                    return discord.File(out, filename="r34.png")
                else:
                    return None

    async def __get_random_post(self, tags) -> list | Post:
        r34 = rule34Api()
        post = r34.random_post(tags)
        if post._video:
            if post._video != "":
                post = await self.__get_random_post(tags)
        if not ".png" in post._image:
            post._image = await self.__convert_png(post._image)
        return post

    @rule34.command(
        name=text["RULE34_ICAME_NAME"],
        description=text["RULE34_ICAME_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rule34_icame(self, interaction: discord.Interaction) -> None:
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

        await respond(interaction, color=PURPLE, title=text["RULE34_ICAME_TITLE"], message=result, response_type=1)

    @rule34.command(
        name=text["RULE34_RANDOM_NAME"],
        description=text["RULE34_RANDOM_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rule34_random(self, interaction: discord.Interaction, tags: str=None) -> None:
        if not tags:
            return await respond(interaction, RED, message=text["RULE34_RANDOM_NO_TAG"])

        if "," in tags:
            return await respond(interaction, RED, message=text["RULE34_ERROR_COMMA_ON_TAG"])

        await interaction.response.defer()

        tags = tags.split(" ")
        post = await self.__get_random_post(tags)

        if isinstance(post._image, discord.File):
            await interaction.followup.send(
                content=f"{text['RULE34_RANDOM_LINK_TEST']} [Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})",
                file=post._image)
        else:
            await interaction.followup.send(
                content=f"{text['RULE34_RANDOM_LINK_TEXT']} [Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})")

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Rule34(bot))