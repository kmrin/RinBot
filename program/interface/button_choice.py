import discord
from program.base.helpers import load_lang

text = load_lang()

class ButtonChoice(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
    @discord.ui.button(label=f"{text['INTERFACE_FUN_HEADS']}", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "heads"
        self.stop()
    @discord.ui.button(label=f"{text['INTERFACE_FUN_TAILS']}", style=discord.ButtonStyle.blurple)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "tails"
        self.stop()