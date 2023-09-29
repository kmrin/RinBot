"""
RinBot v1.5.0 (GitHub release)
made by rin
"""

# Imports
import discord
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.music.player import Player
from program.music.interface import MediaControls
from program.music.history_manager import showHistory, clearHistory
from program.checks import *

# Active players tracking
players = {}

# 'music' command block
class Music(commands.Cog, name='music'):
    def __init__(self, bot):
        self.bot = bot
    
    # Main command, starts playing tracks
    @commands.hybrid_command(name='play', description='Plays songs / playlists from youtube')
    @app_commands.describe(song='Song or Playlist link / Search query')
    @app_commands.describe(shuffle='Activates shuffling (optional) (for playlists)')
    @app_commands.describe(history='Plays a song from history (by ID)')
    @app_commands.choices(
        shuffle=[
            Choice(name='Yes', value=1)])
    @not_blacklisted()
    async def play(self, ctx: Context, song:str=None, shuffle:Choice[int]=0, history:int=0) -> None:
        
        # Defer so discord doesn't go kaboom
        await ctx.defer()
        
        # In case a dummy doesn't provide a song
        if not song:
            embed = discord.Embed(
                description=" ❌  'song' attribute empty.",
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
        connection = await current_player.connect()
        if isinstance(connection, bool):
            if not connection:
                embed = discord.Embed(
                    description=" ❌  Couldn't connect to voice channel. Check my permissions.",
                    color=0xd91313)
                await ctx.send(embed=embed)
                return
        
        # Activate shuffling for playlists
        if shuffle != 0:
            current_player.is_shuffling = True
        
        # Start media processing
        await current_player.addToQueue(song, history_item=history)

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
                    description=f"```{message}```",
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
        for file in os.listdir('program/music/cache/'):
            if file.endswith('.json'):
                try:
                    id = int(file.split('-')[1].split('.')[0])
                except (ValueError, IndexError):
                    continue
                with open(f'program/music/cache/{file}', 'r', encoding='utf-8') as f:
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
                        description=f"```{message}```",
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
                message = current_player.showHistory(False if url == 0 else True)
                if not message:
                    embed = discord.Embed(
                        description = " ❌ The history is empty",
                        color=0xd91313)
                else:
                    embed = discord.Embed(
                        title=" 🕒  History:",
                        description=f"```{message}```",
                        color=0x25D917)
                await ctx.send(embed=embed)
            
            # Clear history
            elif clear.value == 1:
                current_player.clearHistory()
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

# SETUP
async def setup(bot):
    await bot.add_cog(Music(bot))