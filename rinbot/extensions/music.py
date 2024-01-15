"""
#### RinBot's music command cog
- commands:
    * /play `Plays tracks from various sources on a voice channel`
    * /queue show `Shows the current song queue`
    * /queue clear `Clears the current song queue`
    * /nightcore `Toggles a nightcore effect on and off`
    * /recommended `Toggles the autoplay of recommended tracks on and off`
    * /shuffle `Shuffles the current queue`
    * /volume `Changes the player's volume`
    * /show_controls `Shows the multimedia controls view`
"""

# Imports
import discord, wavelink
from discord import Interaction
from discord import app_commands
from discord.ext.commands import Bot, Cog
from rinbot.base.interface import VideoSearchView, MediaControls
from rinbot.base.responder import respond
from rinbot.base.helpers import load_lang, format_exception, format_millsec
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.base.interface import Paginator
from typing import cast

# Load text
text = load_lang()

# "music" command cog
class Music(Cog, name="music"):
    def __init__(self, bot):
        self.bot:Bot = bot

    # Command groups
    queue_group = app_commands.Group(name=f"{text['MUSIC_QUEUE_GROUP_NAME']}", description=f"{text['MUSIC_QUEUE_GROUP_DESC']}")

    # Play music on the user's voice channel
    @app_commands.command(
        name=text['MUSIC_PLAY_NAME'],
        description=text['MUSIC_PLAY_DESC'])
    @app_commands.describe(track=text['MUSIC_PLAY_TRACK'])
    @not_blacklisted()
    async def _play_link(self, interaction:Interaction, track:str=None) -> None:
        if not track:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        
        # Search. Defaults to youtube for non URL based queries
        tracks:wavelink.Search = await wavelink.Playable.search(track,)
        if not tracks:
            return await respond(interaction, RED, message=f"{text['MUSIC_PLAY_NO_RESULTS']} `{track}`")
        
        # Summon player
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            except AttributeError:
                return await respond(interaction, RED, message=text['MUSIC_PLAY_NOT_CONNECTED'])
            except discord.ClientException:
                return await respond(interaction, RED, message=text['MUSIC_PLAY_UNABLE'])
            except Exception as e:
                return await respond(interaction, RED, title=text['ERROR'], message=f"`{format_exception(e)}`")

        # Custom player values
        player.selected = []
        player.nightcore = False

        # AutoPlay on partial by default
        player.autoplay = wavelink.AutoPlayMode.partial
        
        # Lock the player to this channel
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            return await respond(interaction, RED, message=f"{text['MUSIC_PLAY_LOCKED']} {player.home.mention}!")
        
        if isinstance(tracks, wavelink.Playlist):
            # tracks are a playlist...
            added:int = await player.queue.put_wait(tracks)
            await respond(interaction, PURPLE, message=f"{text['MUSIC_PLAY_ADDED'][0]} `{added}` {text['MUSIC_PLAY_ADDED'][1]} **{tracks.name}** {text['MUSIC_PLAY_ADDED'][2]}")
        else:
            if len(tracks) > 1:
                player.results = []
                view = VideoSearchView(tracks, player)
                await respond(interaction, PURPLE, message=f"{text['MUSIC_PLAY_SEARCH_RESULTS']} `{track}`:", view=view)
                await view.wait()
                if not player.results:
                    await player.disconnect()
                    return await respond(interaction, RED, message=text['MUSIC_PLAY_TIMEOUT'], response_type=1)
                for track in player.results:
                    await player.queue.put_wait(track)
            else:
                await respond(interaction, PURPLE, message=f"{text['MUSIC_PLAY_ADDED'][0]} `{tracks[0].title}` {text['MUSIC_PLAY_ADDED'][2]}")
                await player.queue.put_wait(tracks[0])
        
        if not player.playing:
            # Play now since we aren't doing anything
            await player.play(player.queue.get(), volume=100)
    
    # Shows the queue
    @queue_group.command(
        name=text['MUSIC_QUEUE_SHOW_NAME'],
        description=text['MUSIC_QUEUE_SHOW_DESC'])
    @not_blacklisted()
    async def _queue_show(self, interaction:Interaction) -> None:
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        queue = player.queue
        if len(queue) == 0:
            return await respond(interaction, RED, message=text['MUSIC_QUEUE_SHOW_EMPTY'])
        total = 0
        individual = []
        for i in queue:
            if i.length:
                total += i.length
                individual.append(format_millsec(i.length))
            else:
                individual.append("N/A")
        message = [f"**{i+1}.** `[{individual[i]}]` - {track.title}"
                for i, track in enumerate(queue)]
        message = "\n".join(message)
        if len(queue) > 15:
            lines = message.split("\n")
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed = discord.Embed(title=text['MUSIC_QUEUE_SHOW_CURRENT'], color=PURPLE)
            embed.description="\n".join(chunks[0])
            embed.set_footer(text=f"{text['MUSIC_QUEUE_SHOW_RUNTIME']} {format_millsec(total)}")
            view = Paginator(embed, chunks)
            await respond(interaction, message=embed, view=view)
        else:
            embed = discord.Embed(
                title=text['MUSIC_QUEUE_SHOW_CURRENT'],
                description=f"{message}", color=PURPLE)
            embed.set_footer(text=f"{text['MUSIC_QUEUE_SHOW_RUNTIME']} {format_millsec(total)}")
            await respond(interaction, message=embed)
    
    # Clears the queue
    @queue_group.command(
        name=text['MUSIC_QUEUE_CLEAR_NAME'],
        description=text['MUSIC_QUEUE_CLEAR_DESC'])
    @app_commands.describe(id=text['MUSIC_QUEUE_CLEAR_ID'])
    @not_blacklisted()
    async def _queue_clear(self, interaction:Interaction, id:str=None) -> None:
        if id:
            if not id.isnumeric():
                return await respond(interaction, RED, message=text['MUSIC_QUEUE_CLEAR_NO_NUM'])
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        queue = player.queue
        if len(queue) == 0:
            return await respond(interaction, RED, message=text['MUSIC_QUEUE_CLEAR_ALREADY'])
        try:
            track:wavelink.Playable = queue[int(id)-1]
            await queue.delete(int(id)-1)
            await respond(interaction, GREEN, message=f"{text['MUSIC_QUEUE_CLEAR_REMOVED'][0]} `{track.title}` {text['MUSIC_QUEUE_CLEAR_REMOVED'][1]}")
        except IndexError:
            await respond(interaction, RED, message=f"{text['MUSIC_QUEUE_CLEAR_INDEX_ERROR'][0]} `{id}` {text['MUSIC_QUEUE_CLEAR_INDEX_ERROR'][1]}")
    
    # Applies a nightcore filter to the song
    @app_commands.command(
        name=text['MUSIC_NIGHTCORE_NAME'],
        description=text['MUSIC_NIGHTCORE_DESC'])
    @not_blacklisted()
    async def _nightcore(self, interaction:Interaction) -> None:
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        if not player.nightcore:
            player.nightcore = True
            filters:wavelink.Filters = player.filters
            filters.timescale.set(pitch=1.5, speed=1.5, rate=1)
            await player.set_filters(filters)
            await respond(interaction, GREEN, message=text['MUSIC_NIGHTCORE_ACTIVE'])
        else:
            player.nightcore = False
            await player.set_filters()
            await respond(interaction, GREEN, message=text['MUSIC_NIGHTCORE_INNACTIVE'])
    
    # Toggles the recommended tracks feature on and off
    @app_commands.command(
        name=text['MUSIC_REC_NAME'],
        description=text['MUSIC_REC_DESC'])
    @not_blacklisted()
    async def _recommended(self, interaction:Interaction) -> None:
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        if player.autoplay.name == "partial":
            player.autoplay = wavelink.AutoPlayMode.enabled
            await respond(interaction, PURPLE, message=f"{text['MUSIC_REC_TOGGLE'][0]} {text['MUSIC_REC_TOGGLE'][1]}")
        elif player.autoplay.name == "enabled":
            player.autoplay = wavelink.AutoPlayMode.partial
            await respond(interaction, PURPLE, message=f"{text['MUSIC_REC_TOGGLE'][0]} {text['MUSIC_REC_TOGGLE'][1]}!")
    
    # Shuffles the current queue
    @app_commands.command(
        name=text['MUSIC_SHUFFLE_NAME'],
        description=text['MUSIC_SHUFFLE_DESC'])
    @not_blacklisted()
    async def _shuffle(self, interaction:Interaction) -> None:
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        player.queue.shuffle()
        await respond(interaction, PURPLE, message=text['MUSIC_SHUFFLE_SHUFFLED'])
    
    # Controls the player's volume
    @app_commands.command(
        name=text['MUSIC_VOLUME_NAME'],
        description=text['MUSIC_VOLUME_DESC'])
    @not_blacklisted()
    async def _volume(self, interaction:Interaction, volume:str=None) -> None:
        if not volume:
            return await respond(interaction, RED, message=f"{text['ERROR_INVALID_PARAMETERS']}")
        if not volume.isnumeric():
            return await respond(interaction, RED, message=text['MUSIC_VOLUME_INVALID'])
        if int(volume) < 0 or int(volume) > 100:
            return await respond(interaction, RED, message=text['MUSIC_VOLUME_INVALID'])
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        await player.set_volume(int(volume))
        await respond(interaction, GREEN, message=f"{text['MUSIC_VOLUME_CHANGED']} `{volume}`")

    # Shows a view with the multimedia controls
    @app_commands.command(
        name=text['MUSIC_SCT_NAME'],
        description=text['MUSIC_SCT_DESC'])
    @not_blacklisted()
    async def _show_ct(self, interaction:Interaction):
        player:wavelink.Player = cast(wavelink.Player, interaction.user.guild.voice_client)
        if not player:
            return await respond(interaction, RED, message=text['MUSIC_NO_PLAYERS'])
        
        await respond(interaction, view=MediaControls(player))

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Music(bot))