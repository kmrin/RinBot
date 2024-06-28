import nextcord, requests, re, torch
from nextcord.ext import commands
from PIL import Image
from io import BytesIO
from transformers import BlipForConditionalGeneration, BlipProcessor

from rinbot.core.client import RinBot
from rinbot.core.command_checks import not_blacklisted

class ImageCaption(commands.Cog, name='image_caption'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base",
                                                                  torch_dtype=torch.float32).to("cpu")
    
    @commands.command('comment_image')
    @not_blacklisted()
    async def comment_image(self, message: nextcord.Message, msg_content) -> None:
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        if "https://tenor.com/view/" in msg_content:
            start_index = msg_content.index("https://tenor.com/view/")
            end_index = msg_content.find(" ", start_index)
            if end_index == -1:
                tenor_url = msg_content[start_index:]
            else:
                tenor_url = msg_content[start_index:end_index]
            parts = tenor_url.split("/")
            words = parts[-1].split("-")[:-1]
            sentence = " ".join(words)
            msg_content = f"{msg_content} [{message.author.name} posts an animated {sentence} ]"
            msg_content = msg_content.replace(tenor_url, "")
            return msg_content
        
        elif url_pattern.match(msg_content):
            response = requests.get(msg_content)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        else:
            image_url = message.attachments[0].url
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        
        caption = self.caption_image(image)
        message_content = f"{message_content} [{message.author.name} posts a picture of {caption}]"
        
        return message_content

    def caption_image(self, raw_image):
        inputs = self.processor(raw_image.convert('RGB'), return_tensors="pt").to("cpu", torch.float32)
        out = self.model.generate(**inputs, max_new_tokens=50)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        
        return caption

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(ImageCaption(bot))
