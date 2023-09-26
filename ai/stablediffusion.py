"""
RinBot v1.4.3
feita por rin
"""

# Imports
import discord, requests, io, base64
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from PIL import Image, PngImagePlugin
from program.checks import *

file_path = 'ai/temp/output.png'  # Saída padrão do cache da imagem gerada
url = "http://127.0.0.1:7860"     # URL do servidor rodando o stablediffusion

class StableDiffusion(commands.Cog, name='stablediffusion'):
    def __init__(self, bot):
        self.bot = bot

    # Comando para gerar uma imagem com o stablediffusion
    @commands.hybrid_command(name='gerarimagem', description='Gera uma imagem com o Stable Diffusion')
    @app_commands.describe(prompt='O prompt da imagem, (best quality, masterpiece já são adicionados automaticamente)')
    @not_blacklisted()
    async def gerarimagem(self, ctx: Context, prompt: str = None) -> None:
        await ctx.defer()  # Defer pq demora pra caceta
        try:
            response = requests.get(url)
            if response.status_code == 200:
                payload = {
                    "prompt": f"masterpiece, best quality, {prompt}",
                    "negative_prompt": "EasyNegativeV2",  # Inversão Textual ENv2
                    "seed": -1, 
                    "steps": 28, 
                    "cfg_scale": 12,
                    "width": 512, 
                    "height": 512, 
                    "sampler_index": "Euler"}
                
                # Receber resposta do servidor
                response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
                r = response.json()
                
                for i in r['images']:
                    # Reconstruir imagem
                    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))
                    png_payload = {"image": "data:image/png;base64," + i}
                    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
                    pnginfo = PngImagePlugin.PngInfo()
                    pnginfo.add_text("parameters", response2.json().get("info"))
                    
                    # Salvar imagem
                    image.save(file_path, pnginfo=pnginfo)
                    
                    # Abrir imagem e enviar no chat
                    with open(file_path, 'rb') as f:
                        image = discord.File(f)
                        await ctx.send(file=image)
                    
                    # Deletar a imagem pra evitar uso de armazenamento excessivo
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                embed = discord.Embed(
                    description=f" ❌ Erro {response.status_code}.",
                    color=0xD81313)
                await ctx.send(embed=embed)
        except requests.ConnectionError:
            embed = discord.Embed(
                description=f" ❌ Erro, o Stable Diffusion não está rodando.",
                color=0xD81313)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f" ❌ Erro: {e}.",
                color=0xD81313)
            await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(StableDiffusion(bot))