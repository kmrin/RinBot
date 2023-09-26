"""
RinBot v1.4.3
feita por rin
"""

# Imports
import discord, subprocess, os
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.checks import *

extensions_list = []

# Bloco de comandos 'owner'
class Owner(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
    
    # Manipula as extensões da bot
    @commands.hybrid_command(
        name='extensão',
        description='Manipula as extensões individuais da RinBot')
    @app_commands.describe(ação='A ação a ser feita')
    @app_commands.describe(extensão='A extensão a ser manipulada')
    @app_commands.choices(
        ação=[
            Choice(name='carregar', value=0),
            Choice(name='descarregar', value=1),
            Choice(name='recarregar', value=2)])
    @app_commands.choices(
        extensão=extensions_list)
    @not_blacklisted()
    @is_owner()
    async def extension(self, ctx: Context, ação: Choice[int], extensão: Choice[str] = None) -> None:
        # Carrega extensões
        if ação.value == 0 and extensão is not None:
            try:
                await self.bot.load_extension(f"extensions.{extensão.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Não consegui carregar a extensão `{extensão.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"Extensão `{extensão.value}` carregada com sucesso.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Descarrega extensões
        elif ação.value == 1 and extensão is not None:
            if extensão.value == 'owner':
                embed = discord.Embed(
                    description="A extensão `owner` não pode ser desligada, invés disso, resete-a.",
                    color=0xE02B2B)
                ctx.send(embed=embed)
                return
            try:
                await self.bot.unload_extension(f"extensions.{extensão.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Não consegui descarregar a extensão `{extensão.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"Extensão `{extensão.value}` descarregada com sucesso.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Recarrega extensões
        elif ação.value == 2 and extensão is not None:
            try:
                await self.bot.reload_extension(f"extensions.{extensão.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Não consegui recarregar a extensão `{extensão.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"Extensão `{extensão.value}` recarregada com sucesso.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Ação / extensão inválida
        else:
            embed = discord.Embed(
                title="Erro",
                description=f"Ação inválida ou extensão inválida",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Reseta a bot iniciando uma outra instância e matando a atual
    @commands.hybrid_command(
        name='reset',
        description='Reseta a RinBot')
    @not_blacklisted()
    @is_owner()
    async def reset(self, ctx: Context) -> None:
        embed = discord.Embed(
            title='Resetando...',
            color=0xE02B2B)
        await ctx.send(embed=embed)
        rin_path = f"{os.path.realpath(os.path.dirname(__file__))}/../init.py"
        try:
            subprocess.Popen(['python', rin_path, 'reset'])
            print(f"Resetando.")
        except Exception as e:
            print(f"[ERRO] Reset: {e}")
        await self.bot.close()
    
    # Deliga a bot
    @commands.hybrid_command(
        name='desligar',
        description='Tchau!')
    @not_blacklisted()
    @is_owner()
    async def shutdown(self, ctx: Context) -> None:
        embed = discord.Embed(
            description="Desligando. Tchauzinho! :wave:", color=0x9C84EF)
        await ctx.send(embed=embed)
        await self.bot.close()

# SETUP
async def setup(bot):
    # Listar as extensões atuais
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}"):
        if file.endswith(".py"):
            extension = file[:-3]
            extensions_list.append(Choice(name=extension, value=extension))
    await bot.add_cog(Owner(bot))