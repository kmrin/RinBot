import discord
from discord.ext.commands import Bot
from program.base.helpers import load_lang

text = load_lang()

class PageSwitcher(discord.ui.View):
    def __init__(self, bot:Bot, embed:discord.Embed, chunks:list, current_chunk=0):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = embed
        self.chunks = chunks
        self.current_chunk = current_chunk
        self.max_chunk = len(chunks) - 1
        self.id = 'PageSwitcher'
        self.is_persistent = True
    
    @discord.ui.button(label=f"{text['INTERFACE_PAGESWITCHER_PREV']}", style=discord.ButtonStyle.green, custom_id='prev')
    async def prev(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == 0:
            self.current_chunk -= 1
        self.embed.description = '\n'.join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)
    @discord.ui.button(label=f"{text['INTERFACE_PAGESWITCHER_NEXT']}", style=discord.ButtonStyle.green, custom_id='next')
    async def next(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == self.max_chunk:
            self.current_chunk += 1
        self.embed.description = '\n'.join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)