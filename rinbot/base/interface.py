import discord, random
from discord.ext.commands import Bot, Cog
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang
from rinbot.music.youtube import process_playlist

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

class MediaControls(discord.ui.View):
    def __init__(self, bot:Bot, player):
        super().__init__(timeout=None)
        self.bot = bot
        self.player = player
        self.id = "MediaControls"
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

class VideoSearchCancelButton(discord.ui.Button):
    def __init__(self, bot, player):
        self.bot:Bot = bot
        self.player = player
        super().__init__(style=discord.ButtonStyle.red, label=f"{text['INTERFACE_SEARCH_CANCEL_BUTTON']}", custom_id="VideoSearchCancel")

    async def callback(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        if not self.player.client.is_playing() and not self.player.is_paused:
            self.player.manual_dc = True
            await self.player.disconnect()

class VideoSearchSelect(discord.ui.Select):
    def __init__(self, bot, results, player):
        self.bot:Bot = bot
        self.results = results
        self.player = player
        temp_titles = []
        for index, item in enumerate(self.results["titles"]):
            if item in temp_titles:
                self.results["titles"].pop(index)
                self.results["urls"].pop(index)
                self.results["durations"].pop(index)
                self.results["uploaders"].pop(index)
            temp_titles.append(item)
        options=[discord.SelectOption(label=str(f"{result}")) for result in self.results["titles"]]
        super().__init__(placeholder=f"{text['INTERFACE_SEARCH_PLACEHOLDER']}", options=options,
                         min_values=1, max_values=len(results["titles"]))
        
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        for index, video in enumerate(self.results["titles"]):
            for selected in self.values:
                if selected == video:
                    data["titles"].append(self.results["titles"][index])
                    data["urls"].append(self.results["urls"][index])
                    data["durations"].append(self.results["durations"][index])
                    data["uploaders"].append(self.results["uploaders"][index])
        # Send tracks to player for processing
        await self.player.add_to_queue(interaction, data)

class PlaylistSearchSelect(discord.ui.Select):
    def __init__(self, bot, results, player):
        self.bot:Bot = bot
        self.results = results
        self.player = player
        temp_titles = []
        for index, item in enumerate(self.results["titles"]):
            if item in temp_titles:
                self.results["titles"].pop(index)
                self.results["urls"].pop(index)
            temp_titles.append(item)
        options=[discord.SelectOption(label=str(f"{result}")) for result in self.results["titles"]]
        super().__init__(placeholder=f"{text['INTERFACE_SEARCH_PLACEHOLDER']}", options=options,
                         min_values=1, max_values=len(results["titles"]))
    
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await interaction.message.delete()
        data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        for index, playlist in enumerate(self.results["titles"]):
            for selected in self.values:
                if selected == playlist:
                    pl_data = await process_playlist(self.results["urls"][index])
                    for index, item in enumerate(pl_data["titles"]):
                        data["titles"].append(item)
                        data["urls"].append(pl_data["urls"][index])
                        data["durations"].append(pl_data["durations"][index])
                        data["uploaders"].append(pl_data["uploaders"][index])
                    embed = discord.Embed(
                        description=f"{text['MUSIC_ADDING_PL'][0]} `{pl_data['count']}` {text['MUSIC_ADDING_PL'][1]} `{pl_data['title']}`",
                        color=YELLOW)
                    await interaction.followup.send(embed=embed)
                    # Send tracks to player for processing
                    await self.player.add_to_queue(interaction, data)

class VideoSearchView(discord.ui.View):
    def __init__(self, bot, results, player):
        super().__init__(timeout=60)
        self.is_persistent = False
        self.add_item(VideoSearchSelect(bot, results, player))
        self.add_item(VideoSearchCancelButton(bot, player))

class PlaylistSearchView(discord.ui.View):
    def __init__(self, bot, results, player):
        super().__init__(timeout=60)
        self.is_persistent = False
        self.add_item(PlaylistSearchSelect(bot, results, player))
        self.add_item(VideoSearchCancelButton(bot, player))