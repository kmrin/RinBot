"""
RinBot v1.6.0 (GitHub release)
made by rin
"""

# Imports
import discord
from discord.ext.commands import Context, Bot

# Multimedia control buttons interface
class MediaControls(discord.ui.View):
    def __init__(self, ctx:Context, bot:Bot, player):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = player
        self.id = 'MediaControls'
        self.is_persistent = True
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.green, custom_id='playbutton')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.resume()
    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.secondary, custom_id='pausebutton')
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.pause()
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.blurple, custom_id='skipbutton')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.skip()
    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger, custom_id='stopbutton')
    async def disconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.player.manual_dc = True
        await self.player.disconnect()

# Search query result selector buttons interface
class SearchSelector(discord.ui.View):
    def __init__(self, ctx:Context, bot:Bot, player):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = player
        self.id = 'SearchSelector'
        self.is_persistent = False
    
    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.secondary, custom_id='one')
    async def one(self, interaction: discord.Interaction, button: discord.ui.button):
        self.player.query_selected = 1
        await interaction.response.defer()
    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.secondary, custom_id='two')
    async def two(self, interaction: discord.Interaction, button: discord.ui.button):
        self.player.query_selected = 2
        await interaction.response.defer()
    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.secondary, custom_id='three')
    async def three(self, interaction: discord.Interaction, button: discord.ui.button):
        self.player.query_selected = 3
        await interaction.response.defer()
    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.secondary, custom_id='four')
    async def four(self, interaction: discord.Interaction, button: discord.ui.button):
        self.player.query_selected = 4
        await interaction.response.defer()

# Page switcher for long playlists (more than 20 songs)
class PlaylistPageSwitcher(discord.ui.View):
    def __init__(self, ctx:Context, bot:Bot, embed:discord.Embed, chunks:list, current_chunk=0):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.embed = embed
        self.chunks = chunks
        self.current_chunk = current_chunk
        self.max_chunk = len(chunks) - 1
        self.id = 'PlaylistPageSwitcher'
        self.is_persistent = True
    
    @discord.ui.button(label=' ⏪  Previous page', style=discord.ButtonStyle.green, custom_id='prev')
    async def prev(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == 0:
            self.current_chunk -= 1
        self.embed.description = '\n'.join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)
    @discord.ui.button(label="Next page  ⏩ ", style=discord.ButtonStyle.green, custom_id='next')
    async def next(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == self.max_chunk:
            self.current_chunk += 1
        self.embed.description = '\n'.join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)