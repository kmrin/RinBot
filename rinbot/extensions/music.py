"""
RinBot's music command cog
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

import asyncio
import discord
import wavelink

from typing import cast
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext.commands import Cog

from rinbot.music.player import Player
from rinbot.music.search import search_video, search_playlist

from rinbot.base import MediaControls, VideoSearchView, Paginator
from rinbot.base import log_exception
from rinbot.base import translate
from rinbot.base import ms_to_str
from rinbot.base import respond
from rinbot.base import is_url
from rinbot.base import Colour
from rinbot.base import RinBot
from rinbot.base import logger
from rinbot.base import conf
from rinbot.base import text

# from rinbot.base import is_owner
# from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Music(Cog, name="music"):
    def __init__(self, bot: RinBot):
        self.bot = bot
    
    @Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        logger.info(text['MUSIC_WAVELINK_TRACK_STARTED'].format(
            title=payload.track.title, guild=payload.player.guild.name
        ))
        
        try:
            player: Player | None = payload.player
            if not player:
                return
            
            original: wavelink.Playable | None = payload.original
            track: wavelink.Playable = payload.track
            
            embed = discord.Embed(title=text['MUSIC_WAVELINK_NOW_PLAYING'][0], colour=Colour.PURPLE)
            embed.description = f'```{track.title}```'
            embed.set_footer(text=text['MUSIC_WAVELINK_NOW_PLAYING'][1].format(author=track.author))
            
            if track.artwork:
                embed.set_image(url=track.artwork)
            if track.length:
                embed.set_footer(
                    text=f'{embed.footer.text} | {text["MUSIC_WAVELINK_NOW_PLAYING"][2].format(length=ms_to_str(track.length))}'
                )
            
            if original and original.recommended:
                embed.set_footer(
                    text=f'{embed.footer.text} | {text["MUSIC_WAVELINK_NOW_PLAYING"][3].format(source=track.source)}'
                )
            
            view = MediaControls(player)
            if track.uri:
                view.add_item(
                    discord.ui.Button(
                        label=" 🔗  Link", style=discord.ButtonStyle.link, url=track.uri
                    )
                )
            
            await player.home.send(embed=embed, view=view)
        except Exception as e:
            log_exception(e)
    
    @Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        try:
            player: Player | None = payload.player
            
            if not player:
                return
            
            logger.info(
                text['MUSIC_WAVELINK_TRACK_ENDED'].format(
                    title=payload.track.title, guild=payload.player.guild.name
                )
            )
            
            if len(player.queue) == 0 and not player.autoplay.name == 'enabled':
                embed = discord.Embed(
                    description=text['MUSIC_WAVELINK_DISCONNECTING'], colour=Colour.YELLOW)
                
                await asyncio.sleep(2)
                await player.home.send(embed=embed)
                await player.disconnect()
                
                player.cleanup()
            elif len(player.queue) == 0 and payload.track.source == 'soundcloud' and player.autoplay.name == 'enabled':
                embed = discord.Embed(
                    description=text['MUSIC_WAVELINK_DISCONNECTING_SC'], colour=Colour.RED)
                
                await asyncio.sleep(2)
                await player.home.send(embed=embed)
                await player.disconnect()
                
                player.cleanup()
        except Exception as e:
            log_exception(e)
    
    queue_group = app_commands.Group(name=text['MUSIC_QUEUE_NAME'], description=text['MUSIC_QUEUE_DESC'])
    
    @app_commands.command(
        name=text['MUSIC_PLAY_NAME'],
        description=text['MUSIC_PLAY_DESC'])
    @app_commands.describe(track=text['MUSIC_PLAY_TRACK'])
    @app_commands.describe(search_for_playlist=text['MUSIC_PLAY_SEARCH_FOR_PLAYLIST'])
    @app_commands.choices(search_for_playlist=[Choice(name=text['YES'], value=1)])
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _play_single(self, interaction: Interaction, track: str, search_for_playlist: Choice[int]=0) -> None:
        try:
            if interaction.guild.id in self.bot.tts_clients.keys():
                return await respond(interaction, Colour.RED, text['MUSIC_PLAY_TTS_ACTIVE'])
            
            if interaction.guild.id in self.bot.music_clients.keys():
                return await respond(interaction, Colour.RED, text['MUSIC_PLAY_PLAYER_ACTIVE'])
            
            playables = []
            through_view = False
            
            player: Player = cast(Player, interaction.user.guild.voice_client)
            
            if not player:
                try:
                    player = await interaction.user.voice.channel.connect(cls=Player)
                    self.bot.music_clients[interaction.guild.id] = player
                except AttributeError:
                    return await respond(interaction, Colour.RED, text['MUSIC_PLAY_NOT_CONNECTED'])
                except Exception as e:
                    log_exception(e)
                    return
            
            player.autoplay = wavelink.AutoPlayMode.partial

            if not player.home:
                player.home = interaction.channel
            elif player.home != interaction.channel:
                return await respond(interaction, Colour.RED, text['MUSIC_PLAY_LOCKED'].format(channel=player.home.mention))
            
            if is_url(track):
                playable: wavelink.Search = await wavelink.Playable.search(track,)
                if playable:
                    playables.append(playable)
            else:
                through_view = True
                                
                if search_for_playlist == 0:
                    query = await search_video(track)
                else:
                    query = await search_playlist(track)
                
                if isinstance(query, discord.Embed):
                    return await respond(interaction, message=query)
            
                await interaction.response.defer()
                            
                view = VideoSearchView(query)
                
                await respond(
                    interaction,
                    Colour.PURPLE,
                    text['MUSIC_PLAY_RESULTS'].format(
                        search=track
                    ),
                    view=view,
                    response_type=1
                )
                await view.wait()
                
                if not view.result:
                    embed = discord.Embed(
                        description=text['MUSIC_PLAY_TIMEOUT'],
                        colour=Colour.RED
                    )
                    
                    player.home = None
                    await player.disconnect()
                    
                    return await interaction.edit_original_response(content=None, embed=embed, view=None)
                
                for result in view.result:
                    playable: wavelink.Search = await wavelink.Playable.search(result['url'])
                    if playable:
                        playables.append(playable)
            
            for playable in playables:
                if isinstance(playable, wavelink.Playlist):
                    added: int = await player.queue.put_wait(playable)
                    
                    await respond(interaction, Colour.PURPLE, text['MUSIC_PLAY_ADDED_PL'].format(
                        added=added, name=playable.name))
                    
                    continue  
                  
                await player.queue.put_wait(playable)
                
                if not through_view:
                    await respond(interaction, Colour.PURPLE, text['MUSIC_PLAY_ADDED'].format(
                        added=playable[0].title
                    ))
            
                if not player.playing:
                    await player.play(player.queue.get(), volume=100)
            
            through_view = False
        except wavelink.exceptions.QueueEmpty:
            player.home = None
            await player.disconnect()
            await respond(interaction, Colour.RED, text['MUSIC_PLAY_NO_TRACKS_ADDED'])
        except wavelink.exceptions.LavalinkLoadException as e:
            log_exception(e)
            player.home = None
            await player.disconnect()
            error = translate(e.error, 'en', conf['LANGUAGE'])
            await respond(interaction, Colour.RED, text['MUSIC_PLAY_LOAD_ERROR'].format(e=error))
        except Exception as e:
            log_exception(e)
    
    @queue_group.command(
        name=text['MUSIC_QUEUE_SHOW_NAME'],
        description=text['MUSIC_QUEUE_SHOW_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _queue_show(self, interaction: Interaction) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, text['MUSIC_NO_PLAYERS'])
        
        queue = player.queue
        
        if len(queue) == 0:
            return await respond(interaction, Colour.RED, text['MUSIC_QUEUE_SHOW_EMPTY'])
        
        total = 0
        individual = []
        
        for i in queue:
            if i.length:
                total += i.length
                individual.append(ms_to_str(i.length))
            else:
                individual.append('N/A')
        
        message = [f'**{i+1}.** `{individual[i]}` - {track.title}'
                   for i, track in enumerate(queue)]
        message = '\n'.join(message)
        
        if len(queue) > 15:
            lines = message.split('\n')
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed = discord.Embed(title=text['MUSIC_QUEUE_SHOW_CURRENT'], colour=Colour.PURPLE)
            embed.description='\n'.join(chunks[0])
            embed.set_footer(text=text['MUSIC_QUEUE_SHOW_RUNTIME'].format(runtime=ms_to_str(total)))
            view = Paginator(embed, chunks)
            await respond(interaction, message=embed, view=view)
        else:
            embed = discord.Embed(
                title=text['MUSIC_QUEUE_SHOW_CURRENT'],
                description=message,
                colour=Colour.PURPLE
            )
            embed.set_footer(text=text['MUSIC_QUEUE_SHOW_RUNTIME'].format(runtime=ms_to_str(total)))
            await respond(interaction, message=embed)
    
    @queue_group.command(
        name=text['MUSIC_QUEUE_CLEAR_NAME'],
        description=text['MUSIC_QUEUE_CLEAR_DESC'])
    @app_commands.describe(id=text['MUSIC_QUEUE_CLEAR_ID'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _queue_clear(self, interaction: Interaction, id: int=None) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, text['MUSIC_NO_PLAYERS'])
        
        queue = player.queue
        
        if len(queue) == 0:
            return await respond(interaction, Colour.RED, text['MUSIC_QUEUE_CLEAR_ALREADY'])
        
        try:
            if id:
                track: wavelink.Playable = queue[id - 1]
                queue.delete(id - 1)
                await respond(
                    interaction, Colour.GREEN, text['MUSIC_QUEUE_CLEAR_REMOVED'].format(track=track.title)
                )
            else:
                queue.clear()
                await respond(interaction, Colour.GREEN, text['MUSIC_QUEUE_CLEAR_CLEARED'])
        except IndexError:
            await respond(interaction, Colour.RED, text['MUSIC_QUEUE_CLEAR_INDEX_ERROR'].format(id=id))

    @app_commands.command(
        name=text['MUSIC_NIGHTCORE_NAME'],
        description=text['MUSIC_NIGHTCORE_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _nightcore(self, interaction: Interaction) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, message=text['MUSIC_NO_PLAYERS'])
        
        if not player.nightcore:
            player.nightcore = True
            
            filters: wavelink.Filters = player.filters
            filters.timescale.set(pitch=1.3, speed=1.3, rate=1)
            
            await player.set_filters(filters)
            await respond(interaction, Colour.GREEN, text['MUSIC_NIGHTCORE_ACTIVE'])
        else:
            player.nightcore = False
            
            filters: wavelink.Filters = player.filters
            
            await player.set_filters()
            
            await respond(interaction, Colour.GREEN, text['MUSIC_NIGHTCORE_INACTIVE'])

    @app_commands.command(
        name=text['MUSIC_REC_NAME'],
        description=text['MUSIC_REC_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _recommended(self, interaction: Interaction) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, text['MUSIC_NO_PLAYERS'])
        
        if player.autoplay.name == 'partial':
            player.autoplay = wavelink.AutoPlayMode.enabled
            await respond(interaction, Colour.GREEN, f"{text['MUSIC_REC_TOGGLE'][0]} {text['MUSIC_REC_TOGGLE'][1]}")
        elif player.autoplay.name == "enabled":
            player.autoplay = wavelink.AutoPlayMode.partial
            await respond(interaction, Colour.GREEN, f"{text['MUSIC_REC_TOGGLE'][0]} {text['MUSIC_REC_TOGGLE'][2]}!")
    
    @app_commands.command(
        name=text['MUSIC_SHUFFLE_NAME'],
        description=text['MUSIC_SHUFFLE_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _shuffle(self, interaction: Interaction) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, text['MUSIC_NO_PLAYERS'])
        
        player.queue.shuffle()
        
        await respond(interaction, Colour.GREEN, text['MUSIC_SHUFFLE_SHUFFLED'])
    
    @app_commands.command(
        name=text['MUSIC_VOLUME_NAME'],
        description=text['MUSIC_VOLUME_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _volume(self, interaction: Interaction, volume: app_commands.Range[int, 0, 100]) -> None:
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, text['MUSIC_NO_PLAYERS'])
        
        await player.set_volume(volume)
        await respond(interaction, Colour.GREEN, text['MUSIC_VOLUME_CHANGED'].format(vol=volume))
    
    @app_commands.command(
        name=text['MUSIC_SCT_NAME'],
        description=text['MUSIC_SCT_DESC'])
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _show_ct(self, interaction: Interaction):
        player: Player = cast(Player, interaction.user.guild.voice_client)
        
        if not player:
            return await respond(interaction, Colour.RED, message=text['MUSIC_NO_PLAYERS'])
        
        await respond(interaction, view=MediaControls(player))

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Music(bot))
