import nextcord
import nextlink

from nextcord import TextChannel, Embed
from nextlink import Playable
from typing import List, TYPE_CHECKING

from rinbot.core.helpers import get_localized_string, ms_to_str
from rinbot.core.db import DBTable

if TYPE_CHECKING:
    from rinbot.core.client import RinBot

class Player(nextlink.Player):
    def __init__(self, bot: 'RinBot', locale: str, home: TextChannel, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.bot = bot
        self.locale = locale
        self.home = home
        self.autoplay = nextlink.AutoPlayMode.partial
        self.history: List[Playable] = []
        self.nightcore: bool = False
        self.last_message: nextcord.Message = None
        self.playable_before_prev: Playable = None
        self.from_previous_interaction: bool = False
    
    async def play_playable(self, playable: nextlink.Playable) -> None:
        await self.play(playable, replace=True, filters=self.filters)
    
    async def play_last_in_history(self) -> None:
        if not self.history:
            return
        
        self.from_previous_interaction = True
        self.playable_before_prev = self.current
        
        await self.play_playable(self.history.pop(-1))
        
        self.queue.put_at(0, self.playable_before_prev)
    
    async def dc(self, force: bool = False) -> None:
        try:
            old_embed = self.last_message.embeds[0]
            new_embed = Embed(
                title=get_localized_string(
                    self.locale, 'MUSIC_PLAYED'
                ),
                description=old_embed.description,
                colour=old_embed.colour
            )
            if old_embed.image:
                new_embed.set_thumbnail(old_embed.image.url)
            
            await self.last_message.edit(embed=new_embed, view=None)
        except AttributeError:
            pass
        
        del self.bot.music_clients[self.home.guild.id]
        await self.disconnect(force=force)
        self.cleanup()

    async def add_to_user_favourites(self, user_id: int) -> None:
        music = await self.bot.db.get(DBTable.FAV_TRACKS, f'user_id={user_id}')
        
        if music:
            for track in music:
                if track[2] == self.current.uri:
                    return
        
        data = {
            'user_id': user_id,
            'title': self.current.title,
            'url': self.current.uri,
            'duration': ms_to_str(self.current.length),
            'uploader': self.current.author
        }
        
        await self.bot.db.put(DBTable.FAV_TRACKS, data)
