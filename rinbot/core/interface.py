import random
import nextcord

from typing import Union, Awaitable, List, TYPE_CHECKING
from nextcord import Interaction, Embed, Colour, ButtonStyle, SelectOption
from nextcord.ui import Button, button
from nextlink.tracks import Playlist as Pl
from nextlink import Playable, Queue

from rinbot.music.player import Player
from rinbot.valorant.db import DATABASE

from .db import DBTable
from .errors import InteractionTimedOut
from .types import StoreItem
from .loggers import Loggers
from .helpers import get_localized_string, get_interaction_locale, is_hex_colour, hex_to_colour, url_to_playable, ms_to_str
from .responder import respond
from .types import Track, Playlist, VideoSearchViewMode, QueueEditViewMode

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.INTERFACE

def get_timeout_embed(locale: str) -> nextcord.Embed:
    return nextcord.Embed(
        description=get_localized_string(locale, 'INTERFACE_TIMEOUT_EMBED'),
        colour=Colour.red()
    )

class HeadsOrTails(nextcord.ui.View):
    def __init__(self, locale: str):
        super().__init__()
        self.value = None
        
        self._heads.label = get_localized_string(locale, 'INTERFACE_HEADS')
        self._tails.label = get_localized_string(locale, 'INTERFACE_TAILS')
    
    @button(label='', style=ButtonStyle.blurple)
    async def _heads(self, button: Button, interaction: Interaction) -> None:
        self.value = 'heads'
        self.stop()
    
    @button(label='', style=ButtonStyle.blurple)
    async def _tails(self, button: Button, interaction: Interaction) -> None:
        self.value = 'tails'
        self.stop()

class RockPaperScissors(nextcord.ui.Select):
    def __init__(self, locale: str):
        self.locale = locale
        options = [
            SelectOption(
                label=get_localized_string(locale, 'INTERFACE_RPS_ROCK_NAME'),
                description=get_localized_string(locale, 'INTERFACE_RPS_ROCK_DESC'),
                emoji='🪨',
                value='rock'
            ),
            SelectOption(
                label=get_localized_string(locale, 'INTERFACE_RPS_PAPER_NAME'),
                description=get_localized_string(locale, 'INTERFACE_RPS_PAPER_DESC'),
                emoji='🧻',
                value='paper'
            ),
            SelectOption(
                label=get_localized_string(locale, 'INTERFACE_RPS_SCISSORS_NAME'),
                description=get_localized_string(locale, 'INTERFACE_RPS_SCISSORS_DESC'),
                emoji='✂',
                value='scissors'
            )
        ]
        super().__init__(
            placeholder=get_localized_string(locale, 'INTERFACE_RPS_TAUNT'),
            options=options
        )
    
    async def callback(self, interaction: Interaction) -> None:
        choices = {
            'rock': 0,
            'paper': 1,
            'scissors': 2
        }
        
        choices_localizations = {
            'rock': {'pt-BR': 'pedra'},
            'paper': {'pt-BR': 'papél'},
            'scissors': {'pt-BR': 'tesoura'}
        }
        
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]
        
        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]
        
        result_embed = nextcord.Embed(colour=Colour.gold())
        result_embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        
        # Draw
        if user_choice_index == bot_choice_index:
            result_embed.description = get_localized_string(
                self.locale, 'INTERFACE_RPS_DRAW',
                user = choices_localizations[user_choice][self.locale],
                bot = choices_localizations[bot_choice][self.locale]
            )
        
        # User won
        elif      (user_choice_index == 0 and bot_choice_index == 2
             ) or (user_choice_index == 1 and bot_choice_index == 0
             ) or (user_choice_index == 2 and bot_choice_index == 1
             ):
                result_embed.description = get_localized_string(
                    self.locale, 'INTERFACE_RPS_USER',
                    user = choices_localizations[user_choice][self.locale],
                    bot = choices_localizations[bot_choice][self.locale]
                )
                result_embed.colour = Colour.green()
        
        # Bot won
        else:
            result_embed.description = get_localized_string(
                self.locale, 'INTERFACE_RPS_BOT',
                user = choices_localizations[user_choice][self.locale],
                bot = choices_localizations[bot_choice][self.locale]
            )
            result_embed.colour = Colour.red()
        
        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None
        )

