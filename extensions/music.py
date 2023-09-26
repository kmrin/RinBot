"""
RinBot v1.4.3 (GitHub release)
made by rin
"""

# Imports
import discord, re, urllib, yt_dlp, asyncio, urllib.parse, random, platform
from collections import deque
from discord import app_commands
from discord.utils import get
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.is_url import is_url
from program.checks import *

# Initial variable values
song_queue = deque()
max_history_lenght = 50
current_vc = None
is_paused = False
is_playing = False
is_playlist = False
current_playlist = ''
current_playlist_title = ''
items_added = 0
playlist_index = 0
playlist_count = 0
playlist_available = True
initial_playlist_message_shown = False
manual_dc = False
is_shuffling = 0
from_next = False
shuffle_list = []
query_selected = 0
start_from = 0

# Try to load history cache file, generates an empty one if none are found
try:
    with open('cache/song_history.json', 'r', encoding='utf-8') as f:
        song_history = json.load(f)
except FileNotFoundError:
    song_history = []

# Youtube-DL and FFMPEG CLI options
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': 'in_playlist',
    'nocheckcertificate': True,
    'ignoreerrors': True}
ffmpeg_opts = {
    'options': '-vn -b:a 128k',  # 128kbps bitrate
    'executable':
        
        # Use included ffmpeg executable if on windows
        './ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg',
    
    # Theses options make sure ffmpeg doesn't piss itself on unstable connections
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

# 'Music' command cog
class Music(commands.Cog, name='music'):
    def __init__(self, bot):
        self.bot = bot

    # General multimedia funcions
    async def pause(self, ctx: Context):
        global is_paused
        client = ctx.voice_client
        if client and client.is_playing() and not is_paused:
            client.pause()
            is_paused = True
    async def resume(self, ctx: Context):
        global is_paused
        client = ctx.voice_client
        if client and client.is_paused() and is_paused:
            client.resume()
            is_paused = False
    async def skip(self, ctx: Context):
        client = ctx.voice_client
        if client and client.is_playing():
            client.stop()
        else:
            embed = discord.Embed(
                description=" ❌ No songs being played.",
                color=0xd81313)
            await ctx.send(embed=embed)
    
    # Changes the status depending on if a song is being played or not
    async def updateStatus(self, playing:bool):
        if not playing:
            await self.bot.change_presence(
                status=discord.Status.online, activity=discord.Game("Available! ✅"))
        else:
            await self.bot.change_presence(
                status=discord.Status.online, activity=discord.Game("Kinda busy! ❌"))
    
    # Formats time in seconds to HH:MM
    async def formatTime(self, time:int):
        m, s = time // 60, time % 60
        time = f"{m:02d}:{s:02d}"
        return time
    
    # Removes duplicate items from a list
    async def removeListDuplicates(self, list):
        nodupe = []
        for i in list:
            if i not in nodupe:
                nodupe.append(i)
        return nodupe
    
    # Selects a song from history, returns it's URL and deletes it
    async def pickFromHistory(self, entry:int):
        global song_history
        try:
            song = song_history[entry - 1]['url']
            song_history.remove(song_history[entry -1])  # Remove item to prevent dupes
            await self.updateHistoryCache(song_history)  # Update history with new data
            return song
        
        # If there are errors, return an embed, error treatment will be done on the "play" function
        except IndexError:
            embed = discord.Embed(
                title=' ❌ Error',
                description=f"Item not found in history. {entry} out of range.",
                color=0xD81313)
            return embed
    
    # Does a youtube search query and returns the first 4 results
    async def processYoutubeSearch(self, search):
        try:
            query_data = []
            query = urllib.parse.quote(search)
            html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={query}')
            video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
            video_ids = await self.removeListDuplicates(video_ids)
            video_urls = []
            for i in video_ids[:4]:
                video_urls.append('https://www.youtube.com/watch?v=' + i)
            for i in video_urls:
                video = await self.processYoutubeLink(i)
                query_data.append(video)
            return query_data
        
        # If there are errors, return an embed, error treatment will be done on the "play" function
        except Exception as e:
            embed = discord.Embed(
                title=" ❌ Error trying to process search",
                description=f"`{e}`",
                color=0xD81313)
            return embed
    
    # Processes playlist links and returns the necessary info for the player
    async def processYoutubePlaylist(self, ctx: Context, entry:int, link:str, shuffle:bool):
        global is_playlist, current_playlist, current_playlist_title, is_shuffling, shuffle_list, items_added, initial_playlist_message_shown, playlist_available, playlist_count, playlist_index
        
        items_added = 0  # Make sure this starts at 0
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                
                # Playlist loading message (only shows once per playlist)
                if not initial_playlist_message_shown:
                    embed = discord.Embed(
                        description=" ⏳  Please wait. Loading playlist data.",
                        color=0xF7C50C)
                    await ctx.send(embed=embed)
                    initial_playlist_message_shown = True
                
                # Process playlist only if there are no other playlists around
                if playlist_available:
                    playlist_available = False  # Make sure no other playlists get mixed in
                    playlist_info = ydl.extract_info(link, download=False)
                    playlist_count = len(playlist_info.get('entries', []))  # Number of songs in the playlist
                    
                    # Generate shuffling list
                    if is_shuffling != 1:
                        shuffle_list = list(range(playlist_count))
                    
                    # Choose a random song if shuffling is active
                    if shuffle:
                        is_shuffling = 1
                        shuffle_song = random.choice(shuffle_list)
                        shuffle_list.remove(shuffle_song)
                        entry = shuffle_song
                    
                    # Extract info
                    entries = playlist_info['entries']
                    entry = entries[entry]
                    entry_info = await self.processYoutubeLink(entry['url'])
                    
                    # Update values and return
                    is_playlist = True
                    current_playlist = link
                    playlist_index += 1
                    current_playlist_title = playlist_info['title']
                    return entry_info
                
                # If there is another playlist running
                else:
                    embed = discord.Embed(
                        description=" ❌ Already playing a playlist, cancel it and try again.",
                        color=0xD81313)
                    await ctx.send(embed=embed)
        
        # If there are errors, return an embed, error treatment will be done on the "play" function
        except yt_dlp.DownloadError as e:
            embed = discord.Embed(
                title=" ❌ Erro no YDL:",
                description=f"``{e}``",
                color=0xD81313)
            return embed

    # Process single youtube links and returns the necessary info for the player
    async def processYoutubeLink(self, link):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                duration = await self.formatTime(info['duration'])
                thumbnail = info.get('thumbnail', '')
                if 'formats' in info and info['formats']:
                    audio = next((format for format in info['formats'] 
                                  if format.get('acodec') == 'opus'), None)
                if audio:
                    data = {
                        'title': info['title'],
                        'url': link,
                        'thumb': thumbnail,
                        'duration': duration,
                        'uploader': info['uploader'],
                        'source': discord.FFmpegOpusAudio(audio['url'], **ffmpeg_opts)}
                    return data
        
        # If there are errors, return an embed, error treatment will be done on the "play" function
                else:
                    embed = discord.Embed(
                        title='Erro',
                        description=" ❌ Error on yt-dlp, could not grab song data :(",
                        color=0xD81313)
                    return embed
        except yt_dlp.DownloadError as e:
            embed = discord.Embed(
                title=" ❌ Error on yt-dlp:",
                description=f"``{e}``",
                color=0xD81313)
            return embed
    
    # Checks and tries to play the next song in queue
    async def play_next(self, ctx: Context, client):
        global from_next, song_history, playlist_available, start_from, manual_dc
        
        from_next = True  # We're in 'play_next', So... makes sense right? :p
        
        if len(song_queue) > 0:
            
            # Grab next song in queue
            next_song = song_queue.popleft()
            
            # Play next song, then repeat this function until queue is over
            client.play(next_song['source'], after=lambda e: self.bot.loop.create_task(
                self.play_next(ctx, client)))

            # Add last played song to history and update cache file
            history_data = {
                'title': next_song['title'], 'duration': next_song['duration'],
                'uploader': next_song['uploader'], 'url': next_song['url']}
            song_history.append(history_data)
            await self.updateHistoryCache(song_history)
            
            # Song info embed
            embed = discord.Embed(
                title=" 🎵  Now Playing:",
                description=f"```{next_song['title']}```",
                color=0x25d917)
            embed.set_footer(text=f"Duration: {next_song['duration']}  |  By: {next_song['uploader']}")
            embed.set_image(url=next_song['thumb'])
            
            # Interface
            view = MediaControls(ctx, self.bot)
            view.add_item(discord.ui.Button(label='🔗 Link', style=discord.ButtonStyle.link, url=next_song['url']))

            # Show
            await ctx.send(embed=embed, view=view)
            
            # Treatment in case it is a playlist
            if is_playlist:
                # Define this variable as true temporarily, so that the
                # playlist data aquisition function runs properly
                playlist_available = True
                
                if playlist_index <= playlist_count:
                    # Update playlist index
                    start_from=playlist_index
                    await self.play(ctx, current_playlist, shuffle=is_shuffling)
                
                # End of playlist
                else:
                    await asyncio.sleep(2)
                    await client.disconnect()
                    await self.resetValues()
                    await self.updateStatus(False)
                    if not manual_dc:
                        embed = discord.Embed(
                            description=" 👋  Disconnecting. End of queue.",
                            color=0x25d917)
                        await ctx.send(embed=embed)
                    manual_dc = False
        
        # End of queue
        else:
            if not client.is_playing() and not is_paused:
                await asyncio.sleep(2)
                await client.disconnect()
                await self.cancelPlaylist(ctx, fromdc=True)
                await self.resetValues()
                await self.updateStatus(False)
                if not manual_dc:
                    embed = discord.Embed(
                        description=' 👋  Disconnecting. End of queue.',
                        color=0x25d917)
                    await ctx.send(embed=embed)
                manual_dc = False
    
    # Disconnects from voice chat and resets everything
    async def disconnect(self, ctx: Context):
        global manual_dc
        manual_dc = True
        client = get(self.bot.voice_clients, guild=ctx.guild)
        if client:
            await self.cancelPlaylist(self, ctx, fromdc=True)
            if client.is_playing() or is_paused:
                client.stop()
            await client.disconnect()
            await self.updateStatus(False)
            await self.resetValues()
        else:
            embed = discord.Embed(
            description=" ❌ Stop what?",
            color=0xD81313)
            await ctx.send(embed=embed)

    # Resets all variables (panic function)
    async def resetValues(self):
        global song_queue, song_history, is_playlist, current_playlist, current_playlist_title, items_added, playlist_index, playlist_count, playlist_available, initial_playlist_message_shown, is_shuffling, shuffle_list, from_next, start_from
        
        song_queue.clear()
        is_playlist = False
        current_playlist = ''
        current_playlist_title = ''
        items_added = 0
        playlist_index = 0
        playlist_count = 0
        playlist_available = True
        initial_playlist_message_shown = False
        is_shuffling = 0
        shuffle_list = []
        from_next = False
        start_from = 0
        try:
            with open('cache/song_history.json', 'r', encoding='utf-8') as f:
                song_history = json.load(f)
        except FileNotFoundError:
            song_history = []
    
    # Updates the history cache file with the current history data in memory
    async def updateHistoryCache(self, new_data):
        try:
            with open('cache/song_history.json', 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4)
        except Exception as e:
            self.bot.logger.error(f'Error trying to update history cache: {e}')

    # Main command, starts playing / adds songs to queue
    @commands.hybrid_command(name='play', description='Play youtube songs / playlists')
    @app_commands.describe(song='Youtube Link / Search query')
    @app_commands.describe(shuffle='Enables shuffling (for playlists)')
    @app_commands.describe(history='Plays a song from the history (by ID)')
    @app_commands.choices(
        shuffle=[
            Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def play(self, ctx: Context, song:str=None, shuffle:Choice[int]=0, history:int=0) -> None:
        global from_next, query_selected
        
        # Do not use defer() when 'play()' gets called by 'play_next()'
        if not from_next:
            await ctx.defer()
        from_next = False
        
        # Connect to voice channel
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            client = get(self.bot.voice_clients, guild=ctx.guild)
            if client and client.is_connected():
                await client.move_to(channel)
            else:
                client = await channel.connect()
                await self.updateStatus(True)
        else:
            embed = discord.Embed(
                description=" ❌ You're either in a invalid voice channel, not in a voice channel, or I don't have the necessary permissions to access voice channels on this server.",
                color=0xD81313)
            await ctx.send(embed=embed)
            return
        
        # In case the user chooses a song from history
        if history != 0:
            song = await self.pickFromHistory(history)
            
            # Error treatment (embeds)
            if isinstance(song, discord.Embed):
                await ctx.send(embed=song)
                return

        # Makes a youtube search query if the user doesn't provide a URL
        if not is_url(song):
            query_data = await self.processYoutubeSearch(song)
            
            # Error treatment (embeds)
            if isinstance(query_data, discord.Embed):
                await ctx.send(embed=query_data)
                return
            
            # Show search results to user
            query_list = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                          in enumerate(query_data)]
            message = '\n'.join(query_list)
            embed = discord.Embed(
                title=f' 🌐  Search results for `"{song}"`:',
                description=f"```{message}```",
                color=0x25d917)
            view = SearchSelector(ctx, self.bot)
            await ctx.send(embed=embed, view=view)
            
            # Wait for user input
            while query_selected == 0:
                await asyncio.sleep(1)
            
            song = query_data[query_selected - 1]['url']
            query_selected = 0
        
        # Checks if the URL is a playlist
        if "playlist?" in song:
            song = await self.processYoutubePlaylist(ctx, playlist_index, song, 
                                                     shuffle=(True if shuffle != 0 else False))
        else:
            song = await self.processYoutubeLink(song)
        
        # Error treatment (embeds)
        if isinstance(song, discord.Embed):
            await ctx.send(embed=embed)
            return
        
        # Add song to queue
        song_queue.append(song)
        
        # Show message only if it is a individual song, not a playlist
        if not is_playlist:
            embed = discord.Embed(
                title=" 🎵  Added to queue:",
                description=f"```{song['title']}```",
                color=0x25d917)
            embed.set_thumbnail(url=song['thumb'])
            embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        
        # Start playing
        if not client.is_playing() and not is_paused:
            await self.play_next(ctx, client)

        # While playing, wait
        while client.is_playing() or is_paused:
            await asyncio.sleep(1)
        
        # When playback ends, disconnect and reset
        await asyncio.sleep(2)  # Little delay to not disconnect abruptly
        await client.disconnect()
        await self.updateStatus(False)

    # Command to manipulate the song queue
    @commands.hybrid_command(name='queue', description='Manipulates the song queue')
    @app_commands.describe(clear='Clears the song queue')
    @app_commands.describe(clear_id='Clears a specific song from the queue (by ID)')
    @app_commands.describe(url='Show URLs instead of titles')
    @app_commands.choices(
        url=[Choice(name='Yes', value=1)],
        clear=[Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def queue(self, ctx: Context, clear: Choice[int] = 0, clear_id: int = 0, url: Choice[int] = 0) -> None:
        if not song_queue and clear == 0:
            embed = discord.Embed(
                description=" ❌ The queue is empty",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif not song_queue and clear.value == 1:
            embed = discord.Embed(
                description=" ❌ The queue is empty",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif song_queue and clear == 0:
            if url == 0:
                queue_data = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                              in enumerate(song_queue)]
            else:
                queue_data = [f'{index + 1}. {item["url"]}' for index, item
                              in enumerate(song_queue)]
            message = '\n'.join(queue_data)
            embed = discord.Embed(
                title=" 📋  Queue atual:",
                description=f"```{message}```",
                color=0x25D917)
            await ctx.send(embed=embed)
        elif song_queue and clear.value == 1 and clear_id == 0:
            song_queue.clear()
            if not song_queue:
                embed = discord.Embed(
                    description=" ✅  Queue cleared!",
                    color=0x25D917)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=' ❌ Error',
                    description="For some reason the queue didn't clear, and no, the dev doesn't know why.",
                    color=0xD81313)
                await ctx.send(embed=embed)
        elif song_queue and clear.value == 1 and clear_id != 0:
            try:
                if clear_id <= 0 or clear_id > len(song_queue):
                    embed = discord.Embed(
                        title=' ❌ Error',
                        description=f'``ID out of queue range``',
                        color=0xD81313)
                    await ctx.send(embed=embed)
                    return
                removed_song = song_queue[clear_id - 1]
                song_queue.remove(removed_song)
                embed = discord.Embed(
                    title=' ✅  Removed from queue:',
                    description=f"``{removed_song['title']}``",
                    color=0x25D917)
                embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)
            except ValueError:
                embed = discord.Embed(
                    title=' ❌ Error',
                    description="Item not found in queue.",
                    color=0xD81313)
                await ctx.send(embed=embed)

    # Command to manipulate the song history
    @commands.hybrid_command(name='history', description='Shows or manipulates the song history')
    @app_commands.describe(clear='Clears the history')
    @app_commands.describe(url='Show URLs instead of titles')
    @app_commands.choices(
        clear=[Choice(name='Yes', value=1)],
        url=[Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def history(self, ctx: Context, clear: Choice[int] = 0, url: Choice[int] = 0) -> None:
        if not song_history and clear == 0:
            embed = discord.Embed(
                description = " ❌ The history is empty",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif not song_history and clear.value == 1:
            embed = discord.Embed(
                description = " ❌ The history is empty",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif song_history and clear == 0:
            if url == 0:
                history_data = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                                in enumerate(song_history)]
            else:
                history_data = [f'{index + 1}. {item["url"]}' for index, item
                                in enumerate(song_history)]
            message = '\n'.join(history_data)
            embed = discord.Embed(
                title=" 🕒  Song History:",
                description=f"```{message}```",
                color=0x25D917)
            await ctx.send(embed=embed)
        elif song_history and clear.value == 1:
            song_history.clear()
            await self.updateHistoryCache(song_history)
            if not song_history:
                embed = discord.Embed(
                    description=" ✅  History cleared!",
                    color=0x25D917)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=' ❌ Error',
                    description="For some reason the history didn't clear, and no, the dev doesn't know why.",
                    color=0xD81313)
                await ctx.send(embed=embed)

    # Cancels the current playlist being played
    @commands.hybrid_command(name='cancelplaylist', description='Cancels the current playing playlist')
    @not_blacklisted()
    async def cancelPlaylist(self, ctx: Context, fromdc=False):
        global playlist_available, is_playlist, current_playlist_title, initial_playlist_message_shown
        if playlist_available and not fromdc:
            embed = discord.Embed(
                description=' ❌  No playlist active',
                color=0xd81313)
            await ctx.send(embed=embed)
            await self.resetValues()
        else:
            playlist_available = True
            is_playlist = False
            initial_playlist_message_shown = False
            if not fromdc:
                embed = discord.Embed(
                    title=" 🛑  Playlist canceled:",
                    description=f"```{current_playlist_title}```",
                    color=0x25D917)
                await ctx.send(embed=embed)

    # Command to show a standalone of the multimedia control interface
    @commands.hybrid_command(name='showcontrols', description='Shows multimedia controls')
    @not_blacklisted()
    async def showControls(self, ctx: Context):
        client = get(self.bot.voice_clients, guild=ctx.guild)
        if client and client.is_connected():
            if client.is_playing() or is_paused:
                view = MediaControls(ctx, self.bot)
                await ctx.send(view=view)
            else:
                embed = discord.Embed(
                    description=" ❌ No media playing",
                    color=0xD81313)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=" ❌ No media playing",
                color=0xD81313)
            await ctx.send(embed=embed)

# Multimedia control buttons (UI)
class MediaControls(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = Music(bot)
        self.id = 'MediaControls'
        self.is_persistent = True
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.green, custom_id='playbutton')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.resume(self.ctx)
    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.secondary, custom_id='pausebutton')
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.pause(self.ctx)
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.blurple, custom_id='skipbutton')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.skip(self.ctx)
    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger, custom_id='stopbutton')
    async def disconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.disconnect(self.ctx)

# Search selector buttons (search query number buttons)
class SearchSelector(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = Music(bot)
        self.id = 'SearchSelector'
        self.is_persistent = False
    
    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.secondary, custom_id='one')
    async def one(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 1
        await interaction.response.defer()
    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.secondary, custom_id='two')
    async def two(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 2
        await interaction.response.defer()
    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.secondary, custom_id='three')
    async def three(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 3
        await interaction.response.defer()
    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.secondary, custom_id='four')
    async def four(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 4
        await interaction.response.defer()

# SETUP
async def setup(bot):
    await bot.add_cog(Music(bot))