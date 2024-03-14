"""
#### RinBot's event handler cog
"""

import os, asyncio, discord, platform, wavelink
from discord import app_commands
from datetime import datetime
from discord.ext.commands import Cog
from rinbot.base.helpers import load_config, load_lang, millisec_to_str
from rinbot.base.interface import MediaControls
from rinbot.base.errors import Exceptions as E
from rinbot.base.logger import logger
from rinbot.base.colors import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rinbot.base.client import RinBot

config = load_config()
text = load_lang()
message_count = {}
time_window_milliseconds = 5000
max_msg_per_window = 5
author_msg_times = {}

HOURS = {text['HOURS']}
MINUTES = {text['MINUTES']}
SECONDS = {text['SECONDS']}
OWNER = {text['OWNER']}
ADMIN = {text['ADMIN']}

class EventHandler(Cog):
    def __init__(self, bot: "RinBot"):
        self.bot = bot
        bot.tree.error(coro=self.__dispatch_to_app_command_handler)
        
    async def __dispatch_to_app_command_handler(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        self.bot.dispatch("app_command_error", interaction, error)
    
    @Cog.listener()
    async def on_ready(self):
        logger.info("--------------------------------------")
        logger.info(f"  > {config['VER']}")
        logger.info("--------------------------------------")
        logger.info(f" {text['INIT_SPLASH_LOGGED_AS']} {self.bot.user.name}")
        logger.info(f" {text['INIT_SPLASH_API_VER']} {discord.__version__}")
        logger.info(f" {text['INIT_SPLASH_PY_VER']} {platform.python_version()}")
        logger.info(f" {text['INIT_SPLASH_RUNNING_ON']} {platform.system()}-{platform.release()} ({os.name})")
        logger.info("--------------------------------------")

        # Update db data
        await self.bot.db.check_economy()
        await self.bot.db.check_guilds()
        await self.bot.db.check_valorant()

        # Run tasks
        await self.bot.task_handler.start()

        # Sync commands
        logger.info(text["INIT_SYNCHING_COMMANDS"])
        await self.bot.tree.sync()
    
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        logger.info(f"{text['INIT_JOINED_GUILD']} '{guild.name}'! ID: {guild.id}")
        await self.bot.db.check_guilds()

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        logger.info(f"{text['INIT_LEFT_GUILD']} '{guild.name}'. ID: {guild.id}")

        joined = await self.bot.db.get("guilds")

        if str(guild.id) in joined:
            joined.remove(str(guild.id))

        update = await self.bot.db.update("guilds", joined)
        if update:
            logger.info(text['INIT_REMOVED_GUILD'])
        else:
            logger.error(text['INIT_ERROR_REMOVING_GUILD'])
    
    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_channels = await self.bot.db.get("welcome_channels")

        if str(member.guild.id) in welcome_channels.keys():
            channel_id = int(welcome_channels[str(member.guild.id)]["channel_id"])
            channel: discord.TextChannel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            is_active = welcome_channels[str(member.guild.id)]["active"]
            custom_msg = welcome_channels[str(member.guild.id)]["custom_message"]

            if channel and is_active:
                embed = discord.Embed(
                    title=f"{text['INIT_NEW_MEMBER_TITLE'][0]} {member.name}{text['INIT_NEW_MEMBER_TITLE'][1]}")
                if custom_msg:
                    embed.description = f"{custom_msg}"

                await channel.send(embed=embed)
    
    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass  # Got no use for this yet but it's here

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.author.bot:
            return

        try:
            global author_msg_times

            aid = message.author.id
            ct = datetime.now().timestamp() * 1000
            et = ct - time_window_milliseconds

            if not author_msg_times.get(aid, False):
                author_msg_times[aid] = []

            em = [mt for mt in author_msg_times[aid] if mt < et]

            for mt in em:
                author_msg_times[aid].remove(mt)

            if not len(author_msg_times[aid]) > max_msg_per_window:

                # Update user message count and reward after 30 messages
                currency = await self.bot.db.get("currency")
                user_data = currency[str(message.guild.id)][str(message.author.id)]

                user_data["messages"] += 1

                if user_data["messages"] >= 50:
                    user_data["wallet"] += 25
                    user_data["messages"] = 0

                currency[str(message.guild.id)][str(message.author.id)] = user_data

                await self.bot.db.update("currency", currency, from_msg=True)
        except AttributeError:
            pass

    @Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"{text['INIT_COMM_ERROR_DELAY']} {f'{round(hours)} {HOURS}' if round(hours) > 0 else ''} {f'{round(minutes)} {MINUTES}' if round(minutes) > 0 else ''} {f'{round(seconds)} {SECONDS}' if round(seconds) > 0 else ''}.",
                color=0xE02B2B, )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, E.UserBlacklisted):
            embed = discord.Embed(
                description=f"{text['INIT_BLOCKED']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_COMM_GUILD']} {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_BLOCKED']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_BLOCKED']}")
        elif isinstance(error, E.UserNotOwner):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_OWNER']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        elif isinstance(error, E.UserNotAdmin):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_ADMIN']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        elif isinstance(error, E.UserNotInGuild):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_IN_GUILD']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed)
        elif isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                description=f"{text['INIT_USER_NO_PERMS_1']}"
                            + ", ".join(error.missing_permissions)
                            + f"{text['INIT_USER_NO_PERMS_2']}",
                color=0xE02B2B, )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed = discord.Embed(
                description=f"{text['INIT_BOT_NO_PERMS_1']}"
                            + ", ".join(error.missing_permissions)
                            + f"{text['INIT_BOT_NO_PERMS_2']}",
                color=0xE02B2B, )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error

    @Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logger.info(f"{text['INIT_WAVELINK_NODE_CONNECTED'][0]} {payload.node} | {text['INIT_WAVELINK_NODE_CONNECTED'][1]} {payload.resumed} | {text['INIT_WAVELINK_NODE_CONNECTED'][2]} {payload.session_id}")

    @Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        logger.info(
            f"{text['INIT_WAVELINK_TRACK_STARTED'][0]} {payload.track.title} | {text['INIT_WAVELINK_TRACK_STARTED'][1]} {payload.player.guild.name} ({payload.player.guild.id})")

        player: wavelink.Player | None = payload.player
        if not player: return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        # Now Playing embed
        embed = discord.Embed(title=text['INIT_WAVELINK_NOW_PLAYING'][0], color=PURPLE)
        embed.description = f"```{track.title}```"
        embed.set_footer(text=f"{text['INIT_WAVELINK_NOW_PLAYING'][1]} {track.author}")

        if track.artwork:
            embed.set_image(url=track.artwork)
        if track.length:
            embed.set_footer(
                text=f"{embed.footer.text} | {text['INIT_WAVELINK_NOW_PLAYING'][2]} {millisec_to_str(track.length)}")
        if original and original.recommended:
            embed.set_footer(text=f"{embed.footer.text} | {text['INIT_WAVELINK_NOW_PLAYING'][3]} {track.source}")

        # Media controls view
        view = MediaControls(player)
        if track.uri:
            view.add_item(
                discord.ui.Button(
                    label=" 🔗  Link", style=discord.ButtonStyle.link, url=track.uri))

        await player.home.send(embed=embed, view=view)

    @Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

        logger.info(
            f"{text['INIT_WAVELINK_TRACK_ENDED'][0]} {payload.track.title} | {text['INIT_WAVELINK_TRACK_ENDED'][1]} {player.guild.name} ({player.guild.id})")

        if len(player.queue) == 0 and not player.autoplay.name == "enabled":
            embed = discord.Embed(
                description=text['INIT_WAVELINK_DISCONNECTING'], color=YELLOW)
            await asyncio.sleep(2)
            await player.home.send(embed=embed)
            await player.disconnect()
            player.cleanup()
        elif len(player.queue) == 0 and payload.track.source == "soundcloud" and player.autoplay.name == "enabled":
            embed = discord.Embed(
                description=text['INIT_WAVELINK_DISCONNECTING_SC'], color=RED)
            await asyncio.sleep(2)
            await player.home.send(embed=embed)
            await player.disconnect()
            player.cleanup()
    
    @Cog.listener("on_app_command_error")
    async def get_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = discord.Embed(
                description=f"{text['INIT_COMM_ERROR_DELAY']} {f'{round(hours)} {HOURS}' if round(hours) > 0 else ''} {f'{round(minutes)} {MINUTES}' if round(minutes) > 0 else ''} {f'{round(seconds)} {SECONDS}' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, E.UserBlacklisted):
            embed = discord.Embed(
                description=f"{text['INIT_BLOCKED']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_COMM_GUILD']} {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_BLOCKED']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_BLOCKED']}")
        elif isinstance(error, E.UserNotOwner):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_OWNER']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        elif isinstance(error, E.UserNotAdmin):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_ADMIN']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if interaction.guild:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
            else:
                logger.warning(
                    f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        elif isinstance(error, E.UserNotInGuild):
            embed = discord.Embed(
                description=f"{text['INIT_NOT_IN_GUILD']}", color=0xE02B2B)
            await interaction.response.send_message(embed=embed)
        elif isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                description=f"{text['INIT_USER_NO_PERMS_1']}"
                + ", ".join(error.missing_permissions)
                + f"{text['INIT_USER_NO_PERMS_2']}",
                color=0xE02B2B,)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed = discord.Embed(
                description=f"{text['INIT_BOT_NO_PERMS_1']}"
                + ", ".join(error.missing_permissions)
                + f"{text['INIT_BOT_NO_PERMS_2']}",
                color=0xE02B2B,)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            raise error