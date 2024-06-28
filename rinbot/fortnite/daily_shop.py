import os
import asyncio
import nextcord

from nextcord import Interaction, Embed, Colour

from rinbot.core.loggers import Loggers, log_exception
from rinbot.core.helpers import get_interaction_locale, get_localized_string
from rinbot.core.paths import get_os_path
from rinbot.core.db import DBTable

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.core.client import RinBot

logger = Loggers.FORTNITE

async def show_fn_daily_shop(client: "RinBot", interaction: Interaction=None) -> None:
    locale = get_interaction_locale(interaction)
    
    try:
        shop = await client.fortnite_api.get_shop()

        img_dir = get_os_path('../instance/cache/fortnite/composites')
        img_files = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        
        embed = Embed(
            title=get_localized_string(
                locale, 'FN_DS_SHOP_EMBED_TITLE',
                time=f'**{shop["date"]}**'
            ),
            description=get_localized_string(
                locale, 'FN_DS_SHOP_EMBED_DESC',
                show=f'**{len(img_files)}**',
                total=f'**{shop["count"]}**'
            ),
            colour=Colour.purple()
        )

        async def generate_file(img_name) -> nextcord.File:
            path = os.path.join(img_dir, img_name)
            return nextcord.File(path, filename=img_name)

        async def generate_batches(guild) -> list:
            batches = []
            for i in range(0, len(img_files), 6):
                batch = []
                img_names = img_files[i:i+6]
                tasks = [generate_file(img) for img in img_names]
                results = await asyncio.gather(*tasks)
                batch.extend(results)
                batches.append(batch)

            logger.info(f'Image batch generated for "{guild}"')
            return batches

        async def send_batches_channel(channel: nextcord.TextChannel):
            me = channel.guild.get_member(client.user.id) or await channel.guild.fetch_member(client.user.id)
            
            if not me.guild_permissions.send_messages:
                logger.error(f'No message sending permissions for "{channel.guild} (ID: {channel.guild.id})"')
            if not me.guild_permissions.attach_files:
                logger.error(f'No attach files permissions for "{channel.guild}" (ID: {channel.guild.id})')
            
            batches = await generate_batches(channel.guild.name)

            await channel.send(embed=embed)

            for i, batch in enumerate(batches):
                await channel.send(files=batch)

                logger.info(f'Batch {i} sent to "{channel.name}" (ID: {channel.id})')

        async def send_batches_interaction(ctx: Interaction) -> None:
            me = ctx.guild.get_member(client.user.id) or await ctx.guild.fetch_member(client.user.id)
            
            if not me.guild_permissions.send_messages:
                logger.error(f'No message sending permissions for "{ctx.guild} (ID: {ctx.guild.id})"')
            if not me.guild_permissions.attach_files:
                logger.error(f'No attach files permissions for "{ctx.guild}" (ID: {ctx.guild.id})')
            
            batches = await generate_batches(ctx.guild.name)

            await ctx.followup.send(embed=embed)

            for i, batch in enumerate(batches):
                await ctx.channel.send(files=batch)

                logger.info(f'Batch {i} sent to "{ctx.channel.name}" (ID: {ctx.channel.id})')

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
        
        logger.info('Daily shop shown')
    except Exception as e:
            log_exception(e)
