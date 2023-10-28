"""
RinBot v1.7.0 (GitHub release)
made by rin
"""

# Imports
import discord, requests, io, base64
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from PIL import Image, PngImagePlugin
from program.checks import *
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
file_path = os.getenv('STABLE_DIFFUSION_CACHE_DIR') # Default cache image output
url = os.getenv('STABLE_DIFFUSION_ENDPOINT')        # URL of the server running stablediffusion

# Negative prompt (what you don't want in your image)
negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name"

class StableDiffusion(commands.Cog, name='stablediffusion'):
    def __init__(self, bot):
        self.bot = bot

    # Command to generate an image with stable diffusion
    @commands.hybrid_command(name='generateimage', description='Generates an image with Stable Diffusion')
    @app_commands.describe(prompt='The image prompt, (best quality, masterpiece are automatically included)')
    @not_blacklisted()
    async def generateimage(self, ctx: Context, prompt: str = None) -> None:
        await ctx.defer()  # Defer because this takes a lot of time
        try:
            response = requests.get(url)
            if response.status_code == 200:
                payload = {
                    "prompt": f"masterpiece, best quality, {prompt}",
                    "negative_prompt": negative_prompt,
                    "seed": -1, 
                    "steps": 28, 
                    "cfg_scale": 12,
                    "width": 512, 
                    "height": 512, 
                    "sampler_index": "Euler"}
                
                # Receive response from server
                response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
                r = response.json()
                
                for i in r['images']:
                    # Rebuilt image
                    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
                    png_payload = {"image": "data:image/png;base64," + i}
                    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
                    pnginfo = PngImagePlugin.PngInfo()
                    pnginfo.add_text("parameters", response2.json().get("info"))
                    
                    # Save image
                    image.save(file_path, pnginfo=pnginfo)
                    
                    # Open image and send in chat
                    with open(file_path, 'rb') as f:
                        image = discord.File(f)
                        await ctx.send(file=image)
                    
                    # Delete the cached image file to save on storage
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                embed = discord.Embed(
                    description=f" ❌ Error {response.status_code}.",
                    color=0xD81313)
                await ctx.send(embed=embed)
        except requests.ConnectionError:
            embed = discord.Embed(
                description=f" ❌ Error, Stable Diffusion is not running, or my connection to the server was blocked / is not configured correctly.",
                color=0xD81313)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f" ❌ Error: {e}.",
                color=0xD81313)
            await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(StableDiffusion(bot))