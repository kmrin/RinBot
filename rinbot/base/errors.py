"""
#### Errors\n
Exceptions raised when a failure happens
"""

from discord import app_commands
from rinbot.base.helpers import load_lang

text = load_lang()

OWNER = {text['OWNER']}
ADMIN = {text['ADMIN']}

class Exceptions:
    class UserBlacklisted(app_commands.CheckFailure):
        pass

    class UserNotOwner(app_commands.CheckFailure):
        pass

    class UserNotAdmin(app_commands.CheckFailure):
        pass

    class UserNotInGuild(app_commands.CheckFailure):
        pass

    class InvalidSilentSetting(Exception):
        def __str__(self):
            return text['EXECUTOR_INVALID_SILENT_SETTING']

    class InvalidRuntimesSelected(Exception):
        def __str__(self):
            return text['EXECUTOR_INVALID_RUNTIME_SELECTED']

    class InvalidRoutineSelected(Exception):
        def __str__(self):
            return text['EXECUTOR_INVALID_ROUTINE_SELECTED']