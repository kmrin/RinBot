import asyncio, random, re, nextcord
from nextcord.ext import commands
from rinbot.core.client import RinBot

class Listener(commands.Cog, name='Listener'):
    def __init__(self, bot: RinBot):
        self.bot = bot
    
    async def has_image_attachment(self, message: nextcord.Message):
        url_pattern = re.compile(r'http[s]?://[^\s/$.?#].[^\s]*\.(jpg|jpeg|png|gif)', re.IGNORECASE)
        tenor_pattern = re.compile(r'https://tenor.com/view/[\w-]+')
        for attachment in message.attachments:
            if attachment.filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                return True
        if url_pattern.search(message.content):
            return True
        elif tenor_pattern.search(message.content):
            return True
        else:
            return False
    
    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        guild_ids = [guild.id for guild in self.bot.guilds]
        
        if message.author == self.bot.user or message.content.startswith((".", "/")):
            return
        if message.mentions and self.bot.user.name not in [mention.name for mention in message.mentions]:
            return
        if message.channel.id in [int(channel_id) for channel_id in guild_ids] or message.guild is None:
            if await self.has_image_attachment(message):
                image_response = await self.bot.get_cog("image_caption").comment_image(message, message.clean_content)
                response = await self.bot.get_cog("chatbot").chat(message, image_response)
                if response:
                    async with message.channel.typing():
                        await asyncio.sleep(1)  # Simulate "typing... (we need to make it real boys)
                        await message.reply(response)
            else:
                response = await self.bot.get_cog("chatbot").chat(message, message.clean_content)
                if response:
                    async with message.channel.typing():
                        await asyncio.sleep(1)  # Simulate "typing... (we need to make it real boys)
                        if random.random() < 0.8:
                            await message.channel.send(response)
                        else:
                            await message.reply(response)
                            return

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Listener(bot))
