import asyncio
import discord

from youtubesearchpython.__future__ import *
from typing import Union, Dict, List

from rinbot.base.json_loader import get_lang
from rinbot.base.colours import Colour

text = get_lang()

async def search_video(search: str) -> Union[List[Dict[str, str]], discord.Embed]:
    query = await VideosSearch(search, limit=25).next()
    data = []
    
    if not query['result']:
        return discord.Embed(
            description=text['MUSIC_SEARCH_NO_RESULTS'].format(
                search=search
            ),
            colour=Colour.RED
        )
    
    for v in query['result']:
        data.append(
            {
                'url': v['link'],
                'title': v['title'],
                'duration': v['duration'],
                'uploader': v['channel']['name']
            }
        )
    
    return data

async def search_playlist(search: str) -> Union[List[Dict[str, str]], discord.Embed]:
    query = await PlaylistsSearch(search, limit=25).next()
    data = []
    
    if not query['result']:
        return discord.Embed(
            description=text['MUSIC_SEARCH_NO_RESULTS'].format(
                search=search
            ),
            colour=Colour.RED
        )
    
    for p in query['result']:
        data.append(
            {
                'url': p['link'],
                'count': p['videoCount'],
                'title': p['title']
            }
        )
    
    return data

async def __main():
    search = await search_video("Hatsune Miku")
    for v in search:
        print(v)
    
    search = await search_playlist("Vocaloid")
    for p in search:
        print(p)

if __name__ == '__main__':
    asyncio.run(__main())