class RockPaperScissorsView(nextcord.ui.View):
    def __init__(self, locale: str):
        super().__init__()
        self.add_item(RockPaperScissors(locale))

class StoreCreateRoleModal(nextcord.ui.Modal):
    def __init__(self, bot: "RinBot", original_interaction: Interaction, price: int) -> None:
        self.original_interaction = original_interaction
        self.bot = bot
        self.item = StoreItem(id=0, name='', price=price, type=0)
        self.locale = get_interaction_locale(original_interaction)
        
        super().__init__(
            get_localized_string(
                self.locale, 'INTERFACE_CREATE_ROLE_MODAL_TITLE'
            ),
            timeout = 60
        )
        
        self.role_name = nextcord.ui.TextInput(
            label = get_localized_string(self.locale, 'INTERFACE_CREATE_ROLE_MODAL_NAME'),
            placeholder=get_localized_string(self.locale, 'INTERFACE_CREATE_ROLE_MODAL_NAME_DESC'),
            min_length=1,
            max_length=32,
            required=True
        )
        self.role_colour = nextcord.ui.TextInput(
            label = get_localized_string(self.locale, 'INTERFACE_CREATE_ROLE_MODAL_COL'),
            placeholder=get_localized_string(self.locale, 'INTERFACE_CREATE_ROLE_MODAL_COL_DESC'),
            min_length=7,
            max_length=7,
            required=True
        )
        
        self.add_item(self.role_name)
        self.add_item(self.role_colour)
    
    async def on_timeout(self) -> None:
        self.stop()
        
        raise InteractionTimedOut(self.original_interaction)
            
    async def callback(self, interaction: Interaction) -> None:
        if not is_hex_colour(self.role_colour.value):
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    self.locale, 'INTERFACE_CREATE_ROLE_MODAL_INVALID_COLOUR',
                    colour = self.role_colour.value
                ),
                hidden=True
            )
                
        self.item.name = self.role_name.value
        
        # Check if item of same name already exists
        existing_item = await self.bot.db.get(
            DBTable.STORE, f'guild_id={interaction.guild.id} AND name={self.item.name}'
        )
        if existing_item:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    self.locale, 'INTERFACE_CREATE_ROLE_MODAL_ITEM_NAME_CONFLICT',
                    name = self.item.name
                ),
                hidden=True
            )
        
        # Check if there's a role of same name too
        roles = interaction.guild.roles
        for guild_role in roles:
            if guild_role.name == self.item.name:
                return await respond(
                    interaction, Colour.red(),
                    get_localized_string(
                        self.locale, 'INTERFACE_CREATE_ROLE_MODAL_ROLE_EXISTS',
                        name = self.item.name
                    ),
                    hidden=True
                )
        
        # Create role
        role = await interaction.guild.create_role(
            name=self.role_name.value, colour=hex_to_colour((self.role_colour.value))
        )
        self.item.id = role.id
        
        data = {
            'guild_id': interaction.guild.id,
            'id': self.item.id,
            'name': self.item.name,
            'price': self.item.price,
            'type': 0
        }
        
        # Add role to db
        await self.bot.db.put(DBTable.STORE, data)
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                self.locale, 'INTERFACE_CREATE_ROLE_MODAL_CREATED',
                name = self.role_name.value
            ),
            hidden=True
        )

