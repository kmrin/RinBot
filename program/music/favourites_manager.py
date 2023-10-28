"""
RinBot v1.7.0 (GitHub release)
made by rin
"""

# Imports
import os, json, discord
from program.music.youtube import processYoutubePlaylist

# Global favourite tracking
favourites = {}

# Reads current favourites
def readFavourites():
    for file in os.listdir('program/music/cache/'):
        if file.endswith('fav_playlists.json'):
            try:
                id = int(file.split('-')[0])
            except (ValueError, IndexError):
                continue
            with open(f'program/music/cache/{file}', 'r', encoding='utf-8') as f:
                favourite = json.load(f)
            favourites[id] = favourite

# Returns a list of favourites to view
def showFavourites(id, url:bool=False):
    readFavourites()
    try:
        favourite_data = [f'**{index + 1}**. `{item["count"]} tracks` - {item["title"]}'
                        if not url else
                        f'**{index + 1}**. `{item["count"]} tracks` - {item["url"]}' 
                        for index, item in enumerate(favourites[id])]
        message = '\n'.join(favourite_data)
    except KeyError:
        message = None
    return message

# Adds a playlist to someone's favourites
def addFavourite(id, item):
    readFavourites()
    item = processYoutubePlaylist(item)
    if isinstance(item, discord.Embed):
        return item
    item = {
        'title': item['title'],
        'url': item['url'],
        'count': item['count']}
    try:
        data:list = favourites[id]
    except KeyError:
        data = []
    data.append(item)
    try:
        with open(f'program/music/cache/{id}-fav_playlists.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except FileNotFoundError:
        pass
    return item

# Removes a playlist from someone's favourites
def removeFavourite(id, item_id):
    readFavourites()
    data:list = favourites[id]
    try:
        item = data[item_id]
        data.pop(item_id)
    except IndexError:
        embed = discord.Embed(
            description = " ❌ ID out of range.",
            color=0xd91313)
        return embed
    try:
        with open(f'program/music/cache/{id}-fav_playlists.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        embed = discord.Embed(
            description = f" ✅ `{item['title']}` removed from your favourites!",
            color=0x25D917)
        return embed
    except FileNotFoundError:
        embed = discord.Embed(
            description = " ❌ Cache file not found :(",
            color=0xd91313)
        return embed

# Clears someone's favourites
def clearFavourites(id):
    try:
        with open(f'program/music/cache/{id}-fav_playlists.json', 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    except FileNotFoundError:
        pass