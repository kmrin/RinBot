"""
#### RinBot's interfaces (views)
"""

# Imports
import discord, random, wavelink
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang

# Load text
text = load_lang()

# Paginator
class Paginator(discord.ui.View):
    def __init__(self, embed:discord.Embed, chunks:list, current_chunk=0):
        super().__init__(timeout=None)
        self.embed = embed
        self.chunks = chunks
        self.current_chunk = current_chunk
        self.max_chunk = len(chunks) - 1
        self.id = 'Paginator'
        self.is_persistent = True
    
    @discord.ui.button(label=f"{text['INTERFACE_PAGINATOR_PREV']}", style=discord.ButtonStyle.green, custom_id='prev')
    async def prev(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == 0:
            self.current_chunk -= 1
        self.embed.description = "\n".join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)
    @discord.ui.button(label=f"{text['INTERFACE_PAGINATOR_NEXT']}", style=discord.ButtonStyle.green, custom_id='next')
    async def next(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        if not self.current_chunk == self.max_chunk:
            self.current_chunk += 1
        self.embed.description = "\n".join(self.chunks[self.current_chunk])
        await interaction.edit_original_response(embed=self.embed)

# Rock Paper Scissors
class RockPaperScissors(discord.ui.Select):
    
    def __init__(self):
        
        options = [
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_SCISSORS'][0]}", description=f"{text['INTERFACE_FUN_SCISSORS'][1]}", emoji="✂"),
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_ROCK'][0]}", description=f"{text['INTERFACE_FUN_ROCK'][1]}", emoji="🪨"),
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_PAPER'][0]}", description=f"{text['INTERFACE_FUN_PAPER'][1]}", emoji="🧻"),]
        super().__init__(
            placeholder=f"{text['INTERFACE_FUN_TAUNT']}",
            min_values=1,
            max_values=1,
            options=options,)

    async def callback(self, interaction: discord.Interaction):
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2,}
        
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]
        
        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]
        
        result_embed = discord.Embed(color=0x9C84EF)
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if user_choice_index == bot_choice_index:
            result_embed.description = f"**{text['INTERFACE_FUN_DRAW']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0xF59E42
        elif user_choice_index == 0 and bot_choice_index == 2:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 1 and bot_choice_index == 0:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 2 and bot_choice_index == 1:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        else:
            result_embed.description = (
                f"**\n{text['INTERFACE_FUN_I_WON!']}** {text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}.")
            result_embed.colour = 0xE02B2B
        
        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None)
class RockPaperScissorsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RockPaperScissors())

# Heads & Tails
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

# Zero owners
class ZeroOwnersSelect(discord.ui.Select):    
    def __init__(self, users:list=None, cog=None, uid=None):
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
    def __init__(self, users, cog, uid):
        self.users = users
        self.cog = cog
        self.uid = uid
        super().__init__()
        self.add_item(ZeroOwnersSelect(self.users, self.cog, self.uid))

# Media controls
class MediaControls(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player:wavelink.Player = player
        self.id = "MediaControls"
        self.is_persistent = True
    
    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.green, custom_id='togglebutton')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.pause(not self.player.paused)
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.blurple, custom_id='skipbutton')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.skip(force=True)
    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger, custom_id='stopbutton')
    async def disconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.disconnect()

# Video search select
class VideoSearchSelect(discord.ui.Select):
    def __init__(self, view, results, player):
        self.search_view:discord.ui.View = view
        self.player:wavelink.Player = player
        self.results:list = results
        self.titles = []
        self.added = []
        for item in self.results:
            if item.title not in self.titles:
                self.titles.append(item.title)
            else:
                self.results.remove(item)
        options=[discord.SelectOption(label=str(f"{result}")) for result in self.titles[:25]]
        super().__init__(placeholder=f"Select", options=options, min_values=1, max_values=len(self.titles))
    
    async def callback(self, interaction:discord.Interaction):
        for video in self.results:
            for selected in self.values:
                if selected == video.title and selected not in self.added:
                    self.player.results.append(video)
                    self.added.append(video.title)
        message = [f"**{index+1}.** {item}" for index, item in enumerate(self.added)]
        message = "\n".join(message)
        embed = discord.Embed(title=" 📃  Added to queue", description=message, color=0xFFFFFF)
        await interaction.response.edit_message(content=None, embed=embed, view=None)
        self.search_view.stop()
class VideoSearchView(discord.ui.View):
    def __init__(self, results, player):
        super().__init__()
        self.timeout = 60
        self.is_persistent = False
        self.add_item(VideoSearchSelect(self, results, player))

    async def on_timeout(self):
        self.stop()

class VideoSearchView(discord.ui.View):
    def __init__(self, results, player):
        super().__init__()
        self.timeout = 60
        self.is_persistent = False
        self.add_item(VideoSearchSelect(self, results, player))
    
    async def on_timeout(self):
        self.stop()