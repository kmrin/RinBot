from nextcord import Embed, Colour, Member, TextChannel
from datetime import datetime, timedelta, UTC
from typing import Union, Dict, List, TYPE_CHECKING

from rinbot.valorant.useful import GetFormat
from rinbot.valorant.endpoint import API_ENDPOINT

from rinbot.core.db import DBTable
from rinbot.core.helpers import get_expiration_time, get_localized_string
from rinbot.core.json_manager import get_conf
from rinbot.core.loggers import Loggers

if TYPE_CHECKING:
    from rinbot.core.client import RinBot

logger = Loggers.VALORANT
conf = get_conf()

def _embed(skin: Dict) -> Embed:
    embed = Embed(
        description=f'**{skin["name"]}**\n{skin["price"]}',
        colour=Colour.purple()
    )
    embed.set_thumbnail(url=skin['icon'])
    
    return embed

def _gen_store_embeds(player: str, offer: Dict) -> List[Embed]:
    player = player.split('#')[0]
    data = GetFormat.offer_format(offer, conf['VALORANT_DAILY_SHOP_LANG'])
    duration = data.pop('duration')
    expires = get_expiration_time(datetime.now(UTC) + timedelta(seconds=duration), conf['VALORANT_DAILY_SHOP_LANG'])
    description = get_localized_string(
            conf['VALORANT_DAILY_SHOP_LANG'], 'VALORANT_USER_STORE',
            player=player, time=expires
    )
    
    embed = Embed(description=description, colour=Colour.purple())
    embeds = [embed]
    
    [embeds.append(_embed(data[skin])) for skin in data]
    
    return embeds

async def _get_endpoint(client: 'RinBot', user_id: int) -> Union[API_ENDPOINT, bool]:
    data = await client.val_db.is_data(user_id)
    
    if not data:
        return False
    
    endpoint = client.val_endpoint
    endpoint.activate(data)
    
    return endpoint

async def _show_private_shop(client: 'RinBot', user: Member, warn=False) -> None:
    endpoint: API_ENDPOINT = await _get_endpoint(client, user.id)
    
    if not endpoint:
        return
    
    skin_price = endpoint.store_fetch_offers()
    
    client.val_db.insert_skin_price(skin_price)
    
    data = endpoint.store_fetch_storefront()
    embeds = _gen_store_embeds(endpoint.player, data)
    
    await user.send(embeds=embeds)
    
    if warn:
        await user.send(
            get_localized_string(
                conf['VALORANT_DAILY_SHOP_LANG'], 'VALORANT_DS_PRIVATE'
            )
        )

async def _show_channel_shop(client: 'RinBot', channel: TextChannel, user: Member) -> None:
    endpoint: API_ENDPOINT = await _get_endpoint(client, user.id)
    
    if not endpoint:
        return
    
    skin_price = endpoint.store_fetch_offers()
    client.val_db.insert_skin_price(skin_price)
    data = endpoint.store_fetch_storefront()
    embeds = _gen_store_embeds(endpoint.player, data)
    
    await channel.send(
        get_localized_string(
            conf['VALORANT_DAILY_SHOP_LANG'], 'VALORANT_DS_CHANNEL',
            player=user.mention
        ),
        embeds=embeds
    )

async def show_val_daily_shop(client: 'RinBot') -> None:
    val = await client.db.get(DBTable.VALORANT)
    
    for row in val:
        if row[1] != 1:
            continue
        
        user = client.get_user(row[0]) or await client.fetch_user(row[0])
        guild = client.get_guild(row[3] or await client.fetch_guild(row[3]))

        if not user or not guild:
            continue
        
        if row[2] == 0:  # Private type
            await _show_private_shop(client, user)
        elif row[2] == 1:  # Channel type
            ds = await client.db.get(
                DBTable.DAILY_SHOP_CHANNELS,
                f'guild_id={guild.id}'
            )
            
            if ds[0][3] != 1:
                await _show_private_shop(client, user, True)
                continue
            
            channel = guild.get_channel(ds[0][4]) or await guild.fetch_channel(ds[0][4])

            if not channel:
                await _show_private_shop(client, user, True)
                continue

            await _show_channel_shop(client, channel, user)
