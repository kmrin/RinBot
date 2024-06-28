"""
RinBot's general command cog
- Commands:
    * /rininfo        - Shows info about rinbot
    * /help           - Shows a paginated embed with the list of all commands and what they do
    * /translate      - Translates text from one language to another
    * /list-languages - Shows a paginated embed with the list of all languages supported by the /translate command
    * /specs          - Shows the system specs of the host running RinBot
"""

import nextcord
import platform

from nextcord import Interaction, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.core import RinBot
from rinbot.core import Loggers
from rinbot.core import Paginator
from rinbot.core import ResponseType
from rinbot.core import remove_nl_from_string_iterable
from rinbot.core import get_localized_string, get_interaction_locale, get_conf, get_os_path, get_specs
from rinbot.core import not_blacklisted
from rinbot.core import respond
from rinbot.core import translate

logger = Loggers.EXTENSIONS
conf = get_conf()

class General(Cog, name='general'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.language_codes = [
            'ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 
            'bm', 'ba', 'eu', 'be', 'bn', 'bi', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 
            'zh', 'cu', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'en', 'eo', 
            'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'fy', 'ff', 'gd', 'gl', 'lg', 'ka', 'de', 'el', 
            'kl', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'is', 'io', 'ig', 'id', 
            'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 
            'rw', 'ky', 'kv', 'kg', 'ko', 'kj', 'ku', 'lo', 'la', 'lv', 'li', 'ln', 'lt', 'lu', 
            'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'gv', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'nd', 
            'nr', 'ng', 'ne', 'no', 'nb', 'nn', 'ii', 'oc', 'oj', 'or', 'om', 'os', 'pi', 'ps', 
            'fa', 'pl', 'pt', 'pt-br', 'pa', 'qu', 'ro', 'rm', 'rn', 'ru', 'se', 'sm', 'sg', 
            'sa', 'sc', 'sr', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'st', 'es', 'su', 'sw', 'ss', 
            'sv', 'tl', 'ty', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'to', 'ts', 'tn', 'tr', 
            'tk', 'tw', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'wo', 'xh', 'yi', 
            'yo', 'za', 'zu'
        ]
    
    # /inforin
    @slash_command(
        name=get_localized_string('en-GB', 'GENERAL_INFO_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_INFO_NAME')
        },
        description=get_localized_string('en-GB', 'GENERAL_INFO_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_INFO_DESC')
        }
    )
    @not_blacklisted()
    async def _inforin(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        embed = nextcord.Embed(
            title=get_localized_string(locale, 'GENERAL_INFO_TITLE'),
            colour=Colour.gold())

        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_INFO_CREATED')[0],
            value=get_localized_string(locale, 'GENERAL_INFO_CREATED')[1],
            inline=True)
        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_INFO_VERSION'),
            value=f"{conf['VERSION']}",
            inline=True)
        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_INFO_CODER')[0],
            value=get_localized_string(locale, 'GENERAL_INFO_CODER')[1],
            inline=True)
        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_INFO_BUG')[0],
            value=get_localized_string(locale, 'GENERAL_INFO_BUG')[1],
            inline=True)
        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_INFO_PY'),
            value=f"{platform.python_version()}",
            inline=True)

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)

        embed.set_footer(
            text=get_localized_string(
                locale, 'GENERAL_REQUESTED', user=interaction.user.name),
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        
        await respond(interaction, message=embed)

    # /help
    @slash_command(
        name=get_localized_string('en-GB', 'GENERAL_HELP_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_HELP_NAME')
        },
        description=get_localized_string('en-GB', 'GENERAL_HELP_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_HELP_DESC')
        }
    )
    @not_blacklisted()
    async def _help(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        try:
            with open(get_os_path(f'assets/docs/help_{locale}.md'), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = '\n'.join(remove_nl_from_string_iterable(lines)).split('\n')
                
                chunks = [lines[i:i + 15] for i in range(0, len(lines), 15)]
                
                embed = nextcord.Embed(
                    title=get_localized_string(locale, 'GENERAL_HELP_TITLE'),
                    description='\n'.join(chunks[0]),
                    colour=Colour.gold()
                )
                
                view = Paginator(embed, chunks)
                await respond(interaction, message=embed, view=view)
        except FileNotFoundError:
            await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'GENERAL_HELP_NOT_FOUND')
            )

    # /translate
    @slash_command(
        name=get_localized_string('en-GB', 'GENERAL_TRANSLATE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_NAME')
        },
        description=get_localized_string('en-GB', 'GENERAL_TRANSLATE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_DESC')
        }
    )
    @not_blacklisted()
    async def _translate(
        self, interaction: Interaction,
        text: str = SlashOption(
            name=get_localized_string('en-GB', 'GENERAL_TRANSLATE_TEXT_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_TEXT_NAME')
            },
            description=get_localized_string('en-GB', 'GENERAL_TRANSLATE_TEXT_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_TEXT_DESC')
            },
            max_length=100,
            required=True
        ),
        from_lang: str = SlashOption(
            name=get_localized_string('en-GB', 'GENERAL_TRANSLATE_FROM_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_FROM_NAME')
            },
            description=get_localized_string('en-GB', 'GENERAL_TRANSLATE_FROM_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_FROM_DESC')
            },
            required=True,
            default='en'
        ),
        to_lang: str = SlashOption(
            name=get_localized_string('en-GB', 'GENERAL_TRANSLATE_LANG_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_LANG_NAME')
            },
            description=get_localized_string('en-GB', 'GENERAL_TRANSLATE_LANG_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_TRANSLATE_LANG_DESC')
            },
            required=False,
            default='pt-br'
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        # I know this can be an "or" expression
        # But I need to be able to get the incorrect value separately
        # There's probably a better way to do this but this just works
        # also it's 4 AM, come on
        if from_lang not in self.language_codes:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'GENERAL_TRANSLATE_INVALID', lang=from_lang)
            )
        elif to_lang not in self.language_codes:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'GENERAL_TRANSLATE_INVALID', lang=to_lang)
            )
        
        await interaction.response.defer()
        
        text = translate(text, from_lang, to_lang)
        
        await respond(interaction, Colour.gold(), text, resp_type=ResponseType.FOLLOWUP)
    
    # /list-languages
    @slash_command(
        name=get_localized_string('en-GB', 'GENERAL_LANGUAGES_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_LANGUAGES_NAME')
        },
        description=get_localized_string('en-GB', 'GENERAL_LANGUAGES_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_LANGUAGES_DESC')
        }
    )
    @not_blacklisted()
    async def _translate_languages(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        try:
            with open(get_os_path(f'assets/docs/languages.md'), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = '\n'.join(remove_nl_from_string_iterable(lines)).split('\n')
                
                chunks = [lines[i:i + 15] for i in range(0, len(lines), 15)]
                
                embed = nextcord.Embed(
                    title=get_localized_string(locale, 'GENERAL_LANGUAGES_TITLE'),
                    description='\n'.join(chunks[0]),
                    colour=Colour.gold()
                )
                
                view = Paginator(embed, chunks)
                await respond(interaction, message=embed, view=view)
        except FileNotFoundError:
            await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'GENERAL_LANGUAGE_FILE_NOT_FOUND')
            )

    # /specs
    @slash_command(
        name=get_localized_string('en-GB', 'GENERAL_SPECS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_SPECS_NAME')
        },
        description=get_localized_string('en-GB', 'GENERAL_SPECS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'GENERAL_SPECS_DESC')
        }
    )
    @not_blacklisted()
    async def _specs(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        await interaction.response.defer()
        
        specs = get_specs()
        embed = nextcord.Embed(
            title=get_localized_string(locale, 'GENERAL_SPECS_TITLE'),
            colour=Colour.gold()
        )
        
        embed.set_thumbnail(
            url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url
        )
        
        embed.add_field(
            name=get_localized_string(locale, 'GENERAL_SPECS_SYSTEM'),
            value=specs.os, inline=False
        )
        
        embed.add_field(name=' 🧇  CPU:', value=specs.cpu, inline=False)
        embed.add_field(name=' 💾  RAM:', value=specs.ram, inline=False)
        
        embed.add_field(
            name=' 🖼️  GPU:', value=specs.gpu if specs.gpu else get_localized_string(
                locale, 'GENERAL_SPECS_NO_GPU'
            ),
            inline=False
        )
        
        embed.set_footer(
            text=get_localized_string(
                locale, 'GENERAL_REQUESTED', user=interaction.user.name),
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        
        await respond(interaction, message=embed, resp_type=ResponseType.FOLLOWUP)

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(General(bot))
