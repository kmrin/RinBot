import discord
from rinbot.valorant.useful import GetFormat
from datetime import datetime, timedelta
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.base.db import DBTable
from rinbot.base.colours import Colour
from rinbot.base.helpers import get_expiration_time
from rinbot.base.json_loader import get_lang, get_conf
from rinbot.base.exception_handler import log_exception
from typing import Union, Dict, List

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

conf = get_conf()
text = get_lang()

def _embed(skin:Dict) -> discord.Embed:
    try:
        embed = discord.Embed(
            description=f"**{skin['name']}**\n{skin['price']}", colour=Colour.PURPLE)
        embed.set_thumbnail(url=skin['icon'])
        return embed
    except Exception as e:
        log_exception(e)

def _gen_store_embeds(player:str, offer:Dict) -> List[discord.Embed]:
    try:
        data = GetFormat.offer_format(offer, conf['LANGUAGE'])
        duration = data.pop("duration")

        description = text['VAL_DS_EMBED'].format(
            player=player,
            time=get_expiration_time(datetime.utcnow() + timedelta(seconds=duration))
        )

        embed = discord.Embed(description=description, colour=Colour.PURPLE)
        embeds = [embed]

        [embeds.append(_embed(data[skin])) for skin in data]

        return embeds
    except Exception as e:
        log_exception(e)

async def _get_endpoint(client: "RinBot", user_id:int) -> Union[API_ENDPOINT, bool]:
    try:
        data = await client.val_db.is_data(user_id)

        if not data:
            return False

        endpoint = client.val_endpoint
        endpoint.activate(data)

        return endpoint
    except Exception as e:
        log_exception(e)
        return False

async def _show_private_shop(client: "RinBot", user, warn=False) -> None:
    try:
        endpoint:API_ENDPOINT = await _get_endpoint(client, user.id)

        if not endpoint:
            return
        skin_price = endpoint.store_fetch_offers()

        client.val_db.insert_skin_price(skin_price)

        data = endpoint.store_fetch_storefront()
        embeds = _gen_store_embeds(endpoint.player, data)

        await user.send(embeds=embeds)

        if warn:
            await user.send(text['VAL_DS_CHANNEL_ERROR'])
    except Exception as e:
        log_exception(e)

async def _show_channel_shop(client: "RinBot", channel, user) -> None:
    try:
        endpoint: API_ENDPOINT = await _get_endpoint(client, user.id)

        if not endpoint:
            return

        skin_price = endpoint.store_fetch_offers()
        client.val_db.insert_skin_price(skin_price)
        data = endpoint.store_fetch_storefront()
        embeds = _gen_store_embeds(endpoint.player, data)

        await channel.send(content=f"{text['VAL_DS_MENTION']} {user.mention}!", embeds=embeds)
    except Exception as e:
        log_exception(e)

async def show_val_daily_shop(client: "RinBot") -> None:
    try:
        val = await client.db.get(DBTable.VALORANT)

        for row in val:
            if row[1] != 1:
                continue

            user = client.get_user(row[0]) or await client.fetch_user(row[0])
            guild = client.get_guild(row[3] or await client.fetch_guild(row[3]))

            if not user or not guild:
                continue

            if row[2] == 0:    # Private type
                await _show_private_shop(client, user)
            elif row[2] == 1:  # Channel type
                ds = await client.db.get(DBTable.DAILY_SHOP_CHANNELS,
                    condition=f"guild_id={guild.id}")

                if ds[0][3] != 1:
                    await _show_private_shop(client, user, True)
                    continue

                channel = guild.get_channel(ds[0][4]) or await guild.fetch_channel(ds[0][4])

                if not channel:
                    await _show_private_shop(client, user, True)
                    continue

                await _show_channel_shop(client, channel, user)
    except Exception as e:
        log_exception(e)
