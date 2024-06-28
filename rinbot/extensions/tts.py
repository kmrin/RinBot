"""
RinBot's tts command cog
- Commands:
    * /tts connect    - Connects and enables TTS
    * /tts disconnect - Disconnects and disables TTS
"""

from nextcord import Interaction, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog

from rinbot.core import RinBot
from rinbot.core import TTSClient
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted, is_guild
from rinbot.core import respond

class TTS(Cog, name='tts'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.tts_languages = [
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
    
    # /tts
    @slash_command(
        name=get_localized_string('en-GB', 'TTS_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'TTS_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_ROOT_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _tts_root(self, interaction: Interaction) -> None:
        pass
    
    # /tts connect
    @_tts_root.subcommand(
        name=get_localized_string('en-GB', 'TTS_CONNECT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_CONNECT_NAME')
        },
        description=get_localized_string('en-GB', 'TTS_CONNECT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_CONNECT_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _tts_connect(
        self, interaction: Interaction,
        lang: str = SlashOption(
            name=get_localized_string('en-GB', 'TTS_LANG_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'TTS_LANG_NAME')
            },
            description=get_localized_string('en-GB', 'TTS_LANG_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'TTS_LANG_DESC')
            },
            required=True
        ),
        blame: int = SlashOption(
            name=get_localized_string('en-GB', 'TTS_BLAME_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'TTS_BLAME_NAME')
            },
            description=get_localized_string('en-GB', 'TTS_BLAME_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'TTS_BLAME_DESC')
            },
            required=False,
            default=0,
            choices={
                'Yes': 1,
                'No': 0
            },
            choice_localizations={
                'Yes': {
                    Locale.pt_BR: 'Sim'
                },
                'No': {
                    Locale.pt_BR: 'Não'
                }
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if lang.lower() not in self.tts_languages:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'GENERAL_TRANSLATE_INVALID',
                    lang=lang
                ),
                hidden = True
            )
        
        if not interaction.user.voice:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'USER_NOT_IN_VOICE'
                ),
                hidden = True
            )
        
        if interaction.user.voice.channel:
            if interaction.guild.id in self.bot.tts_clients.keys():
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'VOICE_BUSY_TTS'
                    ),
                    hidden = True
                )
            if interaction.guild.id in self.bot.music_clients.keys():
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        locale, 'VOICE_BUSY_MUSIC'
                    ),
                    hidden = True
                )
        
        client = TTSClient(
            channel=interaction.channel,
            client=await interaction.user.voice.channel.connect(),
            language=lang,
            blame=blame
        )
        
        await client.client.guild.change_voice_state(
            channel=client.client.channel, self_mute=False, self_deaf=True
        )
        
        self.bot.tts_clients[interaction.guild.id] = client
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'TTS_CONNECT_SUCCESS'
            )
        )
    
    # /tts disconnect
    @_tts_root.subcommand(
        name=get_localized_string('en-GB', 'TTS_DC_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_DC_NAME')
        },
        description=get_localized_string('en-GB', 'TTS_DC_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'TTS_DC_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _tts_disconnect(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.tts_clients.keys():
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'TTS_DC_NOT_CONNECTED'
                ),
                hidden = True
            )
        
        voice = self.bot.tts_clients[interaction.guild.id].client
        await voice.disconnect()
        del self.bot.tts_clients[interaction.guild.id]
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'TTS_DC_SUCCESS'
            )
        )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(TTS(bot))
