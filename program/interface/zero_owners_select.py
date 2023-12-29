import discord
from discord.ext.commands import Bot, Cog
from program.base.helpers import load_lang

text = load_lang()

class ZeroOwnersSelect(discord.ui.Select):    
    def __init__(self, bot:Bot=None, users:list=None, cog:Cog=None, uid=None):
        self.bot = bot
        self.cog = cog
        self.uid = uid
        options=[discord.SelectOption(label=str(user)) for user in users]
        super().__init__(placeholder=f"{text['INTERFACE_ZEROOWNERS_SELECT_PLACEHOLDER']}",
                         options=options, min_values=1, max_values=1)
        print(self.cog.selected_user)
    
    async def callback(self, interaction:discord.Interaction):
        if self.uid == interaction.user.id:
            await interaction.response.defer()
            self.cog.selected_user = self.values[0]
        else:
            pass
class ZeroOwnersView(discord.ui.View):
    def __init__(self, bot, users, cog, uid):
        self.bot = bot
        self.users = users
        self.cog = cog
        self.uid = uid
        super().__init__()
        self.add_item(ZeroOwnersSelect(self.bot, self.users, self.cog, self.uid))