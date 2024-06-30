"""
RinBot's valorant command cog
- Commands:
    * /valorant login       - Logs into the user's Riot account
    * /valorant logout      - Logs out of the user's Riot account
    * /valorant cookie      - Logs into the user's Riot account using a cookie
    * /valorant store       - Shows the user's daily store
    * /valorant user-config - Sets user settings regarding the store
"""

from nextcord import Interaction, Embed, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog
from typing import Dict, List
from datetime import datetime, timedelta, UTC

from rinbot.core import RinBot
from rinbot.core import DBTable
from rinbot.core import ResponseType
from rinbot.core import Valorant2FAView
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted
from rinbot.core import get_expiration_time
from rinbot.core import respond

from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.valorant.useful import GetFormat

class Valorant(Cog, name='valorant'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    async def __get_endpoint(self, interaction: Interaction, username: str=None, password: str=None) -> API_ENDPOINT:
        user_id = interaction.user.id
        locale_code = get_interaction_locale(interaction)
        
        if username is not None and password is not None:
            auth = self.bot.val_db.auth
            auth.locale_code = locale_code
            data = await auth.temp_auth(username, password)
        elif username or password:
            await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale_code, 'VALORANT_PROVIDE_BOTH'
                ),
                hidden=True
            )
        else:
            data = await self.bot.val_db.is_data(user_id)
            
            if data:
                data['locale-code'] = locale_code
                
                endpoint = self.bot.val_endpoint
                endpoint.activate(data)
                
                return endpoint
            else:
                await respond(
                    interaction, Colour.red,
                    get_localized_string(
                        locale_code, 'VALORANT_NO_LOGIN'
                    )
                )
    
    @staticmethod
    def __embed(skin: Dict) -> Embed:
        embed = Embed(
            description=f'**{skin["name"]}**\n{skin["price"]}',
            colour=Colour.purple()
        )
        embed.set_thumbnail(url=skin['icon'])
        
        return embed
    
    @classmethod
    def __get_store_embeds(cls, player: str, offer: Dict, locale: str) -> List[Embed]:
        data = GetFormat.offer_format(offer, locale)
        
        duration = data.pop('duration')
        expires = get_expiration_time(datetime.now(UTC) + timedelta(seconds=duration), locale)
        description = get_localized_string(
            locale, 'VALORANT_USER_STORE',
            player=player, time=expires
        )
        
        embed = Embed(description=description, colour=Colour.purple())
        embeds = [embed]
        [embeds.append(cls.__embed(data[skin])) for skin in data]
        
        return embeds
    
    # /valorant
    @slash_command(
        name=get_localized_string('en-GB', 'VALORANT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant(self, interaction: Interaction) -> None:
        pass
    
    # /valorant login
    @_valorant.subcommand(
        name=get_localized_string('en-GB', 'VALORANT_LOGIN_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_LOGIN_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant_login(
        self, interaction: Interaction,
        username: str = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_LOGIN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_LOGIN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_USER_DESC')
            },
            required=True,
            min_length=3,
            max_length=16
        ),
        password: str = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_LOGIN_PASS_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_PASS_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_LOGIN_PASS_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_PASS_DESC')
            },
            required=True,
            min_length=8,
            max_length=128
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        user_id = interaction.user.id
        auth = self.bot.val_db.auth
        auth.locale_code = interaction.locale
        authenticate = await auth.authenticate(username, password)
        
        if authenticate['auth'] == 'response':
            await interaction.response.defer(ephemeral=True)
            
            login = await self.bot.val_db.login(user_id, authenticate)
            
            if login['auth']:
                return await respond(
                    interaction, Colour.green(),
                    get_localized_string(
                        locale, 'VALORANT_LOGIN_SUCCESS',
                        player=login['player']
                    ),
                    resp_type=ResponseType.FOLLOWUP
                )
            
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'VALORANT_LOGIN_FAILURE'
                ),
                resp_type=ResponseType.FOLLOWUP,
                hidden=True
            )
        
        elif authenticate['auth'] == '2fa':
            cookies = authenticate['cookie']
            message = authenticate['message']
            label = authenticate['label']
            
            modal = Valorant2FAView(
                interaction, locale, self.bot.val_db, cookies, message, label
            )
            
            await interaction.response.send_modal(modal)

    # /valorant logout
    @_valorant.subcommand(
        name=get_localized_string('en-GB', 'VALORANT_LOGOUT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGOUT_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_LOGOUT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGOUT_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant_logout(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        user_id = interaction.user.id
        
        if logout := self.bot.val_db.logout(user_id):
            if not logout:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'VALORANT_LOGOUT_FAILURE'
                    ),
                    hidden=True
                )
            
            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'VALORANT_LOGOUT_SUCCESS'
                ),
                hidden=True
            )

    # /valorant cookie
    @_valorant.subcommand(
        name=get_localized_string('en-GB', 'VALORANT_COOKIE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_COOKIE_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_COOKIE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_COOKIE_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant_cookie(
        self, interaction: Interaction,
        cookie: str = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_COOKIE_COOKIE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_COOKIE_COOKIE_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_COOKIE_COOKIE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_COOKIE_COOKIE_DESC')
            },
            required=True,
            min_length=1
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction.locale)
        login = await self.bot.val_db.cookie_login(
            interaction.user.id, cookie, interaction.locale
        )
        
        if login['auth']:
            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'VALORANT_COOKIE_SUCCESS',
                    player=login['player']
                ),
                hidden=True
            )
        else:
            await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'VALORANT_COOKIE_FAILURE',
                    player=login['player']
                ),
                hidden=True
            )
    
    # /valorant store
    @_valorant.subcommand(
        name=get_localized_string('en-GB', 'VALORANT_STORE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_STORE_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_STORE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_STORE_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant_store(
        self, interaction: Interaction,
        username: str = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_LOGIN_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_USER_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_LOGIN_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_USER_DESC')
            },
            required=False,
            min_length=3,
            max_length=16
        ),
        password: str = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_LOGIN_PASS_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_PASS_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_LOGIN_PASS_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_LOGIN_PASS_DESC')
            },
            required=False,
            min_length=8,
            max_length=128
        )
    ) -> None:
        is_private = True if username is not None or password is not None else False
        locale = get_interaction_locale(interaction)
        
        await interaction.response.defer(ephemeral=is_private)
        
        endpoint = await self.__get_endpoint(interaction, username, password)
        skin_price = endpoint.store_fetch_offers()
        self.bot.val_db.insert_skin_price(skin_price)
        
        data = endpoint.store_fetch_storefront()
        embeds = self.__get_store_embeds(endpoint.player, data, locale)
        
        await interaction.followup.send(embeds=embeds)

    # /valorant user-config
    @_valorant.subcommand(
        name=get_localized_string('en-GB', 'VALORANT_CONFIG_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_NAME')
        },
        description=get_localized_string('en-GB', 'VALORANT_CONFIG_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_DESC')
        }
    )
    @not_blacklisted()
    async def _valorant_config(
        self, interaction: Interaction,
        active: int = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_CONFIG_ACTIVE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_ACTIVE_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_CONFIG_ACTIVE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_ACTIVE_DESC')
            },
            required=True,
            default=0,
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
            }
        ),
        type: int = SlashOption(
            name=get_localized_string('en-GB', 'VALORANT_CONFIG_TYPE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_TYPE_NAME')
            },
            description=get_localized_string('en-GB', 'VALORANT_CONFIG_TYPE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'VALORANT_CONFIG_TYPE_DESC')
            },
            required=True,
            choices={
                'Send it to my DMs!': 0,
                'Send it on the server!': 1
            },
            choice_localizations={
                'Send it to my DMs!': {
                    Locale.pt_BR: 'Manda pro meu privado!'
                },
                'Send it on the server!': {
                    Locale.pt_BR: 'Manda aqui no servidor!'
                }
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if type == 1:
            dsc = await self.bot.db.get(
                DBTable.DAILY_SHOP_CHANNELS,
                f'guild_id={interaction.guild.id}'
            )
            
            if not dsc[0][3]:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'VALORANT_CONFIG_GUILD_MISCONFIG'
                    )
                )
            
            channel = interaction.guild.get_channel(dsc[0][4]) or await interaction.guild.fetch_channel(dsc[0][4])
            
            if not channel:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'VALORANT_CONFIG_GUILD_MISCONFIG_NO_CHANNEL'
                    )
                )
        
        data = {
            'active': active,
            'type': type,
            'target_guild': interaction.guild.id
        }
        
        await self.bot.db.update(
            DBTable.VALORANT, data, f'user_id={interaction.user.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'VALORANT_CONFIG_SET'
            )
        )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Valorant(bot))
