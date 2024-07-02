"""
RinBot's music command cog
- Commands:
    * /play                      - Plays songs through URLs or search queries
    * /queue show                - Shows the current song queue
    * /queue skip                - Shows the current song queue and allows you to choose and skip to a specific track
    * /queue clear               - Shows the current song queue and allows you to choose and remove tracks from it
    * /queue shuffle             - Shuffles the current song queue
    * /recommend                 - Toggles on and off the auto-filling of the song queue
    * /nightcore                 - Toggles on and off a nightcore effect
    * /controls                  - Shows the multimedia controls
    * /favourite tracks show     - Shows your favourite tracks
    * /favourite tracks add      - Adds a track to your favourite tracks
    * /favourite tracks edit     - Shows your favourite tracks and allows you to choose and remove them
    * /favourite tracks play     - Plays one or more of your favourite tracks
    * /favourite playlists show  - Shows your favourite playlists
    * /favourite playlists add   - Adds a playlist to your favourite playlists
    * /favourite playlists edit  - Shows your favourite playlists and allows you to choose and remove them
    * /favourite playlists play  - Plays one or more of your favourite playlists
"""

import asyncio
import nextlink

from nextcord import Interaction, Embed, Colour, Locale, SlashOption, slash_command
from nextcord.ext.commands import Cog
from typing import List

from rinbot.core import RinBot
from rinbot.core import Loggers
from rinbot.core import VideoSearchViewMode, QueueEditViewMode
from rinbot.core import ResponseType
from rinbot.core import DBTable
from rinbot.core import Track, Playlist
from rinbot.core import VideoSearchView, MediaControls, Paginator, QueueEditView, FavouritesEditView, FavouritesPlayView
from rinbot.core import log_exception
from rinbot.core import is_url, ms_to_str
from rinbot.core import get_localized_string, get_interaction_locale
from rinbot.core import not_blacklisted, is_guild
from rinbot.core import respond

from rinbot.music.player import Player
from rinbot.music.search import search_video, search_playlist

logger = Loggers.EXTENSIONS

