"""
RinBot v1.9.0 (GitHub release)
made by rin
"""

# Imports
from discord.ext import commands

# Exceptions that are raised when things go oopsie

# User is in blacklist
class UserBlacklisted(commands.CheckFailure):
    def __init__(self, message="User in blacklist!"):
        self.message = message
        super().__init__(self.message)

# User is not an owner
class UserNotOwner(commands.CheckFailure):
    def __init__(self, message="User not in `owners` class!"):
        self.message = message
        super().__init__(self.message)

# User is not an admin
class UserNotAdmin(commands.CheckFailure):
    def __init__(self, message="User not in `admins` class!"):
        self.message = message
        super().__init__(self.message)

# Invalid DM command (unused, but here just in case it get's used again, we never know)
class NoDms(commands.CheckFailure):
    def __init__(self, message="This command doesn't work in my DMs love OwO"):
        self.message = message
        super().__init__(self.message)