"""
#### RinBot's fun command cog
- Commands:
    * /pet `:3`
    * /cat `Shows a random cat`
    * /dog `Shows a random dog`
    * /fact `Shows a random fact`
    * /heads-or-tails `Plays heads-or-tails with rinbot`
    * /rps `Plays rock paper scissors with rinbot`
"""

# Imports
import random, aiohttp, discord, io
from discord import app_commands
from discord.ext.commands import Bot, Cog
from rinbot.base.interface import ButtonChoice, RockPaperScissorsView
from rinbot.base.helpers import translate, load_lang
from rinbot.base.responder import respond
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.petpet.petpet import make_petpet

# Load text
text = load_lang()

# Fun command cog
class Fun(Cog, name="fun"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    # PatPat :3
    @app_commands.command(
        name=text['FUN_PET_NAME'],
        description=text['FUN_PET_DESC'])
    @not_blacklisted()
    async def _pet_pet(self, interaction:Interaction, member:discord.Member) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        try:
            image = await member.avatar.read()
        except AttributeError:
            image = await member.default_avatar.read()
        await interaction.response.defer()
        source = io.BytesIO(image)
        dest = io.BytesIO()
        make_petpet(source, dest)
        dest.seek(0)
        await interaction.followup.send(f"{interaction.user.mention} {text['FUN_PET_PETTED']} {member.mention}"
                                        if not interaction.user.id == member.id else
                                        f"{interaction.user.mention} {text['FUN_PET_SCHITZO']}",
                                        file=discord.File(dest, filename=f'{image[0]}-petpet.gif'))
    
    # Shows a random cat
    @app_commands.command(
        name=text['FUN_CAT_NAME'],
        description=text['FUN_CAT_DESC'])
    @not_blacklisted()
    async def _cat(self, interaction:Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    return await respond(interaction, RED, text['FUN_CAT_SAD_MEOW'], text['FUN_CAT_NOT_FOUND'])
                js = await resp.json()
                embed = discord.Embed(color=PURPLE)
                embed.set_image(url=js[0]["url"])
                await respond(interaction, message=embed)
    
    # Shows a random dog
    @app_commands.command(
        name=text['FUN_DOG_NAME'],
        description=text['FUN_DOG_DESC'])
    @not_blacklisted()
    async def _dog(self, interaction:Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.dog/woof") as resp:
                if resp.status != 200:
                    return await respond(interaction, RED, text['FUN_DOG_SAD_WOOF'], text[''])
                filename = await resp.text()
                url = f"https://random.dog/{filename}"
                filesize = interaction.guild.filesize_limit if interaction.guild else 8388608
                if filename.endswith((".mp4", ".webm")):
                    async with interaction.channel.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                return await respond(interaction, RED, text['FUN_DOG_SAD_WOOF'], text['FUN_DOG_NOT_FOUND'])
                            if int(other.headers["Content-Length"]) >= filesize:
                                await self._dog(interaction)
                            fp = io.BytesIO(await other.read())
                            await interaction.response.send_message(file=discord.File(fp, filename=filename))
                else:
                    embed = discord.Embed(color=RED)
                    embed.set_image(url=url)
                    await interaction.response.send_message(embed=embed)
    
    # Receives, translates (optional) and shows a random fact from "uselessfacts"
    @app_commands.command(
        name=text['FUN_FACT_NAME'],
        description=text['FUN_FACT_DESC'])
    @app_commands.describe(language=text['FUN_FACT_LANGUAGE_DESC'])
    @not_blacklisted()
    async def _randomfact(self, interaction:Interaction, language:str="en") -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    text = data["text"]
                    if not language == "en":
                        text = translate(data["text"], to_lang=language)
                        if not text:
                            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
                    embed = discord.Embed(description=text, color=GREEN)
                else:
                    embed = discord.Embed(
                        title=text['ERROR'],
                        description=text['FUN_FACT_API_ERROR'],
                        color=RED)
                await respond(interaction, message=embed, response_type=1)
    
    # Heads or tails, very self explanatory
    @app_commands.command(
        name=text['FUN_HOT_NAME'],
        description=text['FUN_HOT_DESC'])
    @not_blacklisted()
    async def _heads_or_tails(self, interaction:Interaction) -> None:
        buttons = ButtonChoice()
        embed = discord.Embed(description=text['FUN_HOT_EMBED_DESC'], color=GREEN)
        await interaction.response.send_message(embed=embed, view=buttons)
        await buttons.wait()
        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_WON'][0]} `{buttons.value}` {text['FUN_HOT_WON'][1]} `{result}`.",
                color=GREEN,)
        else:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_LOST'][0]} `{buttons.value}` {text['FUN_HOT_LOST'][1]} `{result}`.",
                color=RED,)
        await interaction.edit_original_response(embed=embed, view=None, content=None)
    
    # RPS = RockPaperScissors
    @app_commands.command(
        name=text['FUN_RPS_NAME'],
        description=text['FUN_RPS_DESC'])
    @not_blacklisted()
    async def _rps(self, interaction:Interaction) -> None:
        await interaction.response.send_message(text['FUN_RPS_CHOOSE'], view=RockPaperScissorsView())

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Fun(bot))