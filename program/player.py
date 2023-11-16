"""
RinBot v1.9.0 (GitHub release)
made by rin
"""

# Imports
import discord, json, asyncio, os, random
from discord.ext.commands import Bot, Context
from program.interface import SearchSelector, MediaControls
from program.song_queue import SongQueue
from program.youtube import processYoutubeLink, processYoutubePlaylist, processYoutubeSearch
from program.helpers import is_url

# Active voice channel tracking
voice_channels = {}

# Load histories
histories = {}
for file in os.listdir('cache/histories/'):
    if file.endswith('history.json'):
        try:
            id = int(file.split('-')[0])
        except (ValueError, IndexError):
            continue
        with open(f'cache/histories/{file}', 'r', encoding='utf-8') as f:
            history = json.load(f)
        histories[id] = history

# Player class
class Player():
    def __init__(self, bot: Bot, ctx: Context, guild_id: int):
        self.bot = bot
        self.ctx = ctx
        self.guild_id = guild_id
        self.is_paused = False
        self.is_playing = False
        self.in_playlist = False
        self.manual_dc = False
        self.playlist_data = {}
        self.playlist_index = 0
        self.shuffle_list = []
        self.shuffle_created = False
        self.is_shuffling = False
        self.query_selected = 0
        self.queue = SongQueue()
        
        # Load server specific history file
        try:
            with open(f'cache/histories/{self.guild_id}-history.json', 'r', encoding='utf-8') as f:
                self.song_history = json.load(f)
        except FileNotFoundError:
            self.song_history = []
    
    # Connects to the user's voice channel
    async def connect(self):
        if self.ctx.guild and self.ctx.author.voice:
            if self.ctx.guild.id not in voice_channels:
                voice_channel = self.ctx.author.voice.channel
                self.client: discord.VoiceClient = await voice_channel.connect()
                voice_channels[self.ctx.guild.id] = self.client
                return True
            else:
                self.client: discord.VoiceClient = voice_channels[self.ctx.guild.id]
                if self.ctx.author.voice.channel.id != self.client.channel.id:
                    embed = discord.Embed(
                        title=' ❌  Error',
                        description="I'm already connected to a voice channel on this server!",
                        color=0xd81313)
                    await self.ctx.send(embed=embed)
                    return False
        else:
            embed = discord.Embed(
                description=" ❌ You are either on a invalid channel, or I don't have the necessary permissions to access it.",
                color=0xD81313)
            await self.ctx.send(embed=embed)
            return False
    
    # Disconnects and resets values
    async def disconnect(self):
        if self.ctx.guild:
            if self.ctx.guild.id in voice_channels:
                self.client: discord.VoiceClient = voice_channels.pop(self.ctx.guild.id)
                await self.client.disconnect()
                await self.cancelPlaylist(fromdc=True)
    
    # Does the necessary treatment of the requested song, adds it to queue, and begins playing
    async def addToQueue(self, song, pl_item=False, history_item=0, playlist_id=0):
        
        # If it ain't a URL, do a search query
        if not is_url(song):
            song_query = processYoutubeSearch(song)
            if isinstance(song_query, discord.Embed):
                await self.ctx.send(embed=song_query)
                await self.disconnect()
                return
            
            # Show results to user
            query_list = [f'**{i+1}.** `[{v["duration"]}]` - {v["title"]}' for i, v
                          in enumerate(song_query)]
            message = '\n'.join(query_list)
            embed = discord.Embed(
                title=f' 🌐  Search results for `"{song}"`:',
                description=f"{message}",
                color=0x25d917)
            view = SearchSelector(self.ctx, self.bot, self)
            await self.ctx.send(embed=embed, view=view)
            
            # Wait for user response
            while self.query_selected == 0:
                await asyncio.sleep(1)
            
            song = song_query[self.query_selected - 1]['url']
            self.query_selected = 0
        
        # If the user chooses a song from history
        if history_item != 0:
            song = await self.pickFromHistory(history_item)
        if isinstance(song, discord.Embed):
            await self.ctx.send(embed=song)
            return
        
        # If the URL is a playlist
        if "playlist?" in song:
            self.in_playlist = True
            self.playlist_data = processYoutubePlaylist(song)
            
            # Generate shuffling list (only one time (shuffle_created))
            if not self.shuffle_created:
                self.shuffle_list = list(range(self.playlist_data['count']))
                self.shuffle_created = True
            
            # Choose a random song if shuffling is active
            if self.is_shuffling:
                self.playlist_index = random.choice(self.shuffle_list)
                self.shuffle_list.remove(self.playlist_index)
            
            # Process playlist song
            song = processYoutubeLink(self.playlist_data['entries'][self.playlist_index]['url'])
        elif "playlist?" in song and playlist_id != 0:
            temp_pl_data = processYoutubePlaylist(song)
            song = processYoutubeLink(temp_pl_data['entries'][playlist_id - 1]['url'])
        else:
            song = processYoutubeLink(song)
        if isinstance(song, discord.Embed):
            await self.ctx.send(embed=song)
            await self.disconnect()
            return
        
        # Add to queue
        self.queue.add(song)
        
        # Start playing if nothing is happening
        if not self.client.is_playing() and not self.is_paused:
            await self.play()
        else:
            # Don't show "added to queue" message if it is a playlist song
            # (prevents spamming in chat)
            if not pl_item:
                embed = discord.Embed(
                    title=" 🎵  Added to queue:",
                    description=f"```{song['title']}```",
                    color=0x25d917)
                embed.set_thumbnail(url=song['thumb'])
                try:
                    embed.set_footer(text=f"Requested by: {self.ctx.author}", icon_url=self.ctx.author.avatar.url)
                except AttributeError:
                    embed.set_footer(text=f"Requested by: {self.ctx.author}")
                await self.ctx.send(embed=embed)
    
    # Checks if there are songs in queue, plays them, then disconnects when done
    async def play(self):
        if self.queue.len() > 0:
            
            # Grab next song in queue
            next_song = self.queue.next()
            self.client.play(next_song['source'], after=lambda e: self.bot.loop.create_task(
                self.play()))
            
            # Add currently playing song to history
            history_data = {
                'title': next_song['title'], 'duration': next_song['duration'],
                'uploader': next_song['uploader'], 'url': next_song['url']}
            self.song_history.append(history_data)
            
            # Keep history below 50 items
            if len(self.song_history) > 50:
                self.song_history.pop(0)
            
            # Update history cache
            await self.updateHistoryCache()
            
            # Respond to user
            embed = discord.Embed(
                title=" 🎵  Now playing:",
                description=f"```{next_song['title']}```",
                color=0x25d917)
            embed.set_footer(text=f"Duration: {next_song['duration']}  |  By: {next_song['uploader']}")
            embed.set_image(url=next_song['thumb'])
            view = MediaControls(self.ctx, self.bot, self)
            view.add_item(discord.ui.Button(label='🔗 Link', style=discord.ButtonStyle.link, url=next_song['url']))
            await self.ctx.send(embed=embed, view=view)
            
            # Add next song if in a playlist
            if self.in_playlist:
                self.playlist_index += 1
                if self.playlist_index <= self.playlist_data['count']:
                    await self.addToQueue(self.playlist_data['url'], pl_item=True)

                # Reset values after reaching end of playlist
                else:
                    await self.cancelPlaylist(True)
        
        # End of queue
        else:
            if not self.client.is_playing() and not self.is_paused:
                await asyncio.sleep(2)
                await self.disconnect()
                if not self.manual_dc:
                    embed = discord.Embed(
                        description=" 👋  Disconnecting. End of queue.",
                        color=0x25d917)
                    await self.ctx.send(embed=embed)
                self.manual_dc = False
    
    # General multimedia control functions (triggered by the UI buttons)
    async def pause(self):
        if self.client and self.client.is_playing() and not self.is_paused:
            self.client.pause()
            self.is_paused = True
    async def resume(self):
        if self.client and self.client.is_paused() and self.is_paused:
            self.client.resume()
            self.is_paused = False
    async def skip(self):
        if self.client and self.client.is_playing():
            self.client.stop()
        else:
            embed = discord.Embed(
                description=" ❌ No songs playing.",
                color=0xd81313)
            await self.ctx.send(embed=embed)
    
    # Cancels a playlist
    async def cancelPlaylist(self, fromdc=False):
        if not self.in_playlist and not fromdc:
            embed = discord.Embed(
                description=' ❌  No playlists active',
                color=0xd81313)
            await self.ctx.send(embed=embed)
        else:
            self.in_playlist = False
            self.playlist_data = {}
            self.playlist_index = 0
            self.shuffle_list = []
            self.shuffle_created = False
            self.is_shuffling = False
            if not fromdc:
                embed = discord.Embed(
                    title=" 🛑  Playlist canceled:",
                    description=f"```{self.playlist_data['title']}```",
                    color=0x25D917)
                await self.ctx.send(embed=embed)
    
    # Shows history
    async def showHistory(self, url=False):
        history_data = [f'**{index + 1}.** `[{item["duration"]}]` - {item["title"]}'
                        if not url else f'**{index + 1}.** {item["url"]}'
                        for index, item in enumerate(self.song_history)]
        message = '\n'.join(history_data)
        return message
    
    # Chooses a song from history, deletes it, then returns it's URL
    async def pickFromHistory(self, entry:int):
        try:
            song = self.song_history[entry - 1]['url']
            self.song_history.remove(self.song_history[entry - 1])  # Remove item to prevent duplicates
            await self.updateHistoryCache()
            return song
        except IndexError:
            embed = discord.Embed(
                title=' ❌ Error',
                description=f"Item not found in history. {entry} is out of range.",
                color=0xD81313)
            return embed
    
    # Clears the history
    async def clearHistory(self):
        self.song_history.clear()
        await self.updateHistoryCache()
    
    # Updates the history cache with fresh data
    async def updateHistoryCache(self):
        try:
            with open(f'cache/histories/{self.guild_id}-history.json', 'w', encoding='utf-8') as f:
                json.dump(self.song_history, f, indent=4)
        except Exception as e:
            self.bot.logger.error(f'Erro ao atualizar o cache {self.guild_id}: {e}')
        for file in os.listdir('cache/histories/'):
            if file.endswith('history.json'):
                try:
                    id = int(file.split('-')[0])
                except (ValueError, IndexError):
                    continue
                with open(f'cache/histories/{file}', 'r', encoding='utf-8') as f:
                    history = json.load(f)
                histories[id] = history