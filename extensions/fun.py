"""
RinBot v1.9.0 (GitHub release)
made by rin
"""

# Imports
import random, aiohttp, discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from program.helpers import translate_to
from program.checks import *

# Heads or Tails interface
class ButtonChoice(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
    @discord.ui.button(label="Heads", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "heads"
        self.stop()
    @discord.ui.button(label="Tails", style=discord.ButtonStyle.blurple)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "tails"
        self.stop()

# Interface and rock paper scissors embed
class RockPaperScissors(discord.ui.Select):
    def __init__(self):
        
        # Choices
        options = [
            discord.SelectOption(
                label="Scissors", description="You chose scissors.", emoji="✂"),
            discord.SelectOption(
                label="Rock", description="You chose rock.", emoji="🪨"),
            discord.SelectOption(
                label="Paper", description="You chose paper.", emoji="🧻"),]
        super().__init__(
            placeholder="Choose and prepare to looooose!!!",
            min_values=1,
            max_values=1,
            options=options,)

    async def callback(self, interaction: discord.Interaction):
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2,}
        
        # Read user choice
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]
        
        # Make the bot's decision
        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]
        
        # Result embed
        result_embed = discord.Embed(color=0x9C84EF)
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if user_choice_index == bot_choice_index:
            result_embed.description = f"**It's a draw!**\nYou chose {user_choice} and I chose {bot_choice}."
            result_embed.colour = 0xF59E42
        elif user_choice_index == 0 and bot_choice_index == 2:
            result_embed.description = f"**Bruuuh, you won.**\nYou chose {user_choice} and I chose {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 1 and bot_choice_index == 0:
            result_embed.description = f"**Bruuuh, you won.**\nYou chose {user_choice} and I chose {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 2 and bot_choice_index == 1:
            result_embed.description = f"**Bruuuh, you won.**\nYou chose {user_choice} and I chose {bot_choice}."
            result_embed.colour = 0x9C84EF
        else:
            result_embed.description = (
                f"**HAHA! I won!**\nYou chose {user_choice} and I chose {bot_choice}.")
            result_embed.colour = 0xE02B2B
        
        # Dynamically edit the same message instead of spaming
        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None)

# Rock paper scissors UI initializer
class RockPaperScissorsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RockPaperScissors())

# 'Fun' command cog
class Fun(commands.Cog, name='fun'):
    def __init__(self, bot):
        self.bot = bot
    
    # Receives, translates, and shows a random fact from 'uselessfacts'
    @commands.hybrid_command(
        name='fact',
        description='Shows a random fact')
    @app_commands.describe(language='Translate the fact to a specific language')
    @not_blacklisted()
    async def randomfact(self, ctx: Context, language='en') -> None:
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    text = data["text"]
                    if not language == 'en':
                        text = translate_to(data["text"], from_lang='en', to_lang=language)
                    embed = discord.Embed(description=text, color=0xD75BF4)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There's something wrong with the API. Try again later!",
                        color=0xE02B2B)
                await ctx.send(embed=embed)
    
    # Heads or tails, very self explanatory
    @commands.hybrid_command(
        name='heads-or-tails',
        description='Plays heads-or-tails with RinBot')
    @not_blacklisted()
    async def heads_or_tails(self, ctx: Context) -> None:
        buttons = ButtonChoice()
        embed = discord.Embed(description="What is your bet?", color=0x9C84EF)
        message = await ctx.send(embed=embed, view=buttons)
        await buttons.wait()
        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"Nice! You betted `{buttons.value}` and I got `{result}`.",
                color=0x9C84EF,)
        else:
            embed = discord.Embed(
                description=f"Unlucky. You betted `{buttons.value}` and I got `{result}`.",
                color=0xE02B2B,)
        await message.edit(embed=embed, view=None, content=None)
    
    # RPS = RockPaperScissors (in case you haven't figured it out)
    @commands.hybrid_command(
        name='rps',
        description='Plays rock paper scissors with RinBot!')
    @not_blacklisted()
    async def rps(self, ctx: Context) -> None:
        view = RockPaperScissorsView()
        await ctx.send("Choose...", view=view)

# SETUP
async def setup(bot):
    await bot.add_cog(Fun(bot))