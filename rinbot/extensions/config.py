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

    @set.command(
        name = text['CONFIG_SET_CURRENCY_EMOJI_NAME'],
        description = text['CONFIG_SET_CURRENCY_EMOJI_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _set_currency_emoji(self, interaction: Interaction, emoji: str) -> None:
        async def is_emoji(string: str) -> bool:
            """
            Checks if a string is an emoji.

            Args:
                string (str): the potential emoji

            Returns:
                bool: True or False if the string contains an emoji.
            """

            if len(string) != 1:
                return False
            
            code_point = ord(string)
            
            # Define common emoji ranges based on Unicode standards
            emoji_ranges = [
                (0x1F600, 0x1F64F),  # Emoticons
                (0x1F300, 0x1F5FF),  # Miscellaneous Symbols and Pictographs
                (0x1F680, 0x1F6FF),  # Transport and Map Symbols
                (0x1F700, 0x1F77F),  # Alchemical Symbols
                (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
                (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
                (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
                (0x1FA00, 0x1FA6F),  # Chess Symbols
                (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
                (0x2600, 0x26FF),    # Miscellaneous Symbols
                (0x2700, 0x27BF),    # Dingbats
                (0xFE00, 0xFE0F),    # Variation Selectors
                (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols
                (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
            ]

            for start, end in emoji_ranges:
                if start <= code_point <= end:
                    return True
            
            return False

        async def currency_embed(description: str) -> discord.Embed:
            """
            Creates an error embed for currency setting.

            Args:
                description (str): The database table

            Returns:
                discord.Embed: Represents a Discord embed.
            """
            embed=discord.Embed(title = text["CONFIG_SET_CURRENCY_EMOJI_ERROR_EMBED_TITLE"],
                                description = f"{description}\n/set {text['CONFIG_SET_CURRENCY_EMOJI_NAME']} emoji:{emoji}", 
                                color = Colour.YELLOW)
            
            embed.set_author(name = self.bot.user.name.upper(), 
                             icon_url = self.bot.user.avatar.url)
            
            embed.add_field(name = text["CONFIG_SET_CURRENCY_EMOJI_ERROR_FIELD_TITLE"],
                            value = "/set currency-emoji emoji::wave:")
            
            embed.set_footer(text = f"{interaction.guild.name.upper()} | {interaction.guild.id}")
            
            return embed

        if len(emoji) > 1: # If they're trying to add more than one emoji
            await interaction.response.send_message(embed = await currency_embed(text["CONFIG_SET_CURRENCY_EMOJI_ERROR_MULTI"]), ephemeral = True)
            return
        elif await is_emoji(emoji) is False: # Checks if they're attempting to set an emoji
            await interaction.response.send_message(embed = await currency_embed(text["CONFIG_SET_CURRENCY_EMOJI_ERROR_NO_EMOJI"]), ephemeral = True)
            return

        # Updating table with the emoji requested.
        await self.bot.db.update(DBTable.GUILDS, data = {DBColumns.guilds.CURRENCY_EMOJI.value: emoji}, condition = f"{DBColumns.guilds.GUILD_ID} = {interaction.guild.id}")

        # Completion embed
        embed=discord.Embed(title = text["CONFIG_SET_CURRENCY_EMOJI_SUCCESS_EMBED_TITLE"],
                                description = f"{text['CONFIG_SET_CURRENCY_EMOJI_SUCCESS_EMBED_DESC']} {emoji}", 
                                color = Colour.YELLOW)
            
        embed.set_author(name = self.bot.user.name.upper(), 
                            icon_url = self.bot.user.avatar.url)
        
        embed.add_field(name = text["CONFIG_SET_CURRENCY_EMOJI_SUCCESS_FIELD_TITLE"],
                        value = f"/set currency-emoji emoji:{emoji}")

        embed.set_footer(text = f"{interaction.guild.name.upper()} | {interaction.guild.id}")

        await interaction.response.send_message(embed = embed)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Config(bot))
