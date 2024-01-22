import discord
from rinbot.valorant.useful import GetFormat
from datetime import datetime, timedelta
from discord.ext.commands import Bot
from rinbot.valorant.endpoint import API_ENDPOINT
from rinbot.base.logger import logger
from rinbot.base.db_man import *
from rinbot.base.colors import *
from rinbot.base.helpers import format_expiration_time
from typing import Dict, List

def _embed(skin:Dict) -> discord.Embed:
    embed = discord.Embed(
        description=f"**{skin['name']}**\n{skin['price']}", color=PURPLE)
    embed.set_thumbnail(url=skin['icon'])
    return embed

def _gen_store_embeds(player:str, offer:Dict) -> List[discord.Embed]:
    data = GetFormat.offer_format(offer)
    duration = data.pop("duration")
    description = f"{text['VAL_DS_EMBED'][0]}**{player}**{text['VAL_DS_EMBED'][1]}\n{text['VAL_DS_EMBED'][2]} `{format_expiration_time(datetime.utcnow() + timedelta(seconds=duration))}`"
    embed = discord.Embed(description=description, color=PURPLE)
    embeds = [embed]
    [embeds.append(_embed(data[skin])) for skin in data]
    return embeds

async def _get_endpoint(client, user_id:int) -> API_ENDPOINT:
    try:
        data = await client.val_db.is_data(user_id)
        if not data: return False
        endpoint = client.val_endpoint
        endpoint.activate(data)
        return endpoint
    except Exception as e:
        logger.error(f"{text['VAL_DS_ENDPOINT_ERROR']} {user_id}: {e}")
        return False

async def _get_webhook(client:Bot, channel_id) -> discord.Webhook:
    try:
        channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
        channel_hooks = await channel.webhooks()
        if not channel_hooks:
            channel_hook = await channel.create_webhook(name=text['VAL_DS_HOOK_NAME'])
        else:
            channel_hook = channel_hooks[0]
        await channel_hook.edit(name=text['VAL_DS_HOOK_NAME'], avatar=await client.user.avatar.read())
        return channel_hook
    except Exception as e:
        logger.error(f"{text['VAL_DS_HOOK_ERROR']} {e}")
        return False

async def _show_private_shop(client:Bot, user_id, warn=False) -> None:
    try:
        user = client.get_user(user_id) or await client.fetch_user(user_id)
        endpoint:API_ENDPOINT = await _get_endpoint(client, user_id)
        if not endpoint: return
        skin_price = endpoint.store_fetch_offers()
        client.val_db.insert_skin_price(skin_price)
        data = endpoint.store_fetch_storefront()
        embeds = _gen_store_embeds(endpoint.player, data)
        await user.send(embeds=embeds)
        if warn:
            await user.send(text['VAL_DS_CHANNEL_ERROR'])
    except Exception as e:
        logger.error(f"{text['VAL_DS_ERROR_SENDING']} {e}")

async def _show_channel_shop(client:Bot, guild_id, channel_id, user_id) -> None:
    try:
        user = client.get_user(user_id) or await client.fetch_user(user_id)
        guild = client.get_guild(guild_id) or await client.fetch_guild(guild_id)
        channel = guild.get_channel(channel_id) or await guild.fetch_channel(channel_id)
        endpoint:API_ENDPOINT = await _get_endpoint(client, user_id)
        if not endpoint: return
        skin_price = endpoint.store_fetch_offers()
        client.val_db.insert_skin_price(skin_price)
        data = endpoint.store_fetch_storefront()
        embeds = _gen_store_embeds(endpoint.player, data)
        hook = await _get_webhook(client, channel_id)
        if hook:
            await hook.send(content=f"{text['VAL_DS_MENTION']} {user.mention}!", embeds=embeds)
        else:
            await channel.send(content=f"{text['VAL_DS_MENTION']} {user.mention}!", embeds=embeds)
    except Exception as e:
        logger.error(f"{text['VAL_DS_ERROR_SENDING_CHANNEL']} {e}")

async def show_val_daily_shop(client:Bot) -> None:
    val = await get_table("valorant")
    for guild_id, guild in val.items():
        active = guild["active"]
        channel_id = guild["channel_id"]
        members = guild["members"]
        for member_id, member in members.items():
            if member["active"] and member["type"] == 0:
                await _show_private_shop(client, int(member_id))
            elif member["active"] and member["type"] == 1:
                if active: 
                    await _show_channel_shop(client, int(guild_id), int(channel_id), int(member_id))
                else:
                    await _show_private_shop(client, int(member_id), True)