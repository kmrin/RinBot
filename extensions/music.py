# Imports
import discord, asyncio, os, json
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.player import Player
from program.interface import MediaControls, PlaylistPageSwitcher
from program.history_manager import showHistory, clearHistory
from program.favorites_manager import showFavorites, addFavorite, removeFavorite, clearFavorites
from program.helpers import is_url, formatTime
from program.youtube import processYoutubePlaylist
from program.checks import *

# Active players tracking
players = {}

# Active favorite playlists tracking
favorites = {}

# 'music' command block
class Music(commands.Cog, name='music'):
    def __init__(self, bot):
        self.bot = bot
    
    # Main command, starts playing tracks
    @commands.hybrid_command(name='play', description='Plays songs / playlists from youtube')
    @app_commands.describe(favorite_playlist='If you want to play one of your favorite playlists')
    @app_commands.describe(song='Song or Playlist link / Search query / Favorite playlist ID')
    @app_commands.describe(playlist_id='Adds only a specific song from a playlist into the queue')
    @app_commands.describe(shuffle='Activates shuffling (optional) (for playlists)')
    @app_commands.describe(history='Plays a song from history (by ID)')
    @app_commands.choices(
        shuffle=[
            Choice(name='Yes', value=1)],
        favorite_playlist=[
            Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def play(self, ctx: Context, song:str=None, playlist_id:int=0, shuffle:Choice[int]=0, favorite_playlist:Choice[int]=0, history:int=0) -> None:
        
        # Defer so discord doesn't go kaboom
        await ctx.defer()
        
        # In case a dummy doesn't provide a song
        if not song:
            embed = discord.Embed(
                description=" ❌  'song' attribute empty.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        
        # In case the user asks for a favorite playlist
        if song.isnumeric() and favorite_playlist != 0:
            self.readFavorites()
            try:
                song = favorites[ctx.author.id][int(song)-1]['url']
            except KeyError:
                embed = discord.Embed(
                    description = " ❌ Inexistant playlist or out of range.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
        
        # Generate player object
        try:
            if ctx.guild.id not in players:
                players[ctx.guild.id] = Player(self.bot, ctx, ctx.guild.id)
        except AttributeError:
            pass
        
        # Define current player (who is running the command)
        current_player:Player = players[ctx.guild.id]
        
        # Connect to the voice channel
        print("Before connection")
        connection = await current_player.connect()
        print("After var")
        if isinstance(connection, bool):
            print("In instance")
            if not connection:
                embed = discord.Embed(
                    description=" ❌  Couldn't connect to voice channel. Check my permissions.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
        print("After connection")
        
        # Activate shuffling for playlists
        if shuffle != 0:
            current_player.is_shuffling = True
        
        # Start media processing
        await current_player.addToQueue(song, history_item=history, playlist_id=playlist_id)

        # Wait while the bot is playing
        while current_player.client.is_playing() or current_player.is_paused:
            await asyncio.sleep(1)
        
        # Delete player object after playback ends
        try:
            del players[ctx.guild.id]
        except KeyError:
            pass

    # Manipulates the queue
    @commands.hybrid_command(name='queue', description='Shows or manipulates the song queue')
    @app_commands.describe(clear='Clears the song queue')
    @app_commands.describe(id='Clears a specific song from queue (by ID)')
    @app_commands.describe(url='Show URLs instead of titles')
    @app_commands.choices(
        url=[Choice(name='Yes', value=1)],
        clear=[Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def queue(self, ctx:Context, clear:Choice[int]=0, id:int=0, url:Choice[int]=0) -> None:
        
        # If we're not playing anything
        if ctx.guild.id not in players:
            embed = discord.Embed(
                description=" ❌  No instance running on this server.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            # If yes, grab the current player object
            current_player:Player = players[ctx.guild.id]
            
            # Show queue
            if clear == 0:
                message = current_player.queue.show(False if url == 0 else True)
                if not message:
                    embed = discord.Embed(
                    description=" ❌ The queue is empty",
                    color=0xd91313)
                else:
                    embed = discord.Embed(
                    title=" 📋  Current queue:",
                    description=f"{message}",
                    color=0x25D917)
                await ctx.send(embed=embed)
            
            # Clear the entire queue
            elif clear.value == 1 and id == 0:
                current_player.queue.clear()
                embed = discord.Embed(
                    description=" ✅  Queue cleared!",
                    color=0x25D917)
                await ctx.send(embed=embed)
            
            # Clear a specific queue item
            elif clear.value == 1 and id != 0:
                cleared_song = current_player.queue.clear_specific(id)
                if cleared_song:
                    embed = discord.Embed(
                        title=" ✅  Removed from queue:",
                        description=f"``{cleared_song['title']}``",
                        color=0x25D917)
                else:
                    embed = discord.Embed(
                        title=' ❌ Error',
                        description=f'``ID out of queue range``',
                        color=0xD81313)
                    await ctx.send(embed=embed)
                await ctx.send(embed=embed)

    # Manipulates the song history
    @commands.hybrid_command(name='history', description='Shows or manipulates the song history')
    @app_commands.describe(clear='Clears the history')
    @app_commands.describe(url='Show URLs instead of titles')
    @app_commands.choices(
        clear=[Choice(name='Yes', value=1)],
        url=[Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def history(self, ctx:Context, clear:Choice[int]=0, url:Choice[int]=0) -> None:
        
        # Load current histories
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
        
        # If the history doesn't exist
        if ctx.guild.id not in histories:
            embed = discord.Embed(
                description = " ❌ The history is empty",
                color=0xd91313)
            await ctx.send(embed=embed)
        
        # If there are no player instances (use "offline" history functions)
        if ctx.guild.id not in players:
            
            # Show history
            if clear == 0:
                message = showHistory(ctx.guild.id, False if url == 0 else True)
                if not message:
                    embed = discord.Embed(
                        description = " ❌ The history is empty",
                        color=0xd91313)
                else:
                    embed = discord.Embed(
                        title=" 🕒  History:",
                        description=f"{message}",
                        color=0x25D917)
                await ctx.send(embed=embed)
            
            # Clear history
            elif clear.value == 1:
                clearHistory(ctx.guild.id)
                embed = discord.Embed(
                    description=" ✅  History cleared!",
                    color=0x25D917)
                await ctx.send(embed=embed)
        
        # If yes define the current player (use "online" history functions)
        else:
            current_player:Player = players[ctx.guild.id]
            
            # Show history
            if clear == 0:
                message = await current_player.showHistory(False if url == 0 else True)
                if not message:
                    embed = discord.Embed(
                        description = " ❌ The history is empty",
                        color=0xd91313)
                else:
                    embed = discord.Embed(
                        title=" 🕒  History:",
                        description=f"{message}",
                        color=0x25D917)
                await ctx.send(embed=embed)
            
            # Clear history
            elif clear.value == 1:
                await current_player.clearHistory()
                embed = discord.Embed(
                    description=" ✅  History cleared!",
                    color=0x25D917)
                await ctx.send(embed=embed)

    # Cancels the playthrough of the current active playlist
    @commands.hybrid_command(name='cancelplaylist', description='Cancels the active playlist')
    @not_blacklisted()
    async def cancelPlaylist(self, ctx:Context):
        
        # If we're doing nothing
        if ctx.guild.id not in players:
            embed = discord.Embed(
                description=" ❌  No instance running on this server.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            current_player:Player = players[ctx.guild.id]
            current_player.cancelPlaylist()

    # Shows the multimedia controls (useful if they went too far up on the text channel, that's why I made it :p)
    @commands.hybrid_command(name='showcontrols', description='Shows multimedia controls')
    @not_blacklisted()
    async def showControls(self, ctx:Context):
        
        # If we're doing nothing
        if ctx.guild.id not in players:
            embed = discord.Embed(
                description=" ❌  No instance running on this server.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            current_player:Player = players[ctx.guild.id]
            view = MediaControls(ctx, self.bot, current_player)
            await ctx.send(view=view)

    # Command to manipulate favorite playlists
    @commands.hybrid_command(name='playlists', description='Shows or manipulates your favorite playlists!')
    @app_commands.describe(url='Shows URLs instead of song titles')
    @app_commands.describe(action='The action to be taken (if any)')
    @app_commands.describe(item='The playlist to be manipulated')
    @app_commands.choices(
        url=[Choice(name='Yes', value=1)],
        action=[Choice(name='Add', value=1),
                Choice(name='Remove', value=2),
                Choice(name='Clear', value=3)])
    @not_blacklisted()
    async def playlists(self, ctx:Context, action:Choice[int]=0, item:str=None, url:Choice[int]=False) -> None:
        await ctx.defer()
        
        # Load current playlists
        playlists = {}
        for file in os.listdir('cache/favorites/'):
            if file.endswith('favorites.json'):
                try:
                    id = int(file.split('-')[0])
                except (ValueError, IndexError):
                    continue
                with open(f'cache/favorites/{file}', 'r', encoding='utf-8') as f:
                    playlist_list = json.load(f)
                playlists[id] = playlist_list
        
        # Show favorites
        if action == 0:
            message = showFavorites(ctx.author.id, False if url == 0 else True)
            if not message:
                embed = discord.Embed(
                        description = " ❌ You don't have favorite playlists.",
                        color=0xd91313)
            else:
                embed = discord.Embed(
                        title=f" :play_pause:  {ctx.author.global_name}'s playlists:",
                        description=f"{message}",
                        color=0x25D917)
                try:
                    embed.set_footer(text=f"{ctx.author.global_name}", icon_url=ctx.author.avatar.url)
                except AttributeError:
                    embed.set_footer(text=f"{ctx.author.global_name}")
            await ctx.send(embed=embed)
        
        # Add to favorites
        elif action.value == 1:
            if is_url(item):
                if 'playlist?' in item:
                    item = addFavorite(ctx.author.id, item)
                    if not isinstance(item, discord.Embed):
                        embed = discord.Embed(
                            description=f" ✅  `{item['title']}` added to your favorite playlists!",
                            color=0x25D917)
                    else:
                        embed = item
                else:
                    embed = discord.Embed(
                        description = " ❌ Please give me a valid playlist URL.",
                        color=0xd91313)
            else:
                embed = discord.Embed(
                    description = " ❌ Please give me a valid URL.",
                    color=0xd91313)
            await ctx.send(embed=embed)
        
        # Remover dos favoritos
        elif ctx.author.id in playlists and action.value == 2:
            try:
                item = int(item)
                embed = removeFavorite(ctx.author.id, item - 1)
            except ValueError:
                embed = discord.Embed(
                    description = " ❌ Value error, please give me numbers (ID).",
                    color=0xd91313)
            await ctx.send(embed=embed)
                
        # Limpar favoritos
        elif action.value == 3:
            clearFavorites(ctx.author.id)
            embed = discord.Embed(
                description=f" ✅  Your favorite playlists have been cleared!",
                color=0x25D917)
            await ctx.send(embed=embed)

    # Command to show the songs inside a playlist
    @commands.hybrid_command(name='showplaylist', description='Shows the current playlist or any other')
    @app_commands.describe(url='Specifies the playlist URL to be shown')
    @app_commands.describe(showurl='Shows URLs instead of song titles')
    @app_commands.describe(favorite='Lists one of your favorite playlists')
    @app_commands.choices(showurl=[Choice(name='Yes', value=1)])
    async def showPlaylist(self, ctx:Context, url:str=None, favorite:int=0, showurl:Choice[int]=0) -> None:
        
        # Load playlist cache
        playlists = {}
        for file in os.listdir('cache/favorites/'):
            if file.endswith('favorites.json'):
                try:
                    id = int(file.split('-')[0])
                except (ValueError, IndexError):
                    continue
                with open(f'cache/favorites/{file}', 'r', encoding='utf-8') as f:
                    playlist_list = json.load(f)
                playlists[id] = playlist_list
        
        # If there are no players
        if ctx.guild.id not in players and not url and favorite == 0:
            embed = discord.Embed(
                description = " ❌ Nenhuma instância ativa.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        
        # If there is one check if there is a playlist active and act accordingly
        elif ctx.guild.id in players and not url and favorite == 0:
            current_player:Player = players[ctx.guild.id]
            if not current_player.in_playlist:
                embed = discord.Embed(
                    description = " ❌ No playlist active.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
            entries = []
            for entry in current_player.playlist_data['entries']:
                entry_data = {
                    'title': entry['title'],
                    'url': entry['url'],
                    'duration': formatTime(entry['duration'])}
                entries.append(entry_data)
            entry_list = [f'**{index + 1}.** `[{item["duration"]}]` - {item["title"]}'
                if showurl == 0 else
                f'**{index + 1}.** {item["url"]}'
                for index, item in enumerate(entries)]
            message = '\n'.join(entry_list)
            message_lines = message.split('\n')
            chunks = [message_lines[i:i+20] for i in range(
                0, len(message_lines), 20)]
            embed = discord.Embed(title=f" 🎵  {pl_data['title']}'songs (current playlist)")
            embed.description='\n'.join(chunks[0])
        
        # In case a specific URL was given
        elif url and favorite == 0:
            if not is_url(url):
                embed = discord.Embed(
                    description = " ❌ Invalid URL.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
            pl_data = processYoutubePlaylist(url)
            entries = []
            for entry in pl_data['entries']:
                entry_data = {
                    'title': entry['title'],
                    'url': entry['url'],
                    'duration': formatTime(entry['duration'])}
                entries.append(entry_data)
            entry_list = [f'**{index + 1}.** `[{item["duration"]}]` - {item["title"]}'
                if showurl == 0 else
                f'**{index + 1}.** {item["url"]}'
                for index, item in enumerate(entries)]
            message = '\n'.join(entry_list)
            message_lines = message.split('\n')
            chunks = [message_lines[i:i+20] for i in range(
                0, len(message_lines), 20)]
            embed = discord.Embed(title=f" 🎵  {pl_data['title']}'songs (external URL)")
            embed.description='\n'.join(chunks[0])
        
        # If a favorite playlist was given
        elif not url and favorite != 0:
            self.readFavorites()
            try:
                pl_data = processYoutubePlaylist(favorites[ctx.author.id][int(favorite)-1]['url'])
            except KeyError:
                embed = discord.Embed(
                    description = " ❌ Inexistant playlist or out of range.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
            entries = []
            for entry in pl_data['entries']:
                entry_data = {
                    'title': entry['title'],
                    'url': entry['url'],
                    'duration': formatTime(entry['duration'])}
                entries.append(entry_data)
            entry_list = [f'**{index + 1}.** `[{item["duration"]}]` - {item["title"]}'
                if showurl == 0 else
                f'**{index + 1}.** {item["url"]}'
                for index, item in enumerate(entries)]
            message = '\n'.join(entry_list)
            message_lines = message.split('\n')
            chunks = [message_lines[i:i+20] for i in range(
                0, len(message_lines), 20)]
            embed = discord.Embed(title=f" 🎵  {pl_data['title']}'songs ({ctx.author.global_name}'s favorite)")
            embed.description='\n'.join(chunks[0])
        
        # Return
        view = PlaylistPageSwitcher(ctx, self.bot, embed, chunks)
        await ctx.send(embed=embed, view=view)

    # Read current favorites
    def readFavorites(self):
        for file in os.listdir('cache/favorites/'):
            if file.endswith('favorites.json'):
                try:
                    id = int(file.split('-')[0])
                except (ValueError, IndexError):
                    continue
                with open(f'cache/favorites/{file}', 'r', encoding='utf-8') as f:
                    favorite = json.load(f)
                favorites[id] = favorite

# SETUP
async def setup(bot):
    await bot.add_cog(Music(bot))