class SetWelcomeConfirmation(nextcord.ui.View):
    def __init__(self, original_interaction: Interaction) -> None:
        super().__init__(
            timeout=60
        )
        
        self.response: bool = None
        locale = get_interaction_locale(original_interaction)
        
        self.confirm_embed = nextcord.Embed(
            description=get_localized_string(locale, 'INTERFACE_SET_WELCOME_APROVED'),
            colour=Colour.green()
        )
        self.cancel_embed = nextcord.Embed(
            description=get_localized_string(locale, 'INTERFACE_SET_WELCOME_NOT_APROVED'),
            colour=Colour.yellow()
        )
        
        self._confirm.label = get_localized_string(locale, 'INTERFACE_CONFIRM_LABEL')
        self._cancel.label = get_localized_string(locale, 'INTERFACE_CANCEL_LABEL')
    
    async def on_timeout(self) -> None:
        self.stop()
    
    @button(label='', style=ButtonStyle.green)
    async def _confirm(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        self.response = True
        self.stop()
        
        await interaction.edit_original_message(content=None, embed=self.confirm_embed, view=None)
    
    @button(label='', style=ButtonStyle.red)
    async def _cancel(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        self.response = False
        self.stop()
        
        await interaction.edit_original_message(content=None, embed=self.cancel_embed, view=None)

class Paginator(nextcord.ui.View):
    def __init__(self, embed: nextcord.Embed, chunks: List, current_chunk: bool = 0) -> None:
        super().__init__(timeout=None)
        
        self.embed = embed
        self.chunks = chunks
        self.curr_chunk = current_chunk
        self.max_chunk = len(chunks) - 1
        
        self.page.label = f'{self.curr_chunk + 1}/{self.max_chunk + 1}'

    def __update_button_states(self) -> None:
        # Change page label
        self.page.label = f'{self.curr_chunk + 1}/{self.max_chunk + 1}'
        
        # Page is at starting point
        if self.curr_chunk == 0:
            self.home.disabled = True
            self.prev.disabled = True
            self.next.disabled = False
            self.end.disabled = False
        
        # Page is between min and max
        if self.curr_chunk > 0 and self.curr_chunk < self.max_chunk:
            self.home.disabled = False
            self.prev.disabled = False
            self.next.disabled = False
            self.end.disabled = False
        
        # Page is at max point
        if self.curr_chunk == self.max_chunk:
            self.home.disabled = False
            self.prev.disabled = False
            self.next.disabled = True
            self.end.disabled = True

    @button(
        label='⏪', style=ButtonStyle.blurple, custom_id='persistent_view:home', disabled=True
    )
    async def home(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        self.curr_chunk = 0
        self.embed.description = '\n'.join(self.chunks[self.curr_chunk])
        self.__update_button_states()
        
        await interaction.edit_original_message(embed=self.embed, view=self)
    
    @button(
        label='◀️', style=ButtonStyle.green, custom_id='persistent_view:prev', disabled=True
    )
    async def prev(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        if not self.curr_chunk == 0:
            self.curr_chunk -= 1
        
        self.embed.description = '\n'.join(self.chunks[self.curr_chunk])
        self.__update_button_states()
        
        await interaction.edit_original_message(embed=self.embed, view=self)
    
    @button(
        label='', style=ButtonStyle.grey, custom_id='persistent_view:page', disabled=True
    )
    async def page(self, button: Button, interaction: Interaction) -> None:
        pass
    
    @button(
        label='▶️', style=ButtonStyle.green, custom_id='persistent_view:next'
    )
    async def next(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        if not self.curr_chunk == self.max_chunk:
            self.curr_chunk += 1
        
        self.embed.description = '\n'.join(self.chunks[self.curr_chunk])
        self.__update_button_states()
        
        await interaction.edit_original_message(embed=self.embed, view=self)
    
    @button(
        label='⏩', style=ButtonStyle.blurple, custom_id='persistent_view:end'
    )
    async def end(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        self.curr_chunk = self.max_chunk
        self.embed.description = '\n'.join(self.chunks[self.curr_chunk])
        self.__update_button_states()
        
        await interaction.edit_original_message(embed=self.embed, view=self)

class MediaControls(nextcord.ui.View):
    def __init__(self, player: Player) -> None:
        super().__init__(timeout=None)
        
        self.id = 'MediaControls'
        self.locale = player.locale
        self.player = player
        
        self.update_buttons()
        self._favourite.label = get_localized_string(
            player.locale, 'INTERFACE_FAVOURITE')
    
    def show_url_button(self, url: str) -> None:
        url_button = Button(
            label=' 🔗  Link', style=ButtonStyle.link, url=url
        )

        self.add_item(url_button)
    
    def update_buttons(self) -> None:        
        # Update volume value button
        self._vol_value.label = f'{self.player.volume}%'
    
    # Play / Pause
    @button(label='⏯️', style=ButtonStyle.green, custom_id='togglebutton')
    async def _toggle(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.pause(not self.player.paused)
    
    # Previous
    @button(label='⏮️', style=ButtonStyle.blurple, custom_id='prevbutton')
    async def _prev(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.play_last_in_history()
    
    # Next
    @button(label='⏭️', style=ButtonStyle.blurple, custom_id='nextbutton')
    async def _next(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.skip(force=True)
    
    # Stop
    @button(label='⏹️', style=ButtonStyle.red, custom_id='stopbutton')
    async def _stop(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.dc()
    
    # Repeat
    @button(label='🔄️', style=ButtonStyle.grey, custom_id='repeatbutton')
    async def _repeat(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        self.player.queue.put_at(0, self.player.current)
        
        await interaction.edit_original_message(view=self)
    
    # Volume down
    @button(label='🔉', style=ButtonStyle.blurple, custom_id='voldown')
    async def _vol_down(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        if self.player.volume <= 0:
            return
        
        await self.player.set_volume(self.player.volume - 10)
        self.update_buttons()
        
        await interaction.edit_original_message(view=self)
    
    # Volume value
    @button(label='', style=ButtonStyle.grey, custom_id='volvalue', disabled=True)
    async def _vol_value(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
    
    # Volume up
    @button(label='🔊', style=ButtonStyle.blurple, custom_id='volup')
    async def _vol_up(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        
        if self.player.volume >= 100:
            return
        
        await self.player.set_volume(self.player.volume + 10)
        self.update_buttons()
        
        await interaction.edit_original_message(view=self)
    
    # Favourite
    @button(label='', style=ButtonStyle.green, custom_id='favoritebutton')
    async def _favourite(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer()
        await self.player.add_to_user_favourites(interaction.user.id)

class FavouritesPlayView(nextcord.ui.View):
    def __init__(self, bot: 'RinBot', locale: str, favourites: Union[List[Track], List[Playlist]], mode: VideoSearchViewMode) -> None:
        super().__init__(timeout=60)
        
        self.user_choices: List[Playable] = []
        self.bot = bot
        self.locale = locale
        self.mode = mode
        self.favourites = favourites
        self.current_page = 0
        self.favourites_parts = self.split_favourites(favourites)
        
        self.prev_button = Button(label='◀️', style=ButtonStyle.green, custom_id='buttonprev')
        self.next_button = Button(label='▶️', style=ButtonStyle.green, custom_id='buttonnext')
        self.prev_button.callback = self.callback_prev
        self.next_button.callback = self.callback_next
        
        self.select = self.create_select()
        
        if mode.value == 0:
            self.select.callback = self.callback_select_track
        elif mode.value == 1:
            self.select.callback = self.callback_select_playlist
        
        self.add_item(self.select)
        if len(self.favourites_parts) > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
        
        self.update_buttons()

    async def on_timeout(self) -> None:
        self.stop()
    
    def split_favourites(self, favourites) -> List[Union[List[Track], List[Playlist]]]:
        return [favourites[i:i+25] for i in range(0, len(favourites), 25)]
    
    def create_select(self) -> nextcord.ui.Select:
        options = [
            nextcord.SelectOption(
                label=item.title, value=item.url,
                description=get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_PLAYLIST_DESC',
                    tracks=item.count, uploader=item.uploader
                )
                if self.mode.value == 1 else get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_TRACK_DESC',
                    duration=item.duration, uploader=item.uploader
                )
            )
            for item in self.favourites_parts[self.current_page]
        ]
        
        return nextcord.ui.Select(
            placeholder=get_localized_string(
                self.locale, 'INTERFACE_FAV_PICK_PLACEHOLDER'
            ),
            options=options,
            min_values=1,
            max_values=len(options)
        )
    
    def update_buttons(self) -> None:
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.favourites_parts) - 1)
    
    def update_select(self) -> None:
        options = [
            nextcord.SelectOption(
                label=item.title, value=item.url,
                description=get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_PLAYLIST_DESC',
                    tracks=item.count, uploader=item.uploader
                )
                if self.mode.value == 1 else get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_TRACK_DESC',
                    duration=item.duration, uploader=item.uploader
                )
            )
            for item in self.favourites_parts[self.current_page]
        ]
        
        self.select.options = options
        self.select.max_values = len(options)
    
    async def callback_select_track(self, interaction: Interaction) -> None:
        self.user_choices = [await url_to_playable(url) for url in self.select.values]
        
        embed = Embed(
            description=get_localized_string(
                self.locale, 'INTERFACE_FAV_PLAYING'
            ),
            colour=Colour.gold()
        )
        
        self.stop()
        await interaction.response.edit_message(content=None, embed=embed, view=None)
    
    async def callback_select_playlist(self, interaction: Interaction) -> None:        
        for url in self.select.values:
            playlist: Pl = await Playable.search(url,)
            
            for track in playlist.tracks:
                self.user_choices.append(track)
            
        embed = Embed(
            description=get_localized_string(
                self.locale, 'INTERFACE_FAV_PLAYING'
            ),
            colour=Colour.gold()
        )
        
        self.stop()
        await interaction.response.edit_message(content=None, embed=embed, view=None)
    
    async def callback_prev(self, interaction: Interaction) -> None:
        self.current_page -= 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)
    
    async def callback_next(self, interaction: Interaction) -> None:
        self.current_page += 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)

class FavouritesEditView(nextcord.ui.View):
    def __init__(self, bot: 'RinBot', locale: str, favourites: List, mode: VideoSearchViewMode) -> None:
        super().__init__(timeout=60)
        
        self.bot = bot
        self.locale = locale
        self.mode = mode
        self.favourites = favourites
        self.current_page = 0
        self.favourites_parts = self.split_favourites(favourites)
        
        self.prev_button = Button(label='◀️', style=ButtonStyle.green, custom_id='buttonprev')
        self.next_button = Button(label='▶️', style=ButtonStyle.green, custom_id='buttonnext')
        self.prev_button.callback = self.callback_prev
        self.next_button.callback = self.callback_next
        
        self.select = self.create_select()
        self.select.callback = self.callback_select
        
        self.add_item(self.select)
        if len(self.favourites_parts) > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
        
        self.update_buttons()

    async def on_timeout(self) -> None:
        self.stop()
    
    def split_favourites(self, favourites):
        return [favourites[i:i+25] for i in range(0, len(favourites), 25)]
    
    def create_select(self) -> nextcord.ui.Select:
        options = [
            nextcord.SelectOption(
                label=item[1], value=str(i),
                description=get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_PLAYLIST_DESC',
                    tracks=item[3], uploader=item[4]
                )
                if self.mode.value == 1 else get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_TRACK_DESC',
                    duration=item[3], uploader=item[4]
                )
            )
            for i, item in enumerate(self.favourites_parts[self.current_page])
        ]
        
        return nextcord.ui.Select(
            placeholder=get_localized_string(
                self.locale, 'INTERFACE_FAV_EDIT_PLACEHOLDER'
            ),
            options=options,
            min_values=1,
            max_values=len(options)
        )
    
    def update_buttons(self) -> None:
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.favourites_parts) - 1)
    
    def update_select(self) -> None:
        options = [
            nextcord.SelectOption(
                label=item[1], value=str(i),
                description=get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_PLAYLIST_DESC',
                    tracks=item[3], uploader=item[4]
                )
                if self.mode.value == 1 else get_localized_string(
                    self.locale, 'INTERFACE_FAV_EDIT_TRACK_DESC',
                    duration=item[3], uploader=item[4]
                )
            )
            for i, item in enumerate(self.favourites_parts[self.current_page])
        ]
        
        self.select.options = options
        self.select.max_values = len(options)
    
    async def callback_select(self, interaction: Interaction) -> None:
        indices = [int(value) for value in self.select.values]
        to_remove = [self.favourites_parts[self.current_page][i] for i in indices]
        
        for favourite in to_remove:
            await self.bot.db.delete(
                DBTable.FAV_TRACKS if self.mode.value == 0 else DBTable.FAV_PLAYLISTS,
                f'user_id={interaction.user.id} AND url="{favourite[2]}"'
            )
        
        embed = Embed(
            description=get_localized_string(
                self.locale, 'INTERFACE_FAV_EDIT_REMOVED'
            ),
            colour=Colour.green()
        )
        
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def callback_prev(self, interaction: Interaction) -> None:
        self.current_page -= 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)
    
    async def callback_next(self, interaction: Interaction) -> None:
        self.current_page += 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)

