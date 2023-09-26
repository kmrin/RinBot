"""
RinBot v1.4.3
feita por rin
"""

# Imports
from discord.ext import commands

# Exceções que são levantadas por checks de identidade

# Usuário presente na blacklist
class UserBlacklisted(commands.CheckFailure):
    def __init__(self, message="Usuário na blacklist!"):
        self.message = message
        super().__init__(self.message)

# Usuário não é da classe 'owners'
class UserNotOwner(commands.CheckFailure):
    def __init__(self, message="Usuário não está na classe `owners` da RinBot!"):
        self.message = message
        super().__init__(self.message)

# Usuário não é da classe 'admin'
class UserNotAdmin(commands.CheckFailure):
    def __init__(self, message="Usuário não está na classe `admins` da RinBot!"):
        self.message = message
        super().__init__(self.message)

# Comando inválido por mensagem direta
class NoDms(commands.CheckFailure):
    def __init__(self, message="Esse comando não funciona nas minhas DMs amorzin <3"):
        self.message = message
        super().__init__(self.message)