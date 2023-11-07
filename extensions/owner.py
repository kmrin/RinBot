"""
RinBot v1.8.0 (GitHub release)
made by rin
"""

# Imports
import discord, subprocess, os
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.checks import *

extensions_list = []

# 'Owner' command block
class Owner(commands.Cog, name='owner'):
    def __init__(self, bot):
        self.bot = bot
    
    # Manipulates bot extensions
    @commands.hybrid_command(
        name='extension',
        description='Manipulates bot extensions')
    @app_commands.describe(action='The action to be taken')
    @app_commands.describe(extension='The extension about to be manipulates')
    @app_commands.choices(
        action=[
            Choice(name='load', value=0),
            Choice(name='unload', value=1),
            Choice(name='reload', value=2)])
    @app_commands.choices(
        extension=extensions_list)
    @not_blacklisted()
    @is_owner()
    async def extension(self, ctx: Context, action: Choice[int], extension: Choice[str] = None) -> None:
        # Loads extensions
        if action.value == 0 and extension is not None:
            try:
                await self.bot.load_extension(f"extensions.{extension.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Could not load `{extension.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"extension `{extension.value}` loaded.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Unloads extensions
        elif action.value == 1 and extension is not None:
            if extension.value == 'owner':
                embed = discord.Embed(
                    description="The `owner` cannot be unloaded, reload it instead.",
                    color=0xE02B2B)
                ctx.send(embed=embed)
                return
            try:
                await self.bot.unload_extension(f"extensions.{extension.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Could not unload `{extension.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"extension `{extension.value}` unloaded.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Reloads extensions
        elif action.value == 2 and extension is not None:
            try:
                await self.bot.reload_extension(f"extensions.{extension.value}")
            except Exception:
                embed = discord.Embed(
                    description=f"Não consegui recarregar a extension `{extension.value}`.",
                    color=0xE02B2B)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(
                description=f"extension `{extension.value}` reloaded.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Invalid action / extension
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid action or extension name",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Resets the bot starting a new instance and killing this one
    @commands.hybrid_command(
        name='reset',
        description='Resets RinBot')
    @not_blacklisted()
    @is_owner()
    async def reset(self, ctx: Context) -> None:
        embed = discord.Embed(
            title='Reseting...',
            color=0xE02B2B)
        await ctx.send(embed=embed)
        rin_path = f"{os.path.realpath(os.path.dirname(__file__))}/../init.py"
        try:
            subprocess.Popen(['python', rin_path, 'reset'])
            print(f"Reseting.")
        except Exception as e:
            print(f"[ERRO] - Reset: {e}")
        await self.bot.close()
    
    # Shuts RinBot down
    @commands.hybrid_command(
        name='shutdown',
        description='Bye!')
    @not_blacklisted()
    @is_owner()
    async def shutdown(self, ctx: Context) -> None:
        embed = discord.Embed(
            description="Shutting down! ByeBye :wave:", color=0x9C84EF)
        await ctx.send(embed=embed)
        await self.bot.close()

    # Manipulates the users in the 'owners' class
    @commands.hybrid_command(
        name="owners",
        description="Manipulates the owners class")
    @app_commands.describe(action="The action to be taken")
    @app_commands.describe(user="The user to be manipulated")
    @app_commands.choices(
        action=[
            Choice(name='add', value=0),
            Choice(name='remove', value=1)])
    @not_blacklisted()
    @is_owner()
    async def owners(self, ctx: Context, action: Choice[int], user: discord.User = None) -> None:
        
        # Adds someone to the owners class
        if action.value == 0 and user is not None:
            user_id = user.id
            if await db_manager.is_owner(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is already an owner.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.add_user_to_owners(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** was successfuly added to the owners class.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Removes someone from the owners class
        elif action.value == 1 and user is not None:
            user_id = user.id
            if not await db_manager.is_owner(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is not on the owners class.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.remove_user_from_owners(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** was successfuly removed from the owners class.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Invalid action / invalid user
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid action or user.",
                color=0xE02B2B,)
            await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    # Lists current extensions
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}"):
        if file.endswith(".py"):
            extension = file[:-3]
            extensions_list.append(Choice(name=extension, value=extension))
    await bot.add_cog(Owner(bot))