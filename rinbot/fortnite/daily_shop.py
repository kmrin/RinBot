import os, asyncio, discord
from rinbot.base.helpers import load_lang
from rinbot.base.logger import logger
from rinbot.base.colors import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

text = load_lang()

async def show_fn_daily_shop(client: "RinBot", interaction: discord.Interaction=None) -> None:
    logger.info(text["DAILY_SHOP_UPDATING"])
    
    shop = await client.fortnite_api.get_shop()
    
    img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/composites"
    img_files = [f for f in os.listdir(img_dir) if f.endswith(".png")]
        
    embed = discord.Embed(
        title=f"{text['DAILY_SHOP_EMBED'][0]} **{shop['date']}**",
        description=f"{text['DAILY_SHOP_EMBED'][1]} **{len(img_files)}** {text['DAILY_SHOP_EMBED'][2]} **{shop['count']}** {text['DAILY_SHOP_EMBED'][3]}",
        color=PURPLE)
        
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
        
        logger.info(f"{text['FN_DS_BATCH_GEN']} {guild}")
        
        return batches
    
    async def send_batches_channel(channel: discord.TextChannel):
        batches = await generate_batches(channel.guild.name)
        
        await channel.send(embed=embed)
        
        for i, batch, in enumerate(batches):
            await channel.send(files=batch)
            
            logger.info(f"{text['FN_DS_BATCH_SEND'][0]} {i} {text['FN_DS_BATCH_SEND'][1]} {channel.name} (ID: {channel.id})")
    
    async def send_batches_interaction(interaction: discord.Interaction):
        batches = await generate_batches(interaction.guild.name)
        
        await interaction.followup.send(embed=embed)
        
        for i, batch in enumerate(batches):
            await interaction.channel.send(files=batch)
            
            logger.info(f"{text['FN_DS_BATCH_SEND'][0]} {i} {text['FN_DS_BATCH_SEND'][1]} {interaction.channel.name} (ID: {interaction.channel.id})")
    
    send_batch_tasks = []
    
    if not interaction:
        for guild in client.guilds:
            shop_channels = await client.db.get("daily_shop_channels")
            
            if str(guild.id) in shop_channels:
                if shop_channels[str(guild.id)]["active"]:
                    channel_id = shop_channels[str(guild.id)]["channel_id"]
                    channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
                    send_batch_tasks.append(asyncio.create_task(send_batches_channel(channel)))
    
    else:
        send_batch_tasks.append(asyncio.create_task(send_batches_interaction(interaction)))
    
    await asyncio.gather(*send_batch_tasks)
    
    for file in os.listdir(img_dir):
        os.remove(os.path.join(img_dir, file))
    
    logger.info(text["DAILY_SHOP_UPDATED"])