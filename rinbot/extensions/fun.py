"""
#### RinBot's fun command cog
- Commands:
    * /pet `:3`
    * /cat `Shows a random cat`
    * /dog `Shows a random dog`
    * /fact `Shows a random fact`
    * /heads-or-tails `Plays heads-or-tails with rinbot`
    * /rps `Plays rock paper scissors with rinbot`

- NekoBot commands:
    * /threats
    * /captcha
    * /whowouldwin
    * /deepfry
    * /stickbug
"""

import io, os, random, aiohttp, discord
from PIL import Image
from io import BytesIO
from discord import app_commands
from discord.ext.commands import Cog
from rinbot.petpet.petpet import make_petpet
from rinbot.nekobot import NekoBotAsync
from rinbot.stickbug.stick_bug import StickBug
from rinbot.base.interface import ButtonChoice, RockPaperScissorsView
from rinbot.base.helpers import load_lang, translate
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

text = load_lang()

# noinspection PyUnresolvedReferences,PyBroadException
class Fun(Cog, name="fun"):
    def __init__(self, bot: RinBot):
        self.bot = bot
        self.neko_api = NekoBotAsync()

    @app_commands.command(
        name=text["FUN_PET_NAME"],
        description=text["FUN_PET_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _pet_pet(self, interaction: discord.Interaction, member: discord.Member) -> None:
        if not member:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        try:
            image = await member.avatar.read()
        except AttributeError:
            image = await member.default_avatar.read()

        await interaction.response.defer()

        source = io.BytesIO(image)
        dest = io.BytesIO()

        make_petpet(source, dest)

        dest.seek(0)

        await interaction.followup.send(
            f"{interaction.user.mention} {text['FUN_PET_PETTED']} {member.mention}"
            if not interaction.user.id == member.id else
            f"{interaction.user.mention} {text['FUN_PET_SCHITZO']}",
            file=discord.File(dest, filename=f"{image[0]}-petpet.gif"))

    @app_commands.command(
        name=text['FUN_CAT_NAME'],
        description=text['FUN_CAT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _cat(self, interaction: Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    return await respond(interaction, RED, text['FUN_CAT_SAD_MEOW'], text['FUN_CAT_NOT_FOUND'])
                js = await resp.json()
                embed = discord.Embed(color=PURPLE)
                embed.set_image(url=js[0]["url"])
                await respond(interaction, message=embed)

    # noinspection PyCallingNonCallable
    @app_commands.command(
        name=text['FUN_DOG_NAME'],
        description=text['FUN_DOG_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _dog(self, interaction: Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.dog/woof") as resp:
                if resp.status != 200:
                    return await respond(interaction, RED, text['FUN_DOG_SAD_WOOF'])
                filename = await resp.text()
                url = f"https://random.dog/{filename}"
                filesize = interaction.guild.filesize_limit if interaction.guild else 8388608
                if filename.endswith((".mp4", ".webm")):
                    async with interaction.channel.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                return await respond(interaction, RED, text['FUN_DOG_SAD_WOOF'],
                                                     text['FUN_DOG_NOT_FOUND'])
                            if int(other.headers["Content-Length"]) >= filesize:
                                await self._dog(interaction)
                            fp = io.BytesIO(await other.read())
                            await interaction.response.send_message(file=discord.File(fp, filename=filename))
                else:
                    embed = discord.Embed(color=RED)
                    embed.set_image(url=url)
                    await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name=text['FUN_FACT_NAME'],
        description=text['FUN_FACT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    @app_commands.describe(language=text['FUN_FACT_LANGUAGE_DESC'])
    async def _randomfact(self, interaction: Interaction, language: str = "en") -> None:
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    fact = data["text"]
                    if not language == "en":
                        fact = translate(fact, to_lang=language)
                        if not fact:
                            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
                    embed = discord.Embed(description=fact, color=GREEN)
                else:
                    embed = discord.Embed(
                        title=text['ERROR'],
                        description=text['FUN_FACT_API_ERROR'],
                        color=RED)
                print("PORRA")
                await respond(interaction, message=embed, response_type=1)

    @app_commands.command(
        name=text['FUN_HOT_NAME'],
        description=text['FUN_HOT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _heads_or_tails(self, interaction: Interaction) -> None:
        buttons = ButtonChoice()

        embed = discord.Embed(description=text['FUN_HOT_EMBED_DESC'], color=GREEN)

        await interaction.response.send_message(embed=embed, view=buttons)
        await buttons.wait()

        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_WON'][0]} `{buttons.value}` {text['FUN_HOT_WON'][1]} `{result}`.",
                color=GREEN, )
        else:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_LOST'][0]} `{buttons.value}` {text['FUN_HOT_LOST'][1]} `{result}`.",
                color=RED, )

        await interaction.edit_original_response(embed=embed, view=None, content=None)

    @app_commands.command(
        name=text['FUN_RPS_NAME'],
        description=text['FUN_RPS_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rps(self, interaction: Interaction) -> None:
        await interaction.response.send_message(text['FUN_RPS_CHOOSE'], view=RockPaperScissorsView())

    @app_commands.command(name="threats")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _threats(self, interaction: Interaction, member: discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        await interaction.response.defer()

        try:
            resp = await self.neko_api.threats(member.avatar.url)
        except AttributeError:
            resp = await self.neko_api.threats(member.default_avatar.url)

        await interaction.followup.send(resp.message)

    @app_commands.command(name="captcha")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _captcha(self, interaction: Interaction, member: discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        await interaction.response.defer()

        try:
            avatar = member.avatar.url
        except AttributeError:
            avatar = member.default_avatar.url

        resp = await self.neko_api.captcha(avatar, member.name)

        await interaction.followup.send(resp.message)

    @app_commands.command(name="whowouldwin")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _whowouldwin(self, interaction: Interaction, member_1: discord.Member=None, member_2: discord.Member=None):
        if not member_1 or not member_2:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        await interaction.response.defer()

        try: avatar_1 = member_1.avatar.url
        except AttributeError: avatar_1 = member_1.default_avatar.url
        try: avatar_2 = member_2.avatar.url
        except AttributeError: avatar_2 = member_2.default_avatar.url

        resp = await self.neko_api.whowouldwin(avatar_1, avatar_2)

        await interaction.followup.send(resp.message)

    @app_commands.command(name="deepfry")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _deepfry(self, interaction: Interaction, member: discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        await interaction.response.defer()

        try: avatar = member.avatar.url
        except AttributeError: avatar = member.default_avatar.url

        resp = await self.neko_api.deepfry(avatar)

        await interaction.followup.send(resp.message)

    @app_commands.command(name="stickbug")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _stickbug(self, interaction: Interaction, member: discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text["ERROR_INVALID_PARAMETERS"])

        await interaction.response.defer()
        
        try: avatar = await member.avatar.read()
        except AttributeError: avatar = await member.default_avatar.read()
        
        image = Image.open(BytesIO(avatar))
        path = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/stickbug"
        video_path = f"{path}/{member.name}.mp4"
        
        bug = StickBug(img=image)
        bug.save_video(video_path)
        
        await interaction.followup.send(file=discord.File(video_path))

        if os.path.isfile(video_path):
            os.remove(video_path)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Fun(bot))