"""
RinBot's moderation command cog
- Commands:
    * /warnings show    - Shows the list of warnings a user has
    * /warnings add     - Adds a warning to a user
    * /warnings remove  - Removes a warning from a user
    * /admins add       - Adds a user to the admins class of a guild
    * /admins remove    - Removes a user from the admins class of a guild
    * /admins add-me    - Check if the author has admin privileges and if so, add them to the admins class of a guild
    * /blacklist show   - Shows the blacklist of a guild
    * /blacklist add    - Adds a user to the guild's blacklist
    * /blacklist remove - Removes a user from the guild's blacklist
    * /censor           - Deletes a certain amount of messages from the current text channel
"""

import nextcord

from nextcord import Locale, Embed, Colour, Interaction, SlashOption, slash_command
from nextcord.ext.application_checks import has_permissions, bot_has_permissions
from nextcord.ext.commands import Cog

from rinbot.core import RinBot
from rinbot.core import DBTable
from rinbot.core import Paginator
from rinbot.core import ResponseType
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted, is_admin, is_guild
from rinbot.core import get_conf
from rinbot.core import respond

conf = get_conf()

class Moderation(Cog, name='moderation'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot

    # /warnings
    @slash_command(
        name=get_localized_string('en-GB', 'MOD_WARN_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_WARN_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ROOT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _warn_root(self, interaction: Interaction) -> None:
        pass
    
    # /warnings show
    @_warn_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_WARN_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_SHOW_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_WARN_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_SHOW_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _warn_show(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        warnings = await self.bot.db.get(
            DBTable.WARNS, f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        
        if not warnings:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'MOD_WARN_NO_WARNINGS',
                                     member = member.display_name)
            )
        
        embed = Embed(
            title=f'''
            {
                get_localized_string(
                    locale, "MOD_WARN_SHOW_WARNS",
                    member = member.display_name
                )
            }
            ''',
            description='', colour=Colour.yellow()
        )
        
        warns = {}
        for warning in warnings:
            warns[warning[4]] = {
                'guild': warning[0],
                'user': warning[1],
                'moderator': warning[2],
                'warn': warning[3],
                'id': warning[4]
            }
        
        warn_strings = []
        
        for warning in warns.values():
            mod = interaction.guild.get_member(warning['moderator']) or await interaction.guild.fetch_member(warning['moderator'])
            
            warn_strings.append(f'''
            {
                get_localized_string(
                    locale, "MOD_WARN_SHOW_EMBED_DESC",
                    mod = mod.display_name,
                    warn_id = warning["id"],
                    warn = warning['warn']
                )
            }
            ''')
        
        embed.description = ''.join(warn for warn in warn_strings)
        
        await respond(interaction, message=embed)
    
    # /warnings add
    @_warn_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_WARN_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ADD_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_WARN_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ADD_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    @has_permissions(kick_members = True)
    @bot_has_permissions(kick_members = True)
    async def _warn_add(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        ),
        warn: str = SlashOption(
            name=get_localized_string('en-GB', 'MOD_WARN_WARN_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_WARN_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_WARN_WARN_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_WARN_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        new_warn = {
            'guild_id': interaction.guild.id,
            'user_id': member.id,
            'moderator_id': interaction.user.id,
            'warn': warn
        }
        
        await self.bot.db.put(DBTable.WARNS, new_warn)
        
        warns = await self.bot.db.get(
            DBTable.WARNS, f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        total = len(warns)
                
        embed = Embed(
            description=f'''
            {
                get_localized_string(
                    locale, 'MOD_WARN_ADD_WARNED',
                    member = member.mention,
                    moderator = interaction.user.display_name,
                    total = total
                )
            }
            ''',
            colour=Colour.yellow()
        )
        
        embed.add_field(
            name=get_localized_string(locale, 'MOD_WARN_ADD_WARN'),
            value=warn
        )
        
        await respond(interaction, message=embed)
        
        try:
            await member.send(
                f'''
                {
                    get_localized_string(
                        locale, 'MOD_WARN_ADD_PRIVATE',
                        moderator = interaction.user.display_name,
                        guild = interaction.guild.name,
                        warn = warn
                    )
                }
                '''
            )
        except (nextcord.Forbidden, nextcord.HTTPException):
            await respond(
                interaction, Colour.yellow(),
                f'''
                {
                    get_localized_string(
                        locale, 'MOD_WARN_ADD_TEXT_CHANNEL',
                        member = member.mention,
                        moderator = interaction.user.display_name,
                        warn = warn
                    )
                }
                '''
            )
        
        if conf['AUTO_KICK_ENABLED'] and total >= conf['AUTO_KICK_WARN_LIMIT']:
            await respond(
                interaction, Colour.yellow(),
                get_localized_string(
                    locale, 'MOD_WARN_LIMIT_REACHED_EMBED',
                    member = member.name,
                    limit = conf['AUTO_KICK_WARN_LIMIT']
                ),
                resp_type=ResponseType.FOLLOWUP
            )
            
            await member.kick(
                reason=get_localized_string(
                    locale, 'MOD_WARN_LIMIT_REACHED',
                    member = member.name,
                    limit = conf['AUTO_KICK_WARN_LIMIT']
                )
            )
            
            await self.bot.db.delete(
                DBTable.WARNS, f'guild_id={interaction.guild.id} AND user_id={member.id}'
            )
    
    # /warnings remove
    @_warn_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_WARN_REMOVE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_REMOVE_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_WARN_REMOVE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_REMOVE_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _warn_rem(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        ),
        warn_id: int = SlashOption(
            name=get_localized_string('en-GB', 'MOD_WARN_ID_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ID_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_WARN_ID_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_WARN_ID_DESC')
            },
            required=True,
            max_value=6
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        warns = await self.bot.db.get(
            DBTable.WARNS,
            f'guild_id={interaction.guild.id} AND user_id={member.id} AND id={warn_id}'
        )
        
        if not warns:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'MOD_WARN_NO_WARNINGS',
                                     member = member.display_name)
            )
        
        await self.bot.db.delete(
            DBTable.WARNS,
            f'guild_id={interaction.guild.id} AND user_id={member.id} AND id={warn_id}'
        )
        
        warns = await self.bot.db.get(
            DBTable.WARNS,
            f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        
        total = len(warns)
        
        await respond(
            interaction, Colour.green(),
            f'''
            {
                get_localized_string(
                    locale, 'MOD_WARN_REMOVE_REMOVED',
                    warn = warn_id,
                    member = member.display_name,
                    total = total
                )
            }
            '''
        )
    
    # /admins
    @slash_command(
        name=get_localized_string('en-GB', 'MOD_ADMIN_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_ADMIN_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ROOT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _admin_root(self, interaction: Interaction) -> None:
        pass
    
    # /admins add
    @_admin_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_ADMIN_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ADD_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_ADMIN_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ADD_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _admin_add(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if not member.guild_permissions.administrator:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MOD_ADMIN_ADD_NOT_ADMIN',
                    member = member.display_name
                )
            )
        
        is_already_admin = await self.bot.db.get(
            DBTable.ADMINS, f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        if is_already_admin:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MOD_ADMIN_ALREADY_ADMIN',
                    member = member.display_name
                )
            )
        
        await self.bot.db.put(
            DBTable.ADMINS, {
                'guild_id': interaction.guild.id,
                'user_id': member.id
            }
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MOD_ADMIN_ADDED', member=member.display_name
            )
        )
    
    # /admins remove
    @_admin_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_ADMIN_REMOVE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_REMOVE_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_ADMIN_REMOVE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_REMOVE_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _admin_remove(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        is_already_admin = await self.bot.db.get(
            DBTable.ADMINS, f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        if not is_already_admin:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MOD_ADMIN_NOT_ADMIN',
                    member = member.display_name
                )
            )
        
        await self.bot.db.delete(
            DBTable.ADMINS,
            f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MOD_ADMIN_REMOVED',
                member = member.display_name
            )
        )
    
    # /admins add-me
    @_admin_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_ADMIN_ME_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ME_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_ADMIN_ME_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_ADMIN_ME_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    @has_permissions(administrator = True)
    async def _admin_add_me(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        is_already_admin = await self.bot.db.get(
            DBTable.ADMINS, f'guild_id={interaction.guild.id} AND user_id={interaction.user.id}'
        )
        if is_already_admin:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(locale, 'MOD_ADMIN_ME_ALREADY_ADMIN')
            )
        
        await self.bot.db.put(
            DBTable.ADMINS, {
                'guild_id': interaction.guild.id,
                'user_id': interaction.user.id
            }
        )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'MOD_ADMIN_ME_ADDED'
            )
        )
    
    # /blacklist
    @slash_command(
        name=get_localized_string('en-GB', 'MOD_BL_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_BL_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_ROOT_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _bl_root(self, interaction: Interaction) -> None:
        pass
    
    # /blacklist show
    @_bl_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_BL_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_SHOW_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_BL_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_SHOW_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _bl_show(self, interaction: Interaction,) -> None:
        locale = get_interaction_locale(interaction)
        
        blacklist = await self.bot.db.get(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id}'
        )
        
        if not blacklist:
            return await respond(
                interaction, Colour.yellow(),
                get_localized_string(
                    locale, 'MOD_BL_EMPTY'
                )
            )
        
        embed = Embed(
            title=get_localized_string(
                locale, 'MOD_BL_EMBED_TITLE',
                server = interaction.guild.name
            ),
            colour=Colour.yellow()
        )
        
        users = []
        for user in blacklist:
            user = self.bot.get_user(user[1]) or await self.bot.fetch_user(user[1])
            users.append(
                get_localized_string(
                    locale, 'MOD_BL_BLACKLISTED',
                    user = user.display_name
                )
            )
        
        if len(users) >= 15:
            chunks = [users[i:i + 15] for i in range(0, len(users), 15)]
            embed.description = '\n'.join(chunks[0])
            
            view = Paginator(embed, chunks)
            
            return await respond(interaction, message=embed, view=view)
        
        embed.description = '\n'.join(users)
        await respond(interaction, message=embed)

    # /blacklist add
    @_bl_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_BL_ADD_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_ADD_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_BL_ADD_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_ADD_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _bl_add(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        blacklist = await self.bot.db.get(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id}'
        )
        
        users = [row[1] for row in blacklist]
        if member.id in users:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MOD_BL_ALREADY_BLACKLISTED',
                    member = member.display_name
                )
            )
        
        await self.bot.db.put(
            DBTable.BLACKLIST, {
                'guild_id': interaction.guild.id,
                'user_id': member.id
            }
        )
        
        blacklist = await self.bot.db.get(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id}'
        )
        
        total = len(blacklist)
        
        embed = Embed(
            description=get_localized_string(
                locale, 'MOD_BL_CANT_USE_ME',
                member = member.mention
            ),
            colour=Colour.yellow()
        )
        embed.set_footer(
            text=get_localized_string(
                locale, 'MOD_BL_TOTAL_USERS',
                total = total
            )
        )
        
        await respond(interaction, message=embed)

    # /blacklist remove
    @_bl_root.subcommand(
        name=get_localized_string('en-GB', 'MOD_BL_REMOVE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_REMOVE_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_BL_REMOVE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_BL_REMOVE_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    async def _bl_remove(
        self, interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        blacklist = await self.bot.db.get(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id}'
        )
        
        users = [row[1] for row in blacklist]
        if member.id not in users:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'MOD_BL_NOT_BLACKLISTED',
                    member = member.display_name
                )
            )
        
        await self.bot.db.delete(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id} AND user_id={member.id}'
        )
        
        blacklist = await self.bot.db.get(
            DBTable.BLACKLIST,
            f'guild_id={interaction.guild.id}'
        )
        
        embed = Embed(
            description=get_localized_string(
                locale, 'MOD_BL_CAN_USE_ME',
                member = member.mention
            ),
            colour = Colour.green()
        )
        
        await respond(interaction, message=embed)

    # /censor
    @slash_command(
        name=get_localized_string('en-GB', 'MOD_CENSOR_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_CENSOR_NAME')
        },
        description=get_localized_string('en-GB', 'MOD_CENSOR_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'MOD_CENSOR_DESC')
        }
    )
    @is_guild()
    @is_admin()
    @not_blacklisted()
    @bot_has_permissions(manage_messages=True)
    async def _censor(
        self, interaction: Interaction,
        amount: int = SlashOption(
            name=get_localized_string('en-GB', 'MOD_CENSOR_AMOUNT_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_CENSOR_AMOUNT_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_CENSOR_AMOUNT_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_CENSOR_AMOUNT_DESC')
            },
            min_value=1,
            max_value=100,
            required=True
        ),
        from_member: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'MOD_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'MOD_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'MOD_MEMBER_DESC')
            },
            required=False
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        def check(msg):
            if from_member is None:
                return True
            return msg.author == from_member
        
        deleted = await interaction.channel.purge(
            limit=amount, check=check
        )
        
        if from_member:
            await respond(
                interaction, Colour.green(),
                f'{get_localized_string(locale, "MOD_CENSOR_DELETED_FROM_MEMBER")[0].format(amount = len(deleted))}'
                f'{get_localized_string(locale, "MOD_CENSOR_DELETED_FROM_MEMBER")[1 if len(deleted) == 1 else 2].format(member = from_member.display_name)}',
                hidden=True
            )
        else:
            await respond(
                interaction, Colour.green(),
                f'{get_localized_string(locale, "MOD_CENSOR_DELETED")[0].format(amount = len(deleted))}'
                f'{get_localized_string(locale, "MOD_CENSOR_DELETED")[1 if len(deleted) == 1 else 2]}',
                hidden=True
            )

# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Moderation(bot))
