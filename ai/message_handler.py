"""
RinBot v1.4.3
feita por rin
"""

# Imports
import asyncio, random, re, os
from discord.ext import commands
from dotenv import load_dotenv
from program.translator import translate_to

load_dotenv()

# Definir linguagem (sempre use 'en' pfv, nem sei pq botei isso aq mas ta ai)
AI_LANG = os.getenv("AI_LANGUAGE")

# Bloco de comandos 'Listener'
class Listener(commands.Cog, name='Listener'):
    def __init__(self, bot):
        self.bot = bot
    
    # Verifica se a mensagem enviada possuí uma imagem / GIF
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
    
    # Ouvidão que ouve tudo ooOOOoooOoOooo
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
                        await asyncio.sleep(1)  # Simular "digitando..."
                        await message.reply(response)
            else:
                response = await self.bot.get_cog("chatbot").chat_command(message, message.clean_content)
                if response:
                    if not AI_LANG == 'en':
                        response = translate_to(response, 'en', AI_LANG)
                    async with message.channel.typing():
                        await asyncio.sleep(1)  # Simular "digitando..."
                        if random.random() < 0.8:
                            await message.channel.send(response)
                        else:
                            await message.reply(response)
                            return

# SETUP
async def setup(bot):
    await bot.add_cog(Listener(bot))