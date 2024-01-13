"""
#### RinBot's config command cog
- commands:
    * /set welcome-channel `Sets what channel on the guild rinbot will use to greet new members`
    * /set fortnite-daily-shop-channel `Sets what channel on the guild rinbot will use to show the daily fortnite daily shop`
    * /toggle welcome-channel `Toggles the welcome channel on and off`
    * /toggle fortnite-daily-shop-channel `Toggles the fortnite daily shop channel on and off`
"""

# Imports
import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog
from rinbot.base.helpers import load_lang
from rinbot.base.responder import respond
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.base.db_man import *

# Load text
text = load_lang()

# "Config" command cog
class Config(Cog, name="config"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    # Command groups
    set = app_commands.Group(name=f"{text['CONFIG_SET_NAME']}", description=f"{text['CONFIG_SET_DESC']}")
    toggle = app_commands.Group(name=f"{text['CONFIG_TOGGLE_NAME']}", description=f"{text['CONFIG_TOGGLE_DESC']}")

    # Set the welcome channel for the guild
    @set.command(
        name=text['CONFIG_SET_WELCOME_CHANNEL_NAME'],
        description=text['CONFIG_SET_WELCOME_CHANNEL_DESC'])
    @app_commands.describe(custom_message=text['CONFIG_SET_WELCOME_CHANNEL_CM'])
    @not_blacklisted()
    @is_admin()
    async def _set_welcome(self, interaction:Interaction, channel:discord.TextChannel=None, custom_message:str=None) -> None:
        if not channel:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        welcome_channels = await get_table("welcome_channels")
        welcome_channels[str(interaction.guild.id)] = {"active": True, "channel_id": str(channel.id), "custom_message": False}
        if custom_message:
            if len(custom_message) >= 255:
                return await respond(interaction, RED, message=text['CONFIG_SET_WELCOME_CHANNEL_MAX_CHAR'])
            welcome_channels[str(interaction.guild.id)]["custom_message"] = custom_message
        await update_table("welcome_channels", welcome_channels)
        await respond(interaction, GREEN, message=text['CONFIG_SET_WELCOME_CHANNEL_SET'])
    
    # Set the fortnite daily shop channel for the guild
    @set.command(
        name=text['CONFIG_SET_DAILY_SHOP_NAME'],
        description=text['CONFIG_SET_DAILY_SHOP_DESC'])
    @not_blacklisted()
    @is_admin()
    async def _set_welcome(self, interaction:Interaction, channel:discord.TextChannel=None) -> None:
        if not channel:
            return await respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        daily_shop_channels = await get_table("daily_shop_channels")
        daily_shop_channels[str(interaction.guild.id)] = {"active": True, "channel_id": str(channel.id)}
        await update_table("daily_shop_channels", daily_shop_channels)
        await respond(interaction, GREEN, message=text['CONFIG_SET_DAILY_SHOP_SET'])
    
    # Toggles the welcome channel on and off
    @toggle.command(
        name=text['CONFIG_TOGGLE_WELCOME_CHANNEL_NAME'],
        description=text['CONFIG_TOGGLE_WELCOME_CHANNEL_DESC'])
    @not_blacklisted()
    @is_admin()
    async def _toggle_welcome(self, interaction:Interaction) -> None:
        welcome_channels = await get_table("welcome_channels")
        if not str(interaction.guild.id) in welcome_channels.keys():
            return await respond(interaction, RED, message=text['CONFIG_TOGGLE_WELCOME_CHANNEL_NOT_SET'])
        new_active_state = True if welcome_channels[str(interaction.guild.id)]["active"] == True else False
        welcome_channels[str(interaction.guild.id)]["active"] = new_active_state
        await update_table("welcome_channels", welcome_channels)
        await respond(interaction, GREEN, message=f"{text['CONFIG_TOGGLE_WELCOME_CHANNEL_TOGGLED']} {text['ON'] if new_active_state == True else text['OFF']}.")
    
    # Toggles the daily shop channel on and off
    @toggle.command(
        name=text['CONFIG_TOGGLE_DAILY_CHANNEL_NAME'],
        description=text['CONFIG_TOGGLE_DAILY_CHANNEL_DESC'])
    @not_blacklisted()
    @is_admin()
    async def _toggle_daily(self, interaction:Interaction) -> None:
        daily_channels = await get_table("daily_shop_channels")
        if not str(interaction.guild.id) in daily_channels.keys():
            return await respond(interaction, RED, message=text['CONFIG_TOGGLE_DAILY_CHANNEL_NOT)SET'])
        new_active_state = not daily_channels[str(interaction.guild.id)]["active"]
        daily_channels[str(interaction.guild.id)]["active"] = new_active_state
        await update_table("daily_shop_channels", daily_channels)
        await respond(interaction, GREEN, message=f"{text['CONFIG_TOGGLE_DAILY_CHANNEL_TOGGLED']} {text['ON'] if new_active_state == True else {text['OFF']}}.")

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Config(bot))