class QueueEditView(nextcord.ui.View):
    def __init__(self, locale: str, player: Player, mode: QueueEditViewMode) -> None:
        super().__init__(timeout=60)
        
        self.mode = mode
        self.locale = locale
        self.player = player
        self.current_page = 0
        self.queue_parts = self.split_queue(player.queue)
        
        self.prev_button = Button(label='◀️', style=ButtonStyle.green, custom_id='buttonprev')
        self.next_button = Button(label='▶️', style=ButtonStyle.green, custom_id='buttonnext')
        self.prev_button.callback = self.callback_prev
        self.next_button.callback = self.callback_next
        
        self.select = self.create_select()
        self.select.callback = self.callback_select if mode.value == 0 else self.callback_select_skip
        
        self.add_item(self.select)
        if len(self.queue_parts) > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
        
        self.update_buttons()
    
    async def on_timeout(self) -> None:
        self.stop()
    
    def split_queue(self, queue: Queue):
        return [queue[i:i+25] for i in range(0, len(queue), 25)]

    def create_select(self) -> nextcord.ui.Select:
        options = [
            nextcord.SelectOption(
                label=track.title, value=str(i),
                description=get_localized_string(
                    self.locale, 'INTERFACE_VIDEO_SEARCH_TRACK_DESC',
                    duration=ms_to_str(track.length), uploader=track.author
                )
            )
            for i, track in enumerate(self.queue_parts[self.current_page])
        ]
        
        return nextcord.ui.Select(
            placeholder=get_localized_string(
                self.locale, 'INTERFACE_QUEUE_EDIT_PLACEHOLDER' if self.mode.value == 0 else 'INTERFACE_QUEUE_EDIT_SKIP_PLACEHOLDER'
            ),
            options=options,
            min_values=1,
            max_values=len(options) if self.mode.value == 0 else 1
        )
    
    def update_buttons(self) -> None:
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.queue_parts) - 1)
    
    def update_select(self) -> None:
        options = [
            nextcord.SelectOption(
                label=track.title, value=str(i),
                description=get_localized_string(
                    self.locale, 'INTERFACE_VIDEO_SEARCH_TRACK_DESC',
                    duration=ms_to_str(track.length), uploader=track.author
                )
            )
            for i, track in enumerate(self.queue_parts[self.current_page])
        ]
        
        self.select.options = options
        self.select.max_values = len(options)
    
    async def callback_select(self, interaction: Interaction) -> None:
        indices = [int(value) for value in self.select.values]
        to_remove = [self.queue_parts[self.current_page][i] for i in indices]
        
        for track in to_remove:
            self.player.queue.remove(track)
        
        embed = Embed(
            description=get_localized_string(
                self.locale, 'INTERFACE_QUEUE_EDIT_REMOVED'
            ),
            colour=Colour.green()
        )
        
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def callback_select_skip(self, interaction: Interaction) -> None:
        index = int(self.select.values[0])
        selected_track = self.queue_parts[self.current_page][index]
        to_remove = self.player.queue[:self.player.queue.index(selected_track)]
        to_remove.reverse()
        
        for track in to_remove:
            self.player.queue.remove(track)
            self.player.history.insert(-1, track)
        
        self.player.performed_skip = True
        
        await self.player.skip(force=True)
        
        embed = Embed(
            description=get_localized_string(
                self.locale, 'INTERFACE_QUEUE_EDIT_SKIP_SKIPPED'
            ),
            colour=Colour.green()
        )
        
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def callback_prev(self, interaction: Interaction) -> None:
        self.current_page -= 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)
    
    async def callback_next(self, interaction: Interaction) -> None:
        self.current_page += 1
        self.update_buttons()
        self.update_select()
        await interaction.response.edit_message(view=self)

