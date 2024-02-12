"""
#### RinBot's fortnite command cog
- Commands:
    * /fortnite daily-shop `Manually shows the fortnite daily shop on the channel`
"""

# Imports
import os, asyncio, discord
from discord import Interaction
from discord import app_commands
from discord.ext.commands import Bot, Cog
from rinbot.fortnite.daily_shop import FortniteAPI
from rinbot.base.helpers import load_lang
from rinbot.base.checks import *
from rinbot.base.colors import *

# Load text & config
text = load_lang()

# Fortnite command cog
class Fortnite(Cog, name="fortnite"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    # Command groups
    fortnite_group = app_commands.Group(name=text['FORTNITE_GROUP_NAME'], description=text['FORTNITE_GROUP_DESC'])
    
    # Daily shop command
    @fortnite_group.command(
        name=text['FORTNITE_DAILY_SHOP_NAME'],
        description=text['FORTNITE_DAILY_SHOP_DESC'])
    @not_blacklisted()
    async def daily_shop(self, interaction:Interaction) -> None:
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
        
        async def send_batches(hook:discord.Webhook):
            batches = await generate_batches(hook.guild.name)
            for i, batch in enumerate(batches):
                await hook.send(files=batch)
                logger.info(f"{text['FN_DS_BATCH_SEND'][0]} {i} {text['FN_DS_BATCH_SEND'][1]} {hook.channel.name} (ID: {hook.channel.id})")
        
        await interaction.response.defer(thinking=True)
        
        api = FortniteAPI(self.bot.fnds_language)
        shop = await api.get_shop()
        
        img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/composites"
        img_files = [f for f in os.listdir(img_dir) if f.endswith(".png")]
        embed = discord.Embed(
            title=f"{text['DAILY_SHOP_EMBED'][0]} **{shop['date']}**",
            description=f"{text['DAILY_SHOP_EMBED'][1]} **{len(img_files)}** {text['DAILY_SHOP_EMBED'][2]} **{shop['count']}** {text['DAILY_SHOP_EMBED'][3]}",
            color=PURPLE)

        channel = interaction.channel
        channel_hooks = await channel.webhooks()
        if not channel_hooks:
            channel_hook = await channel.create_webhook(name=text['FN_DS_HOOK_NAME'])
        else:
            channel_hook = channel_hooks[0]
        await channel_hook.edit(name=text['FN_DS_HOOK_NAME'], avatar=await self.bot.user.avatar.read())
        
        await interaction.followup.send(embed=embed)
        await send_batches(channel_hook)

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Fortnite(bot))