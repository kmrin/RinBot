"""
RinBot's config command cog
- Commands:
    * /set welcome-channel `Sets what channel on the guild rinbot will use to greet new members`
    * /set fortnite-daily-shop-channel `Sets what channel on the guild rinbot will use to show the daily fortnite shop`
    * /set valorant-daily-shop-channel `Sets what channel on the guild rinbot will use to show the dialy valorant shop`
    * /toggle welcome-channel `Toggles the welcome channel on and off`
    * /toggle fortnite-daily-shop-channel `Toggles the fortnite daily shop channel on and off`
    * /toggle valorant-daily-shop-channel `Toggles the valorant daily shop channel on and off`
"""

import discord

from discord import Interaction, app_commands
from discord.ext.commands import Cog

from rinbot.base import respond
from rinbot.base import DBTable
from rinbot.base import DBColumns
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import text

# from rinbot.base import is_owner
from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Config(Cog, name='config'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    set = app_commands.Group(name=text['CONFIG_SET_NAME'], description=text['CONFIG_SET_DESC'])
    toggle = app_commands.Group(name=text['CONFIG_TOGGLE_NAME'], description=text['CONFIG_TOGGLE_DESC'])
    
    @set.command(
        name=text['CONFIG_SET_WELCOME_CHANNEL_NAME'],
        description=text['CONFIG_SET_WELCOME_CHANNEL_DESC'])
    @app_commands.describe(custom_message=text['CONFIG_SET_WELCOME_CHANNEL_CM'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _set_welcome(self, interaction: Interaction, channel: discord.TextChannel,
                           custom_message: str=None) -> None:
        data = {'active': 1, 'channel_id': channel.id}

        if custom_message:
            data['custom_msg'] = custom_message

        await self.bot.db.update(DBTable.WELCOME_CHANNELS, data, f'guild_id={interaction.guild.id}')
        await respond(interaction, Colour.GREEN, text['CONFIG_SET_WELCOME_CHANNEL_SET'])
    
    @set.command(
        name=text['CONFIG_SET_DAILY_SHOP_NAME'],
        description=text['CONFIG_SET_DAILY_SHOP_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _set_fortnite_daily_shop(self, interaction: Interaction, channel: discord.TextChannel) -> None:
        data = {'fortnite_active': 1, 'fortnite_channel_id': channel.id}

        await self.bot.db.update(DBTable.DAILY_SHOP_CHANNELS, data, f'guild_id={interaction.guild.id}')
        await respond(interaction, Colour.GREEN, text['CONFIG_SET_DAILY_SHOP_SET'])
    
    @set.command(
        name=text['CONFIG_SET_VAL_DAILY_SHOP_NAME'],
        description=text['CONFIG_SET_VAL_DAILY_SHOP_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _set_valorant_daily_shop(self, interaction: Interaction, channel: discord.TextChannel) -> None:
        data = {'valorant_active': 1, 'valorant_channel_id': channel.id}

        await self.bot.db.update(DBTable.DAILY_SHOP_CHANNELS, data, f'guild_id={interaction.guild.id}')
        await respond(interaction, Colour.GREEN, text['CONFIG_SET_VAL_DAILY_SHOP_SET'])
    
    @toggle.command(
        name=text['CONFIG_TOGGLE_WELCOME_CHANNEL_NAME'],
        description=text['CONFIG_TOGGLE_WELCOME_CHANNEL_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _toggle_welcome(self, interaction: Interaction) -> None:
        query = await self.bot.db.get(DBTable.WELCOME_CHANNELS, condition=f'guild_id={interaction.guild.id}')

        new_state = 1 if query[0][1] == 0 else 0

        await self.bot.db.update(DBTable.WELCOME_CHANNELS, {'active': new_state},
                                 condition=f'guild_id={interaction.guild.id}')

        await respond(
            interaction, Colour.GREEN,
            f'{text["CONFIG_TOGGLE_WELCOME_CHANNEL_TOGGLED"]} {text["ON"] if new_state == 1 else text["OFF"]}.')

    @toggle.command(
        name=text['CONFIG_TOGGLE_DAILY_CHANNEL_NAME'],
        description=text['CONFIG_TOGGLE_DAILY_CHANNEL_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _toggle_fortnite_daily(self, interaction: Interaction) -> None:
        query = await self.bot.db.get(DBTable.DAILY_SHOP_CHANNELS, condition=f'guild_id={interaction.guild.id}')

        new_state = 1 if query[0][1] == 0 else 0

        await self.bot.db.update(DBTable.DAILY_SHOP_CHANNELS, {'fortnite_active': new_state},
                                 condition=f'guild_id={interaction.guild.id}')

        await respond(interaction, Colour.GREEN,
                      f'{text["CONFIG_TOGGLE_DAILY_CHANNEL_TOGGLED"]} {text["ON"] if new_state == True else text["OFF"]}.')

    @toggle.command(
        name=text['CONFIG_TOGGLE_VAL_CHANNEL_NAME'],
        description=text['CONFIG_TOGGLE_VAL_CHANNEL_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _toggle_valid_channel(self, interaction: Interaction) -> None:
        query = await self.bot.db.get(DBTable.DAILY_SHOP_CHANNELS, condition=f'guild_id={interaction.guild.id}')

        new_state = 1 if query[0][3] == 0 else 0

        await self.bot.db.update(DBTable.DAILY_SHOP_CHANNELS, {'valorant_active': new_state},
                                 condition=f'guild_id={interaction.guild.id}')

        await respond(interaction, Colour.GREEN,
                      f'{text["CONFIG_TOGGLE_VAL_CHANNEL_TOGGLED"]} {text["ON"] if new_state == True else text["OFF"]}.')

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Config(bot))
