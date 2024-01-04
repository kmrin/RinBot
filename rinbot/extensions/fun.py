# Imports
import random, aiohttp, discord, io
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Bot
from rinbot.base.interface import ButtonChoice, RockPaperScissorsView
from rinbot.base.helpers import translate_to, load_lang
from rinbot.base.responder import Responder
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.petpet.petpet import make_petpet

# Load verbose
text = load_lang()

# Fun command cog
class Fun(commands.Cog, name="fun"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.responder = Responder(self.bot)
    
    # PatPat :3
    @commands.hybrid_command(
        name=f"{text['FUN_PET_NAME']}",
        description=f"{text['FUN_PET_DESC']}")
    @not_blacklisted()
    async def pet_pet(self, ctx:Context, user:discord.User=None) -> None:
        await ctx.defer()
        if not user:
            embed = discord.Embed(
                title=f"{text['FUN_PET_SAD_PET']}",
                description=f"{text['FUN_PET_NO_USER']}",
                color=0xd91313)
            return await ctx.send(embed=embed)
        try:
            image = await user.avatar.read()
        except AttributeError:
            image = await user.default_avatar.read()
        source = io.BytesIO(image)
        dest = io.BytesIO()
        make_petpet(source, dest)
        dest.seek(0)
        await ctx.send(
            f"{ctx.author.mention} {text['FUN_PET_PETTED']} {user.mention}"
            if not ctx.author.id == user.id else
            f"{ctx.author.mention} {text['FUN_PET_SCHITZO']}", 
            file=discord.File(dest, filename=f'"{image[0]}-petpet.gif'))
    
    # Shows a random cat
    @commands.hybrid_command(
        name=f"{text['FUN_CAT_NAME']}",
        description=f"{text['FUN_CAT_DESC']}")
    @not_blacklisted()
    async def cat(self, ctx:Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title=f"{text['FUN_CAT_SAD_MEOW']}",
                        description=f"{text['FUN_CAT_NOT_FOUND']}",
                        color=0xd91313)
                    return await ctx.send(embed=embed)
                js = await resp.json()
                embed = discord.Embed(color=0xe3a01b)
                embed.set_image(url=js[0]['url'])
                await ctx.send(embed=embed)
    
    # Shows a random dog
    @commands.hybrid_command(
        name=f"{text['FUN_DOG_NAME']}",
        description=f"{text['FUN_DOG_DESC']}")
    @not_blacklisted()
    async def dog(self, ctx:Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.dog/woof") as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title=f"{text['FUN_DOG_SAD_WOOF']}",
                        description=f"{text['FUN_DOG_NOT_FOUND']}",
                        color=0xd91313)
                    return await ctx.send(embed=embed)
                filename = await resp.text()
                url = f'https://random.dog/{filename}'
                filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
                if filename.endswith(('.mp4', '.webm')):
                    async with ctx.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                embed = discord.Embed(
                                    title=f"{text['FUN_DOG_SAD_WOOF']}",
                                    description=f"{text['FUN_DOG_NOT_FOUND']}",
                                    color=0xd91313)
                                return await ctx.send(embed=embed)
                            if int(other.headers['Content-Length']) >= filesize:
                                await self.dog(ctx)
                            fp = io.BytesIO(await other.read())
                            await ctx.send(file=discord.File(fp, filename=filename))
                else:
                    embed = discord.Embed(color=0xe3a01b)
                    embed.set_image(url=url)
                    await ctx.send(embed=embed)
    
    # Receives, translates, and shows a random fact from 'uselessfacts'
    @commands.hybrid_command(
        name=f"{text['FUN_FACT_NAME']}",
        description=f"{text['FUN_FACT_DESC']}")
    @app_commands.describe(language=f"{text['FUN_FACT_LANGUAGE_DESC']}")
    @not_blacklisted()
    async def randomfact(self, ctx: Context, language='en') -> None:
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    text = data["text"]
                    if not language == 'en':
                        text = translate_to(data["text"], from_lang='en', to_lang=language)
                    embed = discord.Embed(description=text, color=0xD75BF4)
                else:
                    embed = discord.Embed(
                        title=f"{text['ERROR']}",
                        description=f"{text['FUN_FACT_API_ERROR']}",
                        color=0xE02B2B)
                await ctx.send(embed=embed)
    
    # Heads or tails, very self explanatory
    @commands.hybrid_command(
        name=f"{text['FUN_HOT_NAME']}",
        description=f"{text['FUN_HOT_DESC']}")
    @not_blacklisted()
    async def heads_or_tails(self, ctx: Context) -> None:
        buttons = ButtonChoice()
        embed = discord.Embed(description=f"{text['FUN_HOT_EMBED_DESC']}", color=0x9C84EF)
        message = await ctx.send(embed=embed, view=buttons)
        await buttons.wait()
        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_WON'][0]} `{buttons.value}` {text['FUN_HOT_WON'][1]} `{result}`.",
                color=0x9C84EF,)
        else:
            embed = discord.Embed(
                description=f"{text['FUN_HOT_LOST'][0]} `{buttons.value}` {text['FUN_HOT_LOST'][1]} `{result}`.",
                color=0xE02B2B,)
        await message.edit(embed=embed, view=None, content=None)
    
    # RPS = RockPaperScissors (in case you haven't figured it out)
    @commands.hybrid_command(
        name=f"{text['FUN_RPS_NAME']}",
        description=f"{text['FUN_RPS_DESC']}")
    @not_blacklisted()
    async def rps(self, ctx: Context) -> None:
        view = RockPaperScissorsView()
        await ctx.send(f"{text['FUN_RPS_CHOOSE']}", view=view)

# SETUP
async def setup(bot):
    await bot.add_cog(Fun(bot))