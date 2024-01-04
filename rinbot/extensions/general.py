# Imports
import platform, discord, os
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context
from rinbot.base.interface import PageSwitcher
from rinbot.base.responder import Responder
from rinbot.base.helpers import load_lang, translate_to, get_specs, remove_nl
from rinbot.base.checks import *
from rinbot.base.colors import *
from dotenv import load_dotenv

# Load env vars
load_dotenv()
LANG = os.getenv("DISCORD_BOT_LANGUAGE")

# Load verbose
text = load_lang()

# General command cog
class General(Cog, name="general"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.responder = Responder(self.bot)
    
    # Help command
    @commands.hybrid_command(
        name=f"{text['GENERAL_HELP_NAME']}",
        description=f"{text['GENERAL_HELP_DESC']}")
    @not_blacklisted()
    async def help(self, ctx:Context) -> None:
        try:
            with open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/text/help-{LANG}.md", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            return await self.responder.respond(ctx, RED, f"{text['ERROR_FILE_NOT_FOUND']}")
        lines = "\n".join(remove_nl(lines)).split("\n")
        chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
        embed = discord.Embed(title=f"{text['GENERAL_HELP_TITLE']}", color=YELLOW)
        embed.description="\n".join(chunks[0])
        view = PageSwitcher(self.bot, embed, chunks)
        await self.responder.respond(context=ctx, message=embed, view=view)
    
    # Translates text
    @commands.hybrid_command(
        name=f"{text['GENERAL_TRANSLATE_NAME']}",
        description=f"{text['GENERAL_TRANSLATE_DESC']}")
    @app_commands.describe(text=f"{text['GENERAL_TRANSLATE_TEXT']}")
    @app_commands.describe(to_lang=f"{text['GENERAL_TRANSLATE_TO_LANG']}")
    @not_blacklisted()
    async def translate(self, ctx:Context, text:str=None, to_lang:str="pt-br") -> None:
        lang = load_lang()
        if not text:
            return await self.responder.respond(ctx, color=RED, message=f"{lang['ERROR_INVALID_PARAMETERS']}")
        await ctx.defer()
        text = translate_to(text, to_lang)
        await self.responder.respond(ctx, YELLOW, text)
    
    # Shows an embed with the technical specifications of the system running the bot
    @commands.hybrid_command(
        name=f"{text['GENERAL_SPECS_NAME']}",
        description=f"{text['GENERAL_SPECS_DESC']}")
    @not_blacklisted()
    async def specs(self, ctx:Context) -> None:
        await ctx.defer()
        specs = await get_specs()
        embed = discord.Embed(title=f"{text['GENERAL_SPECS_TITLE']}", color=BLUE)
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)
        embed.add_field(name=f"{text['GENERAL_SPECS_SYSTEM']}", value=specs['os'], inline=False)
        embed.add_field(name="CPU", value=specs['cpu'], inline=False)
        embed.add_field(name="RAM", value=specs['ram'], inline=False)
        embed.add_field(name="GPU", value=specs['gpu'], inline=False)
        try:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {ctx.author.global_name}", icon_url=ctx.author.avatar.url)
        except AttributeError:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {ctx.author.global_name}", icon_url=ctx.author.default_avatar.url)
        await self.responder.respond(ctx, message=embed)
    
    # Shows info about the bot
    @commands.hybrid_command(
        name=f"{text['GENERAL_RININFO_NAME']}",
        description=f"{text['GENERAL_RININFO_DESC']}")
    @not_blacklisted()
    async def rininfo(self, ctx:Context) -> None:
        embed = discord.Embed(
            title=f"{text['GENERAL_RININFO_EMBED_TITLE']}",
            color=YELLOW)
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)
        embed.add_field(name=f"{text['GENERAL_RININFO_CREATED_IN'][0]}", value=f"{text['GENERAL_RININFO_CREATED_IN'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_VERSION'][0]}", value=f"{text['GENERAL_RININFO_VERSION'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_PROGRAMMER'][0]}", value=f"{text['GENERAL_RININFO_PROGRAMMER'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_BUGFINDER'][0]}", value=f"{text['GENERAL_RININFO_BUGFINDER'][1]}", inline=True)
        embed.add_field(name=f"{text['GENERAL_RININFO_PY_VER'][0]}", value=f"{platform.python_version()}", inline=True)
        try:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {ctx.author}", icon_url=f"{ctx.author.avatar.url}")
        except AttributeError:
            embed.set_footer(text=f"{text['GENERAL_REQUESTED_BY']} {ctx.author}", icon_url=f"{ctx.author.default_avatar.url}")
        await self.responder.respond(ctx, message=embed)
    
    # Ping-Pong
    @commands.hybrid_command(
        name=f"{text['GENERAL_PING_NAME']}",
        description=f"{text['GENERAL_PING_DESC']}")
    @not_blacklisted()
    async def ping(self, ctx:Context) -> None:
        await self.responder.respond(ctx, color=YELLOW, title="🏓 Pong!", message=f"{text['GENERAL_PING_EMBED_DESC']} {round(self.bot.latency * 1000)}ms.")
        
# SETUP
async def setup(bot:Bot):
    await bot.add_cog(General(bot))