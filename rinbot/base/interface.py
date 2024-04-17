"""
Interfaces (Views)
"""

import random
import discord

from discord import Interaction
from typing import Awaitable

from rinbot.valorant.db import DATABASE
from rinbot.music.player import Player

from .colours import Colour
from .exception_handler import log_exception
from .json_loader import get_lang

text = get_lang()

class Paginator(discord.ui.View):
    def __init__(self, embed: discord.Embed, chunks: list, current_chunk=0):
        try:
            super().__init__(timeout=None)

            self.id = 'Paginator'
            self.is_persistent = True

            self.embed = embed
            self.chunks = chunks
            self.current_chunk = current_chunk
            self.max_chunk = len(chunks) - 1
            
            self.page.label = f'{self.current_chunk + 1}/{self.max_chunk + 1}'
        except Exception as e:
            log_exception(e)
    
    async def __update_button_states(self):
        try:
            # Change page label
            self.page.label = f'{self.current_chunk + 1}/{self.max_chunk + 1}'
            
            # Page is at starting point
            if self.current_chunk == 0:
                self.home.disabled = True
                self.prev.disabled = True
                self.next.disabled = False
                self.end.disabled = False
            
            # Page is between min and max
            if self.current_chunk > 0 and self.current_chunk < self.max_chunk:
                self.home.disabled = False
                self.prev.disabled = False
                self.next.disabled = False
                self.end.disabled = False
            
            # Page is at max point
            if self.current_chunk == self.max_chunk:
                self.home.disabled = False
                self.prev.disabled = False
                self.next.disabled = True
                self.end.disabled = True
        except Exception as e:
            log_exception(e)

    @discord.ui.button(label='⏪', style=discord.ButtonStyle.blurple, custom_id='home', disabled=True)
    async def home(self, interaction: Interaction, button: discord.ui.button):
        try:
            await interaction.response.defer()

            self.current_chunk = 0

            self.embed.description = '\n'.join(self.chunks[self.current_chunk])

            await self.__update_button_states()
            await interaction.edit_original_response(embed=self.embed, view=self)
        except Exception as e:
            log_exception(e)

    @discord.ui.button(label='◀️', style=discord.ButtonStyle.green, custom_id='prev', disabled=True)
    async def prev(self, interaction: Interaction, button: discord.ui.button):
        try:
            await interaction.response.defer()

            if not self.current_chunk == 0:
                self.current_chunk -= 1

            self.embed.description = '\n'.join(self.chunks[self.current_chunk])

            await self.__update_button_states()
            await interaction.edit_original_response(embed=self.embed, view=self)
        except Exception as e:
            log_exception(e)

    @discord.ui.button(label='', style=discord.ButtonStyle.grey, custom_id='page', disabled=True)
    async def page(self, interaction: Interaction, button: discord.ui.button):
        pass

    @discord.ui.button(label='▶️', style=discord.ButtonStyle.green, custom_id='next')
    async def next(self, interaction: Interaction, button: discord.ui.button):
        try:
            await interaction.response.defer()

            if not self.current_chunk == self.max_chunk:
                self.current_chunk += 1

            self.embed.description = '\n'.join(self.chunks[self.current_chunk])

            await self.__update_button_states()
            await interaction.edit_original_response(embed=self.embed, view=self)
        except Exception as e:
            log_exception(e)

    @discord.ui.button(label='⏩', style=discord.ButtonStyle.blurple, custom_id='end')
    async def end(self, interaction: Interaction, button: discord.ui.button):
        try:
            await interaction.response.defer()

            self.current_chunk = self.max_chunk

            self.embed.description = '\n'.join(self.chunks[self.current_chunk])

            await self.__update_button_states()
            await interaction.edit_original_response(embed=self.embed, view=self)
        except Exception as e:
            log_exception(e)

class ButtonChoice(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label=text['INTERFACE_FUN_HEADS'], style=discord.ButtonStyle.blurple)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "heads"
        self.stop()

    @discord.ui.button(label=text['INTERFACE_FUN_TAILS'], style=discord.ButtonStyle.blurple)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = "tails"
        self.stop()

