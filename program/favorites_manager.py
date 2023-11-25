# Imports
import os, json, discord
from program.youtube import processYoutubePlaylist

# Global favorite tracking
favorites = {}

# Reads current favorites
def readFavorites():
    for file in os.listdir('cache/favorites/'):
        if file.endswith('favorites.json'):
            try:
                id = int(file.split('-')[0])
            except (ValueError, IndexError):
                continue
            with open(f'cache/favorites/{file}', 'r', encoding='utf-8') as f:
                favorite = json.load(f)
            favorites[id] = favorite

# Returns a list of favorites to view
def showFavorites(id, url:bool=False):
    readFavorites()
    try:
        favorite_data = [f'**{index + 1}**. `{item["count"]} tracks` - {item["title"]}'
                        if not url else
                        f'**{index + 1}**. `{item["count"]} tracks` - {item["url"]}' 
                        for index, item in enumerate(favorites[id])]
        message = '\n'.join(favorite_data)
    except KeyError:
        message = None
    return message

# Adds a playlist to someone's favorites
def addFavorite(id, item):
    readFavorites()
    item = processYoutubePlaylist(item)
    if isinstance(item, discord.Embed):
        return item
    item = {
        'title': item['title'],
        'url': item['url'],
        'count': item['count']}
    try:
        data:list = favorites[id]
    except KeyError:
        data = []
    data.append(item)
    try:
        with open(f'cache/favorites/{id}-favorites.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except FileNotFoundError:
        pass
    return item

# Removes a playlist from someone's favorites
def removeFavorite(id, item_id):
    readFavorites()
    data:list = favorites[id]
    try:
        item = data[item_id]
        data.pop(item_id)
    except IndexError:
        embed = discord.Embed(
            description = " ❌ ID out of range.",
            color=0xd91313)
        return embed
    try:
        with open(f'cache/favorites/{id}-favorites.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        embed = discord.Embed(
            description = f" ✅ `{item['title']}` removed from your favorites!",
            color=0x25D917)
        return embed
    except FileNotFoundError:
        embed = discord.Embed(
            description = " ❌ Cache file not found :(",
            color=0xd91313)
        return embed

# Clears someone's favorites
def clearFavorites(id):
    try:
        with open(f'cache/favorites/{id}-favorites.json', 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    except FileNotFoundError:
        pass