class VideoSearchView(nextcord.ui.View):
    def __init__(self, locale: str, results: Union[List[Track], List[Playlist]], mode: VideoSearchViewMode) -> None:
        super().__init__(timeout=60)
        
        self.locale = locale
        self.user_choices: List[Playable] = []
        
        self.select = nextcord.ui.Select(
            placeholder=get_localized_string(
                locale, 'INTERFACE_VIDEO_SEARCH_PLACEHOLDER'
            ),
            min_values=1, max_values=len(results),
            options=[
                nextcord.SelectOption(
                    label=item.title if len(item.title) <= 100 else item.title[:100], value=item.url,
                    description=get_localized_string(
                        locale, 'INTERFACE_VIDEO_SEARCH_PLAYLIST_DESC',
                        tracks=item.count, uploader=item.uploader
                    )
                    if isinstance(item, Playlist) else get_localized_string(
                        locale, 'INTERFACE_VIDEO_SEARCH_TRACK_DESC',
                        duration=item.duration, uploader=item.uploader
                    )
                )
                for item in results
            ]
        )
        
        if mode.value == 0:
            self.select.callback = self.callback_track
        elif mode.value == 1:
            self.select.callback = self.callback_playlist
        
        self.add_item(self.select)
    
    def get_embed(self, message: str) -> Embed:
        embed = Embed(
            title=get_localized_string(
                self.locale, 'INTERFACE_VIDEO_SEARCH_ADDED'
            ),
            description=message,
            colour=Colour.purple()
        )
        
        return embed
    
    async def on_timeout(self) -> None:
        self.stop()
    
    async def callback_track(self, interaction: Interaction) -> None:
        self.user_choices = [await url_to_playable(url) for url in self.select.values]
        
        message = [
            f'**{i+1}.** `{ms_to_str(item.length)}` - {item.title}'
            for i, item in enumerate(self.user_choices)
        ]
        message = '\n'.join(message)
        embed = self.get_embed(message)
        
        self.stop()
        await interaction.response.edit_message(content=None, embed=embed, view=None)
    
    async def callback_playlist(self, interaction: Interaction) -> None:
        messages: List[str] = []
        
        for url in self.select.values:
            playlist: Pl = await Playable.search(url,)
            
            for track in playlist.tracks:
                self.user_choices.append(track)
            
            message = get_localized_string(
                self.locale, 'INTERFACE_VIDEO_SEARCH_PLAYLIST_ADDED',
                tracks=len(playlist.tracks), name=playlist.name
            )
            messages.append(message)
        
        message = '\n'.join(messages)
        embed = self.get_embed(message)
        
        self.stop()
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class Valorant2FAView(nextcord.ui.Modal):
    def __init__(
        self, interaction: Interaction, locale: str, db: DATABASE, cookie: dict, message: str, label :str
    ) -> None:
        self.locale = locale
        self.interaction = interaction
        self.db = db
        self.cookie = cookie
        self.two2fa.placeholder = message
        self.two2fa.label = label
        
        super().__init__(
            get_localized_string(
                locale, 'INTERFACE_VAL_2FA_TITLE'
            ),
            timeout=60
        )
    
    two2fa = nextcord.ui.TextInput('', style=nextcord.TextInputStyle.short, max_length=6)
    
    async def on_timeout(self) -> None:
        self.stop()
        
        raise InteractionTimedOut(self.interaction)
            
    async def callback(self, interaction: Interaction) -> None:
        code = self.two2fa.value
        
        if code:
            cookie = self.cookie
            user_id = self.interaction.user.id
            auth = self.db.auth
            auth.locale_code = self.interaction.locale
            
            async def send_embed(content: str) -> Awaitable[None]:
                embed = Embed(
                    description=content, colour=Colour.purple()
                )
                
                if interaction.response.is_done():
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if not code.isdigit():
                return await send_embed(
                    get_localized_string(
                        self.locale, "INTERFACE_VAL_2FA_INVALID",
                        code=code
                    )
                )
            
            auth = await auth.give2facode(code, cookie)
            
            if auth['auth'] == 'response':
                login = await self.db.login(user_id, auth)
                if login['auth']:
                    return await send_embed(
                        get_localized_string(
                            self.locale, 'INTERFACE_VAL_2FA_SUCCESS',
                            player=login['player']
                        )
                    )
                    
                return await send_embed(login['error'])
            
            elif auth['auth'] == 'failed':
                return await send_embed(
                    get_localized_string(
                        self.locale, 'INTERFACE_VAL_2FA_WRONG'
                    )
                )
            else:
                return await send_embed(
                    get_localized_string(
                        self.locale, 'INTERFACE_VAL_2FA_ERROR'
                    )
                )
