"""
RinBot's fun command cog
- Commands:
    * /pet `:3`
    * /cat `Shows a random cat`
    * /dog `Shows a random dog`
    * /fact `Shows a random fact`
    * /heads-or-tails `Plays heads-or-tails with rinbot`
    * /rps `Plays rock paper scissors with rinbot`
    * /stickbug `Stickbugs someone`

- NekoBot commands:
    * /threats
    * /captcha
    * /deepfry
    * /whowouldwin
"""

import io
import os
import random
import aiohttp
import discord

from PIL import Image
from io import BytesIO
from discord import app_commands, Interaction
from discord.ext.commands import Cog

from rinbot.stickbug.stick_bug import StickBug
from rinbot.petpet.petpet import make_petpet
from rinbot.nekobot import NekoBotAsync

from rinbot.base import ButtonChoice, RockPaperScissorsView
from rinbot.base import translate
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import Path
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Fun(Cog, name="fun"):
    def __init__(self, bot: RinBot):
        self.bot = bot
        self.neko_api = NekoBotAsync()
    
    neko = app_commands.Group(name='nekobot', description='nekobot api')
    
    @app_commands.command(
        name=text["FUN_PET_NAME"],
        description=text["FUN_PET_DESC"])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _pet_pet(self, interaction: Interaction, member: discord.Member) -> None:
        try:
            image = await member.avatar.read()
        except AttributeError:
            image = await member.default_avatar.read()
        
        await interaction.response.defer()
        
        source = io.BytesIO(image)
        dest = io.BytesIO()
        
        make_petpet(source, dest)
        
        dest.seek(0)
        
        await interaction.followup.send(
            text['FUN_PET_PETTED'].format(
                petter=interaction.user.mention,
                receiver=member.mention
            ) if not interaction.user == member else
            text['FUN_PET_SCHITZO'].format(
                petter=interaction.user.mention
            ),
            file=discord.File(dest, filename=f'{member.name}-petpet.gif')
        )
    
    @app_commands.command(
        name=text['FUN_CAT_NAME'],
        description=text['FUN_CAT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _cat(self, interaction: Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                if resp.status != 200:
                    return await respond(interaction, Colour.RED, text['FUN_CAT_NOT_FOUND'], text['FUN_CAT_SAD_MEOW'])
                
                js = await resp.json()
                
                embed = discord.Embed(colour=Colour.PURPLE)
                embed.set_image(url=js[0]['url'])
                
                await respond(interaction, message=embed)
    
    @app_commands.command(
        name=text['FUN_DOG_NAME'],
        description=text['FUN_DOG_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _dog(self, interaction: Interaction) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random.dog/woof") as resp:
                if resp.status != 200:
                    return await respond(interaction, Colour.RED, text['FUN_DOG_NOT_FOUND'], text['FUN_DOG_SAD_WOOF'])
                
                filename = await resp.text()
                url = f'https://random.dog/{filename}'
                filesize = interaction.guild.filesize_limit if interaction.guild else 8388608
                
                if filename.endswith(('.mp4', '.webm')):
                    async with interaction.channel.typing():
                        async with session.get(url) as other:
                            if other.status != 200:
                                return await respond(interaction, Colour.RED, text['FUN_DOG_NOT_FOUND'], text['FUN_DOG_SAD_WOOF'])
                            
                            if int(other.headers['Content-Length']) >= filesize:
                                await self._dog(interaction)
                            
                            fp = io.BytesIO(await other.read())
                            
                            await interaction.response.send_message(file=discord.File(fp, filename=filename))
                else:
                    embed = discord.Embed(colour=Colour.RED)
                    embed.set_image(url=url)
                    await interaction.response.send_message(embed=embed)
    
    @app_commands.command(
        name=text['FUN_FACT_NAME'],
        description=text['FUN_FACT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    @app_commands.describe(language=text['FUN_FACT_LANGUAGE_DESC'])
    async def _random_fact(self, interaction: Interaction, language: str='en') -> None:
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://uselessfacts.jsph.pl/random.json?language=en') as request:
                if request.status != 200:
                    return await respond(interaction, Colour.RED, text['FUN_FACT_API_ERROR'], response_type=1)
                
                data = await request.json()
                fact = data['text']
                
                if language != 'en':
                    fact = translate(fact, from_lang='en', to_lang=language)
                    
                    if not fact:
                        return await respond(interaction, Colour.RED, text['FUN_FACT_INVALID_LANGUAGE'], response_type=1)
                
                await respond(interaction, Colour.YELLOW, fact, response_type=1)

    @app_commands.command(
        name=text['FUN_HOT_NAME'],
        description=text['FUN_HOT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _heads_or_tails(self, interaction: Interaction) -> None:
        buttons = ButtonChoice()
        
        embed = discord.Embed(
            description=text['FUN_HOT_EMBED_DESC'],
            colour=Colour.GREEN
        )
        
        await interaction.response.send_message(embed=embed, view=buttons)
        await buttons.wait()
        
        embed = discord.Embed()
        
        result = random.choice(['heads', 'tails'])
        if buttons.value == result:
            embed.description = text['FUN_HOT_WON'].format(
                user_choice=buttons.value,
                bot_choice=result
            )
            embed.colour = Colour.GREEN
        else:
            embed.description = text['FUN_HOT_LOST'].format(
                user_choice=buttons.value,
                bot_choice=result
            )
            embed.colour = Colour.RED
        
        await interaction.edit_original_response(embed=embed, view=None, content=None)
    
    @app_commands.command(
        name=text['FUN_RPS_NAME'],
        description=text['FUN_RPS_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _rps(self, interaction: Interaction) -> None:
        await interaction.response.send_message(text['FUN_RPS_CHOOSE'], view=RockPaperScissorsView())
    
    @app_commands.command(
        name="stickbug",
        description=text['FUN_BUG_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _stickbug(self, interaction: Interaction, member: discord.Member) -> None:
        await interaction.response.defer()
        
        try:
            avatar = await member.avatar.read()
        except AttributeError:
            avatar = await member.default_avatar.read()
        
        image = Image.open(BytesIO(avatar))
        path = os.path.join(Path.instance, 'cache', 'stickbug')
        video_path = os.path.join(path, f'{member.name}.mp4')
        
        bug = StickBug(img=image)
        bug.save_video(video_path)
        
        await interaction.followup.send(
            text['FUN_BUG_BUGGED'].format(
                user=member.mention
            ),
            file=discord.File(video_path)
        )
        
        if os.path.isfile(video_path):
            os.remove(video_path)
    
    @neko.command(name="threats", description="Nekobot Threats")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _threats(self, interaction: Interaction, member: discord.Member) -> None:
        await interaction.response.defer()

        try:
            resp = await self.neko_api.threats(member.avatar.url)
        except AttributeError:
            resp = await self.neko_api.threats(member.default_avatar.url)

        await interaction.followup.send(resp.message)
    
    @neko.command(name="captcha", description="Nekobot Captcha")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _captcha(self, interaction: Interaction, member: discord.Member) -> None:
        await interaction.response.defer()

        try:
            avatar = member.avatar.url
        except AttributeError:
            avatar = member.default_avatar.url

        resp = await self.neko_api.captcha(avatar, member.name)

        await interaction.followup.send(resp.message)
    
    @neko.command(name="deepfry", description="Nekobot deep fry")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _deepfry(self, interaction: Interaction, member: discord.Member) -> None:
        await interaction.response.defer()

        try:
            avatar = member.avatar.url
        except AttributeError:
            avatar = member.default_avatar.url

        resp = await self.neko_api.deepfry(avatar)

        await interaction.followup.send(resp.message)
    
    @neko.command(name="whowouldwin", description="Nekobot Who Would Win")
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _whowouldwin(self, interaction: Interaction, member_1: discord.Member, member_2: discord.Member):
        await interaction.response.defer()

        try:
            avatar_1 = member_1.avatar.url
        except AttributeError:
            avatar_1 = member_1.default_avatar.url
        try:
            avatar_2 = member_2.avatar.url
        except AttributeError:
            avatar_2 = member_2.default_avatar.url

        resp = await self.neko_api.whowouldwin(avatar_1, avatar_2)

        await interaction.followup.send(resp.message)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Fun(bot))
