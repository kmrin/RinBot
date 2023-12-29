import random
from collections import deque
from datetime import timedelta

class SongQueue:
    def __init__(self):
        self.playqueue = deque()
        self.original = list(self.playqueue)
    
    def len(self):
        return len(self.playqueue)
    
    def add(self, song):
        self.playqueue.append(song)
        self.original.append(song)
    
    def remove(self, id):
        if id <= 0 or id > len(self.playqueue): return False
        removed = self.playqueue[id - 1]
        self.playqueue.remove(removed)
        self.original.remove(removed)
        return removed
    
    def prev(self):
        pass
    
    def next(self):
        next = self.playqueue.popleft()
        self.original.remove(next)
        return next
    
    def clear(self):
        self.playqueue.clear()
        self.original.clear()
    
    def clear_specific(self, id):
        if id <= 0 or id > len(self.playqueue):
            return False
        else:
            removed = self.playqueue[id - 1]
            self.playqueue.remove(removed)
            self.original.remove(removed)
            return removed
    
    def shuffle(self):
        random.shuffle(self.playqueue)
    
    def deshuffle(self):
        self.playqueue = list(self.original)
    
    def show(self, url=False):
        return '\n'.join([f"**{i+1}.** `[{s['duration']}]` - {s['title']}" 
                          if not url else f"**{i+1}.** [{s['url']}]" 
                          for i, s in enumerate(self.playqueue)]) if len(self.playqueue) > 0 else False

    def timedelta(self):
        def convert_delta(duration):
            parts = [int(part) for part in duration.split(":")]
            if len(parts) == 2: parts = [0] + parts
            return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
        return sum((convert_delta(item["duration"]) for item in self.playqueue), timedelta())