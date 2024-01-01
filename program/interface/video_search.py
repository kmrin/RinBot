import discord
from discord.ext.commands import Bot
from program.base.colors import *
from program.base.helpers import load_lang
from program.music.youtube import process_playlist

text = load_lang()

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