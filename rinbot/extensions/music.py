# Imports
import discord
from discord import app_commands
from discord.ext.commands import Cog, Bot, Context
from discord.app_commands import Group, Choice
from rinbot.base.helpers import format_exception, load_lang
from rinbot.music.history_mgr import show_history, clear_history
from rinbot.base.interface import VideoSearchView, PlaylistSearchView, PageSwitcher, MediaControls
from rinbot.music.player import Player
from rinbot.music.youtube import *
from rinbot.base.colors import *
from rinbot.base.checks import *
from rinbot.base.responder import Responder

# Load verbose
text = load_lang()

# Global player tracking
players = {}

# Music command cog
class Music(Cog, name="music"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.responder = Responder(self.bot)
    
    # Initial setup for all /play commands
    async def setup_play(self, interaction:discord.Interaction):
        # Generate a player object for the current guild
        try:
            if interaction.guild.id not in players:
                self.bot.logger.info(f"{text['MUSIC_GENERATING_PLAYER']} {interaction.guild.name} (ID: {interaction.guild.id})")
                players[interaction.guild.id] = Player(self.bot, interaction)
            else:
                self.bot.logger.info(f"{text['MUSIC_USING_PLAYER']} {interaction.guild.name} (ID: {interaction.guild.id})")
            current_player:Player = players[interaction.guild.id]
        except Exception as e:
            e = format_exception(e)
            return await self.responder.respond(interaction, RED, text['MUSIC_PLAYER_GEN_ERROR'], response_type=1)
        
        # Connect to vc
        conn = await current_player.connect()
        if isinstance(conn, discord.Embed):
            try:
                if not current_player.client.is_playing() and not current_player.is_paused:
                    current_player.manual_dc = True
                    await current_player.disconnect()
                    del players[interaction.guild.id]
            except AttributeError: pass
            return await self.responder.respond(interaction, message=conn, response_type=1)
        return current_player
    
    # Command groups
    play_group = Group(name=f"{text['MUSIC_PLAY_NAME']}", description=f"{text['MUSIC_PLAY_DESC']}")
    queue_group = Group(name=f"{text['MUSIC_QUEUE_NAME']}", description=f"{text['MUSIC_QUEUE_DESC']}")
    history_group = Group(name=f"{text['MUSIC_HISTORY_NAME']}", description=f"{text['MUSIC_HISTORY_DESC']}")

    # Plays from a single or a list of youtube links
    @play_group.command(
        name=f"{text['MUSIC_PLAY_LINK_NAME']}",
        description=f"{text['MUSIC_PLAY_LINK_DESC']}")
    @app_commands.describe(link=f"{text['MUSIC_PLAY_LINK_DESCRIBE']}")
    @not_blacklisted_ac()
    async def play_link(self, interaction:discord.Interaction, link:str=None) -> None:
        await interaction.response.defer()
        if not link: return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'], response_type=1)
        
        # Setup
        current_player = await self.setup_play(interaction)
        if not current_player: return
        
        # Process links and generate track data
        links = await format_links(link)
        if isinstance(links, discord.Embed):
            try:
                if not current_player.client.is_playing() and not current_player.is_paused:
                    current_player.manual_dc = True
                    await current_player.disconnect()
                    del players[interaction.guild.id]
            except AttributeError: pass
            return await self.responder.respond(interaction, message=links, response_type=1)
        
        data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        for link in links:
            
            # If it's a playlist, grab all playlist videos
            if "playlist?" in link:
                pl_data = await process_playlist(link)
                embed = discord.Embed(
                    description=f"{text['MUSIC_ADDING_PL'][0]} `{pl_data['count']}` {text['MUSIC_ADDING_PL'][1]} `{pl_data['title']}`",
                    color=YELLOW)
                for index, item in enumerate(pl_data["titles"]):
                    data["titles"].append(item)
                    data["urls"].append(pl_data["urls"][index])
                    data["durations"].append(pl_data["durations"][index])
                    data["uploaders"].append(pl_data["uploaders"][index])
                await self.responder.respond(interaction, message=embed)
            
            # If it's a normal video, proceed normally
            else:
                link_data = await process_link(link)
                if isinstance(link_data, discord.Embed):
                    try:
                        if not current_player.client.is_playing() and not current_player.is_paused:
                            current_player.manual_dc = True
                            await current_player.disconnect()
                            del players[interaction.guild.id]
                    except AttributeError: pass
                    return await self.responder.respond(interaction, message=link_data)
                data["titles"].append(link_data["title"])
                data["urls"].append(link_data["url"])
                data["durations"].append(link_data["duration"])
                data["uploaders"].append(link_data["uploader"])
        
        # Send tracks to player for processing
        await current_player.add_to_queue(interaction, data)
    
    # Does a youtube video search query and processes up to 25 user choices
    @play_group.command(
        name=f"{text['MUSIC_PLAY_SEARCH_NAME']}",
        description=f"{text['MUSIC_PLAY_SEARCH_DESC']}")
    @app_commands.describe(search=f"{text['MUSIC_PLAY_SEARCH_DESCRIBE']}")
    @not_blacklisted_ac()
    async def play_search(self, interaction:discord.Interaction, search:str=None) -> None:
        await interaction.response.defer()
        if not search: return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'], response_type=1)
        
        # Setup
        current_player = await self.setup_play(interaction)
        if not current_player: return
        
        # Process search query
        query = await process_video_search(search)
        if isinstance(query, discord.Embed):
            try:
                if not current_player.client.is_playing() and not current_player.is_paused:
                    current_player.manual_dc = True
                    await current_player.disconnect()
                    del players[interaction.guild.id]
            except AttributeError: pass
            return await self.responder.respond(interaction, message=query, response_type=1)
        view = VideoSearchView(self.bot, query, current_player)
        await interaction.followup.send(f"{text['MUSIC_PLAY_SEARCH_RESULTS']} **{search}**", view=view)

    # Does a youtube playlist search query and processes up to 25 user choices
    @play_group.command(
        name=f"{text['MUSIC_PLAY_SEARCH_PL_NAME']}",
        description=f"{text['MUSIC_PLAY_SEARCH_PL_DESC']}")
    @app_commands.describe(search=f"{text['MUSIC_PLAY_SEARCH_PL_DESCRIBE']}")
    @not_blacklisted_ac()
    async def play_search_pl(self, interaction:discord.Interaction, search:str=None) -> None:
        await interaction.response.defer()
        if not search: return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'], response_type=1)
        
        # Setup
        current_player = await self.setup_play(interaction)
        if not current_player: return
        
        # Process search query
        query = await process_playlist_search(search)
        if isinstance(query, discord.Embed):
            try:
                if not current_player.client.is_playing() and not current_player.is_paused:
                    current_player.manual_dc = True
                    await current_player.disconnect()
                    del players[interaction.guild.id]
            except AttributeError: pass
            return await self.responder.respond(interaction, message=query, response_type=1)
        view = PlaylistSearchView(self.bot, query, current_player)
        await interaction.followup.send(f"{text['MUSIC_PLAY_SEARCH_RESULTS']} **{search}**", view=view)

    # Adds songs from history to the queue
    @play_group.command(
        name=f"{text['MUSIC_PLAY_HISTORY_NAME']}",
        description=f"{text['MUSIC_PLAY_HISTORY_DESC']}")
    @app_commands.describe(id=f"{text['MUSIC_PLAY_HISTORY_ID_DESC']}")
    @not_blacklisted_ac()
    async def play_history(self, interaction:discord.Interaction, id:str=None) -> None:
        await interaction.response.defer()
        if not id or not id.isnumeric(): return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'], response_type=1)
        
        # Setup
        current_player = await self.setup_play(interaction)
        if not current_player: return
        
        # Add requested item from song history
        await self.responder.respond(interaction, GREEN, text['MUSIC_PLAY_HISTORY_CHECKING'])
        
        # Send tracks to player for processing
        await current_player.pick_from_history(interaction, int(id))

    # Shows the current player's sound queue
    @queue_group.command(
        name=f"{text['MUSIC_QUEUE_SHOW_NAME']}",
        description=f"{text['MUSIC_QUEUE_SHOW_DESC']}")
    @app_commands.describe(url=f"{text['MUSIC_QUEUE_DESC_URL']}")
    @app_commands.choices(url=[Choice(name=f"{text['CHOICE_YES']}", value=1)])
    @not_blacklisted_ac()
    async def queue_show(self, interaction:discord.Interaction, url:Choice[int]=0) -> None:
        
        # If we're not playing anything
        if interaction.guild.id not in players:
            return await self.responder.respond(interaction, RED, text['MUSIC_NO_INSTANCE'])
        
        # If yes, grab current player
        current_player:Player = players[interaction.guild.id]
        
        # Show queue
        queue = current_player.queue.show(False if url == 0 else True)
        if not queue:
            await self.responder.respond(interaction, RED, text['MUSIC_QUEUE_EMPTY'])
        else:
            if current_player.queue.len() > 15:
                lines = queue.split("\n")
                chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
                embed = discord.Embed(title=f"{text['MUSIC_QUEUE_SHOW']}", color=GREEN)
                embed.description="\n".join(chunks[0])
                embed.set_footer(text=f"{text['MUSIC_QUEUE_LENGHT']} {current_player.queue.timedelta()}")
                view = PageSwitcher(self.bot, embed, chunks)
                await interaction.response.send_message(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title=f"{text['MUSIC_QUEUE_SHOW']}",
                    description=f"{queue}", color=GREEN)
                embed.set_footer(text=f"{text['MUSIC_QUEUE_LENGHT']} {current_player.queue.timedelta()}")
                await interaction.response.send_message(embed=embed)

    # Clears the current song queue
    @queue_group.command(
        name=f"{text['MUSIC_QUEUE_CLEAR_NAME']}",
        description=f"{text['MUSIC_QUEUE_CLEAR_DESC']}")
    @app_commands.describe(id=f"{text['MUSIC_QUEUE_DESC_ID']}")
    @not_blacklisted_ac()
    async def queue_clear(self, interaction:discord.Interaction, id:int=0) -> None:
        
        # If we're not playing anything
        if interaction.guild.id not in players:
            return await self.responder.respond(interaction, RED, text['MUSIC_NO_INSTANCE'])
        
        # If yes, grab current player
        current_player:Player = players[interaction.guild.id]
        
        # Clear the entire queue
        if id == 0:
            current_player.queue.clear()
            await self.responder.respond(interaction, GREEN, text['MUSIC_QUEUE_CLEAR'])
        
        # Clear specific item
        else:
            if not isinstance(id, int):
                return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'], response_type=1)
            cleared = current_player.queue.clear_specific(id)
            if cleared:
                embed = discord.Embed(
                    title=f"{text['MUSIC_QUEUE_REMOVED']}",
                    description=f"``{cleared['title']}``",
                    color=GREEN)
            else:
                embed = discord.Embed(
                    title=f"{text['ERROR']}",
                    description=f"{text['MUSIC_QUEUE_OUT_OF_RANGE']}",
                    color=RED)
            await self.responder.respond(interaction, message=embed)
    
    # Shows the guild's song history
    @history_group.command(
        name=f"{text['MUSIC_HISTORY_SHOW_NAME']}",
        description=f"{text['MUSIC_HISTORY_SHOW_DESC']}")
    @app_commands.describe(url=f"{text['MUSIC_HISTORY_DESC_URL']}")
    @app_commands.choices(url=[Choice(name=f"{text['CHOICE_YES']}", value=1)])
    @not_blacklisted_ac()
    async def history_show(self, interaction:discord.Interaction, url:Choice[int]=0) -> None:
        
        # Show current history
        history = await show_history(interaction.guild.id, True if url !=0 else False)
        
        # If it doesn't exist
        if not history:
            return await self.responder.respond(interaction, RED, text['MUSIC_HISTORY_EMPTY'])
        
        # Show if it does
        await self.responder.respond(interaction, color=GREEN, title=text['MUSIC_HISTORY_TITLE'], message=history)
    
    # Clears the guild's song history
    @history_group.command(
        name=f"{text['MUSIC_HISTORY_CLEAR_NAME']}",
        description=f"{text['MUSIC_HISTORY_CLEAR_DESC']}")
    @not_blacklisted_ac()
    async def history_clear(self, interaction:discord.Interaction) -> None:
        clear = await clear_history(interaction.guild.id)
        if clear:
            embed = discord.Embed(
                description=f"{text['MUSIC_HISTORY_CLEAR']}", color=GREEN)
        else:
            embed = discord.Embed(
                description = f"{text['MUSIC_HISTORY_NOT_CLEAR']}", color=RED)
        await self.responder.respond(interaction, message=embed)
    
    # Shuffles the current queue
    @commands.hybrid_command(
        name=f"{text['MUSIC_SHUFFLE_NAME']}",
        description=f"{text['MUSIC_SHUFFLE_DESC']}")
    @not_blacklisted()
    async def shuffle(self, ctx:Context):
        
        # If we're doing nothing
        if ctx.guild.id not in players:
            embed = discord.Embed(
                description=f"{text['MUSIC_NO_INSTANCE']}",
                color=0xd91313)
            return await ctx.send(embed=embed)
        
        # If yes, grab current player object
        current_player:Player = players[ctx.guild.id]
        
        # Shuffle
        current_player.queue.shuffle()
        
        embed = discord.Embed(
            description=f"{text['MUSIC_SHUFFLE_SHUFFLED']}",
            color=GREEN)
        await ctx.send(embed=embed)
    
    # Shows a view with multimedia controls
    @commands.hybrid_command(
        name=f"{text['MUSIC_SHOWCT_NAME']}",
        description=f"{text['MUSIC_SHOWCT_DESC']}")
    @not_blacklisted()
    async def show_controls(self, ctx:Context):
        
        # If we're doing nothing
        if ctx.guild.id not in players:
            return await self.responder.respond(ctx, RED, text['MUSIC_NO_INSTANCE'])
        
        await self.responder.respond(ctx, view=MediaControls(self.bot, players[ctx.guild.id]))

    # Please
    @commands.Cog.listener("on_voice_state_update")
    async def on_vc_update(self, member, before, after):
        if member == self.bot.user:
            if before.channel and not after.channel:
                if before.channel.guild.id in players:
                    current_player:Player = players[before.channel.guild.id]
                    try:
                        current_player.manual_dc = True
                        await current_player.disconnect()
                        del players[before.channel.guild.id]
                    except AttributeError: pass

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Music(bot))