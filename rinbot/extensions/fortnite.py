"""
RinBot's fortnite command cog
- Commands:
    * /fortnite daily-shop - Manually shows the fortnite daily shop on the channel
    * /fortnite stats      - Shows the player's ingame stats through their username
"""

from nextcord import Interaction, Locale, Colour, File, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.fortnite.daily_shop import show_fn_daily_shop

from rinbot.core import RinBot
from rinbot.core import ResponseType
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted
from rinbot.core import respond

class Fortnite(Cog, name='fortnite'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    # /fortnite (root)
    @slash_command(
        name=get_localized_string('en-GB', 'FORTNITE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_NAME')
        },
        description=get_localized_string('en-GB', 'FORTNITE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_DESC')
        }
    )
    @not_blacklisted()
    async def _fortnite(self, interaction: Interaction) -> None:
        pass
    
    # /fortnite daily-shop
    @_fortnite.subcommand(
        name=get_localized_string('en-GB', 'FORTNITE_DAILY_SHOP_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_DAILY_SHOP_NAME')
        },
        description=get_localized_string('en-GB', 'FORTNITE_DAILY_SHOP_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_DAILY_SHOP_DESC')
        }
    )
    @not_blacklisted()
    async def _fortnite_daily(self, interaction: Interaction) -> None:
        await interaction.response.defer(with_message=True)
        await show_fn_daily_shop(self.bot, interaction)
    
    # /fortnite stats
    @_fortnite.subcommand(
        name=get_localized_string('en-GB', 'FORTNITE_STATS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_NAME')
        },
        description=get_localized_string('en-GB', 'FORTNITE_STATS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_DESC')
        }
    )
    @not_blacklisted()
    async def _fortnite_stats(
        self, interaction: Interaction,
        player: str = SlashOption(
            name=get_localized_string('en-GB', 'FORTNITE_STATS_PLAYER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_PLAYER_NAME')
            },
            description=get_localized_string('en-GB', 'FORTNITE_STATS_PLAYER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_PLAYER_DESC')
            },
            required=True,
            
            # EPIC's username limits
            min_length=3,
            max_length=16
        ),
        season: int = SlashOption(
            name=get_localized_string('en-GB', 'FORTNITE_STATS_SEASON_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_SEASON_NAME')
            },
            description=get_localized_string('en-GB', 'FORTNITE_STATS_SEASON_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FORTNITE_STATS_SEASON_DESC')
            },
            required=False,
            default=0,
            choices={
                'Yes': 1, 'No': 0
            },
            choice_localizations={
                'Yes': {
                    Locale.pt_BR: 'Sim'
                },
                'No': {
                    Locale.pt_BR: 'Não'
                }
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        data = self.bot.fortnite_api.get_stats(
            player, True if season == 0 else False
        )
        
        if 'error' in data:
            errors = {
                'no_api_key': get_localized_string(locale, 'FORTNITE_STATS_ERROR_401'),
                404 : get_localized_string(locale, 'FORTNITE_STATS_ERROR_404', name=player)
            }
            
            return await respond(
                interaction, Colour.red(),
                errors[data['error']],
                resp_type=ResponseType.FOLLOWUP,
                hidden=True
            )
        
        stats = data[0]
        img_path = data[1]
        
        if not img_path:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'FORTNITE_STATS_ERROR_IMG'
                ),
                resp_type=ResponseType.FOLLOWUP,
                hidden=True
            )
        
        img = File(img_path, filename=f'{player}.png')
        
        await interaction.followup.send(file=img)

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Fortnite(bot))
