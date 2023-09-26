"""
RinBot v1.4.3
feita por rin
"""

# Imports
import platform, discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from program.translator import translate_to
from program.checks import *

# Bloco de comandos 'general'
class General(commands.Cog, name='general'):
    def __init__(self, bot):
        self.bot = bot
    
    # Traduz uma string de uma lingua pra outra
    @commands.hybrid_command(
        name='traduzir',
        description='Traduz algo pra outra língua (por padrão traduz EN > PT-BR)',)
    @app_commands.describe(texto='O texto a ser traduzido')
    @app_commands.describe(de='A linguagem de entrada (EN por padrão)')
    @app_commands.describe(para='A língua de saída (PT-BR por padrão)')
    @not_blacklisted()
    async def translate_string(self, ctx: Context, texto: str = None, de: str = 'en', para: str = 'pt-br') -> None:
        await ctx.defer()
        text = translate_to(texto, de, para)
        embed = discord.Embed(
            description=f'{text}', 
            color=0xe3a01b)
        await ctx.send(embed=embed)
    
    # Mostra informações sobre a bot através de um Embed
    @commands.hybrid_command(
        name='inforin',
        description='Mostra informações sobre mim')
    @not_blacklisted()
    async def rininfo(self, ctx: Context) -> None:
        embed = discord.Embed(
            title='Info. da RinBot',
            color=0xe3a01b)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name='Criada em:', value='10/08/23', inline=True)
        embed.add_field(name='Versão:', value='1.4.3', inline=True)
        embed.add_field(name='Programadora:', value='km.rin :flag_br:', inline=True)
        embed.add_field(name='Ver. do Python:', value=f"{platform.python_version()}", inline=True)
        embed.set_footer(text=f"Requisitado por: {ctx.author}", icon_url=f'{ctx.author.avatar.url}')
        await ctx.send(embed=embed)
    
    # Mostra informações do servidor em que a bot está através de um Embed
    @commands.hybrid_command(
        name='infoservidor',
        description='Mostra informações sobre o servidor')
    @not_blacklisted()
    async def serverinfo(self, ctx: Context) -> None:
        roles = [role.name for role in ctx.guild.roles]
        if len(roles) > 50:
            roles = roles[:50]
            roles.append(f" >>>> Mostrando [50/{len(roles)}] cargos.")
        roles = ", ".join(roles)
        embed = discord.Embed(
            title="**Nome do servidor:**", description=f"{ctx.guild}", color=0x9C84EF)
        if ctx.guild.icon is not None:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(name="ID", value=ctx.guild.id)
        embed.add_field(name="N. de membros", value=ctx.guild.member_count)
        embed.add_field(
            name="Canais de Texto/Voz", value=f"{len(ctx.guild.channels)}"
        )
        embed.add_field(name=f"Cargos ({len(ctx.guild.roles)})", value=roles)
        embed.set_footer(text=f"Criado em: {ctx.guild.created_at.strftime('%d/%m/%Y')}")
        await ctx.send(embed=embed)
    
    # Ping-Pong (não, não é o jogo)
    @commands.hybrid_command(
        name="ping",
        description="Verifica se eu to viva.",)
    @not_blacklisted()
    async def ping(self, ctx: Context) -> None:
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latência: {round(self.bot.latency * 1000)}ms.",
            color=0x9C84EF,)
        await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(General(bot))