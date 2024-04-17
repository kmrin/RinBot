import discord
import wavelink

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.home: discord.TextChannel = None
        self.selected = []
        self.nightcore = False
