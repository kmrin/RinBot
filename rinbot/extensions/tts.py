"""
RinBot's tts command cog
- Commands:
    * /tts connect `Connects to your channel`
    * /tts disconnect `Disconnects from your channel`
    * /tts channel `Sets the text channel to read from`
    * /tts language `Sets the language of the TTS voice`
    * /tts say-user `If the TTS should say the user's name or not`
    * /tts active `Enable or disable TTS`
"""

from discord import app_commands, Interaction
from discord.ext.commands import Cog

from rinbot.base import log_exception
from rinbot.base import respond
from rinbot.base import DBTable
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import text

# from rinbot.base import is_admin
# from rinbot.base import is_owner
from rinbot.base import not_blacklisted

class TTS(Cog, name='tts'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        
        self.languages = [
            "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs",
            "bg", "ca", "ceb", "ny", "zh-cn", "zh-tw", "co", "hr", "cs",
            "da", "nl", "en", "eo", "et", "tl", "fi", "fr", "fy", "gl",
            "ka", "de", "el", "gu", "ht", "ha", "haw", "iw", "hi", "hmn",
            "hu", "is", "ig", "id", "ga", "it", "ja", "jw", "kn", "kk",
            "km", "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt", "lb",
            "mk", "mg", "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne",
            "no", "or", "ps", "fa", "pl", "pt", "pt-br", "pa", "ro", "ru", 
            "sm", "gd", "sr", "st", "sn", "sd", "si", "sk", "sl", "so",
            "es", "su", "sw", "sv", "tg", "ta", "tt", "te", "th", "tr", 
            "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu"
        ]
    
    tts_group = app_commands.Group(name=text['TTS_NAME'], description=text['TTS_DESC'])
    
    @tts_group.command(
        name=text['TTS_CONNECT_NAME'],
        description=text['TTS_CONNECT_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_connect(self, interaction: Interaction):
        try:
            if not interaction.user.voice:
                return await respond(interaction, Colour.RED, text['TTS_CONNECT_NOT_IN_VOICE'])
            
            if interaction.user.voice.channel:
                if interaction.guild.id in self.bot.tts_clients.keys() or interaction.guild.id in self.bot.music_clients.keys():
                    return await respond(interaction, Colour.RED, text['TTS_CONNECT_BOT_BUSY'])
                
            voice = await interaction.user.voice.channel.connect()
            self.bot.tts_clients[interaction.guild.id] = voice
            
            await respond(interaction, Colour.GREEN, text['TTS_CONNECT_SUCCESS'])
        except Exception as e:
            log_exception(e)
    
    @tts_group.command(
        name=text['TTS_DISCONNECT_NAME'],
        description=text['TTS_DISCONNECT_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_disconnect(self, interaction: Interaction):
        try:
            if interaction.guild.id not in self.bot.tts_clients.keys():
                return await respond(interaction, Colour.RED, text['TTS_DISCONNECT_NOT_CONNECTED'])
            
            voice = self.bot.tts_clients[interaction.guild.id]
            await voice.disconnect()
            del self.bot.tts_clients[interaction.guild.id]
            
            await respond(interaction, Colour.GREEN, text['TTS_DISCONNECT_SUCCESS'])
        except Exception as e:
            log_exception(e)
    
    @tts_group.command(
        name=text['TTS_CHANNEL_NAME'],
        description=text['TTS_CHANNEL_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_channel(self, interaction: Interaction):
        try:            
            data = {
                'active': 1,
                'channel_id': interaction.channel.id
            }
            
            await self.bot.db.update(DBTable.TTS, data, f'guild_id={interaction.guild.id}')
            
            await respond(interaction, Colour.GREEN, text['TTS_CHANNEL_SET'])
        except Exception as e:
            log_exception(e)
    
    @tts_group.command(
        name=text['TTS_LANGUAGE_NAME'],
        description=text['TTS_LANGUAGE_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_language(self, interaction: Interaction, lang: str):
        try:
            if lang not in self.languages:
                return await respond(interaction, Colour.RED, text['TTS_LANGUAGE_INVALID'])
            
            data = {
                'language': lang
            }
            
            await self.bot.db.update(DBTable.TTS, data, f'guild_id={interaction.guild.id}')
            
            await respond(interaction, Colour.GREEN, text['TTS_LANGUAGE_SET'].format(lang=lang))
        except Exception as e:
            log_exception(e)
    
    @tts_group.command(
        name=text['TTS_SAY_USER_NAME'],
        description=text['TTS_SAY_USER_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_say_user(self, interaction: Interaction):
        try:
            tts = await self.bot.db.get(DBTable.TTS, f'guild_id={interaction.guild.id}')
            
            new_state = 1 if tts[0][3] == 0 else 0
            
            data = {
                'say_user': new_state
            }
            
            await self.bot.db.update(DBTable.TTS, data, f'guild_id={interaction.guild.id}')
            await respond(interaction, Colour.GREEN, f'{text["TTS_SAY_USER_TOGGLED"][2]} {text["TTS_SAY_USER_TOGGLED"][new_state]}')
        except Exception as e:
            log_exception(e)
    
    @tts_group.command(
        name=text['TTS_ACTIVE_NAME'],
        description=text['TTS_ACTIVE_DESC'])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _tts_active(self, interaction: Interaction):
        try:
            tts = await self.bot.db.get(DBTable.TTS, f'guild_id={interaction.guild.id}')
            
            new_state = 1 if tts[0][1] == 0 else 0
            
            if new_state == 0 and interaction.guild.id in self.bot.tts_clients.keys():
                voice = self.bot.tts_clients[interaction.guild.id]
                await voice.disconnect()
                del self.bot.tts_clients[interaction.guild.id]
            
            data = {
                'active': new_state
            }
            
            await self.bot.db.update(DBTable.TTS, data, f'guild_id={interaction.guild.id}')
            await respond(interaction, Colour.GREEN, f'{text["TTS_ACTIVE_TOGGLED"][2]} {text["TTS_ACTIVE_TOGGLED"][new_state]}')
        except Exception as e:
            log_exception(e)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(TTS(bot))
