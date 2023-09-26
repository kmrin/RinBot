"""
RinBot v1.4.3
feita por rin
"""

# Imports
import random, aiohttp, discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from program.translator import translate_to
from program.checks import *

# Interface gráfica (botões) do cara-ou-coroa
class ButtonChoice(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
    @discord.ui.button(label="Cara", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "cara"
        self.stop()
    @discord.ui.button(label="Coroa", style=discord.ButtonStyle.blurple)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "coroa"
        self.stop()

# Interface gráfica e embeds pro Pedra Papel Tesoura
class RockPaperScissors(discord.ui.Select):
    def __init__(self):
        
        # Escolhas
        options = [
            discord.SelectOption(
                label="Tesoura", description="Você escolhe tesoura.", emoji="✂"),
            discord.SelectOption(
                label="Pedra", description="Você escolhe pedra.", emoji="🪨"),
            discord.SelectOption(
                label="Papel", description="Você escolhe papel.", emoji="🧻"),]
        super().__init__(
            placeholder="Escolha...",
            min_values=1,
            max_values=1,
            options=options,)

    async def callback(self, interaction: discord.Interaction):
        choices = {
            "pedra": 0,
            "papel": 1,
            "tesoura": 2,}
        
        # Ler escolhas do usuário
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]
        
        # Realizar a escolha da bot
        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]
        
        # Embed de resultado com alternativas pré-configuradas
        result_embed = discord.Embed(color=0x9C84EF)
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if user_choice_index == bot_choice_index:
            result_embed.description = f"**É um empate!**\nVocê escolheu {user_choice} e eu escolhi {bot_choice}."
            result_embed.colour = 0xF59E42
        elif user_choice_index == 0 and bot_choice_index == 2:
            result_embed.description = f"**Meeh, você venceu.**\nVocê escolheu {user_choice} e eu escolhi {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 1 and bot_choice_index == 0:
            result_embed.description = f"**Meeh, você venceu.**\nVocê escolheu {user_choice} e eu escolhi {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 2 and bot_choice_index == 1:
            result_embed.description = f"**Meeh, você venceu.**\nVocê escolheu {user_choice} e eu escolhi {bot_choice}."
            result_embed.colour = 0x9C84EF
        else:
            result_embed.description = (
                f"**HAHA! Ganhei!**\nVocê escolheu {user_choice} e eu escolhi {bot_choice}.")
            result_embed.colour = 0xE02B2B
        
        # Editar dinâmicamente a mesma mensagem
        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None)

# Inicializador da UI do Pedra Papel Tesoura
class RockPaperScissorsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RockPaperScissors())

# Bloco de comandos 'fun'
class Fun(commands.Cog, name='fun'):
    def __init__(self, bot):
        self.bot = bot
    
    # Recebe, traduz e posta um fato aleatório do 'uselessfacts'
    @commands.hybrid_command(
        name='fato',
        description='Mostra um fato aleatório')
    @app_commands.describe(idioma='Traduzir o fato para uma linguagem específica')
    @not_blacklisted()
    async def randomfact(self, ctx: Context, idioma='pt-br') -> None:
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    text = data["text"]
                    if not idioma == 'en':
                        text = translate_to(data["text"], from_lang='en', to_lang=idioma)
                    embed = discord.Embed(description=text, color=0xD75BF4)
                else:
                    embed = discord.Embed(
                        title="Erro!",
                        description="Tem algo de errado com a API, tente novamente mais tarde.",
                        color=0xE02B2B)
                await ctx.send(embed=embed)
    
    # Cara ou coroa, bem auto-explicativo
    @commands.hybrid_command(
        name='cara-ou-coroa',
        description='Joga cara ou coroa com a RinBot')
    @not_blacklisted()
    async def cara_ou_coroa(self, ctx: Context) -> None:
        buttons = ButtonChoice()
        embed = discord.Embed(description="Qual sua aposta?", color=0x9C84EF)
        message = await ctx.send(embed=embed, view=buttons)
        await buttons.wait()
        result = random.choice(["cara", "coroa"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"Boaaaa! Você chutou `{buttons.value}` e eu tirei `{result}`.",
                color=0x9C84EF,)
        else:
            embed = discord.Embed(
                description=f"Puts. Você chutou `{buttons.value}` e eu tirei `{result}`, mais sorte na próxima!",
                color=0xE02B2B,)
        await message.edit(embed=embed, view=None, content=None)
    
    # PPT = Pedra Papel Tesoura
    @commands.hybrid_command(
        name='ppt',
        description='Joga pedra-papel-tesoura com a RinBot')
    @not_blacklisted()
    async def ppt(self, ctx: Context) -> None:
        view = RockPaperScissorsView()
        await ctx.send("Escolha", view=view)

# SETUP
async def setup(bot):
    await bot.add_cog(Fun(bot))