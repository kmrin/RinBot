"""
RinBot's fun command cog
- Commands:
    * /pet            - :3
    * /cat            - Shows a random cat
    * /dog            - Shows a random dog
    * /fact           - Shows a random fact
    * /heads-or-tails - Plays heads-or-tails with rinbot
    * /rps            - Plays rock paper scissors with rinbot
    * /stickbug       - Stickbugs someone

- NekoBot command:
    * /threats
    * /captcha
    * /deepfry
    * /whowouldwin
"""

import os
import random
import aiohttp
import nextcord

from nextcord import Embed
from nextcord.ext.commands import Cog
from nextcord import Interaction, Colour, Locale, SlashOption, slash_command
from PIL import Image
from io import BytesIO

from rinbot.stickbug.stick_bug import StickBug
from rinbot.petpet.petpet import make_petpet
from rinbot.nekobot import NekoBotAsync

from rinbot.core import Path
from rinbot.core import RinBot
from rinbot.core import ResponseType
from rinbot.core import HeadsOrTails, RockPaperScissorsView
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted
from rinbot.core import translate
from rinbot.core import respond

class Fun(Cog, name='fun'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.neko = NekoBotAsync()
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

    # /heads-or-tails
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_HOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_HOT_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_HOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_HOT_DESC')
        }
    )
    @not_blacklisted()
    async def _hot(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        buttons = HeadsOrTails(locale)
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'FUN_HOT_MSG'
            ),
            view=buttons
        )
        
        await buttons.wait()
        
        embed = Embed()
        result = random.choice(['heads', 'tails'])
        if buttons.value == result:
            embed.description = get_localized_string(locale, 'FUN_HOT_WIN')
            embed.colour = Colour.green()
        else:
            embed.description = get_localized_string(locale, 'FUN_HOT_LOSS')
            embed.colour = Colour.red()
        
        await interaction.edit_original_message(embed=embed, view=None, content=None)
    
    # /rock-paper-scissors
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_RPS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_RPS_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_RPS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_RPS_DESC')
        }
    )
    @not_blacklisted()
    async def _rps(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        await respond(interaction, view=RockPaperScissorsView(locale))

    # /cat
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_CAT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_CAT_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_CAT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_CAT_DESC')
        }
    )
    @not_blacklisted()
    async def _cat(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                if resp.status != 200:
                    return await respond(
                        interaction, Colour.red(),
                        get_localized_string(
                            locale, 'FUN_CAT_NOT_FOUND'
                        )
                    )
                    
                js = await resp.json()
                
                embed = Embed(colour=Colour.purple())
                embed.set_image(url=js[0]['url'])
                
                await respond(interaction, message=embed)
    
    # /dog
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_DOG_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_DOG_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_DOG_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_DOG_DESC')
        }
    )
    @not_blacklisted()
    async def _dog(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://random.dog/woof') as resp:
                if resp.status != 200:
                    return await respond(
                        interaction, Colour.red(),
                        get_localized_string(
                            locale, 'FUN_DOG_NOT_FOUND'
                        )
                    )
                
                filename = await resp.text()
                url = f'https://random.dog/{filename}'
                filesize = interaction.guild.filesize_limit if interaction.guild else 83886087
                
                if filename.endswith(('mp4', '.webm')):
                    async with interaction.channel.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                return await respond(
                                    interaction, Colour.red(),
                                    get_localized_string(
                                        locale, 'FUN_DOG_NOT_FOUND'
                                    )
                                )
                            
                            try:
                                if int(other.headers['Content-Lenght']) >= filesize:
                                    await self._dog(interaction)
                            except KeyError:
                                await self._dog(interaction)
                            
                            fp = BytesIO(await other.read())
                            
                            await interaction.response.send_message(
                                file=nextcord.File(
                                    fp, filename=filename
                                )
                            )
                else:
                    embed = Embed(colour=Colour.red())
                    embed.set_image(url=url)
                    
                    await interaction.response.send_message(embed=embed)
    
    # /fact
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_FACT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_FACT_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_FACT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_FACT_DESC')
        }
    )
    @not_blacklisted()
    async def _fact(
        self, interaction: Interaction,
        lang: str = SlashOption(
            name=get_localized_string('en-GB', 'FUN_LANG_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_LANG_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_LANG_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_LANG_DESC')
            },
            default='en',
            required=False
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://uselessfacts.jsph.pl/random.json?language=en') as request:
                if request.status != 200:
                    return await respond(
                        interaction, Colour.red(),
                        get_localized_string(
                            locale, 'FUN_FACT_API_ERROR'
                        )
                    )
                
                data = await request.json()
                fact = data['text']
                
                if lang not in self.language_codes:
                    return await respond(
                        interaction, Colour.red(),
                        get_localized_string(
                            locale, 'GENERAL_TRANSLATE_INVALID',
                            lang=lang
                        )
                    )
                
                if lang != 'en':
                    fact = translate(fact, from_lang='en', to_lang=lang)
                    
                await respond(interaction, Colour.yellow(), fact, resp_type=ResponseType.FOLLOWUP)

    # /petpet
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_PET_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_PET_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_PET_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_PET_DESC')
        }
    )
    @not_blacklisted()
    async def _pet(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_DESC')
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        await interaction.response.defer(with_message=True)
        
        avatar = await member.avatar.read() if member.avatar else await member.default_avatar.read()
        source = BytesIO(avatar)
        dest = BytesIO()
        
        make_petpet(source, dest)
        
        dest.seek(0)
        
        await interaction.followup.send(
            get_localized_string(
                locale, 'FUN_PET_SCHITZO' if interaction.user == member else 'FUN_PET_PETTED',
                user = member.mention
            ),
            file=nextcord.File(dest, filename=f'{member.name}-petpet.gif')
        )

    # /stickbug
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_STICKBUG_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_STICKBUG_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_STICKBUG_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_STICKBUG_DESC')
        }
    )
    @not_blacklisted()
    async def _stickbug(
        self, interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_DESC')
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        await interaction.response.defer(with_message=True)
        
        avatar = await user.avatar.read() if user.avatar else user.default_avatar.read()
        
        image = Image.open(BytesIO(avatar))
        path = os.path.join(Path.instance, 'cache', 'stickbug')
        video_path = os.path.join(path, f'{user.name}.mp4')
        
        bug = StickBug(img=image)
        bug.save_video(video_path)
        
        await interaction.followup.send(
            get_localized_string(
                locale, 'FUN_STICKBUG_GET_STICKBUGGED',
                user=user.mention
            ),
            file=nextcord.File(video_path)
        )
        
        if os.path.isfile(video_path):
            os.remove(video_path)

    # /threats
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_THREATS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_THREATS_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_THREATS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_THREATS_DESC')
        }
    )
    @not_blacklisted()
    async def _threats(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_DESC')
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        resp = await self.neko.threats(
            member.avatar.url if member.avatar else member.default_avatar.url
        )
        
        await interaction.followup.send(resp.message)
    
    # /captcha
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_CAPTCHA_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_CAPTCHA_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_CAPTCHA_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_CAPTCHA_DESC')
        }
    )
    @not_blacklisted()
    async def _captcha(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_DESC')
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        resp = await self.neko.captcha(
            member.avatar.url if member.avatar else member.default_avatar.url,
            member.display_name
        )
        
        await interaction.followup.send(resp.message)
    
    # /deepfry
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_DEEPFRY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_DEEPFRY_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_DEEPFRY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_DEEPFRY_DESC')
        }
    )
    @not_blacklisted()
    async def _deepfry(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_USER_DESC')
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        resp = await self.neko.deepfry(
            member.avatar.url if member.avatar else member.default_avatar.url
        )
        
        await interaction.followup.send(resp.message)
    
    # /whowouldwin
    @slash_command(
        name=get_localized_string('en-GB', 'FUN_WHOWOULD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_NAME')
        },
        description=get_localized_string('en-GB', 'FUN_WHOWOULD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_DESC')
        }
    )
    @not_blacklisted()
    async def _www(
        self, interaction: Interaction,
        member_1: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_WHOWOULD_M1_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_M1_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_WHOWOULD_M1_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_M1_DESC')
            }
        ),
        member_2: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'FUN_WHOWOULD_M2_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_M2_NAME')
            },
            description=get_localized_string('en-GB', 'FUN_WHOWOULD_M2_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'FUN_WHOWOULD_M2_DESC')
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        resp = await self.neko.whowouldwin(
            member_1.avatar.url if member_1.avatar else member_1.default_avatar.url,
            member_2.avatar.url if member_2.avatar else member_2.default_avatar.url
        )
        
        await interaction.followup.send(resp.message)

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Fun(bot))
