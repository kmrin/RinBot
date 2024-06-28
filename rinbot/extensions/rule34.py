"""
RinBot's rule34 command cog
- Commands:
    * /rule34 random - Shows a random image from rule34
    * /rule34 i-came - Shows a list with the top 10 characters on rule34's i-came list
"""

import aiohttp
import nextcord

from io import BytesIO
from PIL import Image
from typing import Union
from nextcord import Interaction, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.rule34.post import Post
from rinbot.rule34 import rule34Api

from rinbot.core import RinBot
from rinbot.core import ResponseType
from rinbot.core import log_exception
from rinbot.core import get_localized_string, get_interaction_locale
from rinbot.core import not_blacklisted
from rinbot.core import respond

class Rule34(Cog, name='rule34'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.api = rule34Api()
    
    @staticmethod
    async def _convert_png(url: str) -> Union[nextcord.File, None]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                img_b = await response.read()
                img = Image.open(BytesIO(img_b))
                out = BytesIO()
                img.save(out, format='PNG')
                out.seek(0)
                
                return nextcord.File(out, filename='r34_result.png')
    
    async def _get_random_post(self, tags: str) -> Union[list, Post, None]:
        post = self.api.random_post(tags)
        if not post:
            return None
        
        if post._video:
            if post._video != '':
                post = await self._get_random_post(tags)
        
        if not '.png' in post._image:
            self._image = await self._convert_png(post._image)
    
        return post
    
    # /rule34 (root)
    @slash_command(
        name=get_localized_string('en-GB', 'R34_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'R34_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_ROOT_DESC')
        }
    )
    @not_blacklisted()
    async def _rule34(self, interaction: Interaction) -> None:
        pass
    
    # /rule34 random
    @_rule34.subcommand(
        name=get_localized_string('en-GB', 'R34_RANDOM_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_RANDOM_NAME')
        },
        description=get_localized_string('en-GB', 'R34_RANDOM_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_RANDOM_DESC')
        }
    )
    @not_blacklisted()
    async def _rule34_random(
        self, interaction: Interaction,
        tags: str = SlashOption(
            name=get_localized_string('en-GB', 'R34_TAGS_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'R34_TAGS_NAME')
            },
            description=get_localized_string('en-GB', 'R34_TAGS_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'R34_TAGS_DESC')
            },
            required=True,
            min_length=1
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        
        chars = [',', '.', '|', '  ']
        for char in chars:
            if char in tags:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'R34_INVALID_TAGS'
                    ),
                    hidden=True,
                    resp_type=ResponseType.FOLLOWUP
                )
        
        tags = tags.split(' ')
        post = await self._get_random_post(tags)
        
        if not post:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'R34_NO_RESULTS'
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )
        
        if isinstance(post._image, nextcord.File):
            await interaction.followup.send(
                f'{get_localized_string(locale, "R34_LINK_TEXT")} [Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})',
                file=post._image
            )
        else:
            await interaction.followup.send(
                f'{get_localized_string(locale, "R34_LINK_TEXT")} [Rule34](https://rule34.xxx/index.php?page=post&s=view&id={post._id})'
            )
    
    # /rule34 i-came
    @_rule34.subcommand(
        name=get_localized_string('en-GB', 'R34_ICAME_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_ICAME_NAME')
        },
        description=get_localized_string('en-GB', 'R34_ICAME_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'R34_ICAME_DESC')
        }
    )
    @not_blacklisted()
    async def _rule34_icame(self, interaction: Interaction) -> None:        
        await interaction.response.defer(with_message=True)
        
        result = self.api.icame(limit=10)
        chars = []
        
        for char in result:
            char_name = char._character_name.split(' ')
            char_name = [name.capitalize() for name in char_name]
            char_name = ' '.join(char_name)
            chars.append(char_name)
        
        result = [f'**{i+1}.** {r}' for i, r in enumerate(chars)]
        result = '\n'.join(result)
        
        await respond(
            interaction, Colour.purple(), result, ' 📋  I Came',
            resp_type=ResponseType.FOLLOWUP
        )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Rule34(bot))
