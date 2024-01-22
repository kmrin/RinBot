"""
#### Errors
Errors raised when a failure happens
"""

# Imports
from discord import app_commands

# app_commands exceptions
class Exceptions:
    class UserBlacklisted(app_commands.CheckFailure): pass
    class UserNotOwner(app_commands.CheckFailure): pass
    class UserNotAdmin(app_commands.CheckFailure): pass
    class UserNotInGuild(app_commands.CheckFailure): pass