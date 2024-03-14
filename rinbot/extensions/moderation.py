"""
RinBot's moderation command cog
- Commands:
    * /warnings show `Shows a user's warnings`
    * /warnings add `Adds a warning to a user in a guild`
    * /warnings remove `Removes a warning from a user in a guild`
    * /admins add `Adds a user to the admins class of a guild`
    * /admins remove `Removes a user from the admins class of a guild`
    * /blacklist show `Shows the blacklist of a guild`
    * /blacklist add `Adds a user to a guild's blacklist`
    * /blacklist remove `Removes a user from a guild's blacklist`
    * /ban `Bans a member from the guild`
    * /kick `Kicks a member from the guild`
    * /nick `Changes the nickname of a guild member`
"""

import discord
from discord import app_commands
from discord.ext.commands import Cog, Context, hybrid_command
from rinbot.base.helpers import load_lang, format_exception
from rinbot.base.responder import respond
from rinbot.base.client import RinBot
from rinbot.base.checks import *
from rinbot.base.colors import *

text = load_lang()

# noinspection PyUnresolvedReferences,PyBroadException
class Moderation(Cog, name="moderation"):
    def __init__(self, bot: RinBot):
        self.bot = bot

    # Command groups
    warnings = app_commands.Group(name=text['MODERATION_WARNINGS_NAME'], description=text['MODERATION_WARNINGS_DESC'])
    admins = app_commands.Group(name=text['MODERATION_ADMINS_NAME'], description=text['MODERATION_ADMINS_DESC'])
    blacklist = app_commands.Group(name=text['MODERATION_BL_NAME'], description=text['MODERATION_BL_DESC'])

    @warnings.command(
        name=text['MODERATION_WARNINGS_SHOW_NAME'],
        description=text['MODERATION_WARNINGS_SHOW_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _warnings_show(self, interaction: Interaction, member: discord.Member = None) -> None:
        try:
            if not member:
                return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

            embed = discord.Embed(title=f"**{member}** {text['MODERATION_WARNINGS_EMBED_WARN']}", color=GREEN)
            description = ""
            warns = await self.bot.db.get("warns")

            if not warns:
                return await respond(interaction, RED, message=text['MODERATION_WARNINGS_NO_WARNINGS'])

            if str(interaction.guild.id) in warns.keys():
                server_warns: dict = warns[str(interaction.guild.id)]

                if str(member.id) in server_warns.keys():
                    user_warns: list = server_warns[str(member.id)]

                    if len(user_warns) == 0:
                        description = text['MODERATION_WARNINGS_NO_WARNINGS']
                    else:
                        for index, warning in enumerate(user_warns):
                            description += f"{text['MODERATION_WARNINGS_CREATE_WARNING'][0]} <@{warning['moderator_id']}>: **{index + 1}** - {text['MODERATION_WARNINGS_CREATE_WARNING'][1]}{warning['warn']}\n"

                    embed.description = description

                    await respond(interaction, message=embed)
                else:
                    await respond(interaction, RED, message=text['MODERATION_WARNINGS_USER_NO_WARNINGS'])
            else:
                await respond(interaction, RED, message=text['MODERATION_WARNINGS_GUILD_NO_WARNINGS'])
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @warnings.command(
        name=text['MODERATION_WARNINGS_ADD_NAME'],
        description=text['MODERATION_WARNINGS_ADD_DESC'])
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _warnings_add(self, interaction: Interaction, member: discord.Member = None, warn: str = None) -> None:
        try:
            if not member or not warn:
                return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

            warns = await self.bot.db.get("warns")

            if not warns:
                warns[str(str(interaction.guild.id))] = {}
            if not str(interaction.guild.id) in warns.keys():
                warns[str(interaction.guild.id)] = {}
            if not str(member.id) in warns[str(interaction.guild.id)].keys():
                warns[str(interaction.guild.id)][str(member.id)] = []

            new_warn = {"moderator_id": str(interaction.user.id), "warn": warn}
            warns[str(interaction.guild.id)][str(member.id)].append(new_warn)

            await self.bot.db.update("warns", warns)

            guild_warns = warns[str(interaction.guild.id)]
            user_warns = guild_warns[str(member.id)]
            total = len(user_warns)

            embed = discord.Embed(
                description=f"**{member}** {text['MODERATION_WARNINGS_WAS_WARNED'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_WAS_WARNED'][1]} {total}",
                color=GREEN)
            embed.add_field(name=text['MODERATION_WARNINGS_WARN'], value=warn)

            await respond(interaction, message=embed)
            try:
                await member.send(
                    f"{text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}** {text['MODERATION_WARNINGS_PRIVATE_MSG'][1]} **{interaction.guild.name}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}")
            except:
                await respond(interaction, YELLOW,
                              message=f"{member.mention}, {text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}",
                              response_type=1)

            if total >= 6:
                await member.kick(reason=f"{text['MODERATION_WARNINGS_BAN_LIMIT_REACHED']} 6.")
                await respond(interaction, RED,
                              message=f"{member.name} {text['MODERATION_WARNINGS_WARN_LIMIT_REACHED_EMBED']}",
                              response_type=1)
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    # Removes a warning from a user in a given guild
    @warnings.command(
        name=text['MODERATION_WARNINGS_REM_NAME'],
        description=text['MODERATION_WARNINGS_REM_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _warnings_remove(self, interaction: Interaction, member: discord.Member = None,
                               warn_id: str = None) -> None:
        try:
            if not member or not warn_id or not warn_id.isnumeric():
                return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

            warns = await self.bot.db.get("warns")
            if not warns:
                return await respond(interaction, RED, message=text['MODERATION_WARNINGS_NO_WARNINGS'])
            if not str(interaction.guild.id) in warns.keys():
                return await respond(interaction, RED, message=text['MODERATION_WARNINGS_NO_WARNINGS'])
            if not str(member.id) in warns[str(interaction.guild.id)].keys():
                return await respond(interaction, RED, message=text['MODERATION_WARNINGS_NO_WARNINGS'])

            warns[str(interaction.guild.id)][str(member.id)].pop(int(warn_id) - 1)

            await self.bot.db.update("warns", warns)

            guild_warns = warns[str(interaction.guild.id)]

            user_warns = guild_warns[str(member.id)]
            total = len(user_warns)

            await respond(interaction, GREEN,
                          message=f"{text['MODERATION_WARNINGS_WARN_REMOVED'][0]} **#{warn_id}** {text['MODERATION_WARNINGS_WARN_REMOVED'][1]} **{member}**!\n{text['MODERATION_WARNINGS_WARN_REMOVED'][2]} {total}")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @admins.command(
        name=text['MODERATION_ADMINS_ADD_NAME'],
        description=text['MODERATION_ADMINS_ADD_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _admins_add(self, interaction: Interaction, member: discord.Member = None) -> None:
        try:
            if not member:
                return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
            if not member.guild_permissions.administrator:
                return await respond(interaction, RED, message=text['MODERATION_ADMINS_USER_NOT_ADMIN'])

            admins = await self.bot.db.get("admins")
            if not str(interaction.guild.id) in admins.keys():
                admins[str(interaction.guild.id)] = []

            if str(member.id) in admins[str(interaction.guild.id)]:
                return await respond(interaction, RED, message=text['MODERATION_ADMINS_ALREADY_ADMIN'])
            else:
                admins[str(interaction.guild.id)].append(str(member.id))

                await self.bot.db.update("admins", admins)

                await respond(interaction, GREEN,
                              message=f"{text['MODERATION_ADMINS_ADDED'][0]}{member.name} {text['MODERATION_ADMINS_ADDED'][1]}")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @admins.command(
        name=text['MODERATION_ADMINS_REM_NAME'],
        description=text['MODERATION_ADMINS_REM_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _admins_rem(self, interaction: Interaction, member: discord.Member = None) -> None:
        try:
            if not member:
                return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

            admins = await self.bot.db.get("admins")
            if not str(interaction.guild.id) in admins.keys():
                return await respond(interaction, RED, message=text['MODERATION_ADMINS_NOT_ADMIN'])
            if not str(member.id) in admins[str(interaction.guild.id)]:
                return await respond(interaction, RED, message=text['MODERATION_ADMINS_NOT_ADMIN'])

            admins[str(interaction.guild.id)].remove(str(member.id))

            await self.bot.db.update("admins", admins)

            await respond(interaction, GREEN,
                          message=f"{text['MODERATION_ADMINS_REMOVED'][0]}{member.name} {text['MODERATION_ADMINS_REMOVED'][1]}")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @admins.command(
        name=text['MODERATION_ADMINS_SET_NAME'],
        description=text['MODERATION_ADMINS_SET_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    @not_blacklisted()
    # @is_admin()
    # @is_owner()
    async def _admins_set(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await respond(interaction, RED, message=text['MODERATION_ADMINS_SET_NOT_ADMIN'])
        else:
            admins = await self.bot.db.get("admins")
            if not str(interaction.guild.id) in admins.keys():
                admins[str(interaction.guild.id)] = []

            admins[str(interaction.guild.id)].append(str(interaction.user.id))

            await self.bot.db.update("admins", admins)

            await respond(interaction, GREEN,
                          message=f"**{interaction.user.name}** {text['MODERATION_ADMINS_SET_ADDED']}")

    @blacklist.command(
        name=text['MODERATION_BL_SHOW_NAME'],
        description=text['MODERATION_BL_SHOW_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _blacklist_show(self, interaction: Interaction) -> None:
        blacklist = await self.bot.db.get("blacklist")

        if not str(interaction.guild.id) in blacklist.keys():
            return await respond(interaction, GREEN, message=text['MODERATION_BLACKLIST_NO_USERS'])
        if not len(blacklist[str(interaction.guild.id)]) > 0:
            return await respond(interaction, GREEN, message=text['MODERATION_BLACKLIST_NO_USERS'])

        embed = discord.Embed = discord.Embed(title=text['MODERATION_BLACKLIST_USER_COUNT'], color=YELLOW)
        users = []

        for bluser in blacklist[str(interaction.guild.id)]:
            user = self.bot.get_user(bluser) or await self.bot.fetch_user(bluser)
            users.append(f" • {user.mention} ({user}) {text['MODERATION_BLACKLIST_BLACKLISTED']}")

        embed.description = "\n".join(users)

        await respond(interaction, message=embed)

    @blacklist.command(
        name=text['MODERATION_BL_ADD_NAME'],
        description=text['MODERATION_BL_ADD_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _blacklist_add(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        blacklist = await self.bot.db.get("blacklist")

        if not str(interaction.guild.id) in blacklist.keys():
            blacklist[str(interaction.guild.id)] = []
        if str(member.id) in blacklist[str(interaction.guild.id)]:
            return await respond(interaction, RED,
                                 message=f"**{member.name}** {text['MODERATION_BLACKLIST_IS_BLACKLISTED']}")

        blacklist[str(interaction.guild.id)].append(str(member.id))

        await self.bot.db.update("blacklist", blacklist)

        total = len(blacklist[str(interaction.guild.id)])

        embed = discord.Embed(
            description=f"**{member.mention}** {text['MODERATION_BLACKLIST_CANT_USE_ME']}",
            color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")

        await respond(interaction, message=embed)

    @blacklist.command(
        name=text['MODERATION_BL_REM_NAME'],
        description=text['MODERATION_BL_REM_DESC'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _blacklist_rem(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        blacklist = await self.bot.db.get("blacklist")

        if not str(interaction.guild.id) in blacklist.keys():
            return await respond(interaction, GREEN, message=text['MODERATION_BLACKLIST_NO_USERS'])
        if not str(member.id) in blacklist[str(interaction.guild.id)]:
            return await respond(interaction, RED,
                                 message=f"**{member.name}** {text['MODERATION_BLACKLIST_NOT_ON_BLACKLIST']}")

        blacklist[str(interaction.guild.id)].remove(str(member.id))

        await self.bot.db.update("blacklist", blacklist)

        total = len(blacklist[str(interaction.guild.id)])

        embed = discord.Embed(
            description=f"**{member.mention}** {text['MODERATION_BLACKLIST_CAN_USE_ME']}", color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")

        await respond(interaction, message=embed)

    @app_commands.command(
        name=text['MODERATION_BAN_NAME'],
        description=text['MODERATION_BAN_DESC'])
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _ban(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        try:
            await interaction.guild.ban(member)

            await respond(interaction, GREEN, message=f"{text['MODERATION_BAN_EMBED']} **{member.name}**!")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @app_commands.command(
        name=text['MODERATION_KICK_NAME'],
        description=text['MODERATION_KICK_DESC'])
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _kick(self, interaction: Interaction, member: discord.Member = None) -> None:
        if not member:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        try:
            await interaction.guild.kick(member)

            await respond(interaction, GREEN, message=f"{text['MODERATION_KICK_EMBED']} **{member.name}**!")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @app_commands.command(
        name=text['MODERATION_NICK_NAME'],
        description=text['MODERATION_NICK_DESC'])
    @app_commands.checks.has_permissions(change_nickname=True)
    @app_commands.checks.bot_has_permissions(change_nickname=True)
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _nick(self, interaction: Interaction, member: discord.Member = None, nick: str = None) -> None:
        if not member or not nick:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])

        try:
            old = member.nick

            await member.edit(nick=nick)

            await respond(interaction, GREEN,
                          message=f"{member.mention}{text['MODERATION_NICK_CHANGED'][0]} `{old}` {text['MODERATION_NICK_CHANGED'][1]} `{nick}`")
        except Exception as e:
            await respond(interaction, RED, message=f"{format_exception(e)}")

    @hybrid_command(
        name=text['MODERATION_CENSOR_NAME'],
        description=text['MODERATION_CENSOR_DESC'])
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.describe(from_user=text['MODERATION_CENSOR_FROM_USER'])
    @not_blacklisted()
    @is_admin()
    # @is_owner()
    async def _censor(self, ctx: Context, amount: str=None, from_user: discord.Member=None) -> None:
        if not amount or not amount.isnumeric():
            return await respond(ctx, RED, message=text['ERROR_INVALID_PARAMETERS'])

        def is_me(m):
            return m.author == from_user

        try:
            await respond(ctx, YELLOW,
                          message=f"{text['MODERATION_CENSOR_EMBED'][0]} {amount} {text['MODERATION_CENSOR_EMBED'][1]} `{ctx.channel.name}`")

            if from_user:
                await ctx.channel.purge(limit=int(amount), check=is_me)
            else:
                await ctx.channel.purge(limit=int(amount))
        except Exception as e:
            await respond(ctx, RED, message=f"{format_exception(e)}")

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Moderation(bot))