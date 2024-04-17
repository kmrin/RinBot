"""
RinBot's moderation command cog

- Command:
    * /warnings show `Shows a user's warnings`
    * /warnings add `Adds a warning to a user in a guild`
    * /warnings remove `Removes a warning from a user in a guild`
    * /admins add `Adds a user to the admins class of a guild`
    * /admins remove `Removes a user from the admins class of a guild`
    * /admins set `Adds a user with admin privileges to the admins class of a guild`
    * /blacklist show `Shows the blacklist of a guild`
    * /blacklist add `Adds a user to a guild's blacklist`
    * /blacklist remove `Removes a user from a guild's blacklist`
    * /censor `Deletes a certain amount of messages from the channel`
"""

import asyncio
import discord

from discord import app_commands, Interaction
from discord.ext.commands import Cog, Context, hybrid_command

from rinbot.base import log_exception
from rinbot.base import respond
from rinbot.base import DBTable
from rinbot.base import RinBot
from rinbot.base import Colour
from rinbot.base import conf
from rinbot.base import text

# from rinbot.base import is_owner
from rinbot.base import is_admin
from rinbot.base import not_blacklisted

class Moderation(Cog, name='moderation'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    warnings = app_commands.Group(name=text['MODERATION_WARNINGS_NAME'], description=text['MODERATION_WARNINGS_DESC'])
    admins = app_commands.Group(name=text['MODERATION_ADMINS_NAME'], description=text['MODERATION_ADMINS_DESC'])
    blacklist = app_commands.Group(name=text['MODERATION_BL_NAME'], description=text['MODERATION_BL_DESC'])

    @warnings.command(
        name=text['MODERATION_WARNINGS_SHOW_NAME'],
        description=text['MODERATION_WARNINGS_SHOW_DESC'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _warnings_show(self, interaction: Interaction, member: discord.Member) -> None:
        try:            
            warnings = await self.bot.db.get(
                DBTable.WARNS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")
            
            if not warnings:
                return await respond(interaction, Colour.RED, text['MODERATION_WARNINGS_NO_WARNINGS'])

            embed = discord.Embed(
                title=f"**{member}** {text['MODERATION_WARNINGS_EMBED_WARN']}",
                description="",
                colour=Colour.GREEN
            )

            warns = {}
            for warning in warnings:
                warns[warning[4]] = {
                    "guild": warning[0],
                    "user": warning[1],
                    "moderator": warning[2],
                    "warn": warning[3],
                    "id": warning[4]
                }

            description = ""
            for warning in warns.values():
                description += f"""{
                text['MODERATION_WARNINGS_CREATE_WARNING'][0]
                } <@{warning['moderator']}>: <@{warning['user']}> - {
                text['MODERATION_WARNINGS_CREATE_WARNING'][1]}{warning['id']}: `{
                warning['warn']
                }`\n"""

            embed.description = description

            await respond(interaction, message=embed)
        except Exception as e:
            log_exception(e)

    @warnings.command(
        name=text['MODERATION_WARNINGS_ADD_NAME'],
        description=text['MODERATION_WARNINGS_ADD_DESC'])
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _warnings_add(self, interaction: Interaction, member: discord.Member, warn: str) -> None:
        try:
            if not member or not warn:
                return await respond(interaction, Colour.RED, text['ERROR_INVALID_PARAMETERS'])

            new_warn = {
                "guild_id": interaction.guild.id,
                "user_id": member.id,
                "moderator_id": interaction.user.id,
                "warn": warn
            }

            await self.bot.db.put(DBTable.WARNS, new_warn)

            warnings = await self.bot.db.get(DBTable.WARNS,
                                             condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

            total = len(warnings)

            embed = discord.Embed(
                description=f"**{member}** {text['MODERATION_WARNINGS_WAS_WARNED'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_WAS_WARNED'][1]} {total}",
                colour=Colour.GREEN
            )

            embed.add_field(name=text['MODERATION_WARNINGS_WARN'], value=warn)

            await respond(interaction, message=embed)

            try:
                await member.send(
                    f"{text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}** {text['MODERATION_WARNINGS_PRIVATE_MSG'][1]} **{interaction.guild.name}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}"
                )
            except:
                await respond(interaction, Colour.YELLOW,
                    f"{member.mention}, {text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}",
                    response_type=1
                )

            if total >= conf['WARNING_AUTO_KICK_LIMIT'] and conf['WARNING_AUTO_KICK_ENABLED']:
                await member.kick(reason=f"{text['MODERATION_WARNINGS_BAN_LIMIT_REACHED']} {conf['WARNING_AUTO_KICK_LIMIT']}.")
                await respond(interaction, Colour.RED, f"{member.name} {text['MODERATION_WARNINGS_WARN_LIMIT_REACHED_EMBED']}",
                    response_type=1)
        except Exception as e:
            log_exception(e)
    
    @warnings.command(
        name=text['MODERATION_WARNINGS_REM_NAME'],
        description=text['MODERATION_WARNINGS_REM_DESC'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _warnings_remove(self, interaction: Interaction, member: discord.Member, warn_id: int) -> None:
        try:
            warnings = await self.bot.db.get(DBTable.WARNS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id} AND id={warn_id}")

            if not warnings:
                return await respond(interaction, Colour.RED, message=text['MODERATION_WARNINGS_NO_WARNINGS'])

            await self.bot.db.delete(DBTable.WARNS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id} AND id={warn_id}")

            warnings = await self.bot.db.get(DBTable.WARNS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

            total = len(warnings)

            await respond(interaction, Colour.GREEN,
                  message=f"{text['MODERATION_WARNINGS_WARN_REMOVED'][0]} **#{warn_id}** {text['MODERATION_WARNINGS_WARN_REMOVED'][1]} **{member}**!\n{text['MODERATION_WARNINGS_WARN_REMOVED'][2]} {total}")
        except Exception as e:
            log_exception(e)
    
    @admins.command(
        name=text['MODERATION_ADMINS_ADD_NAME'],
        description=text['MODERATION_ADMINS_ADD_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _admins_add(self, interaction: Interaction, member: discord.Member) -> None:
        try:
            if not member.guild_permissions.administrator:
                return await respond(interaction, Colour.RED, text['MODERATION_ADMINS_USER_NOT_ADMIN'])

            is_already_admin = await self.bot.db.get(DBTable.ADMINS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

            if is_already_admin:
                return await respond(interaction, Colour.RED, text['MODERATION_ADMINS_ALREADY_ADMIN'])

            await self.bot.db.put(DBTable.ADMINS, {
                "guild_id": interaction.guild.id,
                "user_id": member.id
            })

            await respond(interaction, Colour.GREEN, f"{text['MODERATION_ADMINS_ADDED'][0]}{member.name} {text['MODERATION_ADMINS_ADDED'][1]}")
        except Exception as e:
            log_exception(e)
    
    @admins.command(
        name=text['MODERATION_ADMINS_REM_NAME'],
        description=text['MODERATION_ADMINS_REM_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _admins_remove(self, interaction: Interaction, member: discord.Member) -> None:
        try:
            is_already_admin = await self.bot.db.get(DBTable.ADMINS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

            if not is_already_admin:
                return await respond(interaction, Colour.RED, text['MODERATION_ADMINS_NOT_ADMIN'])

            await self.bot.db.delete(DBTable.ADMINS,
                condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

            await respond(interaction, Colour.GREEN, f"{text['MODERATION_ADMINS_REMOVED'][0]}{member.name} {text['MODERATION_ADMINS_REMOVED'][1]}")
        except Exception as e:
            log_exception(e)
    
    @admins.command(
        name=text['MODERATION_ADMINS_SET_NAME'],
        description=text['MODERATION_ADMINS_SET_DESC'])
    @app_commands.checks.has_permissions(administrator=True)
    # @is_owner()
    # @is_admin()
    @not_blacklisted()
    async def _admins_set(self, interaction: Interaction) -> None:
        if not interaction.user.guild_permissions.administrator:
            return await respond(interaction, Colour.RED, text['MODERATION_ADMINS_SET_NOT_ADMIN'])

        is_already_admin = await self.bot.db.get(DBTable.ADMINS,
            condition=f"guild_id={interaction.guild.id} AND user_id={interaction.user.id}")

        if is_already_admin:
            return await respond(interaction, Colour.RED, text['MODERATION_ADMINS_ALREADY_ADMIN'])

        await self.bot.db.put(DBTable.ADMINS, {
            "guild_id": interaction.guild.id,
            "user_id": interaction.user.id
        })

        await respond(interaction, Colour.GREEN, f"**{interaction.user.name}** {text['MODERATION_ADMINS_SET_ADDED']}")

    @blacklist.command(
        name=text['MODERATION_BL_SHOW_NAME'],
        description=text['MODERATION_BL_SHOW_DESC'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _blacklist_show(self, interaction: Interaction) -> None:
        blacklist = await self.bot.db.get(DBTable.BLACKLIST,
            condition=f"guild_id={interaction.guild.id}")

        if not blacklist:
            return await respond(interaction, Colour.GREEN, text['MODERATION_BLACKLIST_NO_USERS'])

        embed = discord.Embed(
            title=text['MODERATION_BLACKLIST_USER_COUNT'],
            color=Colour.YELLOW
        )

        users = []
        for user in blacklist:
            user = self.bot.get_user(user[1]) or await self.bot.fetch_user(user[1])
            users.append(f" • {user.mention} ({user}) {text['MODERATION_BLACKLIST_BLACKLISTED']}")

        embed.description = "\n".join(users)

        await respond(interaction, message=embed)
    
    @blacklist.command(
        name=text['MODERATION_BL_ADD_NAME'],
        description=text['MODERATION_BL_ADD_DESC'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _blacklist_add(self, interaction: Interaction, member: discord.Member) -> None:
        blacklist = await self.bot.db.get(DBTable.BLACKLIST,
                                          condition=f"guild_id={interaction.guild.id}")

        users = [row[1] for row in blacklist]
        if member.id in users:
            return await respond(interaction, Colour.RED, message=f"**{member.name}** {text['MODERATION_BLACKLIST_IS_BLACKLISTED']}")

        await self.bot.db.put(DBTable.BLACKLIST, {
            "guild_id": interaction.guild.id,
            "user_id": member.id
        })

        blacklist = await self.bot.db.get(DBTable.BLACKLIST,
            condition=f"guild_id={interaction.guild.id}")

        total = len(blacklist)

        embed = discord.Embed(
            description=f"**{member.mention}** {text['MODERATION_BLACKLIST_CANT_USE_ME']}",
            colour=Colour.GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")

        await respond(interaction, message=embed)
    
    @blacklist.command(
        name=text['MODERATION_BL_REM_NAME'],
        description=text['MODERATION_BL_REM_DESC'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _blacklist_rem(self, interaction: Interaction, member: discord.Member) -> None:
        blacklist = await self.bot.db.get(DBTable.BLACKLIST,
            condition=f"guild_id={interaction.guild.id} AND user_id={interaction.user.id}")

        users = [row[1] for row in blacklist]
        if member.id not in users:
            return await respond(interaction, Colour.RED, f"**{member.name}** {text['MODERATION_BLACKLIST_NOT_ON_BLACKLIST']}")

        await self.bot.db.delete(DBTable.BLACKLIST,
            condition=f"guild_id={interaction.guild.id} AND user_id={member.id}")

        blacklist = await self.bot.db.get(DBTable.BLACKLIST,
            condition=f"guild_id={interaction.guild.id} AND user_id={interaction.user.id}")

        embed = discord.Embed(
            description=f"**{member.mention}** {text['MODERATION_BLACKLIST_CAN_USE_ME']}",
            color=Colour.GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {len(blacklist)}")

        await respond(interaction, message=embed)

    @hybrid_command(
        name=text['MODERATION_CENSOR_NAME'],
        description=text['MODERATION_CENSOR_DESC'])
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.describe(from_user=text['MODERATION_CENSOR_FROM_USER'])
    # @is_owner()
    @is_admin()
    @not_blacklisted()
    async def _censor(self, ctx: Context, amount: app_commands.Range[int, 1, 50], from_user: discord.Member=None) -> None:
        def is_me(m):
            return m.author == from_user or m.author.id == from_user.id

        try:
            await respond(ctx, Colour.YELLOW, f"{text['MODERATION_CENSOR_EMBED'][0]} {amount} {text['MODERATION_CENSOR_EMBED'][1] if amount == 1 else text['MODERATION_CURSOR_EMBED'][2]} `{ctx.channel.name}`")
            await asyncio.sleep(2)
            if from_user:
                await ctx.channel.purge(limit=amount, check=is_me)
            else:
                await ctx.channel.purge(limit=amount)
        except Exception as e:
            log_exception(e)

# SETUP
async def setup(bot: RinBot):
    await bot.add_cog(Moderation(bot))
