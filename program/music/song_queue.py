"""
RinBot v1.5.1 (GitHub release)
made by rin
"""

# Imports
import random
from collections import deque

# Queue class
class SongQueue:
    def __init__(self):
        self.playqueue = deque()
    
    # Returns the queue size
    def len(self):
        return len(self.playqueue)
    
    # Adds a song to the queue
    def add(self, song):
        self.playqueue.append(song)
    
    # Moves to the next song
    def next(self):
        next_song = self.playqueue.popleft()
        return next_song

    # Shows the current songs on the queue
    def show(self, url=False):
        if not url:
            queue_data = [f'{i + 1}. [{s["duration"]}] - {s["title"]}' for i, s 
                          in enumerate(self.playqueue)]
        else:
            queue_data = [f'{i + 1}. [{s["url"]}]' for i, s 
                          in enumerate(self.playqueue)]
        message = '\n'.join(queue_data)
        return message

    # Clears the queue
    def clear(self):
        self.playqueue.clear()
    
    # Clears a specific item from the queue
    def clear_specific(self, id) -> bool:
        if id <= 0 or id > len(self.playqueue):
            return False
        else:
            removed = self.playqueue[id - 1]
            self.playqueue.remove(removed)
            return removed

    # Shuffles the queue (not used at the moment)
    def shuffle(self):
        random.shuffle(self.playqueue)