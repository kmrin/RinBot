# Imports
import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog
from rinbot.base.responder import Responder
from rinbot.base.helpers import load_lang
from rinbot.base.checks import *
from rinbot.base.colors import *

# Load verbose
text = load_lang()

# Config command cog
class Config(Cog, name="config"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.responder = Responder(self.bot)
    
    # Command groups
    set_group = app_commands.Group(name=f"{text['CONFIG_SET_NAME']}", description=f"{text['CONFIG_SET_DESC']}")
    toggle_group = app_commands.Group(name=f"{text['CONFIG_TOGGLE_NAME']}", description=f"{text['CONFIG_TOGGLE_DESC']}")
    
    # Set the welcome channel for the guild
    @set_group.command(
        name=f"{text['CONFIG_SET_WELCOME_CHANNEL_NAME']}",
        description=f"{text['CONFIG_SET_WELCOME_CHANNEL_DESC']}")
    @app_commands.describe(custom_message=f"{text['CONFIG_SET_WELCOME_CHANNEL_CM']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def set_welcome(self, interaction:discord.Interaction, channel:discord.TextChannel=None, custom_message:str=None) -> None:
        if not channel or not custom_message:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if len(custom_message) >= 255:
            return await self.responder.respond(interaction, RED, text['CONFIG_SET_WELCOME_CHANNEL_MAX_CHAR'])            
        current = await db_manager.get_welcome_channel(interaction.guild.id)
        if not current:
            add = await db_manager.add_welcome_channel(channel.id, interaction.guild.id, custom_message)
            if add: await self.responder.respond(interaction, GREEN, text['CONFIG_SET_WELCOME_CHANNEL_SET'])
            else: await self.responder.respond(interaction, RED, text['CONFIG_SET_WELCOME_CHANNEL_NOT_SET'])
        else:
            await db_manager.update_welcome_channel(channel.id, interaction.guild.id)
            await self.responder.respond(interaction, GREEN, text['CONFIG_SET_WELCOME_CHANNEL_SET'])

    # Set the daily fortnite shop channel for the guild
    @set_group.command(
        name=f"{text['CONFIG_SET_DAILY_SHOP_NAME']}",
        description=f"{text['CONFIG_SET_DAILY_SHOP_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def set_daily(self, interaction:discord.Interaction, channel:discord.TextChannel=None) -> None:
        if not channel:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        current = await db_manager.get_daily_shop_channel(interaction.guild.id)
        if not current:
            add = await db_manager.add_daily_shop_channel(channel.id, interaction.guild.id)
            if add: await self.responder.respond(interaction, GREEN, text['CONFIG_SET_DAILY_SHOP_SET'])
            else: await self.responder.respond(interaction, RED, text['CONFIG_SET_DAILY_SHOP_NOT_SET'])
        else:
            await db_manager.update_daily_shop_channel(channel.id, interaction.guild.id)
            await self.responder.respond(interaction, GREEN, text['CONFIG_SET_DAILY_SHOP_SET'])
    
    # Toggles the welcome channel on and off
    @toggle_group.command(
        name=f"{text['CONFIG_TOGGLE_WELCOME_CHANNEL_NAME']}",
        description=f"{text['CONFIG_TOGGLE_WELCOME_CHANNEL_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def toggle_welcome(self, interaction:discord.Interaction) -> None:
        toggle = await db_manager.toggle_welcome_channel(interaction.guild.id)
        await self.responder.respond(
            interaction, GREEN, 
            f"{text['CONFIG_TOGGLE_WELCOME_CHANNEL_TOGGLED']} {text['ON'] if toggle == 1 else text['OFF']}.")
    
    # Toggles the daily shop channel on and off
    @toggle_group.command(
        name=f"{text['CONFIG_TOGGLE_DAILY_CHANNEL_NAME']}",
        description=f"{text['CONFIG_TOGGLE_DAILY_CHANNEL_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def toggle_daily(self, interaction:discord.Interaction) -> None:
        toggle = await db_manager.toggle_daily_shop_channel(interaction.guild.id)
        await self.responder.respond(
            interaction, GREEN, 
            f"{text['CONFIG_TOGGLE_DAILY_CHANNEL_TOGGLED']} {text['ON'] if toggle == 1 else text['OFF']}.")

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Config(bot))