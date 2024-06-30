"""
RinBot's config command cog
- Commands:
    * /set welcome-channel             - Configures a custom embed to be shown when a member enters the server
    * /set daily-shop-channel fortnite - Sets in what channel rinbot should show the fortnite daily shop
    * /set daily-shop-channel valorant - Sets in what channel rinbot should show the valorant daily shop
    * /toggle daily-shop fortnite      - Toggles the fortnite daily shop on and off
    * /toggle daily-shop valorant      - Toggles the valorant daily shop on and off
"""

import nextcord

from nextcord import Interaction, ChannelType, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog
from nextcord.abc import GuildChannel

from rinbot.core import RinBot
from rinbot.core import DBTable
from rinbot.core import Loggers
from rinbot.core import ResponseType
from rinbot.core import SetWelcomeConfirmation

from rinbot.core import get_interaction_locale, get_localized_string, get_timeout_embed
from rinbot.core import hex_to_colour, is_hex_colour
from rinbot.core import not_blacklisted, is_admin, is_guild
from rinbot.core import respond

logger = Loggers.EXTENSIONS

class Config(Cog, name='config'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot

    # /set
    @slash_command(
        name=get_localized_string('en-GB', 'CONFIG_SET_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_SET_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_ROOT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _set_root(self, interaction: Interaction) -> None:
        pass
    
    # /set welcome-channel
    @_set_root.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _set_welcome(
        self, interaction: Interaction,
        channel: GuildChannel = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_DESC')
            },
            channel_types=[ChannelType.text],
            required=True
        ),
        title: str = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_TITLE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_TITLE_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_TITLE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_TITLE_DESC')
            },
            min_length=1, max_length=256,
            required=False
        ),
        description: str = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_DESC_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_DESC_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_DESC_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_DESC_DESC')
            },
            min_length=1, max_length=4096,
            required=False
        ),
        colour: str = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_COLOUR_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_COLOUR_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_EMBED_COLOUR_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_EMBED_COLOUR_DESC')
            },
            default='#FFFFFF',
            min_length=7, max_length=7,
            required=False
        ),
        show_pfp: int = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_PFP_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_PFP_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_WELCOME_PFP_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_WELCOME_PFP_DESC')
            },
            choices={
                'Yes': 1,
                'No': 0
            },
            choice_localizations={
                'Yes': {
                    Locale.pt_BR: 'Sim'
                },
                'No': {
                    Locale.pt_BR: 'Não'
                }
            },
            default=1,
            required=False
        )
    ) -> None:
        await interaction.response.defer()
        locale = get_interaction_locale(interaction),
        
        # If no options were given
        if not title and not description:
            return await respond(
                interaction, Colour.red(), get_localized_string(locale, 'CONFIG_SET_WELCOME_NO_OPTIONS'),
                resp_type=ResponseType.FOLLOWUP
            )
        
        if not is_hex_colour(colour):
            return await respond(
                interaction, Colour.red(), get_localized_string(locale, 'CONFIG_SET_WELCOME_INVALID_COLOUR', c=colour),
                resp_type=ResponseType.FOLLOWUP
            )
        
        example = nextcord.Embed(
            title=title,
            description=description,
            colour=hex_to_colour(colour)
        )
        
        # Edit title if necessary
        if title and '<username>' in title:
            example.title = title.replace('<username>', interaction.user.display_name)

        # Edit description if necessary
        if description and '<username>' in description:
            example.description = description.replace('<username>', interaction.user.display_name)
        if description and '<mention>' in description:
            example.description = description.replace('<mention>', interaction.user.mention)
        
        # Show user PFP
        if show_pfp == 1:
            example.set_thumbnail(
                interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
            )
        
        # Show example and wait for confirmation
        confirm = SetWelcomeConfirmation(interaction)
        
        # Show example to user
        await respond(
            interaction, message=example, view=confirm, resp_type=ResponseType.FOLLOWUP,
            outside_content=get_localized_string(locale, 'CONFIG_SET_WELCOME_INFO'))
        
        # If view times out
        timeout = await confirm.wait()
        if timeout:            
            return await interaction.edit_original_message(
                content=None,
                embed=get_timeout_embed(locale),
                view=None
            )
        
        # Get value from view
        aproved = confirm.response
        if not aproved:
            return
        
        # Create data for DB
        data = {
            'active': 1,
            'channel_id': channel.id,
            'show_pfp': show_pfp
        }
        
        if title:
            data['title'] = title
        if description:
            data['description'] = description
        if colour:
            data['colour'] = colour
        
        # Upload
        await self.bot.db.update(
            DBTable.WELCOME_CHANNELS, data, f'guild_id={interaction.guild.id}'
        )

    # /set daily-shop-channel
    @_set_root.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_SET_DAILY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_DAILY_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_SET_DAILY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_DAILY_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _set_daily(self, interaction: Interaction) -> None:
        pass

    # /set daily-shop-channel fortnite
    @_set_daily.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_SET_FORTNITE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_FORTNITE_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_SET_FORTNITE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_FORTNITE_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _set_daily_fortnite(
        self, interaction: Interaction,
        channel: GuildChannel = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_DESC')
            },
            channel_types=[ChannelType.text],
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        data = {
            'fortnite_active': 1,
            'fortnite_channel_id': channel.id
        }
        
        await self.bot.db.update(
            DBTable.DAILY_SHOP_CHANNELS, data, f'guild_id={interaction.guild.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(locale, 'CONFIG_SET_FORTNITE_SET', channel=channel.name)
        )
        
    # /set daily-shop-channel valorant
    @_set_daily.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_SET_VALORANT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_VALORANT_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_SET_VALORANT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_VALORANT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _set_daily_valorant(
        self, interaction: Interaction,
        channel: GuildChannel = SlashOption(
            name=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_NAME')
            },
            description=get_localized_string('en-GB', 'CONFIG_SET_CHANNEL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_SET_CHANNEL_DESC')
            },
            channel_types=[ChannelType.text],
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        data = {
            'valorant_active': 1,
            'valorant_channel_id': channel.id
        }
        
        await self.bot.db.update(
            DBTable.DAILY_SHOP_CHANNELS, data, f'guild_id={interaction.guild.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(locale, 'CONFIG_SET_VALORANT_SET', channel=channel.name)
        )

    # /toggle
    @slash_command(
        name=get_localized_string('en-GB', 'CONFIG_TOGGLE_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_TOGGLE_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_ROOT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _toggle_root(self, interaction: Interaction) -> None:
        pass
    
    # /toggle daily-shop
    @_toggle_root.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_TOGGLE_DAILY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_DAILY_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_TOGGLE_DAILY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_DAILY_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _toggle_daily(self, interaction: Interaction) -> None:
        pass
    
    # /toggle daily-shop fortnite
    @_toggle_daily.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_TOGGLE_FORTNITE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_FORTNITE_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_TOGGLE_FORTNITE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_FORTNITE_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _toggle_daily_fortnite(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        query = await self.bot.db.get(DBTable.DAILY_SHOP_CHANNELS, f'guild_id={interaction.guild.id}')
        new_state = 1 if query[0][1] == 0 else 0
        
        await self.bot.db.update(
            DBTable.DAILY_SHOP_CHANNELS, {
                'fortnite_active': new_state
            },
            f'guild_id={interaction.guild.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'CONFIG_TOGGLE_FORTNITE_TOGGLED',
                state = get_localized_string(locale, 'ON')
                        if new_state == 1 else 
                        get_localized_string(locale, 'OFF')
            )
        )
    
    # /toggle daily-shop valorant
    @_toggle_daily.subcommand(
        name=get_localized_string('en-GB', 'CONFIG_TOGGLE_VALORANT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_VALORANT_NAME')
        },
        description=get_localized_string('en-GB', 'CONFIG_TOGGLE_VALORANT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CONFIG_TOGGLE_VALORANT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _toggle_daily_valorant(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        query = await self.bot.db.get(DBTable.DAILY_SHOP_CHANNELS, f'guild_id={interaction.guild.id}')
        new_state = 1 if query[0][3] == 0 else 0
        
        await self.bot.db.update(
            DBTable.DAILY_SHOP_CHANNELS, {
                'valorant_active': new_state
            },
            f'guild_id={interaction.guild.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'CONFIG_TOGGLE_VALORANT_TOGGLED',
                state = get_localized_string(locale, 'ON')
                        if new_state == 1 else 
                        get_localized_string(locale, 'OFF')
            )
        )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Config(bot))
