"""
Event handler cog
"""

import os
import asyncio
import discord
import platform
import wavelink

from discord.ext.commands import Cog
from discord import app_commands, Interaction
from datetime import datetime
from typing import TYPE_CHECKING
from gtts import gTTS

from .helpers import gen_random_string
from .get_os_path import get_os_path
from .colours import Colour
from .db import DBTable
from .exception_handler import log_exception
from .json_loader import get_conf, get_lang
from .logger import logger
from .responder import respond

if TYPE_CHECKING:
    from client import RinBot

conf = get_conf()
text = get_lang()
msg_count = {}
time_window_ms = 5000
max_msg_window = 5
author_msg_times = {}

HOURS = {text['HOURS']}
MINUTES = {text['MINUTES']}
SECONDS = {text['SECONDS']}
OWNER = {text['OWNER']}
ADMIN = {text['ADMIN']}

class EventHandler(Cog):
    def __init__(self, bot: "RinBot"):
        self.bot = bot
        self.bot.tree.error(coro=self.__dispatch_to_app_command_handler)
    
    async def __dispatch_to_app_command_handler(self, interaction: Interaction, error: app_commands.AppCommandError):
        self.bot.dispatch('app_command_error', interaction, error)
    
    @Cog.listener()
    async def on_ready(self):
        logger.info("--------------------------------------")
        logger.info(text['SPLASH_NAME'].format(ver=conf['VERSION']))
        logger.info("--------------------------------------")
        logger.info(text['SPLASH_LOGGED'].format(name=self.bot.user.name))
        logger.info(text['SPLASH_API_VER'].format(ver=discord.__version__))
        logger.info(text['SPLASH_PY_VER'].format(ver=platform.python_version()))
        logger.info(text['SPLASH_OS'].format(os=f"{platform.system()}-{platform.release()}"))
        logger.info("--------------------------------------")

        # Update db data
        await self.bot.db.check_all(self.bot)

        # Run tasks
        await self.bot.task_handler.start()

        # Sync command
        logger.info(text['SYNCHING_COMMANDS'])
        await self.bot.tree.sync()

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        logger.info(text['JOINED_GUILD'].format(guild=guild.name, guild_id=guild.id))
        await self.bot.db.check_all(self.bot)

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        logger.info(text['LEFT_GUILD'].format(guild=guild.name, guild_id=guild.id))
        await self.bot.db.check_all(self.bot)
    
    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.db.check_all(self.bot)

        query = await self.bot.db.get(DBTable.WELCOME_CHANNELS,
            condition=f"guild_id={member.guild.id}")

        if not query:
            return

        try:
            active = query[0][1]
            channel_id = query[0][2]
            custom_msg = query[0][3]
            
            if not channel_id:
                return

            channel: discord.TextChannel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

            if channel and active:
                embed = discord.Embed(
                    title=text['WELCOME_TITLE'].format(
                        member=member.name
                    ),
                    colour=Colour.YELLOW
                )

                if custom_msg:
                    embed.description = custom_msg

                await channel.send(embed=embed)
        except Exception as e:
            log_exception(e)

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass  # No use for this yet
    
    @Cog.listener()
    async def on_message(self, message: discord.Message):
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
            query = await self.bot.db.get(DBTable.TTS, condition=f'guild_id={message.guild.id}')
            
            if query and message.content and len(message.content) <= 100:
                if message.guild.id in self.bot.tts_clients.keys():
                    voice = self.bot.tts_clients[message.guild.id]
                    
                    active = query[0][1]
                    channel = query[0][2]
                    say_user = query[0][3]
                    language = query[0][4]
                    
                    if active == 1 and channel:
                        channel = self.bot.get_channel(channel) or await self.bot.fetch_channel(channel)
                        msg = message.content
                        
                        if say_user:
                            msg = f'{message.author.name}: ' + message.content
                        
                        tts = gTTS(text=msg, lang=language)
                        tts.save(get_os_path(f'../instance/tts/{message.guild.id}_{gen_random_string(8)}.mp4'))
                
                    for audio in os.listdir(get_os_path(f'../instance/tts')):
                        # Prevent playing TTS files from other guilds
                        if str(message.guild.id) not in audio:
                            continue
                        
                        audio_path = os.path.join(get_os_path('../instance/tts'), audio)
                        
                        voice.play(discord.FFmpegPCMAudio(audio_path))
                        
                        while voice.is_playing():
                            await asyncio.sleep(0.5)
                        
                        os.remove(audio_path)
            
            # Currency
            query = await self.bot.db.get(DBTable.CURRENCY,
                condition=f"guild_id={message.guild.id} AND user_id={message.author.id}"
            )

            if not query:
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
                    from_msg_event=True
                )
        except AttributeError:
            pass
        except Exception as e:
            log_exception(e)
    
    @Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logger.info(
            text['WAVELINK_NODE_CONNECTED'].format(
                node=payload.node,
                resumed=payload.resumed,
                session=payload.session_id
            )
        )
    
    @Cog.listener()
    async def on_app_command_error(self, interaction: Interaction, error) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)

            seconds = round(seconds)
            minutes = round(minutes)
            hours = round(hours % 24)

            message=text['COMMAND_ON_COOLDOWN'].format(
                time=f"{f'{hours} {HOURS}' if hours > 0 else ''} {f'{minutes} {MINUTES}' if minutes > 0 else ''} {f'{seconds} {SECONDS}' if seconds > 0 else ''}."
            )

            await respond(
                interaction,
                message=message,
                colour=Colour.RED,
                hidden=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            message=text['USER_NO_PERMS'].format(
                perms=", ".join(error.missing_permissions)
            )

            await respond(
                interaction,
                message=message,
                colour=Colour.RED,
                hidden=True
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = text['BOT_NO_PERMS'].format(
                perms=", ".join(error.missing_permissions)
            )

            await respond(
                interaction,
                message=message,
                colour=Colour.RED,
                hidden=True
            )
        else:
            try:
                raise error
            except Exception as e:
                log_exception(e)
