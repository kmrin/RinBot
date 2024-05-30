"""
RinBot's general command cog
- Commands:
    * /help `Shows a help paginated embed with all commands`
    * /translate `Translates a string to another language (Auto -> PT-BR by default)`
    * /specs `Shows the system specs of the computer running the bot`
    * /rininfo `Shows info about the bot`
    * /ping `Sends back a ping-pong response with the bot's network latency`
"""

import discord
import platform

from discord import Interaction
from discord import app_commands
from discord.ext.commands import Cog

from rinbot.base import get_specs
from rinbot.base import translate
from rinbot.base import remove_nl
from rinbot.base import get_os_path
from rinbot.base import log_exception
from rinbot.base import Paginator
from rinbot.base import respond
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import conf
from rinbot.base import text as tx
from rinbot.base import DBTable
from rinbot.base import DBColumns

# from rinbot.base import is_admin
# from rinbot.base import is_owner
from rinbot.base import not_blacklisted

# profile packages
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

class General(Cog, name='general'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    @app_commands.command(
        name=tx['GENERAL_HELP_NAME'],
        description=tx['GENERAL_HELP_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _help(self, interaction: Interaction) -> None:
        try:
            with open(get_os_path(f'assets/text/help-{conf["LANGUAGE"]}.md'), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                lines = '\n'.join(remove_nl(lines)).split('\n')
                
                chunks = [lines[i:i + 15] for i in range(0, len(lines), 15)]
                                
                embed = discord.Embed(
                    title=tx['GENERAL_HELP_TITLE'],
                    colour=Colour.YELLOW
                )
                
                embed.description = '\n'.join(chunks[0])
                
                view = Paginator(embed, chunks)

                await respond(interaction, message=embed, view=view)
        except FileNotFoundError:
            await respond(interaction, Colour.RED, tx['GENERAL_HELP_FILE_NOT_FOUND'])
        except Exception as e:
            log_exception(e)
    
    @app_commands.command(
        name=tx['GENERAL_TRANSLATE_NAME'],
        description=tx['GENERAL_TRANSLATE_DESC'])
    @app_commands.describe(from_lang=tx['GENERAL_TRANSLATE_FROM'])
    @app_commands.describe(to_lang=tx['GENERAL_TRANSLATE_TO'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _translate(self, interaction: Interaction, text: str=None, from_lang: str=None, to_lang: str='pt-br') -> None:
        if not text or not from_lang:
            return await respond(interaction, Colour.RED, tx['GENERAL_TRANSLATE_NO_TEXT_OR_LANG'])
        
        await interaction.response.defer()
        
        text = translate(text, from_lang, to_lang)
        
        await respond(interaction, Colour.YELLOW, text, response_type=1)

    @app_commands.command(
        name=tx['GENERAL_SPECS_NAME'],
        description=tx['GENERAL_SPECS_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _specs(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        specs = get_specs()
        embed = discord.Embed(title=tx['GENERAL_SPECS_TITLE'], color=Colour.BLUE)

        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)

        embed.add_field(name=tx['GENERAL_SPECS_SYSTEM'], value=specs['os'], inline=False)
        embed.add_field(name="CPU", value=specs['cpu'], inline=False)
        embed.add_field(name="RAM", value=specs['ram'], inline=False)
        embed.add_field(name="GPU", value=specs['gpu'], inline=False)
        
        try:
            embed.set_footer(text=tx['GENERAL_REQUESTED_BY'].format(
                user=interaction.user.global_name
            ), icon_url=interaction.user.avatar.url)
        except AttributeError:
            embed.set_footer(text=tx['GENERAL_REQUESTED_BY'].format(
                user=interaction.user.name
            ), icon_url=interaction.user.default_avatar.url)
        
        await respond(interaction, message=embed, response_type=1)
    
    @app_commands.command(
        name=tx['GENERAL_RININFO_NAME'],
        description=tx['GENERAL_RININFO_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _rininfo(self, interaction: Interaction) -> None:
        embed = discord.Embed(
            title=tx['GENERAL_RININFO_EMBED_TITLE'],
            colour=Colour.YELLOW
        )
        
        try:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        except AttributeError:
            embed.set_thumbnail(url=self.bot.user.default_avatar.url)
        
        embed.add_field(
            name=tx['GENERAL_RININFO_CREATED_IN'][0],
            value=tx['GENERAL_RININFO_CREATED_IN'][1]
        )
        embed.add_field(
            name=tx['GENERAL_RININFO_VERSION'],
            value=conf['VERSION']
        )
        embed.add_field(
            name=tx['GENERAL_RININFO_PROGRAMMER'][0],
            value=tx['GENERAL_RININFO_PROGRAMMER'][1]
        )
        embed.add_field(
            name=tx['GENERAL_RININFO_BUGFINDER'][0],
            value=tx['GENERAL_RININFO_BUGFINDER'][1]
        )
        embed.add_field(
            name=tx['GENERAL_RININFO_PY_VER'],
            value=platform.python_version()
        )
        
        try:
            embed.set_footer(text=tx['GENERAL_REQUESTED_BY'].format(
                user=interaction.user.global_name
            ), icon_url=interaction.user.avatar.url)
        except AttributeError:
            embed.set_footer(text=tx['GENERAL_REQUESTED_BY'].format(
                user=interaction.user.name
            ), icon_url=interaction.user.default_avatar.url)
        
        await respond(interaction, message=embed)
    
    @app_commands.command(
        name=tx['GENERAL_PING_NAME'],
        description=tx['GENERAL_PING_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _ping(self, interaction: Interaction) -> None:
        await respond(interaction, Colour.YELLOW, tx['GENERAL_PING_EMBED'].format(
            latency=round(self.bot.latency * 1000)
        ), " 🏓  Pong!")

    @app_commands.command(
        name=tx['GENERAL_PROFILE_NAME'],
        description=tx['GENERAL_PROFILE_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    @app_commands.choices(visibility=[
        app_commands.Choice(name="Public", value="Public"),
    ])

    async def choose(self, interaction: discord.Interaction, visibility: app_commands.Choice[str] = "Private") -> None:
        ephemeral = True if visibility == "Private" else False

        avatar_url = interaction.user.avatar.url or interaction.user.default_avatar.url

        response = requests.get(avatar_url)
        response.raise_for_status()

        # Initial images to layer on top of
        image = Image.open("rinbot/assets/images/profile/background.jpg").convert("RGBA")
        overlay = Image.open("rinbot/assets/images/profile/layer_1.png").convert("RGBA")

        image.paste(overlay, (0, 0), overlay)

        # Avatar image handling
        avatar = Image.open(BytesIO(response.content)).convert("RGBA").resize((125, 125), Image.Resampling.LANCZOS)

        width, height = avatar.size
        x = (width - height) // 2
        cropped_img = avatar.crop((x, 0, x + height, height))
        mask = Image.new("L", cropped_img.size)
        mask_draw = ImageDraw.Draw(mask)
        width, height = cropped_img.size
        mask_draw.ellipse((0, 0, width, height), fill = 255)

        cropped_img.putalpha(mask)

        image.paste(cropped_img, (131, 36), cropped_img)

        # Adding text to the image.
        picture = ImageDraw.Draw(image)

        fonts_dir = "rinbot/assets/fonts"

        regular = ImageFont.truetype(f"{fonts_dir}/gg-sans-regular.ttf", 15)
        #medium = ImageFont.truetype(f"{fonts_dir}/gg-sans-medium.ttf", 10)
        bold = ImageFont.truetype(f"{fonts_dir}/gg-sans-bold.ttf", 20)
        semi_bold = ImageFont.truetype(f"{fonts_dir}/gg-sans-semibold.ttf", 10)

        currency = await self.bot.db.getone(
            DBTable.CURRENCY, 
            DBColumns.currency.WALLET, 
            condition=f"""{DBColumns.currency.USER_ID} = {interaction.user.id} 
            AND {DBColumns.currency.GUILD_ID} = {interaction.guild.id}"""
            )

        picture.text((266, 25), interaction.user.display_name.upper(), fill = (255, 255, 255), anchor = "lm", font = bold)
        picture.text((287, 54), str(currency), fill = (255, 255, 255), anchor = "lm", font = regular)
        picture.text((590, 30), str(interaction.user.id), fill = (255, 255, 255), anchor = "rm", font = semi_bold)
        picture.text((590, 45), interaction.guild.name.upper(), fill = (255, 255, 255), anchor = "rm", font = semi_bold)

        buffer = BytesIO()
        image.save(buffer, format = "PNG")
        buffer.seek(0)

        await interaction.response.send_message(file=discord.File(buffer, filename = "image.png"), ephemeral = ephemeral)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(General(bot))