class RockPaperScissors(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=text['INTERFACE_FUN_SCISSORS'][0],
                description=text['INTERFACE_FUN_SCISSORS'][1],
                emoji="✂"),
            discord.SelectOption(
                label=text['INTERFACE_FUN_ROCK'][0],
                description=text['INTERFACE_FUN_ROCK'][1],
                emoji="🪨"),
            discord.SelectOption(
                label=text['INTERFACE_FUN_PAPER'][0],
                description=text['INTERFACE_FUN_PAPER'][1],
                emoji="🧻")
        ]
        super().__init__(
            placeholder=text['INTERFACE_FUN_TAUNT'],
            options=options
        )
    
    async def callback(self, interaction: Interaction):
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2, }

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

class Valorant2FAView(discord.ui.Modal, title=text['INTERFACE_VAL_2FA_TITLE']):
    def __init__(self, interaction: Interaction, db: DATABASE, cookie: dict, message: str, label: str) -> None:
        super().__init__(timeout=60)
        
        self.interaction = interaction
        self.db = db
        self.cookie = cookie
        self.two2fa.placeholder = message
        self.two2fa.label = label

    two2fa = discord.ui.TextInput(label=text['INTERFACE_VAL_2FA_LABEL'], max_length=6, style=discord.TextStyle.short)

    async def on_submit(self, interaction: Interaction) -> Awaitable[None]:
        code = self.two2fa.value

        if code:
            cookie = self.cookie
            user_id = self.interaction.user.id
            auth = self.db.auth
            auth.locale_code = self.interaction.locale
            
            async def send_embed(content: str) -> Awaitable[None]:
                embed = discord.Embed(
                    description=content, color=Colour.PURPLE
                )

                if interaction.response.is_done():
                    return await interaction.followup.send(embed=embed, ephemeral=True)

                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if not code.isdigit():
                return await send_embed(f"`{code}` {text['INTERFACE_VAL_2FA_INVALID']}")

            auth = await auth.give2facode(code, cookie)

            if auth['auth'] == 'response':
                login = await self.db.login(user_id, auth)
                if login['auth']:
                    return await send_embed(f"{text['INTERFACE_VAL_2FA_LOGGED']} **{login['player']}**!")
                return await send_embed(login['error'])
            elif auth['auth'] == 'failed':
                return await send_embed(f"{text['INTERFACE_VAL_2FA_WRONG']}")
            else:
                return await send_embed(f"{text['INTERFACE_VAL_2FA_ERROR']}")

class VideoSearchSelect(discord.ui.Select):
    def __init__(self, view, results):
        self.search_view: VideoSearchView = view
        self.final_results = []
        self.titles = []
        
        # Prevent duplicate videos
        for item in results:
            if item['title'] not in self.titles:
                self.final_results.append(item)
                self.titles.append(item['title'])
        
        options = [discord.SelectOption(label=title) for title in self.titles[:25]]
        
        super().__init__(
            placeholder=text['INTERFACE_VIDEO_SELECT_PLACEHOLDER'],
            options=options,
            min_values=1,
            max_values=len(self.titles)
        )
    
    async def callback(self, interaction: Interaction):
        added = []
        
        for video in self.final_results:
            for selected in self.values:
                if selected == video['title'] and video not in added:
                    self.search_view.result.append(video)
                    added.append(video)
        
        message = [f'**{i+1}.** `{item["duration"]}` - {item["title"]}' for i, item in enumerate(added)]
        message = '\n'.join(message)
        
        embed = discord.Embed(
            title=text['INTERFACE_VIDEO_SELECT_ADDED'],
            description=message,
            colour=Colour.PURPLE
        )
        
        await interaction.response.edit_message(content=None, embed=embed, view=None)
        
        self.search_view.stop()

class VideoSearchView(discord.ui.View):
    def __init__(self, results):
        super().__init__()
        
        self.result = []
        self.timeout = 60
        self.is_persistent = False
        self.add_item(VideoSearchSelect(self, results))
    
    async def on_timeout(self):
        self.stop()

class MediaControls(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player: Player = player
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
        self.player.home = None
        await self.player.disconnect()