class Music(Cog, name='music'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    @Cog.listener()
    async def on_wavelink_track_start(self, payload: nextlink.TrackStartEventPayload) -> None:
        player: Player = payload.player
        if not player:
            return
        
        logger.info(
            f'Wavelink track started: {payload.track.title} at {payload.player.guild.name} (ID: {payload.player.guild.id})'
        )
        
        original: nextlink.Playable | None = payload.original
        track: nextlink.Playable = payload.track
        
        embed = Embed(
            title=get_localized_string(
                player.locale, 'MUSIC_NOW_PLAYING'
            ),
            description=f'`{track.title}`',
            colour=Colour.purple()
        )
        
        embed.set_footer(
            text=get_localized_string(
                player.locale, 'MUSIC_FOOTER_AUTHOR',
                author=track.author
            )
        )
        
        if track.artwork:
            embed.set_image(url=track.artwork)
        if track.length:
            embed.set_footer(
                text=f'{embed.footer.text} | {get_localized_string(player.locale, "MUSIC_FOOTER_LENGTH",  length=ms_to_str(track.length))}'
            )
        
        if original and original.recommended:
            embed.set_footer(
                text=f'{embed.footer.text} | {get_localized_string(player.locale, "MUSIC_FOOTER_RECOMMENDED", source=track.source)}'
            )
        
        view = MediaControls(player)
        
        if track.uri:
            view.show_url_button(track.uri)
        
        player.last_message = await player.home.send(embed=embed, view=view)
    
    @Cog.listener()
    async def on_wavelink_track_end(self, payload: nextlink.TrackEndEventPayload) -> None:
        player: Player | None = payload.player
        if not player:
            return
        
        logger.info(
            f'Wavelink track ended: {payload.track.title} at {payload.player.guild.name} (ID: {payload.player.guild.id})'
        )
        
        old_embed = player.last_message.embeds[0]
        new_embed = Embed(
            title=get_localized_string(
                player.locale, 'MUSIC_PLAYED',
            ),
            description=old_embed.description,
            colour=old_embed.colour
        )
        if old_embed.image:
            new_embed.set_thumbnail(old_embed.image.url)
        
        await player.last_message.edit(embed=new_embed, view=None)
        
        if not player.from_previous_interaction:
            player.history.append(payload.track)
        
        player.from_previous_interaction = False
        
        if not player.playing and len(player.queue) <= 0 and not player.autoplay.name == 'enabled':
            await asyncio.sleep(5)
            
            embed = Embed(
                description=get_localized_string(
                    player.locale, 'MUSIC_DISCONNECT_MESSAGE'
                ),
                colour=Colour.purple()
            )
            
            await player.home.send(embed=embed)
            
            await player.dc()
    
    # /play
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_PLAY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_PLAY_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_PLAY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_PLAY_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _play(
        self, interaction: Interaction,
        track: str = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_PLAY_TRACK_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_PLAY_TRACK_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_PLAY_TRACK_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_PLAY_TRACK_DESC'
                )
            },
            required=True,
            min_length=1,
            max_length=100
        ),
        search_for_playlist: int = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_PLAY_PL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_PLAY_PL_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_PLAY_PL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_PLAY_PL_DESC'
                )
            },
            required=False,
            default=0,
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            }
        )
    ) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        guild_id = interaction.guild.id
        through_view = False
        is_playlist = False
        playlist_msg = ''
        playables: List[nextlink.Playable] = []
        
        # Check user voice state
        if not interaction.user.voice:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_USER_NOT_IN_VOICE'
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )
        
        # Permission check
        voice_channel = interaction.user.voice.channel
        permissions = voice_channel.permissions_for(interaction.guild.me)
        
        if not permissions.connect and not permissions.speak:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_CHANNEL_PERMS'
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )
        
        """ # Get player
        if guild_id in self.bot.music_clients:
            player = self.bot.music_clients[guild_id]
        else:
            player = await interaction.user.voice.channel.connect(
                cls=Player(self.bot, locale, interaction.channel)
            )
            self.bot.music_clients[guild_id] = player """
        
        # Get player
        try:
            player = self.bot.music_clients.get(guild_id)
            if not player:
                player = await voice_channel.connect(
                    cls=Player(self.bot, locale, interaction.channel)
                )
                self.bot.music_clients[guild_id] = player
        except Exception as e:
            log_exception(e, logger)
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_GET_PLAYER_ERROR'
                ),
                hidden=True,
                resp_type=ResponseType.FOLLOWUP
            )
        
        # If it's a URL
        if is_url(track):
            results = await nextlink.Playable.search(track,)
            
            if isinstance(results, nextlink.tracks.Playlist):
                is_playlist = True
                
                for playable in results.tracks:
                    playables.append(playable)
                
                playlist_msg = get_localized_string(
                    locale, 'MUSIC_PLAY_ADDED_FROM_PL',
                    count=len(results.tracks),
                    name=results.name
                )
            
            else:
                if results:
                    playables.append(results[0])
        
        # If it's a search query
        else:
            through_view = True
            
            # Get Track objects
            if search_for_playlist == 0:
                query = await search_video(locale, track)
            else:
                query = await search_playlist(locale, track)
            
            # If it returns an Embed, it errored out
            if isinstance(query, Embed):
                return await respond(interaction, message=query, hidden=True)

            view = VideoSearchView(
                locale,
                query,
                VideoSearchViewMode.TRACK_MODE if search_for_playlist == 0 else VideoSearchViewMode.PLAYLIST_MODE
            )

            await respond(
                interaction, outside_content=get_localized_string(
                    locale, 'MUSIC_PLAY_SEARCH_RESULTS',
                    track=track
                ),
                view=view,
                resp_type=ResponseType.FOLLOWUP
            )
            
            wait = await view.wait()
            if wait:
                if not player.playing and len(player.queue) <= 0:
                    await player.dc()
                
                embed = Embed(
                    description=get_localized_string(
                        locale, 'MUSIC_PLAY_TIMEOUT'
                    ),
                    colour=Colour.yellow()
                )
                
                return await interaction.edit_original_message(embed=embed, view=None)

            
            for result in view.user_choices:
                playables.append(result)
        
        if not through_view and is_playlist:
            await respond(interaction, Colour.green(), playlist_msg, resp_type=ResponseType.FOLLOWUP)
        
        # Add tracks to player and begin playback
        for playable in playables:
            await player.queue.put_wait(playable)
            
            if not through_view and not is_playlist:
                await respond(
                    interaction, Colour.green(),
                    get_localized_string(
                        locale, 'MUSIC_PLAY_ADDED',
                        title=playable.title
                    ),
                    resp_type=ResponseType.FOLLOWUP
                )
            
            if not player.playing:
                await player.play(player.queue.get(), volume=100)

    # /queue (root)
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_QUEUE_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_ROOT_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_QUEUE_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_ROOT_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _queue(self, interaction: Interaction) -> None:
        pass
    
    # /queue show
    @_queue.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_QUEUE_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SHOW_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_QUEUE_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SHOW_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _queue_show(
        self, interaction: Interaction,
        urls: int = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_QUEUE_SHOW_URL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_QUEUE_SHOW_URL_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_QUEUE_SHOW_URL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_QUEUE_SHOW_URL_DESC'
                )
            },
            required=False,
            default=0,
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        queue = player.queue
        
        if len(queue) <= 0:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_QUEUE_EMPTY'
                ),
                hidden=True
            )
        
        total = 0
        individual = []
        
        for track in queue:
            if track.length:
                total += track.length
                individual.append(ms_to_str(track.length))
            else:
                individual.append('N/A')
        
        message = [
            f'**{i+1}.** `{individual[i]}` - {track.title if urls == 0 else track.uri}'
            for i, track in enumerate(queue)
        ]
        message = '\n'.join(message)
        
        embed = Embed(
            title=get_localized_string(
                locale, 'MUSIC_CURRENT_QUEUE'
            ),
            colour=Colour.purple()
        )
        embed.set_footer(text=get_localized_string(
            locale, 'MUSIC_QUEUE_RUNTIME',
            total=ms_to_str(total)
        ))
        
        if len(queue) > 15:
            lines = message.split('\n')
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed.description='\n'.join(chunks[0])
            view = Paginator(embed, chunks)
            
            return await respond(interaction, message=embed, view=view)
        
        embed.description = message
        await respond(interaction, message=embed)
    
    # /queue skip
    @_queue.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_QUEUE_SKIP_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SKIP_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_QUEUE_SKIP_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SKIP_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _queue_skip(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        queue = player.queue
        
        if len(queue) <= 0:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_QUEUE_EMPTY'
                ),
                hidden=True
            )
        
        view = QueueEditView(locale, player, QueueEditViewMode.SKIP)
        await interaction.response.send_message(view=view)
    
    # /queue clear
    @_queue.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_QUEUE_CLEAR_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_CLEAR_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_QUEUE_CLEAR_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_CLEAR_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _queue_clear(
        self, interaction: Interaction,
        total: int = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_QUEUE_CLEAR_FULL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_QUEUE_CLEAR_FULL_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_QUEUE_CLEAR_FULL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_QUEUE_CLEAR_FULL_DESC'
                )
            },
            required=False,
            default=0,
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            }
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        queue = player.queue
        
        if len(queue) <= 0:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_QUEUE_EMPTY'
                ),
                hidden=True
            )
        
        if total == 1:
            player.queue.clear()
            
            return await respond(
                interaction, Colour.green(),
                get_localized_string(
                    locale, 'MUSIC_QUEUE_CLEARED'
                )
            )
        
        view = QueueEditView(locale, player, QueueEditViewMode.REMOVE)
        await interaction.response.send_message(view=view)
    
    # /queue shuffle
    @_queue.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_QUEUE_SHUFFLE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SHUFFLE_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_QUEUE_SHUFFLE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_QUEUE_SHUFFLE_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _queue_shuffle(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                )
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        
        if len(player.queue) <= 0:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_QUEUE_EMPTY'
                ),
                hidden=True
            )
        
        player.queue.shuffle()
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MUSIC_QUEUE_SHUFFLED'
            )
        )
    
    # /recommend
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_RECOMMEND_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_RECOMMEND_NAME')
        },
        description=get_localized_string('en-GB', 'MUSIC_RECOMMEND_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_RECOMMEND_DESC')
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _recommend(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        
        if player.autoplay.name == 'partial':
            player.autoplay = nextlink.AutoPlayMode.enabled

            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'MUSIC_RECOMMEND_ON'
                )
            )
        elif player.autoplay.name == 'enabled':
            player.autoplay = nextlink.AutoPlayMode.partial
            
            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'MUSIC_RECOMMEND_OFF'
                )
            )
    
    # /nightcore
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_NIGHTCORE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_NIGHTCORE_NAME')
        },
        description=get_localized_string('en-GB', 'MUSIC_NIGHTCORE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_NIGHTCORE_DESC')
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _nightcore(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        
        if player.nightcore:
            player.nightcore = False
            
            await player.set_filters()
            
            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'MUSIC_NIGHTCORE_OFF'
                )
            )
        else:
            player.nightcore = True
            
            filters: nextlink.Filters = player.filters
            filters.timescale.set(pitch=1.3, speed=1.3, rate=1)
            
            await player.set_filters(filters)
            
            await respond(
                interaction, Colour.purple(),
                get_localized_string(
                    locale, 'MUSIC_NIGHTCORE_ON'
                )
            )
    
    # /controls
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_CONTROLS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_CONTROLS_NAME')
        },
        description=get_localized_string('en-GB', 'MUSIC_CONTROLS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MUSIC_CONTROLS_DESC')
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _controls(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        if interaction.guild.id not in self.bot.music_clients:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_PLAYERS'
                ),
                hidden=True
            )
        
        player = self.bot.music_clients[interaction.guild.id]
        await player.last_message.edit(view=None)
        
        view = MediaControls(player)
        await respond(interaction, view=view)

    # /favourite
    @slash_command(
        name=get_localized_string('en-GB', 'MUSIC_FAV_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites(self, interaction: Interaction) -> None:
        pass
    
    # /favourite tracks
    @_favourites.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_tracks(self, interaction: Interaction) -> None:
        pass
    
    # /favourite tracks show
    @_favourites_tracks.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_SHOW_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_SHOW_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_tracks_show(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        favourites = await self.bot.db.get(
            DBTable.FAV_TRACKS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_TRACKS_EMPTY'
                )
            )
        
        message = [
            f'**{i+1}.** `{item[3]}` - {item[1]}'
            for i, item in enumerate(favourites)
        ]
        message = '\n'.join(message)
        
        embed = Embed(
            title=get_localized_string(
                locale, 'MUSIC_FAV_TRACKS_FAVES'
            ),
            colour=Colour.purple()
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        
        if len(favourites) > 15:
            lines = message.split('\n')
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed.description='\n'.join(chunks[0])
            view = Paginator(embed, chunks)
            
            return await respond(interaction, message=embed, view=view)
        
        embed.description = message
        await respond(interaction, message=embed)

    # /favourite tracks add
    @_favourites_tracks.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_ADD_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_ADD_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_tracks_add(
        self, interaction: Interaction,
        url: str = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_URL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_FAV_TRACKS_URL_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_URL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_FAV_TRACKS_URL_DESC'
                )
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if not is_url(url):
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_INVALID_URL'
                )
            )
        
        results = await nextlink.Playable.search(url,)
        
        if isinstance(results, nextlink.tracks.Playlist):
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_LINK_IS_PLAYLIST'
                )
            )
        
        if not results:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_RESULTS_FROM_URL'
                )
            )
        
        exists = await self.bot.db.get(DBTable.FAV_TRACKS, f'user_id={interaction.user.id} AND url="{url}"')
        if exists:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_TRACK_EXISTS',
                    title=results[0].title
                )
            )
        
        data = {
            'user_id': interaction.user.id,
            'title': results[0].title,
            'url': results[0].uri,
            'duration': ms_to_str(results[0].length),
            'uploader': results[0].author
        }
        
        await self.bot.db.put(DBTable.FAV_TRACKS, data)
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MUSIC_FAV_ADDED',
                title=data['title']
            )
        )
    
    # /favourite tracks edit
    @_favourites_tracks.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_EDIT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_EDIT_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_EDIT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_EDIT_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_tracks_edit(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        favourites = await self.bot.db.get(
            DBTable.FAV_TRACKS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_TRACKS_EMPTY'
                )
            )
        
        view = FavouritesEditView(self.bot, locale, favourites, VideoSearchViewMode.TRACK_MODE)
        await interaction.response.send_message(view=view)
    
    # /favourite tracks play
    @_favourites_tracks.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_PLAY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_PLAY_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_TRACKS_PLAY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_TRACKS_PLAY_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_tracks_play(self, interaction: Interaction) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        guild_id = interaction.guild.id
        favourite_tracks: List[Track] = []
        playables: List[nextlink.Playable] = []
        
        favourites = await self.bot.db.get(
            DBTable.FAV_TRACKS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_TRACKS_EMPTY'
                ),
                resp_type=ResponseType.FOLLOWUP,
                hidden=True
            )
        
        # Check user voice state
        if not interaction.user.voice:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_USER_NOT_IN_VOICE'
                ),
                resp_type=ResponseType.FOLLOWUP,
                hidden=True
            )
        
        # Convert favourites into Track objects
        for favourite in favourites:
            track = Track(
                title=favourite[1],
                url=favourite[2],
                duration=favourite[3],
                uploader=favourite[4]
            )
            
            favourite_tracks.append(track)
        
        # Get player
        if guild_id in self.bot.music_clients:
            player = self.bot.music_clients[guild_id]
        else:
            player = await interaction.user.voice.channel.connect(
                cls=Player(self.bot, locale, interaction.channel)
            )
            self.bot.music_clients[guild_id] = player
        
        view = FavouritesPlayView(self.bot, locale, favourite_tracks, VideoSearchViewMode.TRACK_MODE)
        
        await respond(
            interaction, outside_content=get_localized_string(
                locale, 'MUSIC_FAV_CHOOSE'
            ),
            view=view,
            resp_type=ResponseType.FOLLOWUP
        )
        
        wait = await view.wait()
        if wait:
            if not player.playing and len(player.queue) <= 0:
                await player.dc()
            
            embed = Embed(
                description=get_localized_string(
                    locale, 'MUSIC_PLAY_TIMEOUT'
                ),
                colour=Colour.yellow()
            )
            
            return await interaction.edit_original_message(embed=embed, view=None)
        
        for result in view.user_choices:
            playables.append(result)
        
        for playable in playables:
            await player.queue.put_wait(playable)
            
            if not player.playing:
                await player.play(player.queue.get(), volume=100)
    
    # /favourite playlists
    @_favourites.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_PL_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_PL_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_pl(self, interaction: Interaction) -> None:
        pass
    
    # /favourite playlists show
    @_favourites_pl.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_PL_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_SHOW_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_PL_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_SHOW_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_pl_show(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        favourites = await self.bot.db.get(
            DBTable.FAV_PLAYLISTS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_PL_EMPTY'
                )
            )
        
        message = [
            get_localized_string(
                locale, 'MUSIC_FAV_PL_SHOW_MSG',
                index=i+1,
                count=item[3],
                title=item[1]
            )
            for i, item in enumerate(favourites)
        ]
        message = '\n'.join(message)
        
        embed = Embed(
            title=get_localized_string(
                locale, 'MUSIC_FAV_PL_FAVES'
            ),
            colour=Colour.purple()
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        
        if len(favourites) > 15:
            lines = message.split('\n')
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed.description='\n'.join(chunks[0])
            view = Paginator(embed, chunks)
            
            return await respond(interaction, message=embed, view=view)
        
        embed.description = message
        await respond(interaction, message=embed)

    # /favourite playlists add
    @_favourites_pl.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_PL_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_ADD_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_PL_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_ADD_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_pl_add(
        self, interaction: Interaction,
        url: str = SlashOption(
            name=get_localized_string('en-GB', 'MUSIC_FAV_PL_URL_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_FAV_PL_URL_NAME'
                )
            },
            description=get_localized_string('en-GB', 'MUSIC_FAV_PL_URL_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string(
                    'pt-BR', 'MUSIC_FAV_PL_URL_DESC'
                )
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if not is_url(url):
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_INVALID_URL'
                )
            )
        
        results = await nextlink.Playable.search(url,)
        
        if not isinstance(results, nextlink.tracks.Playlist):
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_LINK_IS_NOT_PLAYLIST'
                )
            )
        
        if not results:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_NO_RESULTS_FROM_URL'
                )
            )
        
        exists = await self.bot.db.get(DBTable.FAV_PLAYLISTS, f'user_id={interaction.user.id} AND url="{url}"')
        if exists:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_PL_EXISTS',
                    title=results.name
                )
            )
        
        data = {
            'user_id': interaction.user.id,
            'title': results.name,
            'url': results.url,
            'count': len(results.tracks),
            'uploader': results.author
        }
        
        await self.bot.db.put(DBTable.FAV_PLAYLISTS, data)
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MUSIC_FAV_ADDED',
                title=results.name
            )
        )
    
    # /favourite playlists edit
    @_favourites_pl.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_PL_EDIT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_EDIT_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_PL_EDIT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_EDIT_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_pl_edit(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        favourites = await self.bot.db.get(
            DBTable.FAV_PLAYLISTS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_PL_EMPTY'
                )
            )
        
        view = FavouritesEditView(self.bot, locale, favourites, VideoSearchViewMode.PLAYLIST_MODE)
        await interaction.response.send_message(view=view)

    # /favourite playlists play
    @_favourites_pl.subcommand(
        name=get_localized_string('en-GB', 'MUSIC_FAV_PL_PLAY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_PLAY_NAME'
            )
        },
        description=get_localized_string('en-GB', 'MUSIC_FAV_PL_PLAY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string(
                'pt-BR', 'MUSIC_FAV_PL_PLAY_DESC'
            )
        }
    )
    @not_blacklisted()
    @is_guild()
    async def _favourites_pl_play(self, interaction: Interaction) -> None:
        await interaction.response.defer(with_message=True)
        
        locale = get_interaction_locale(interaction)
        guild_id = interaction.guild.id
        playables: List[nextlink.Playable] = []
        favourites_list: List[Playlist] = []
        favourites = await self.bot.db.get(
            DBTable.FAV_PLAYLISTS, f'user_id={interaction.user.id}'
        )
        
        if not favourites:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_FAV_PL_EMPTY'
                )
            )
        
        # Check user voice state
        if not interaction.user.voice:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MUSIC_USER_NOT_IN_VOICE'
                ),
                resp_type=ResponseType.FOLLOWUP
            )
        
        # Convert favourites into a list of Playlist objects
        for favourite in favourites:
            playlist = Playlist(
                title=favourite[1],
                url=favourite[2],
                count=favourite[3],
                uploader=favourite[4]
            )
            
            favourites_list.append(playlist)
        
        # Get player
        if guild_id in self.bot.music_clients:
            player = self.bot.music_clients[guild_id]
        else:
            player = await interaction.user.voice.channel.connect(
                cls=Player(self.bot, locale, interaction.channel)
            )
            self.bot.music_clients[guild_id] = player
        
        view = FavouritesPlayView(self.bot, locale, favourites_list, VideoSearchViewMode.PLAYLIST_MODE)
        
        await respond(
            interaction, outside_content=get_localized_string(
                locale, 'MUSIC_FAV_CHOOSE'
            ),
            view=view,
            resp_type=ResponseType.FOLLOWUP
        )
        
        wait = await view.wait()
        if wait:
            if not player.playing and len(player.queue) <= 0:
                await player.dc()
            
            embed = Embed(
                description=get_localized_string(
                    locale, 'MUSIC_PLAY_TIMEOUT'
                ),
                colour=Colour.yellow()
            )
            
            return await interaction.edit_original_message(embed=embed, view=None)
        
        for result in view.user_choices:
            playables.append(result)
        
        for playable in playables:
            await player.queue.put_wait(playable)
            
            if not player.playing:
                await player.play(player.queue.get(), volume=100)

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Music(bot))
