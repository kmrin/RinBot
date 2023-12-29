# Imports
import discord, asyncio
from discord.ext.commands import Bot
from program.interface.media_controls import MediaControls
from program.interface.page_switcher import PageSwitcher
from program.music.song_queue import SongQueue
from program.music.youtube import *
from program.base.colors import *
from program.base.helpers import load_lang
from program.base import db_manager

# Load verbose
text = load_lang()

# Global voice channels tracking
vcs = {}

# MediaPlayer class
class Player():
    def __init__(self, bot:Bot, interaction:discord.Interaction):
        self.bot = bot
        self.interaction = interaction
        self.guild_id = self.interaction.guild.id
        self.client:discord.VoiceClient = None
        self.manual_dc = False
        self.is_paused = False
        self.is_playing = False
        self.song_history = []
        self.queue = SongQueue()
        asyncio.create_task(self.load_history())
        
    # Loads the server's song history
    async def load_history(self):
        self.song_history = await db_manager.get_history(self.guild_id)
        if not self.song_history: self.song_history = []
    
    # Connects to the user's voice channel
    async def connect(self):
        if self.interaction.guild and self.interaction.user.voice:
            if self.guild_id not in vcs:
                vc = self.interaction.user.voice.channel
                self.client = await vc.connect(reconnect=True, self_deaf=True)
                vcs[self.guild_id] = self.client
                return True
            else:
                self.client:discord.VoiceClient = vcs[self.guild_id]
                if self.interaction.user.voice.channel.id != self.client.channel.id:
                    return discord.Embed(
                        description=f"{text['PLAYER_ALREADY_CONNECTED']}",
                        color=RED)
        else:
            return discord.Embed(
                description=f"{text['PLAYER_INVALID_CHANNEL']}",
                color=RED)
    
    # Disconnects and resets values
    async def disconnect(self):
        if self.interaction.channel.guild:
            if self.interaction.channel.guild.id in vcs:
                self.client:discord.VoiceClient = vcs.pop(self.guild_id)
                await self.client.disconnect()
        self.client = None
        self.is_paused = False
        self.is_playing = False
        self.song_history = []
        self.queue = SongQueue()
        if not self.manual_dc:
            embed = discord.Embed(
                description=f"{text['PLAYER_DISCONNECTING_MSG']}",
                color=GREEN)
            await self.interaction.channel.send(embed=embed)
            self.manual_dc = False

    # General multimedia control functions (triggered by the UI)
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
    
    # Adds tracks to the player's song queue
    async def add_to_queue(self, data):
        
        """
        data structure:
            data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        
        If it's a playlist, the item will not contain any "duration" or "uploader"
        """
        
        # Recover each track's data and add it to queue
        for index, item in enumerate(data["titles"]):
            track = {"title": item, "url": data["urls"][index],
                     "duration": data["durations"][index], 
                     "uploader": data["uploaders"][index]}
            self.queue.add(track)
        
        # Grab current queue
        queue = self.queue.show()
        
        # If the queue is empty, cancel everything and reset
        # (hopefully this never happens)
        if not queue:
            self.manual_dc = True
            await self.disconnect()
            embed = discord.Embed(
                description=f"{text['PLAYER_SONG_QUEUE_ERROR']}",
                color=RED)
            await self.interaction.channel.send(embed=embed)
        
        # Show recently added tracks
        else:
            if self.queue.len() > 20:
                lines = queue.split("\n")
                chunks = [lines[i:i+10] for i in range(0, len(lines), 20)]
                embed = discord.Embed(
                    title=f"{text['PLAYER_ADDED_TO_QUEUE']}",
                    description="\n".join(chunks[0]), color=GREEN)
                await self.interaction.followup.send(embed=embed, view=PageSwitcher(self.bot, embed, chunks))
            else:
                embed = discord.Embed(
                    title=f"{text['PLAYER_ADDED_TO_QUEUE']}",
                    description=queue, color=GREEN)
                await self.interaction.followup.send(embed=embed)
    
        # Start playing if nothing is happening
        if not self.client.is_playing() and not self.is_paused:
            await self.play()
    
    # Checks if there are songs in queue, processes them and plays them on the vc
    async def play(self):
        if self.queue.len() > 0:
            next_song = self.queue.next()
            
            # Grab audio stream and thumbnail
            media = await get_media(next_song["url"])
            if isinstance(media, discord.Embed):
                self.manual_dc = True
                await self.disconnect()
                return await self.interaction.channel.send(embed=media)
            
            # Add currently playing song to history
            await self.load_history()
            if not self.song_history: self.song_history = []
            self.song_history.append(next_song)
            if len(self.song_history) > 25:
                self.song_history.pop(0)
            
            # Update history cache
            await db_manager.update_history(self.guild_id, self.song_history)
            
            # Begin playback
            try:
                self.client.play(media["source"], after=lambda e: self.bot.loop.create_task(self.play()))

                # Respond to user
                embed = discord.Embed(
                    title=f"{text['PLAYER_NOW_PLAYING']}",
                    description=f"```{next_song['title']}```", color=GREEN)
                embed.set_footer(text=f"{text['PLAYER_NOW_PLAYING_FOOTER'][0]} {next_song['duration']} {text['PLAYER_NOW_PLAYING_FOOTER'][1]} {next_song['uploader']}")
                embed.set_image(url=media["thumb"])
                view = MediaControls(self.bot, self)
                view.add_item(discord.ui.Button(label=f"{text['PLAYER_LINK_BTN']}", style=discord.ButtonStyle.link, url=next_song['url']))
                await self.interaction.channel.send(embed=embed, view=view)
            except AttributeError:
                pass

        # End of queue
        else:
            try:
                if not self.client.is_playing() and not self.is_paused:
                    await asyncio.sleep(2)
                    await self.disconnect()
            except AttributeError:
                pass