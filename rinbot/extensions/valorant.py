"""
#### RinBot's valorant command cog
- commands:
    * /valorant login `Logs into the user's Riot account and saves it's cookie`
    * /valorant logout `Logs out of the user's Riot account and deletes it from the database`
    * /valorant cookie `Logs into the user's Riot account using a cookie`
    * /valorant store `Shows the user's daily valorant store`
"""

# Imports
import contextlib, discord
from discord import app_commands, Interaction
from discord.ext import tasks
from discord.ext.commands import Cog, Bot
from discord.utils import MISSING
from rinbot.valorant import cache as Cache
from rinbot.valorant.db import DATABASE
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.valorant.useful import GetFormat, format_relative
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang
from rinbot.base.colors import *
from rinbot.base.interface import Valorant2FAView
from rinbot.base.checks import *
from rinbot.base.responder import respond
from datetime import datetime, timedelta
from typing import Dict, List

# Verbose
text = load_lang()

# Valorant commands cog
class Valorant(Cog, name="valorant"):
    def __init__(self, bot) -> None:
        self.bot:Bot = bot
        self.endpoint:API_ENDPOINT = None
        self.db:DATABASE = None
        self.reload_cache.start()
    
    def cog_unload(self) -> None:
        self.reload_cache.cancel()
    
    def _reload_cache(self, force=False) -> None:
        with contextlib.suppress(Exception):
            cache = self.db.read_cache()
            version = Cache.get_valorant_version()
            if version != cache["valorant_version"] or force:
                Cache.get_cache()
                cache = self.db.read_cache()
                cache["valorant_version"] = version
                self.db.insert_cache(cache)
                logger.info(text['VALORANT_UPDATED_CACHE'])
    
    @tasks.loop(minutes=30)
    async def reload_cache(self) -> None:
        self._reload_cache()
    
    @reload_cache.before_loop
    async def before_reload_cache(self) -> None:
        await self.bot.wait_until_ready()
    
    @Cog.listener()
    async def on_ready(self) -> None:
        self.bot.val_db = DATABASE()
        self.bot.val_endpoint = API_ENDPOINT()
        self.db = self.bot.val_db
        self.endpoint = self.bot.val_endpoint
    
    async def get_endpoint(self, interaction:Interaction, username:str=None, password:str=None) -> API_ENDPOINT:
        user_id = interaction.user.id
        locale_code = interaction.locale
        if username is not None and password is not None:
            auth = self.db.auth
            auth.locale_code = locale_code
            data = await auth.temp_auth(username, password)
        elif username or password:
            await respond(interaction, RED, message=text['VALORANT_UPDATED_PROVIDE_BOTH'])
        else:
            data = await self.db.is_data(user_id)
        data["locale_code"] = locale_code
        endpoint = self.endpoint
        endpoint.activate(data)
        return endpoint
    
    def __embed(skin:Dict) -> discord.Embed:
        embed = discord.Embed(
            description=f"**{skin['name']}**\n{skin['price']}", color=PURPLE)
        embed.set_thumbnail(url=skin['icon'])
        return embed
    
    def get_store_embeds(cls, player:str, offer:Dict) -> List[discord.Embed]:
        data = GetFormat.offer_format(offer)
        duration = data.pop("duration")
        description = f"{text['VALORANT_USER_STORE'][0]}**{player}**{text['VALORANT_USER_STORE'][1]}\n{text['VALORANT_USER_STORE'][2]}`{format_relative(datetime.utcnow() + timedelta(seconds=duration))}`"
        embed = discord.Embed(description=description, color=PURPLE)
        embeds = [embed]
        [embeds.append(cls.__embed(data[skin])) for skin in data]
        return embeds
    
    # Command groups
    val_group = app_commands.Group(name="valorant", description="Valorant thingies")
    
    # Logs into the user's riot account and keeps a cookie cache of the login
    @val_group.command(
        name=text['VALORANT_LOGIN_NAME'], description=text['VALORANT_LOGIN_DESC'])
    @not_blacklisted()
    async def login(self, interaction:Interaction, username:str=None, password:str=None) -> None:
        if not username or not password:
            return await interaction.response.send_message(text['ERROR_INVALID_PARAMETERS'])
        user_id = interaction.user.id
        auth = self.db.auth
        auth.locale_code = interaction.locale
        authenticate = await auth.authenticate(username, password)
        if authenticate["auth"] == "response":
            await interaction.response.defer(ephemeral=True)
            login = await self.db.login(user_id, authenticate)
            if login["auth"]:
                embed = discord.Embed(
                    description=f"{text['VALORANT_LOGIN_SUCCESS']} **{login['player']}**!",
                    color=PURPLE)
                return await interaction.followup.send(embed=embed, ephemeral=True)
            return await respond(interaction, RED, message=text['VALORANT_LOGIN_FAILURE'])
        elif authenticate["auth"] == "2fa":
            cookies = authenticate["cookie"]
            message = authenticate["message"]
            label = authenticate["label"]
            modal = Valorant2FAView(interaction, self.db, cookies, message, label)
            await interaction.response.send_modal(modal)
    
    # Logs out of a user's account and deletes it from the database
    @val_group.command(
        name=text['VALORANT_LOGOUT_NAME'], description=text['VALORANT_LOGOUT_DESC'])
    @not_blacklisted()
    async def logout(self, interaction:Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        if logout := self.db.logout(user_id):
            if logout:
                embed = discord.Embed(
                    description=text['VALORANT_LOGOUT_SUCCESS'],
                    color=PURPLE)
                return await interaction.followup.send(embed=embed, ephemeral=True)
            return await respond(interaction, RED, message=text['VALORANT_LOGOUT_FAILURE'])
    
    # Logs into the user's account using a cookie
    @val_group.command(
        name=text['VALORANT_COOKIE_NAME'], description=text['VALORANT_COOKIE_DESC'])
    @not_blacklisted()
    async def cookie(self, interaction:Interaction, cookie:str=None) -> None:
        if not cookie:
            return await interaction.response.send_message(text['ERROR_INVALID_PARAMETERS'])
        await interaction.response.defer(ephemeral=True)
        login = await self.db.cookie_login(interaction.user.id, cookie, interaction.locale)
        if login["auth"]:
            embed = discord.Embed(
                description=f"{text['VALORANT_COOKIE_SUCCESS']} **{login['player']}**!",
                color=PURPLE)
            return await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await respond(interaction, RED, message=text['VALORANT_COOKIE_FAILURE'])
    
    # Shows the user's valorant daily shop
    @val_group.command(
        name=text['VALORANT_STORE_NAME'], description=text['VALORANT_STORE_DESC'])
    @not_blacklisted()
    async def store(self, interaction:Interaction, username:str=None, password:str=None) -> None:
        is_private = True if username is not None or password is not None else False
        await interaction.response.defer(ephemeral=is_private)
        endpoint = await self.get_endpoint(interaction, username, password)
        skin_price = endpoint.store_fetch_offers()
        self.db.insert_skin_price(skin_price)
        data = endpoint.store_fetch_storefront()
        embeds = self.get_store_embeds(endpoint.player, data)
        await interaction.followup.send(embeds=embeds)

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Valorant(bot))