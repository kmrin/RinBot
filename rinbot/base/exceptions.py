import asyncio, discord
from discord.ext import commands
from discord import app_commands
from rinbot.base.helpers import load_lang
from rinbot.base.colors import *

text = load_lang()

class Exceptions:
    class UserBlacklisted(commands.CheckFailure):
        def __init__(self, message=f"{text['EXCEPTIONS_BLACKLISTED']}"):
            self.message = message
            super().__init__(self.message)
    class UserNotOwner(commands.CheckFailure):
        def __init__(self, message=f"{text['EXCEPTIONS_NOT_OWNER']}"):
            self.message = message
            super().__init__(self.message)
    class UserNotAdmin(commands.CheckFailure):
        def __init__(self, message=f"{text['EXCEPTIONS_NOT_ADMIN']}"):
            self.message = message
            super().__init__(self.message)
    
    class AC_UserBlacklisted(app_commands.CheckFailure): pass
    class AC_UserNotOwner(app_commands.CheckFailure): pass
    class AC_UserNotAdmin(app_commands.CheckFailure): pass