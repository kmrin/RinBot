# Imports
import discord, os, asyncio
from discord import app_commands
from discord.ext.commands import Bot, Cog, Context
from discord.app_commands.models import Choice
from dotenv import load_dotenv
from program.base import db_manager
from program.base.helpers import load_lang, strtobool, format_exception
from program.interface.zero_owners_select import ZeroOwnersView
from program.base.checks import *
from program.base.colors import *

# Load verbose
text = load_lang()

# Load env vars
load_dotenv()
RULE34_ENABLED = strtobool(os.getenv('RULE34_ENABLED'))
BOORU_ENABLED = strtobool(os.getenv('BOORU_ENABLED'))

# Global extensions tracking
ext_list = []

# "Owner" command block
class Owner(Cog, name="owner"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.selected_user = None
    
    extension_group = app_commands.Group(name=f"{text['OWNER_EXTENSION_NAME']}", description=f"{text['OWNER_EXTENSION_DESC']}")
    owners_group = app_commands.Group(name=f"{text['OWNER_OWNERS_NAME']}", description=f"{text['OWNER_OWNERS_DESC']}")

    # Loads an extension
    @extension_group.command(
        name=f"{text['OWNER_EXTENSION_LOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_LOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_load(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        try:
            await self.bot.load_extension(f"program.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_LOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_LOADING']} {extension.value}: `{e}`",
                color=RED)
        await interaction.response.send_message(embed=embed)
        await self.bot.tree.sync()
    
    # Unloads an extension
    @extension_group.command(
        name=f"{text['OWNER_EXTENSION_UNLOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_UNLOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_unload(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if extension.value == "owner":
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_EXT_IS_OWNER']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        try:
            await self.bot.unload_extension(f"program.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_UNLOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_UNLOADING']} {extension.value}: `{e}`",
                color=RED)
        await interaction.response.send_message(embed=embed)
        await self.bot.tree.sync()
    
    # Reloads an extension
    @extension_group.command(
        name=f"{text['OWNER_EXTENSION_RELOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_RELOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_reload(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        try:
            await self.bot.reload_extension(f"program.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_RELOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_RELOADING']} {extension.value}: `{e}`",
                color=RED)
        await interaction.response.send_message(embed=embed)
        await self.bot.tree.sync()
    
    # Adds a user to the owners class
    @owners_group.command(
        name=f"{text['OWNER_OWNERS_ADD_NAME']}",
        description=f"{text['OWNER_OWNERS_ADD_DESC']}")
    @not_blacklisted()
    @is_owner()
    async def owners_add(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.is_owner(user.id):
            embed = discord.Embed(
                description=f"{text['OWNER_OWNERS_ALREADY_OWNER']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.add_user_to_owners(user.id):
            embed = discord.Embed(
                description=f"{text['OWNER_OWNERS_USER_ADDED']} {user.name}",
                color=GREEN)
        else:
            embed = discord.Embed(
                description=f"{text['OWNER_OWNERS_ERROR_ADDING_USER']}",
                color=RED)
        await interaction.response.send_message(embed=embed)
    
    # Removes a user from the owners class
    @owners_group.command(
        name=f"{text['OWNER_OWNERS_REM_NAME']}",
        description=f"{text['OWNER_OWNERS_REM_DESC']}")
    @not_blacklisted()
    @is_owner()
    async def owners_remove(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if not await db_manager.is_owner(user.id):
            embed = discord.Embed(
                description=f"{user.name} {text['OWNER_OWNERS_NOT_OWNER']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        await db_manager.remove_user_from_owners(user.id)
        await interaction.response.defer()
        embed = discord.Embed(
            description=f"{user.name} {text['OWNER_OWNERS_REMOVED']}",
            color=GREEN)
        await interaction.followup.send(embed=embed)
        owners = await db_manager.get_owners()
        
        # If no owners are left
        if len(owners) < 1:
            # Grab member names and IDs
            members = [m for m in interaction.guild.members if not m.bot]
            unames = [m.global_name for m in members]
            uids = [str(m.id) for m in members]
            
            # Run view and wait for response
            view = ZeroOwnersView(self.bot, unames, self, interaction.user.id)
            msg = await interaction.channel.send(f"{text['OWNER_OWNERS_EMPTY_WARNING']}",
                                           view=view)
            while not self.selected_user:
                await asyncio.sleep(0.5)
            view.stop()
            await msg.delete()
            
            # Grab ID of selected user
            if str(self.selected_user) in unames:
                id = uids[int(unames.index(str(self.selected_user)))]
            
            # Add user to owners, add to admin as well if not present
            if not await db_manager.is_admin(int(id)):
                await db_manager.add_user_to_admins(int(id))
            if await db_manager.add_user_to_owners(int(id)):
                embed = discord.Embed(
                    description=f"{text['OWNER_OWNERS_USER_ADDED']} {self.selected_user}",
                    color=0x9C84EF)
            else:
                embed = discord.Embed(
                    description=f"{text['OWNER_OWNERS_ERROR_ADDING_USER']}",
                    color=0x9C84EF)
            self.selected_user = None
            await interaction.channel.send(embed=embed)
    
    # Shuts the bot down (better than killing the script)
    @commands.hybrid_command(
        name=f"{text['OWNER_SHUTDOWN_NAME']}",
        description=f"{text['OWNER_SHUTDOWN_DESC']}")
    @not_blacklisted()
    @is_owner()
    async def shutdown(self, ctx:Context) -> None:
        embed = discord.Embed(
            description=f"{text['OWNER_SHUTDOWN_EMBED_DESC']}", color=YELLOW)
        await ctx.send(embed=embed)
        await self.bot.close()

# SETUP
async def setup(bot:Bot):
    ai_ext = ["imagecaption", "languagemodel", "message_handler", "stablediffusion"]
    booru_ext = ["danbooru"]
    e621_ext = ["e621"]
    rule34_ext = ["rule34"]
    sum = ai_ext + booru_ext + e621_ext + rule34_ext
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/../../program/extensions"):
        if file.endswith(".py"):
            extension = file[:-3]
            """ if AI_ENABLED and extension in ai_ext:
                extensions_list.append(Choice(name=extension, value=extension)) """
            if BOORU_ENABLED and extension in booru_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif RULE34_ENABLED and extension in rule34_ext:
                ext_list.append(Choice(name=extension, value=extension))
            is_general = all(extension not in sl for sl in sum)
            if is_general:
                ext_list.append(Choice(name=extension, value=extension))
    await bot.add_cog(Owner(bot))