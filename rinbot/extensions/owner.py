"""
#### RinBot's owner command cog
- commands:
    * /extension load `Loads a bot extension`
    * /extension unload `Unloads a bot extension`
    * /extension reload `Reloads a bot extension`
    * /owners add `Adds a user to the owners class`
    * /owners remove `Removes a user from the owners class`
    * /shutdown `Shuts the bot down`
"""

# Imports
import discord, os, asyncio
from discord import app_commands
from discord.ext.commands import Bot, Cog
from discord.app_commands.models import Choice
from rinbot.base.db_man import *
from rinbot.base.responder import respond
from rinbot.base.helpers import load_lang, format_exception
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.base.interface import ZeroOwnersView

# Load text
text = load_lang()

# Load config
CONFIG_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../config/config-rinbot.json"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as c: config = json.load(c)
except Exception as e:
    logger.critical(f"{format_exception(e)}")
    sys.exit()

# Vals
RULE34_ON = config["RULE34_ENABLED"]
BOORU_ON = config["BOORU_ENABLED"]
ext_list = []

# "Owner" command block
class Owner(Cog, name="owner"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.selected_user = None
    
    # Command groups
    extension = app_commands.Group(name=f"{text['OWNER_EXTENSION_NAME']}", description=f"{text['OWNER_EXTENSION_DESC']}")
    owners = app_commands.Group(name=f"{text['OWNER_OWNERS_NAME']}", description=f"{text['OWNER_OWNERS_DESC']}")

    # Loads an extension
    @extension.command(
        name=f"{text['OWNER_EXTENSION_LOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_LOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_load(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        try:
            await self.bot.load_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_LOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_LOADING']} {extension.value}: `{e}`",
                color=RED)
        await respond(interaction, message=embed)
        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)
    
    # Unloads an extension
    @extension.command(
        name=f"{text['OWNER_EXTENSION_UNLOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_UNLOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_unload(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        if extension.value == "owner":
            return await respond(interaction, RED, message=text['OWNER_EXTENSION_EXT_IS_OWNER'])
        try:
            await self.bot.unload_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_UNLOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_UNLOADING']} {extension.value}: `{e}`",
                color=RED)
        await respond(interaction, message=embed)
        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)
    
    # Reloads an extension
    @extension.command(
        name=f"{text['OWNER_EXTENSION_RELOAD_NAME']}",
        description=f"{text['OWNER_EXTENSION_RELOAD_DESC']}")
    @app_commands.choices(extension=ext_list)
    @not_blacklisted()
    @is_owner()
    async def extension_reload(self, interaction:discord.Interaction, extension:Choice[str]=None) -> None:
        if not extension:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        try:
            await self.bot.reload_extension(f"rinbot.extensions.{extension.value}")
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_RELOADED']} {extension.value}",
                color=GREEN)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                description=f"{text['OWNER_EXTENSION_ERROR_RELOADING']} {extension.value}: `{e}`",
                color=RED)
        await respond(interaction, message=embed)
        await self.bot.tree.sync()
        await self.bot.tree.sync(guild=interaction.guild)
    
    # Adds a user to the owners class
    @owners.command(
        name=text['OWNER_OWNERS_ADD_NAME'],
        description=text['OWNER_OWNERS_ADD_DESC'])
    @not_blacklisted()
    @is_owner()
    async def _owners_add(self, interaction:Interaction, member:discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        owners = await get_table("owners")
        if str(member.id) not in owners:
            owners.append(str(member.id))
        else:
            return await respond(interaction, RED, message=text['OWNER_OWNERS_ALREADY_OWNER'])
        await update_table("owners", owners)
        await respond(interaction, GREEN, message=f"{text['OWNER_OWNERS_USER_ADDED']} {member.name}")
    
    # Removes a user from the owners class
    @owners.command(
        name=text['OWNER_OWNERS_REM_NAME'],
        description=text['OWNER_OWNERS_REM_DESC'])
    @not_blacklisted()
    @is_owner()
    async def _owners_remove(self, interaction:Interaction, member:discord.Member=None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        owners = await get_table("owners")
        if not str(member.id) in owners:
            return await respond(interaction, RED, message=f"{member.name} {text['OWNER_OWNERS_NOT_OWNER']}")
        owners.remove(str(member.id))
        await interaction.response.defer()
        await update_table("owners", owners)
        await respond(interaction, GREEN, message=f"{member.name} {text['OWNER_OWNERS_REMOVED']}", response_type=1)
    
        # If no owners are left
        if len(owners) < 1 or not owners:
            # Grab member names and IDs
            members = [m for m in interaction.guild.members if not m.bot]
            unames = [m.global_name for m in members]
            uids = [str(m.id) for m in members]
            
            # Run view and wair for response
            view = ZeroOwnersView(unames, self, interaction.user.id)
            msg = await interaction.channel.send(text['OWNER_OWNERS_EMPTY_WARNING'], view=view)
            while not self.selected_user:
                await asyncio.sleep(0.5)
            view.stop()
            await msg.delete()
        
            # Grab ID of selected user
            if str(self.selected_user) in unames:
                id = uids[int(unames.index(str(self.selected_user)))]
            
            # Add user to owners
            owners.append(str(id))
            await update_table("owners", owners)
            await respond(interaction, color=GREEN, message=f"{text['OWNER_OWNERS_USER_ADDED']} {self.selected_user}", response_type=1)
            self.selected_user = None
    
    # Shuts the bot down (better than killing the script)
    @app_commands.command(
        name=text['OWNER_SHUTDOWN_NAME'],
        description=text['OWNER_SHUTDOWN_DESC'])
    @not_blacklisted()
    @is_owner()
    async def _shutdown(self, interaction:Interaction) -> None:
        await respond(interaction, YELLOW, text['OWNER_SHUTDOWN_EMBED_DESC'])
        await self.bot.close()

# SETUP
async def setup(bot:Bot):
    ai_ext = ["imagecaption", "languagemodel", "message_handler", "stablediffusion"]
    booru_ext = ["booru"]
    e621_ext = ["e621"]
    rule34_ext = ["rule34"]
    sum = ai_ext + booru_ext + e621_ext + rule34_ext
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/"):
        if file.endswith(".py"):
            extension = file[:-3]
            """ if AI_ENABLED and extension in ai_ext:
                extensions_list.append(Choice(name=extension, value=extension)) """
            if BOORU_ON and extension in booru_ext:
                ext_list.append(Choice(name=extension, value=extension))
            elif RULE34_ON and extension in rule34_ext:
                ext_list.append(Choice(name=extension, value=extension))
            is_general = all(extension not in sl for sl in sum)
            if is_general:
                ext_list.append(Choice(name=extension, value=extension))
    await bot.add_cog(Owner(bot))