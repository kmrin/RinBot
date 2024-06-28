import nextcord

from typing import TYPE_CHECKING
from nextcord import Interaction, SlashOption, Colour, Locale, slash_command
from nextcord.ext.commands import Cog
from nextcord.ext.commands import ExtensionNotFound, ExtensionAlreadyLoaded, ExtensionNotLoaded, NoEntryPointError

from .db import DBTable
from .interface import Paginator
from .command_checks import is_owner, not_blacklisted, is_guild
from .loggers import Loggers, log_exception
from .helpers import get_localized_string, get_interaction_locale
from .responder import respond

if TYPE_CHECKING:
    from .client import RinBot

logger = Loggers.COMMANDS

class Core(Cog):
    def __init__(self, bot: 'RinBot') -> None:
        self.bot = bot
    
    # /extension
    @slash_command(
        name=get_localized_string('en-GB', 'CORE_EXT_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_ROOT_NAME')},
        description=get_localized_string('en-GB', 'CORE_EXT_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_ROOT_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _ext_root(self, interaction: Interaction) -> None:
        pass
    
    # /extension list
    @_ext_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_EXT_LIST_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_LIST_NAME')},
        description=get_localized_string('en-GB', 'CORE_EXT_LIST_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_LIST_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _ext_list(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        extensions = self.bot.cogs
        message = '\n'.join([f'`{ext}`' for ext in extensions.keys()])
        
        embed = nextcord.Embed(
            title=get_localized_string(locale, 'CORE_EXT_LIST_EMBED_TITLE'),
            colour=nextcord.Colour.gold()
        )
        embed.set_footer(
            text=get_localized_string(
                locale, 'CORE_EXT_LIST_EMBED_FOOTER', count=len(extensions))
        )
        
        if len(extensions) > 15:
            lines = message.split('\n')
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            embed.description='\n'.join(chunks[0])
            view = Paginator(embed, chunks)
            
            return await respond(interaction, message=embed, view=view)
        
        embed.description = message
        
        await respond(interaction, message=embed)
    
    # /extension load
    @_ext_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_EXT_LOAD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_LOAD_NAME')},
        description=get_localized_string('en-GB', 'CORE_EXT_LOAD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_LOAD_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _ext_load(
        self, interaction: Interaction,
        extension: str = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_OPTION_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_OPTION_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_DESC')
            },
            required=True
        ),
        ai: int = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_AI_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_AI_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_DESC')
            },
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        # If the extension is an internal extension
        if extension.lower() in ['core', 'eventshandler']:
            return await respond(
                interaction, nextcord.Colour.red(),
                get_localized_string(locale, 'CORE_EXT_INTERNAL')
            )
        
        try:
            self.bot.load_extension(
                f'rinbot.extensions.{extension}'   # Normal extensions
                if ai == 0 else
                f'rinbot.kobold.cogs.{extension}'  # AI extensions
            )
            message = get_localized_string(locale, 'CORE_EXT_LOAD_SUCCESS', ext=extension)
            colour = nextcord.Colour.green()
        except ExtensionNotFound:
            message = get_localized_string(locale, 'CORE_EXT_NOT_FOUND', ext=extension)
            colour = nextcord.Colour.red()
        except ExtensionAlreadyLoaded:
            message = get_localized_string(locale, 'CORE_EXT_ALREADY_LOADED', ext=extension)
            colour = nextcord.Colour.red()
        except NoEntryPointError:
            message = get_localized_string(locale, 'CORE_EXT_NO_ENTRY', ext=extension)
            colour = nextcord.Colour.red()
        
        await respond(interaction, colour, message)
        
        # Sync changes to discord
        await self.bot.sync_all_application_commands()
    
    # /extension unload
    @_ext_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_EXT_UNLOAD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_UNLOAD_NAME')},
        description=get_localized_string('en-GB', 'CORE_EXT_UNLOAD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_UNLOAD_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _ext_unload(
        self, interaction: Interaction,
        extension: str = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_OPTION_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_OPTION_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_DESC')
            },
            required=True
        ),
        ai: int = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_AI_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_AI_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_DESC')
            },
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        # If the extension is an internal extension
        if extension.lower() in ['core', 'eventshandler']:
            return await respond(
                interaction, nextcord.Colour.red(),
                get_localized_string(locale, 'CORE_EXT_INTERNAL')
            )
        
        try:
            self.bot.unload_extension(
                f'rinbot.extensions.{extension}'   # Normal extensions
                if ai == 0 else
                f'rinbot.kobold.cogs.{extension}'  # AI extensions
            )
            message = get_localized_string(locale, 'CORE_EXT_UNLOAD_SUCCESS', ext=extension)
            colour = nextcord.Colour.green()
        except ExtensionNotFound:
            message = get_localized_string(locale, 'CORE_EXT_NOT_FOUND', ext=extension)
            colour = nextcord.Colour.red()
        except ExtensionNotLoaded:
            message = get_localized_string(locale, 'CORE_EXT_NOT_LOADED', ext=extension)
            colour = nextcord.Colour.red()
        
        await respond(interaction, colour, message)
        
        # Sync changes to discord
        await self.bot.sync_all_application_commands()
    
    # /extension reload
    @_ext_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_EXT_RELOAD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_RELOAD_NAME')},
        description=get_localized_string('en-GB', 'CORE_EXT_RELOAD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_RELOAD_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _ext_reload(
        self, interaction: Interaction,
        extension: str = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_OPTION_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_OPTION_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_OPTION_DESC')
            },
            required=True
        ),
        ai: int = SlashOption(
            name=get_localized_string('en-GB', 'CORE_EXT_AI_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_EXT_AI_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_EXT_AI_DESC')
            },
            choices={
                "Yes": 1,
                "No": 0
            },
            choice_localizations={
                "Yes": {
                    Locale.pt_BR: "Sim"
                },
                "No": {
                    Locale.pt_BR: "Não"
                }
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        # If the extension is an internal extension
        if extension.lower() in ['core', 'eventshandler']:
            return await respond(
                interaction, nextcord.Colour.red(),
                get_localized_string(locale, 'CORE_EXT_INTERNAL')
            )
        
        try:
            self.bot.reload_extension(
                f'rinbot.extensions.{extension}'   # Normal extensions
                if ai == 0 else
                f'rinbot.kobold.cogs.{extension}'  # AI extensions
            )
            message = get_localized_string(locale, 'CORE_EXT_RELOAD_SUCCESS', ext=extension)
            colour = nextcord.Colour.green()
        except ExtensionNotFound:
            message = get_localized_string(locale, 'CORE_EXT_NOT_FOUND', ext=extension)
            colour = nextcord.Colour.red()
        except Exception as e:
            e = log_exception(e, logger)
            message = get_localized_string(locale, 'CORE_EXT_GENERIC_ERROR', ext=extension, e=e)
            colour = nextcord.Colour.red()
        
        await respond(interaction, colour, message)
    
        # Sync changes to discord
        await self.bot.sync_all_application_commands()
    
    # /owner
    @slash_command(
        name=get_localized_string('en-GB', 'CORE_OWNER_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_ROOT_NAME')},
        description=get_localized_string('en-GB', 'CORE_OWNER_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_ROOT_DESC')})
    @not_blacklisted()
    @is_owner()
    @is_guild()
    async def _owner_root(self, interaction: Interaction) -> None:
        pass
    
    # /owner add
    @_owner_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_OWNER_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_ADD_NAME')},
        description=get_localized_string('en-GB', 'CORE_OWNER_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_ADD_DESC')})
    @not_blacklisted()
    @is_owner()
    @is_guild()
    async def _owner_add(
        self, interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'CORE_OWNER_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_USER_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_OWNER_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_USER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        owners = await self.bot.db.get(DBTable.OWNERS)
        
        if user.id in [row[0] for row in owners]:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'CORE_OWNER_ADD_ALREADY_OWNER', user=user.name
                ), hidden=True
            )
        
        await self.bot.db.put(DBTable.OWNERS, {'user_id': user.id})
        await respond(
            interaction, Colour.green(),
            get_localized_string(locale, 'CORE_OWNER_ADD_ADDED', user=user.name),
            hidden=True
        )
    
    # /owner remove
    @_owner_root.subcommand(
        name=get_localized_string('en-GB', 'CORE_OWNER_REM_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_REM_NAME')},
        description=get_localized_string('en-GB', 'CORE_OWNER_REM_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_REM_DESC')})
    @not_blacklisted()
    @is_owner()
    @is_guild()
    async def _owner_remove(
        self, interaction: Interaction,
        user: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'CORE_OWNER_USER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_USER_NAME')
            },
            description=get_localized_string('en-GB', 'CORE_OWNER_USER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'CORE_OWNER_USER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        owners = await self.bot.db.get(DBTable.OWNERS)
        
        if not user.id in [row[0] for row in owners]:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'CORE_OWNER_REM_NOT_OWNER', user=user.name),
                hidden=True
            )
        
        await self.bot.db.delete(DBTable.OWNERS, f'user_id={user.id}')
        await respond(
            interaction, Colour.green(),
            get_localized_string(locale, 'CORE_OWNER_REM_REMOVED', user=user.name),
            hidden=True
        )
        
        owners = await self.bot.db.get(DBTable.OWNERS)
        if not owners:
            await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'CORE_OWNER_EMPTY'),
                hidden=True
            )
    
    # /ping
    @slash_command(
        name=get_localized_string('en-GB', 'CORE_PING_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_PING_NAME')},
        description=get_localized_string('en-GB', 'CORE_PING_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_PING_DESC')})
    @not_blacklisted()
    async def _ping(self, interaction: Interaction) -> None:
        await respond(
            ctx=interaction,
            colour=Colour.gold(),
            message=get_localized_string(
                get_interaction_locale(interaction),
                'CORE_PING_EMBED',
                latency=round(self.bot.latency * 1000)))

    # /shutdown
    @slash_command(
        name=get_localized_string('en-GB', 'CORE_SHUTDOWN_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_SHUTDOWN_NAME')},
        description=get_localized_string('en-GB', 'CORE_SHUTDOWN_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'CORE_SHUTDOWN_DESC')})
    @not_blacklisted()
    @is_owner()
    async def _shutdown(self, interaction: Interaction) -> None:
        await respond(
            ctx=interaction,
            colour=Colour.gold(),
            message=get_localized_string(
                get_interaction_locale(interaction),
                'CORE_SHUTDOWN_EMBED'))
        await self.bot.stop()
