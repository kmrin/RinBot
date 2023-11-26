# Imports
import platform, discord
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord import app_commands
from program.helpers import translate_to, get_specs
from program.checks import *

# 'general' command block
class General(commands.Cog, name='general'):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    # Shows an embed with the technical specifications of the system running the bot
    @commands.hybrid_command(
        name='specs',
        description='Shows the specs. of the system running the bot')
    @not_blacklisted()
    async def specs(self, ctx:Context) -> None:
        await ctx.defer()
        specs = await get_specs()
        embed = discord.Embed(title=' :desktop:  System Specs', color=discord.Color.blue())
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)
        embed.add_field(name="System", value=specs['os'], inline=False)
        embed.add_field(name="CPU", value=specs['cpu'], inline=False)
        embed.add_field(name="RAM", value=specs['ram'], inline=False)
        embed.add_field(name="GPU", value=specs['gpu'], inline=False)
        try:
            embed.set_footer(text=f"Requested by: {ctx.author.global_name}", icon_url=ctx.author.avatar.url)
        except AttributeError:
            embed.set_footer(text=f"Requested by: {ctx.author.global_name}", icon_url=ctx.author.default_avatar.url)
        await ctx.send(embed=embed)
    
    # Translates a string from one language to another
    @commands.hybrid_command(
        name='translate',
        description='Translates something (EN -> PT-BR by default)',)
    @app_commands.describe(text='The text to be translated')
    @app_commands.describe(from_lang='The input language (EN by default)')
    @app_commands.describe(to_lang='The output language (PT-BR by default)')
    @not_blacklisted()
    async def translate_string(self, ctx: Context, text: str = None, from_lang: str = 'en', to_lang: str = 'pt-br') -> None:
        await ctx.defer()
        text = translate_to(text, from_lang, to_lang)
        embed = discord.Embed(
            description=f'{text}', 
            color=0xe3a01b)
        await ctx.send(embed=embed)
    
    # Show info about the bot in a embed
    @commands.hybrid_command(
        name='rininfo',
        description='Shows info about me UwU')
    @not_blacklisted()
    async def rininfo(self, ctx: Context) -> None:
        embed = discord.Embed(
            title=' 🍊  RinBot Info',
            color=0xe3a01b)
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            pass
        embed.add_field(name='Created in:', value='10/08/23', inline=True)
        embed.add_field(name='Version:', value='1.9.1-GitHub', inline=True)
        embed.add_field(name='Programmer:', value='km.rin :flag_br:', inline=True)
        embed.add_field(name='Collaborator:', value='Nyarkll :flag_br:', inline=True)
        embed.add_field(name='Python Version:', value=f"{platform.python_version()}", inline=True)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=f'{ctx.author.avatar.url}')
        await ctx.send(embed=embed)
    
    # Shows info about the server the bot is in through an embed
    @commands.hybrid_command(
        name='serverinfo',
        description='Shows info about the current server')
    @not_blacklisted()
    async def serverinfo(self, ctx: Context) -> None:
        roles = [role.name for role in ctx.guild.roles]
        if len(roles) > 50:
            roles = roles[:50]
            roles.append(f" >>>> Showing [50/{len(roles)}] roles.")
        roles = ", ".join(roles)
        embed = discord.Embed(
            title="**Server Name:**", description=f"{ctx.guild}", color=0x9C84EF)
        if ctx.guild.icon is not None:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(name="ID", value=ctx.guild.id)
        embed.add_field(name="Member Count", value=ctx.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(ctx.guild.channels)}")
        embed.add_field(name=f"Roles ({len(ctx.guild.roles)})", value=roles)
        embed.set_footer(text=f"Created in: {ctx.guild.created_at.strftime('%d/%m/%Y')}")
        await ctx.send(embed=embed)
    
    # Ping-Pong (no, not the game)
    @commands.hybrid_command(
        name="ping",
        description="Checks if I'm alive.",)
    @not_blacklisted()
    async def ping(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {round(self.bot.latency * 1000)}ms.",
            color=0x9C84EF,)
        await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(General(bot))
