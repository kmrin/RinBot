# Imports
from rinbot.base import db_manager

# Return a history
async def show_history(id, url:bool=False):
    history = await db_manager.get_history(id)
    try:
        data = [f'**{i + 1}.** `[{h["duration"]}]` - {h["title"]}'
                if not url else f'**{i + 1}.** {h["url"]}'
                for i,h in enumerate(history)]
        return '\n'.join(data)
    except: return None

# Clears a server's history
async def clear_history(id):
    clear = await db_manager.clear_history(id)
    return clear