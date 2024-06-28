"""
RinBot's gemini command cog
- Commands:
    * /gemini talk  - Begin a conversation with google's gemini AI
    * /gemini reset - Reset your conversation
"""

from nextcord import Interaction, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.core import RinBot
from rinbot.core import respond
from rinbot.core import not_blacklisted
from rinbot.core import get_interaction_locale, get_localized_string

class Gemini(Cog, name='gemini'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    # /gemini
    @slash_command(
        name=get_localized_string('en-GB', 'GEMINI_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'GEMINI_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_ROOT_DESC')
        }
    )
    @not_blacklisted()
    async def _gemini_root(self, interaction: Interaction) -> None:
        pass
    
    # /gemini talk
    @_gemini_root.subcommand(
        name=get_localized_string('en-GB', 'GEMINI_TALK_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_TALK_NAME')
        },
        description=get_localized_string('en-GB', 'GEMINI_TALK_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_TALK_DESC')
        }
    )
    @not_blacklisted()
    async def _gemini_talk(
        self, interaction: Interaction,
        prompt: str = SlashOption(
            name=get_localized_string('en-GB', 'GEMINI_PROMPT_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_PROMPT_NAME')
            },
            description=get_localized_string('en-GB', 'GEMINI_PROMPT_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_PROMPT_DESC')
            },
            min_length=1,
            max_length=1000,
            required=True
        ),
        private: int = SlashOption(
            name=get_localized_string('en-GB', 'GEMINI_PRIVATE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_PRIVATE_NAME')
            },
            description=get_localized_string('en-GB', 'GEMINI_PRIVATE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_PRIVATE_DESC')
            },
            default=0,
            choices={
                'Yes': 1,
                'No': 0
            },
            choice_localizations={
                'Yes': {Locale.pt_BR: 'Sim'},
                'No': {Locale.pt_BR: 'Não'}
            },
            required=False
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if not self.bot.gemini:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'GEMINI_NOT_AVAILABLE'
                ),
                hidden=True
            )
        
        ephemeral = False if private == 0 else True
        await interaction.response.defer(with_message=True, ephemeral=ephemeral)
        msg = self.bot.gemini.message(prompt, interaction.user.name)
        await interaction.followup.send(msg, ephemeral=ephemeral)
    
    # /gemini reset
    @_gemini_root.subcommand(
        name=get_localized_string('en-GB', 'GEMINI_RESET_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_RESET_NAME')
        },
        description=get_localized_string('en-GB', 'GEMINI_RESET_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GEMINI_RESET_DESC')
        }
    )
    @not_blacklisted()
    async def _gemini_reset(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if not self.bot.gemini:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'GEMINI_NOT_AVAILABLE'
                ),
                hidden=True
            )
        
        self.bot.gemini.reset(interaction.user.name)
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'GEMINI_RESET'
            ),
            hidden=True
        )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Gemini(bot))
