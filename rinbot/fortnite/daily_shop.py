import os
import asyncio
import discord

from discord import Interaction

from rinbot.base.exception_handler import log_exception
from rinbot.base.get_os_path import get_os_path
from rinbot.base.db import DBTable
from rinbot.base.logger import logger
from rinbot.base.colours import Colour
from rinbot.base.json_loader import get_lang

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base import RinBot

text = get_lang()

async def show_fn_daily_shop(client: "RinBot", interaction: Interaction=None) -> None:
    try:
        shop = await client.fortnite_api.get_shop()

        img_dir = get_os_path('../instance/cache/fortnite/composites')
        img_files = [f for f in os.listdir(img_dir) if f.endswith('.png')]

        embed = discord.Embed(
            title=text['FN_DS_SHOP_EMBED_TITLE'].format(
                time=f'**{shop["date"]}**'
            ),
            description=text['FN_DS_SHOP_EMBED_DESC'].format(
                show=f'**{len(img_files)}**',
                total=f'**{shop["count"]}**'
            ),
            color=Colour.PURPLE
        )

        async def generate_file(img_name) -> discord.File:
            path = os.path.join(img_dir, img_name)
            return discord.File(path, filename=img_name)

        async def generate_batches(guild) -> list:
            batches = []
            for i in range(0, len(img_files), 6):
                batch = []
                img_names = img_files[i:i+6]
                tasks = [generate_file(img) for img in img_names]
                results = await asyncio.gather(*tasks)
                batch.extend(results)
                batches.append(batch)

            logger.info(f"{text['FN_DS_BATCH_GEN']} '{guild}'")
            return batches

        async def send_batches_channel(channel: discord.TextChannel):
            
            if not me.guild_permissions.send_messages:
                logger.error(text['FN_DS_BATCH_NO_SEND_MESSAGES_PERM'].format(
                    guild=channel.guild
                ))
            if not me.guild_permissions.attach_files:
                logger.error(text['FN_DS_BATCH_NO_ATTACH_FILES_PERM'].format(
                    guild=channel.guild
                ))
            
            batches = await generate_batches(channel.guild.name)

            await channel.send(embed=embed)

            for i, batch in enumerate(batches):
                await channel.send(files=batch)

                logger.info(text['FN_DS_BATCH_SEND'].format(
                    batch_no=i, ch=channel.id
                ))

        async def send_batches_interaction(ctx: Interaction) -> None:
            me = ctx.guild.get_member(client.user.id) or await ctx.guild.fetch_member(client.user.id)
            
            if not me.guild_permissions.send_messages:
                logger.error(text['FN_DS_BATCH_NO_SEND_MESSAGES_PERM'].format(
                    guild=ctx.guild
                ))
            if not me.guild_permissions.attach_files:
                logger.error(text['FN_DS_BATCH_NO_ATTACH_FILES_PERM'].format(
                    guild=ctx.guild
                ))
            
            batches = await generate_batches(ctx.guild.name)

            await ctx.followup.send(embed=embed)

            for i, batch in enumerate(batches):
                await ctx.channel.send(files=batch)

                logger.info(text['FN_DS_BATCH_SEND'].format(
                    batch_no=i, ch=ctx.channel.id
                ))

        send_batch_tasks = []

        if not interaction:
            shop_channels = await client.db.get(DBTable.DAILY_SHOP_CHANNELS)

            for row in shop_channels:
                if row[1] == 1:
                    ch = client.get_channel(row[2]) or await client.fetch_channel(row[2])
                    if ch:
                        send_batch_tasks.append(asyncio.create_task(send_batches_channel(ch)))
        else:
            send_batch_tasks.append(asyncio.create_task(send_batches_interaction(interaction)))
        
        await asyncio.gather(*send_batch_tasks)
        
        for file in os.listdir(img_dir):
            os.remove(os.path.join(img_dir, file))
        
        logger.info(text['FN_DS_UPDATED'])
    except Exception as e:
            log_exception(e)
