import os
import asyncio
import nextcord
import platform
import nextlink

from nextcord.ext.application_checks import ApplicationBotMissingPermissions, ApplicationMissingPermissions
from nextcord.ext.commands import Cog
from nextcord.colour import Colour
from nextcord import Interaction
from datetime import datetime
from typing import TYPE_CHECKING
from gtts import gTTS

from .helpers import get_random_string, get_localized_string, get_interaction_locale, hex_to_colour
from .paths import get_os_path
from .db import DBTable
from .loggers import Loggers, log_exception
from .json_manager import get_conf
from .responder import respond

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.EVENTS
conf = get_conf()
msg_count = {}
time_window_ms = 5000
max_msg_window = 5
author_msg_times = {}

class EventHandler(Cog):
    def __init__(self, bot: 'RinBot'):
        self.bot = bot
    
    @Cog.listener()
    async def on_ready(self) -> None:
        logger.info("--------------------------------------")
        logger.info(f' > RinBot {conf["VERSION"]}')
        logger.info("--------------------------------------")
        logger.info(f' > Logged in as: {self.bot.user.name}')
        logger.info(f' > Nextcord version: {nextcord.__version__}')
        logger.info(f' > Python ver: {platform.python_version()}')
        logger.info(f' > Running on: {platform.system()}-{platform.release()}')
        logger.info("--------------------------------------")
        
        # Connect to lavalink server
        nodes = [
            nextlink.Node(
                uri=conf['LAVALINK_ENDPOINT'],
                password=conf['LAVALINK_PASSWORD']
            )
        ]
        
        await nextlink.Pool.connect(nodes=nodes, client=self.bot)
        
        # Update db data
        await self.bot.db.check_all(self.bot)
        
        # Run tasks
        await self.bot.task_handler.start()
        
        # Sync commands
        logger.info('Synching commands globally')
        await self.bot.sync_all_application_commands()
        
        # Sync commands to testing guild
        if conf['TESTING_GUILDS']:
            msg = 'Synching commands to testing guild'
            
            for guild_id in conf['TESTING_GUILDS']:
                try:
                    guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
                except nextcord.errors.NotFound:
                    return
                
                if guild:
                    msg += f" '{guild.name}' (ID: {guild.id})"
                
                logger.info(msg)
                
                await self.bot.sync_application_commands(guild_id=guild_id)
    
    @Cog.listener()
    async def on_wavelink_node_ready(self, payload: nextlink.NodeReadyEventPayload) -> None:
        logger.info(f'Wavelink node ready [Node: {payload.node} | Res.: {payload.resumed} | S. ID: {payload.session_id}]')
    
    @Cog.listener()
    async def on_guild_join(self, guild: nextcord.Guild) -> None:
        logger.info(f"Joined guild '{guild.name}' (ID: {guild.id})")
        await self.bot.db.check_all(self.bot)
    
    @Cog.listener()
    async def on_guild_remove(self, guild: nextcord.Guild) -> None:
        logger.info(f"Left guild '{guild.name}' (ID: {guild.id})")
        await self.bot.db.check_all(self.bot)
    
    @Cog.listener()
    async def on_member_join(self, member: nextcord.Member) -> None:
        await self.bot.db.check_all(self.bot)
        
        query = await self.bot.db.get(
            DBTable.WELCOME_CHANNELS,
            f'guild_id={member.guild.id}')
        
        if not query:
            return
        
        active = query[0][1]
        channel_id = query[0][2]
        title: str = query[0][3]
        description: str = query[0][4]
        colour = query[0][5]
        show_pfp = query[0][6]
        
        if not channel_id:
            return
        
        channel: nextcord.TextChannel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
        
        if channel and active == 1:
            # Edit title
            if '<username>' in title:
                title = title.replace('<username>', member.name)
            
            # Edit description
            if title and '<username>' in description:
                description = description.replace('<username>', member.name)
            elif description and '<mention>' in description:
                description = description.replace('<mention>', member.mention)
            
            embed = nextcord.Embed(
                title=title,
                colour=hex_to_colour(colour)
            )
            
            if description:
                embed.description = description
            if show_pfp == 1:
                embed.set_thumbnail(
                    member.avatar.url if member.avatar else member.default_avatar.url
                )
            
            await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_member_remove(self, member: nextcord.Member):
        pass  # No use for this yet

    @Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author == self.bot.user or message.author.bot:
            return
        
        if not message.guild:
            return
        
        try:
            global author_msg_times
            
            aid = message.author.id
            ct = datetime.now().timestamp() * 1000
            et = ct - time_window_ms

            if not author_msg_times.get(aid, False):
                author_msg_times[aid] = []

            em = [mt for mt in author_msg_times[aid] if mt < et]

            for mt in em:
                author_msg_times[aid].remove(mt)

            # Only do any action if user isn't spaming
            if len(author_msg_times[aid]) > max_msg_window:
                return
            
            # TTS
            if message.content and len(message.content) <= 100:
                if message.guild.id in self.bot.tts_clients.keys():
                    tts_client = self.bot.tts_clients[message.guild.id]
                    
                    msg = message.content
                    if tts_client.blame == 1:
                        msg = f'{message.author.name}: ' + message.content
                    
                    tts = gTTS(text=msg, lang=tts_client.language)
                    tts.save(get_os_path(f'../instance/tts/{message.guild.id}_{get_random_string(8)}.mp4'))
                
                for audio in os.listdir(get_os_path(f'../instance/tts')):
                    # Prevent playing TTSs from other guilds
                    if str(message.guild.id) not in audio:
                        continue
                    
                    audio_path = os.path.join(get_os_path('../instance/tts'), audio)
                    tts_client.client.play(nextcord.FFmpegPCMAudio(audio_path))
                    
                    while tts_client.client.is_playing():
                        await asyncio.sleep(0.5)
                    
                    os.remove(audio_path)
            
            # Currency
            query = await self.bot.db.get(
                DBTable.CURRENCY,
                f"guild_id={message.guild.id} AND user_id={message.author.id}", silent=True
            )

            if query:
                wallet = query[0][2]
                messages = query[0][3]

                messages += 1

                if messages >= 30:
                    wallet += 25
                    messages = 0

                await self.bot.db.update(
                    table=DBTable.CURRENCY,
                    data={"wallet": wallet, "messages": messages},
                    condition=f"guild_id={message.guild.id} AND user_id={message.author.id}",
                    silent=True
                )
        except AttributeError:
            pass
        except Exception as e:
            log_exception(e)
    
    @Cog.listener()
    async def on_voice_state_update(self, member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState) -> None:
        # If it's not us, don't care
        if member.id != self.bot.user.id:
            return
        
        # Was I here before?
        if before.channel is None:
            return
        
        # Am I still here?
        if after.channel:
            for member in after.channel.members:
                if member.id == self.bot.user.id:
                    return
        
        guild = before.channel.guild
        logger.warning(f'I got manually disconnected from a voice channel at {guild.name} (ID: {guild.id})')
        
        # Delete voice clients
        if guild.id in self.bot.tts_clients.keys():
            del self.bot.tts_clients[guild.id]
            logger.info('Closed a TTS client that was active there')
        elif guild.id in self.bot.music_clients.keys():
            del self.bot.music_clients[guild.id]
            logger.info('Closed a Music client that was active there')
    
    @Cog.listener()
    async def on_wavelink_node_ready(self, payload: nextlink.NodeReadyEventPayload) -> None:
        logger.info(
            f'Wavelink node connected [Node: {payload.node} | Res.: {payload.resumed} | S. ID: {payload.session_id}]'
        )

    @Cog.listener()
    async def on_application_command_completion(self, interaction: Interaction) -> None:
        command = interaction.application_command.name
        
        guild = interaction.guild.name if interaction.guild else 'DMs'
        guild_id = interaction.guild.id if interaction.guild else None
        user = interaction.user.name
        user_id = interaction.user.id
        
        msg = (
            f"Command '/{command}' executed in '{guild}' "
            f"(ID: {guild_id}) by '{user}' (ID: {user_id})"
        )
        
        logger.info(msg)

    @Cog.listener()
    async def on_application_command_error(self, interaction: Interaction, error: Exception) -> None:
        if isinstance(error, ApplicationMissingPermissions):
            locale = get_interaction_locale(interaction)
            
            await respond(
                interaction,
                Colour.red(),
                get_localized_string(locale, 'EVENTS_COMMAND_MISSING_PERMS', perms=", ".join(error.missing_permissions)),
                hidden=True
            )
        
        elif isinstance(error, ApplicationBotMissingPermissions):
            locale = get_interaction_locale(interaction)
            
            await respond(
                interaction,
                Colour.red(),
                get_localized_string(locale, 'EVENTS_COMMAND_BOT_MISSING_PERMS', perms=", ".join(error.missing_permissions)),
                hidden=True
            )
        
        else:
            try:
                raise error
            except Exception as e:
                log_exception(e)
