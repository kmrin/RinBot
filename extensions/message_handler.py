# Imports
import asyncio, random, re, os
from discord.ext import commands
from dotenv import load_dotenv
from program.helpers import translate_to

load_dotenv()

# AI language (please always use 'en' I have no idea why I put this here but it's here anyway)
AI_LANG = os.getenv("AI_LANGUAGE")

class Listener(commands.Cog, name='Listener'):
    def __init__(self, bot):
        self.bot = bot
    
    # Checks if the message has a image / gif attached to it
    async def has_image_attachment(self, message):
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
    
    # Listener that listens to everything oOoooOOOOoo
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.content.startswith((".", "/")):
            return
        if message.mentions and self.bot.user.name not in [mention.name for mention in message.mentions]:
            return
        if message.channel.id in [int(channel_id) for channel_id in self.bot.guild_ids] or message.guild is None:
            if await self.has_image_attachment(message):
                image_response = await self.bot.get_cog("image_caption").comentar_imagem(message, message.clean_content)
                response = await self.bot.get_cog("chatbot").chat_command(message, image_response)
                if response:
                    if not AI_LANG == 'en':
                        response = translate_to(response, 'en', AI_LANG)
                    async with message.channel.typing():
                        await asyncio.sleep(1)  # Simulate "typing... (we need to make it real boys)"
                        await message.reply(response)
            else:
                response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)
                if response:
                    if not AI_LANG == 'en':
                        response = translate_to(response, 'en', AI_LANG)
                    async with message.channel.typing():
                        await asyncio.sleep(1)  # Simulate "typing... (we need to make it real boys)"
                        if random.random() < 0.8:
                            await message.channel.send(response)
                        else:
                            await message.reply(response)
                            return

# SETUP
async def setup(bot):
    await bot.add_cog(Listener(bot))