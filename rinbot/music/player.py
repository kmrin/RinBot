# Imports
import discord, asyncio
from discord.ext.commands import Bot
from rinbot.base.responder import Responder
from rinbot.base.interface import MediaControls, PageSwitcher
from rinbot.music.song_queue import SongQueue
from rinbot.music.youtube import *
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang
from rinbot.base import db_manager

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
        self.responder = Responder(self.bot)
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
                        description=f"{text['PLAYER_ALREADY_CONNECTED']}", color=RED)
        else:
            return discord.Embed(
                description=f"{text['PLAYER_INVALID_CHANNEL']}", color=RED)
    
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
            await self.responder.respond(self.interaction, GREEN, text['PLAYER_DISCONNECTING_MSG'], response_type=2)
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
    async def add_to_queue(self, interaction:discord.Interaction, data):
        
        """
        data structure:
            data: dict = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        
        returns:
            data: list = [embed, view]
            Note: The view item will only be returned if the items added to the queue
                  are more than 15, otherwise it returns None
        
        If it's a playlist, the item will not contain any "duration" or "uploader"
        """
        
        # Recover each track's data and add it to queue
        added = []
        for index, item in enumerate(data["titles"]):
            track = {"title": item, "url": data["urls"][index],
                     "duration": data["durations"][index], 
                     "uploader": data["uploaders"][index]}
            self.queue.add(track)
            added.append(track)
        
        # Grab current queue
        queue = self.queue.show()
        
        # If the queue is empty, cancel everything and reset
        # (hopefully this never happens)
        if not queue:
            self.manual_dc = True
            await self.disconnect()
            await self.responder.respond(interaction, RED, text['PLAYER_SONG_QUEUE_ERROR'], response_type=1)
        
        # Show recently added tracks
        else:
            added_msg = "\n".join([f"**{i+1}.** `[{s['duration']}]` - {s['title']}"
                                   for i, s in enumerate(added)])
            if len(added) > 20:
                lines = added_msg.split("\n")
                chunks = [lines[i:i+10] for i in range(0, len(lines), 20)]
                embed = discord.Embed(
                    title=f"{text['PLAYER_ADDED_TO_QUEUE']}",
                    description="\n".join(chunks[0]), color=GREEN)
                view=PageSwitcher(self.bot, embed, chunks)
                await self.responder.respond(interaction, message=embed, view=view, response_type=1)
            else:
                await self.responder.respond(interaction, GREEN, title=text['PLAYER_ADDED_TO_QUEUE'], message=added_msg, response_type=1)

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
    
    # Adds a song from history to queue
    async def pick_from_history(self, interaction, entry:int) -> dict:
        try:
            data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
            await self.load_history()
            if not self.song_history:
                return discord.Embed(
                    description=f"{text['PLAYER_HISTORY_EMPTY']}", color=RED)
            song = self.song_history[int(entry) - 1]
            data["titles"].append(song["title"])
            data["urls"].append(song["url"])
            data["durations"].append(song["duration"])
            data["uploaders"].append(song["uploader"])
            self.song_history.remove(self.song_history[int(entry) - 1])
            await db_manager.update_history(self.guild_id, self.song_history)
            return await self.add_to_queue(interaction, data)
        except IndexError:
            self.manual_dc = False
            await self.disconnect()
            return discord.Embed(
                title=f"{text['ERROR']}",
                description=f"{text['PLAYER_HISTORY_OUT_OF_RANGE'][0]} {entry} {text['PLAYER_HISTORY_OUT_OF_RANGE'][1]}",
                color=RED)