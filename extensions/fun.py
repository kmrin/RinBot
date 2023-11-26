# Imports
import random, aiohttp, discord, os, io, requests
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from program.helpers import translate_to
from program.checks import *
from program.petpet import make_petpet
from program.ocr import get_string_from_img

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
    
    # Reads text from an image and returns it
    @commands.hybrid_command(
        name='ocr',
        description='Reads text from a given image and returns it')
    @not_blacklisted()
    async def ocr(self, ctx:Context) -> None:
        try:
            url = ctx.message.attachments[0].url
            r = requests.get(url)
            filename = "cache/ocr/img.png"
            with open(filename, "wb") as out_file:
                out_file.write(r.content)
            ocr = get_string_from_img(filename)
            try:
                await ctx.send(ocr)
                os.remove(filename)
                os.remove("cache/ocr/removed_noise.png")
            except:
                embed = discord.Embed(
                    description=" ❌  Couldn't find the text ಥ_ಥ",
                    color=0xd91313)
                await ctx.send(embed=embed)
        except:
            embed = discord.Embed(
                description=" ❌  Couldn't open image or you didn't send me one.",
                color=0xd91313)
            await ctx.send(embed=embed)
    
    # Meme
    @commands.hybrid_command(
        name='meme',
        description="Memes someone's last message in chat")
    @app_commands.describe(user='The person to be memed')
    @not_blacklisted()
    async def meme(self, ctx:Context, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=" ❌  I can't meme the void bruv.",
                color=0xd91313)
            return await ctx.send(embed=embed)
        messages = []
        async for message in ctx.channel.history(limit=100):
            messages.append(message)
        user_message: discord.Message = next(
            (msg for msg in messages if msg.author == user and msg.content), None)
        if not user_message:
            embed = discord.Embed(
                description=" ❌  Failed to meme, *explodes*",
                color=0xd91313)
            return await ctx.send(embed=embed)
        pranked_message = ''.join([c.upper() if random.choice([True, False]) else c.lower()
                                for c in user_message.content])
        await user_message.reply(pranked_message)
    
    # PatPat :3
    @commands.hybrid_command(
        name='pet',
        description=':3')
    @app_commands.describe(user=':3:3:3')
    @not_blacklisted()
    async def pet_pet(self, ctx:Context, user:discord.User=None) -> None:
        await ctx.defer()
        if not user:
            embed = discord.Embed(
                title="Sad pet :(",
                description=" ❌  Give me a user to pet",
                color=0xd91313)
            return await ctx.send(embed=embed)
        try:
            image = await user.avatar.read()
        except AttributeError:
            image = await user.default_avatar.read()
        source = io.BytesIO(image)
        dest = io.BytesIO()
        make_petpet(source, dest)
        dest.seek(0)
        await ctx.send(
            f"{ctx.author.mention} petted {user.mention}"
            if not ctx.author.id == user.id else
            f"{ctx.author.mention} petted themselves", 
            file=discord.File(dest, filename=f'"{image[0]}-petpet.gif'))
    
    # Shows a random cat
    @commands.hybrid_command(
        name='cat',
        description='meow :3')
    @not_blacklisted()
    async def cat(self, ctx:Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title="Sad meow :(",
                        description=" ❌  Kitty not found.",
                        color=0xd91313)
                    return await ctx.send(embed=embed)
                js = await resp.json()
                embed = discord.Embed(color=0xe3a01b)
                embed.set_image(url=js[0]['url'])
                await ctx.send(embed=embed)
    
    # Shows a random dog
    @commands.hybrid_command(
        name='dog',
        description='Woof >:3')
    @not_blacklisted()
    async def dog(self, ctx:Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.dog/woof") as resp:
                if resp.status != 200:
                    embed = discord.Embed(
                        title="Sad woof :(",
                        description=" ❌  Doggy not found.",
                        color=0xd91313)
                    return await ctx.send(embed=embed)
                filename = await resp.text()
                url = f'https://random.dog/{filename}'
                filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
                if filename.endswith(('.mp4', '.webm')):
                    async with ctx.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                embed = discord.Embed(
                                    title="Sad woof :(",
                                    description=" ❌  Doggy not found.",
                                    color=0xd91313)
                                return await ctx.send(embed=embed)
                            if int(other.headers['Content-Length']) >= filesize:
                                await self.dog(ctx)
                            fp = io.BytesIO(await other.read())
                            await ctx.send(file=discord.File(fp, filename=filename))
                else:
                    embed = discord.Embed(color=0xe3a01b)
                    embed.set_image(url=url)
                    await ctx.send(embed=embed)
    
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