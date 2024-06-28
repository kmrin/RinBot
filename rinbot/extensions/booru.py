"""
RinBot's booru command cog
- Commands:
    * /booru random - Shows a random picture from danbooru with the given tags and rating
"""

import random

from nextcord import Interaction, Embed, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.booru import Danbooru

from rinbot.core import RinBot
from rinbot.core import ResponseType
from rinbot.core import log_exception
from rinbot.core import get_localized_string, get_interaction_locale, get_conf
from rinbot.core import not_blacklisted
from rinbot.core import respond

conf = get_conf()

UNAME = conf['BOORU_USERNAME']
API = conf['BOORU_KEY']
IS_GOLD = conf['BOORU_IS_GOLD']

class Booru(Cog, name='booru'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.client = Danbooru('danbooru', username=UNAME, api_key=API)

    # /booru (root)
    @slash_command(
        name=get_localized_string('en-GB', 'BOORU_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'BOORU_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_ROOT_DESC')
        }
    )
    @not_blacklisted()
    async def _booru(self, interaction: Interaction) -> None:
        pass
    
    # /booru random
    @_booru.subcommand(
        name=get_localized_string('en-GB', 'BOORU_RANDOM_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_RANDOM_NAME')
        },
        description=get_localized_string('en-GB', 'BOORU_RANDOM_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_RANDOM_DESC')
        }
    )
    @not_blacklisted()
    async def _booru_random(
        self, interaction: Interaction,
        rating: str = SlashOption(
            name=get_localized_string('en-GB', 'BOORU_RATING_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_RATING_NAME')
            },
            description=get_localized_string('en-GB', 'BOORU_RATING_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_RATING_DESC')
            },
            required=True,
            choices={
                'G - General': 'g',
                'S - Sensitive': 's',
                'Q - Questionable': 'q'
            },
            choice_localizations={
                'G - General': {
                    Locale.pt_BR: 'G - Geral'
                },
                'S - Sensitive': {
                    Locale.pt_BR: 'S - Sensível'
                },
                'Q - Questionable': {
                    Locale.pt_BR: 'Q - Questionável'
                }
            }
        ),
        tags: str = SlashOption(
            name=get_localized_string('en-GB', 'BOORU_TAGS_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_TAGS_NAME')
            },
            description=get_localized_string('en-GB', 'BOORU_TAGS_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'BOORU_TAGS_DESC')
            },
            required=False,
            min_length=1
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        request_tags = f'rating:{rating}'
        
        if tags:
            chars = [',', '.', '|', '  ']
            for char in chars:
                if char in tags:
                    return await respond(
                        interaction, Colour.red(),
                        get_localized_string(
                            locale, 'BOORU_INVALID_TAGS'
                        ),
                        hidden=True,
                        resp_type=ResponseType.FOLLOWUP
                    )
            
            tag_count = tags.split(' ')
            
            if len(tag_count) >= 3 and not IS_GOLD:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'BOORU_MAX_API'
                    ),
                    hidden=True,
                    resp_type=ResponseType.FOLLOWUP
                )
            elif len(tag_count) >= 6:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'BOORU_MAX_API_GOLD'
                    ),
                    hidden=True,
                    resp_type=ResponseType.FOLLOWUP
                )
            
            request_tags = request_tags + ' ' + tags
        
        try:
            posts = self.client.post_list(limit=100, tags=request_tags)
            post = random.choice(posts)
            
            try:
                url = post['file_url']
            except:
                url = post['source']
            
            embed = Embed(colour=Colour.purple())
            embed.set_image(url=url)
            
            await respond(interaction, message=embed, resp_type=ResponseType.FOLLOWUP)
        except IndexError:
            await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'BOORU_NO_RESULTS'
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )
        except Exception as e:
            e = log_exception(e)
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'BOORU_API_ERROR',
                    e=e
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Booru(bot))
