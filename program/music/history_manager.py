"""
RinBot v1.7.0 (GitHub release)
made by rin
"""

# Imports
import os, json

# Global history tracking
histories = {}

# Read current histories
def readHistories():
    for file in os.listdir('program/music/cache/'):
        if file.endswith('.json'):
            try:
                id = int(file.split('-')[1].split('.')[0])
            except (ValueError, IndexError):
                continue
            with open(f'program/music/cache/{file}', 'r', encoding='utf-8') as f:
                history = json.load(f)
            histories[id] = history

# Return a history
def showHistory(id, url=False):
    readHistories()
    history_data = [f'**{index + 1}.** `[{item["duration"]}]` - {item["title"]}'
                    if not url else f'**{index + 1}.** {item["url"]}'
                    for index, item in enumerate(histories[id])]
    message = '\n'.join(history_data)
    return message

# Clear a history
def clearHistory(id):
    clear = []
    try:
        with open(f'program/music/cache/song_history-{id}.json', 'w', encoding='utf-8') as f:
            json.dump(clear, f, indent=4)
    except FileNotFoundError:
        pass