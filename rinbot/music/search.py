from nextcord import Embed, Colour
from typing import Union, List
from youtubesearchpython.__future__ import VideosSearch, PlaylistsSearch

from rinbot.core.types import Track, Playlist
from rinbot.core.helpers import get_localized_string

def get_no_results_embed(locale: str, search: str) -> Embed:
    return Embed(
        description=get_localized_string(
            locale, 'MUSIC_SEARCH_NO_RESULTS',
            search=search
        ),
        colour=Colour.red()
    )

async def search_video(locale: str, search: str) -> Union[List[Track], Embed]:
    query = await VideosSearch(search, limit=25).next()
    videos = []

    if not query['result']:
        return get_no_results_embed(locale, search)
    
    for v in query['result']:
        video = Track(v['title'], v['link'], v['duration'], v['channel']['name'])
        videos.append(video)
    
    return videos
    
async def search_playlist(locale: str, search: str) -> Union[List[Playlist], Embed]:
    query = await PlaylistsSearch(search, limit=25).next()
    playlists = []

    if not query['result']:
        return get_no_results_embed(locale, search)
    
    for p in query['result']:
        playlist = Playlist(p['title'], p['link'], int(p['videoCount']), p['channel']['name'])
        playlists.append(playlist)
    
    return playlists
