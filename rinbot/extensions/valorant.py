"""
RinBot's valorant command cog
- commands:
    * /valorant login `Logs into the user's Riot account and saves it's cookie`
    * /valorant logout `Logs out of the user's Riot account and deletes it from the database`
    * /valorant cookie `Logs into the user's Riot account using a cookie`
    * /valorant store `Shows the user's daily valorant store`
    * /valorant user-config `Sets user settings regarding the store`
"""

import discord

from discord import app_commands, Interaction
from discord.ext.commands import Cog
from discord.app_commands import Choice
from datetime import datetime, timedelta
from typing import Dict, List

from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.valorant.useful import GetFormat
from rinbot.base import get_expiration_time
from rinbot.base import Valorant2FAView
from rinbot.base import respond
from rinbot.base import DBTable
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import conf
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Valorant(Cog, name='valorant'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    async def __get_endpoint(self, interaction: Interaction, username: str=None, password: str=None) -> API_ENDPOINT:
        user_id = interaction.user.id
        locale_code = interaction.locale
        
        if username is not None and password is not None:
            auth = self.bot.val_db.auth
            auth.locale_code = locale_code
            data = await auth.temp_auth(username, password)
        elif username or password:
            await respond(interaction, Colour.RED, text['VALORANT_PROVIDE_BOTH'])
        else:
            data = await self.bot.val_db.is_data(user_id)
            
            if data:
                data['locale_code'] = locale_code
                endpoint = self.bot.val_endpoint
                endpoint.activate(data)
                return endpoint
            else:
                await respond(interaction, Colour.RED, text['VALORANT_NO_LOGIN'])
    
    @staticmethod
    def __embed(skin: Dict) -> discord.Embed:
        embed = discord.Embed(
            description=f"**{skin['name']}**\n{skin['price']}",
            colour=Colour.PURPLE
        )
        embed.set_thumbnail(url=skin['icon'])
        return embed
    
    @classmethod
    def __get_store_embeds(cls, player: str, offer: Dict) -> List[discord.Embed]:
        data = GetFormat.offer_format(offer, conf['LANGUAGE'])
        duration = data.pop('duration')
        description = text['VALORANT_USER_STORE'].format(
            player=player,
            time=get_expiration_time(datetime.utcnow() + timedelta(seconds=duration))
        )
        
        embed = discord.Embed(description=description, colour=Colour.PURPLE)
        embeds = [embed]
        [embeds.append(cls.__embed(data[skin])) for skin in data]
        
        return embeds
    
    val_group = app_commands.Group(name='valorant', description='VA VA')
    
    @val_group.command(
        name=text['VALORANT_LOGIN_NAME'],
        description=text['VALORANT_LOGIN_DESC'])
    @not_blacklisted()
    async def _login(self, interaction: Interaction, username: str, password: str) -> None:
        user_id = interaction.user.id
        auth = self.bot.val_db.auth
        auth.locale_code = interaction.locale
        authenticate = await auth.authenticate(username, password)
        
        if authenticate['auth'] == 'response':
            await interaction.response.defer(ephemeral=True)

            login = await self.bot.val_db.login(user_id, authenticate)

            if login['auth']:
                return await respond(
                    interaction,
                    colour=Colour.GREEN,
                    message=f'{text["VALORANT_LOGIN_SUCCESS"]} **{login["player"]}**!',
                    response_type=1
                )

            return await respond(
                interaction,
                colour=Colour.RED,
                message=text['VALORANT_LOGIN_FAILURE'],
                response_type=1
            )
        elif authenticate['auth'] == '2fa':
            cookies = authenticate['ookie']
            message = authenticate['message']
            label = authenticate['label']

            modal = Valorant2FAView(interaction, self.bot.val_db, cookies, message, label)

            await interaction.response.send_modal(modal)
    
    @val_group.command(
        name=text['VALORANT_LOGOUT_NAME'],
        description=text['VALORANT_LOGOUT_DESC'])
    @not_blacklisted()
    async def _logout(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        
        user_id = interaction.user.id
        
        if logout := self.bot.val_db.logout(user_id):
            if not logout:
                return await respond(interaction, Colour.RED, text['VALORANT_LOGOUT_FAILURE'])
            
            embed = discord.Embed(
                description=text['VALORANT_LOGOUT_SUCCESS'],
                colour=Colour.PURPLE
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @val_group.command(
        name=text['VALORANT_COOKIE_NAME'],
        description=text['VALORANT_COOKIE_DESC'])
    @not_blacklisted()
    async def _cookie(self, interaction: Interaction, cookie: str) -> None:
        await interaction.response.defer(ephemeral=True)
        
        login = await self.bot.val_db.cookie_login(interaction.user.id, cookie, interaction.locale)
        
        if login['auth']:
            embed = discord.Embed(
                description=f"{text['VALORANT_COOKIE_SUCCESS']} **{login['player']}**!",
                colour=Colour.PURPLE
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
    
    @val_group.command(
        name=text['VALORANT_STORE_NAME'], description=text['VALORANT_STORE_DESC'])
    @not_blacklisted()
    async def _store(self, interaction:Interaction, username:str=None, password:str=None) -> None:
        is_private = True if username is not None or password is not None else False
        await interaction.response.defer(ephemeral=is_private)
        endpoint = await self.__get_endpoint(interaction, username, password)
        skin_price = endpoint.store_fetch_offers()
        self.bot.val_db.insert_skin_price(skin_price)
        data = endpoint.store_fetch_storefront()
        embeds = self.__get_store_embeds(endpoint.player, data)
        await interaction.followup.send(embeds=embeds)
    
    @val_group.command(
        name=text['VALORANT_CONFIG_NAME'], description=text['VALORANT_CONFIG_DESC'])
    @app_commands.choices(active=[
        Choice(name=text['YES'], value=1),
        Choice(name=text['NO'], value=0)])
    @app_commands.choices(type=[
        Choice(name=text['VALORANT_CONFIG_TYPE1'], value=0),
        Choice(name=text['VALORANT_CONFIG_TYPE2'], value=1)])
    @not_blacklisted()
    async def _conf(self, interaction: Interaction, active: Choice[int], type: Choice[int]) -> None:
        try: active = active.value
        except: active = 0
        try: type = type.value
        except: type = 0
        
        if type == 1:
            dsc = await self.bot.db.get(
                DBTable.DAILY_SHOP_CHANNELS,
                condition=f'guild_id={interaction.guild.id}'
            )
            
            if not dsc[0][3]:
                return await respond(interaction, Colour.RED, text['VALORANT_CONFIG_GUILD_MISCONFIG'])
            
            channel = interaction.guild.get_channel(dsc[0][4]) or await interaction.guild.fetch_channel(dsc[0][4])
            
            if not channel:
                return await respond(interaction, Colour.RED, text['VALORANT_CONFIG_GUILD_MISCONFIG'])
        
        data = {
            'active': active,
            'type': type,
            'target_guild': interaction.guild.id
        }
        
        await self.bot.db.update(DBTable.VALORANT, data, condition=f'user_id={interaction.user.id}')
        
        await respond(interaction, Colour.GREEN, text['VALORANT_CONFIG_SET'])

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Valorant(bot))
