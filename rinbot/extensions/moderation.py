# Imports
import discord, os, asyncio
from discord.app_commands import Group, check
from discord.ext.commands import Bot, Cog, Context
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang
from rinbot.base.responder import Responder
from rinbot.base import db_manager
from dotenv import load_dotenv

# Load verbose
text = load_lang()

# Load env vars
load_dotenv()
WARNING_BAN_LIMIT = os.getenv("MOD_WARNING_BAN_LIMIT")

# Moderation command cog
class Moderation(Cog, name="moderation"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.responder = Responder(self.bot)

    # Command groups
    warnings_group = Group(name=f"{text['MODERATION_WARNINGS_NAME']}", description=f"{text['MODERATION_WARNINGS_DESC']}")
    admins_group = Group(name=f"{text['MODERATION_ADMINS_NAME']}", description=f"{text['MODERATION_ADMINS_DESC']}")
    blacklist_group = Group(name=f"{text['MODERATION_BL_NAME']}", description=f"{text['MODERATION_BL_DESC']}")
    
    # Show a user's warnings on that guild
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_SHOW_NAME']}",
        description=f"{text['MODERATION_WARNINGS_SHOW_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def warnings_show(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        warnings_list = await db_manager.get_warnings(user.id, interaction.guild.id)
        embed = discord.Embed(title=f"{user} {text['MODERATION_WARNINGS_EMBED_WARN']}", color=GREEN)
        description = ""
        if len(warnings_list) == 0:
            description = f"{text['MODERATION_WARNINGS_NO_WARNINGS']}"
        else:
            for warning in warnings_list:
                description += f"{text['MODERATION_WARNINGS_CREATE_WARNING'][0]} <@{warning[1]}>: **{warning[2]}** (<t:{warning[3]}>) - {text['MODERATION_WARNINGS_CREATE_WARNING'][1]}{warning[4]}\n"
        embed.description = description
        await self.responder.respond(interaction, message=embed)

    # Adds a warn to a user in a given guild
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_ADD_NAME']}",
        description=f"{text['MODERATION_WARNINGS_ADD_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def warnings_add(self, interaction:discord.Interaction, user:discord.User=None, warn:str=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
        total = await db_manager.add_warn(
            user.id, interaction.guild.id, interaction.user.id, warn)
        embed = discord.Embed(
            description=f"**{member}** {text['MODERATION_WARNINGS_WAS_WARNED'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_WAS_WARNED'][1]} {total}",
            color=0x9C84EF,)
        embed.add_field(name=f"{text['MODERATION_WARNINGS_WARN']}", value=warn)
        await self.responder.respond(interaction, message=embed)
        try: await member.send(f"{text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}** {text['MODERATION_WARNINGS_PRIVATE_MSG'][1]} **{interaction.guild.name}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}")
        except: await interaction.channel.send(f"{member.mention}, {text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}")
        warnings_list = await db_manager.get_warnings(user.id, interaction.guild.id)
        if WARNING_BAN_LIMIT.isnumeric():
            if len(warnings_list) >= int(WARNING_BAN_LIMIT):
                await member.kick(reason=f"{text['MODERATION_WARNINGS_BAN_LIMIT_REACHED']} {WARNING_BAN_LIMIT}.")
                await self.responder.respond(interaction, RED, f"{user.name} {text['MODERATION_WARNINGS_WARN_LIMIT_REACHED_EMBED']}", response_type=2)
    
    # Removes a warning from a user in a given guild
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_REM_NAME']}",
        description=f"{text['MODERATION_WARNINGS_REM_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def warnings_remove(self, interaction:discord.Interaction, user:discord.User=None, warn_id:int=None) -> None:
        if not user or not warn_id:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
        total = await db_manager.remove_warn(warn_id, user.id, interaction.guild.id)
        await self.responder.respond(interaction, GREEN, f"{text['MODERATION_WARNINGS_WARN_REMOVED'][0]} **#{warn_id}** {text['MODERATION_WARNINGS_WARN_REMOVED'][1]} **{member}**!\n{text['MODERATION_WARNINGS_WARN_REMOVED'][2]} {total}")
    
    # Adds a user to the admins class
    @admins_group.command(
        name=f"{text['MODERATION_ADMINS_ADD_NAME']}",
        description=f"{text['MODERATION_ADMINS_ADD_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def admins_add(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if await db_manager.is_admin(user.id, interaction.guild.id):
            return await self.responder.respond(interaction, RED, text['MODERATION_ADMINS_ALREADY_ADMIN'])
        if await db_manager.add_user_to_admins(user.id, interaction.guild.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ADDED'][0]}{user.name} {text['MODERATION_ADMINS_ADDED'][1]}",
                color=GREEN)
        else:
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ERROR_ADDING'][0]}{user.name} {text['MODERATION_ADMINS_ERROR_ADDING'][1]}",
                color=RED)
        await self.responder.respond(interaction, message=embed)

    # Removes a user from the admins class
    @admins_group.command(
        name=f"{text['MODERATION_ADMINS_REM_NAME']}",
        description=f"{text['MODERATION_ADMINS_REM_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def admins_rem(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if not await db_manager.is_admin(user.id, interaction.guild.id):
            return await self.responder.respond(interaction, RED, text['MODERATION_ADMINS_NOT_ADMIN'])
        if await db_manager.remove_user_from_admins(user.id, interaction.guild.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_REMOVED'][0]}{user.name} {text['MODERATION_ADMINS_REMOVED'][1]}",
                color=GREEN)
        else:
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ERROR_REMOVING'][0]}{user.name} {text['MODERATION_ADMINS_ERROR_REMOVING'][1]}",
                color=RED)
        await self.responder.respond(interaction, message=embed)
    
    # Command used by server admins to add themselves to rinbot's admin class
    @admins_group.command(
        name=f"{text['MODERATION_ADMINS_SET_NAME']}",
        description=f"{text['MODERATION_ADMINS_SET_DESC']}")
    @not_blacklisted_ac()
    async def admins_set(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_SET_NOT_ADMIN']}",
                color=RED)
        else:
            if not await db_manager.is_admin(user.id, interaction.guild.id):
                add = await db_manager.add_user_to_admins(user.id, interaction.guild.id)
                embed = discord.Embed(
                    description=f"{user.name} {text['MODERATION_ADMINS_SET_ADDED']}" if add else f"{user.name} {text['MODERATION_ADMINS_SET_NOT_ADDED']}",
                    color=GREEN if add else RED)
            else:
                embed = discord.Embed(
                    description=f"{user.name} {text['MODERATION_ADMINS_ALREADY_ADMIN']}",
                    color=RED)
        await self.responder.respond(interaction, message=embed)
    
    # Show users on the guild's blacklist
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_SHOW_NAME']}",
        description=f"{text['MODERATION_BL_SHOW_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def blacklist_show(self, interaction:discord.Interaction) -> None:
        blacklisted = await db_manager.get_blacklisted(interaction.guild.id)
        if len(blacklisted) == 0:
            return await self.responder.respond(interaction, GREEN, text['MODERATION_BLACKLIST_NO_USERS'])
        embed = discord.Embed(title=f"{text['MODERATION_BLACKLIST_USER_COUNT']}", color=YELLOW)
        users = []
        for bluser in blacklisted:
            user = self.bot.get_user(int(bluser[0])) or await self.bot.fetch_user(int(bluser[0]))
            users.append(f" • {user.mention} ({user}) {text['MODERATION_BLACKLIST_BLACKLISTED']} <t:{bluser[0]}>")
        embed.description = "\n".join(users)
        await self.responder.respond(interaction, message=embed)
    
    # Add a user to the guild's blacklist
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_ADD_NAME']}",
        description=f"{text['MODERATION_BL_ADD_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def blacklist_add(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if await db_manager.is_blacklisted(user.id, interaction.guild.id):
            embed = discord.Embed(
                description=f"**{user.name}** {text['MODERATION_BLACKLIST_IS_BLACKLISTED']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        total = await db_manager.add_user_to_blacklist(user.id, interaction.guild.id)
        embed = discord.Embed(
            description=f"**{user.mention}** {text['MODERATION_BLACKLIST_CANT_USE_ME']}",
            color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")
        await interaction.response.send_message(embed=embed)
    
    # Remove a user from the guild's blacklist
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_REM_NAME']}",
        description=f"{text['MODERATION_BL_REM_DESC']}")
    @not_blacklisted_ac()
    @is_admin_ac()
    async def blacklist_remove(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            return await self.responder.respond(interaction, RED, text['ERROR_INVALID_PARAMETERS'])
        if not await db_manager.is_blacklisted(user.id, interaction.guild.id):
            embed = discord.Embed(
                description=f"**{user.name}** {text['MODERATION_BLACKLIST_NOT_ON_BLACKLIST']}",
                color=RED)
            return await self.responder.respond(interaction, message=embed)
        total = await db_manager.remove_user_from_blacklist(user.id, interaction.guild.id)
        embed = discord.Embed(
            description=f"**{user.mention}** {text['MODERATION_BLACKLIST_CAN_USE_ME']}",
            color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")
        await self.responder.respond(interaction, message=embed)

    # Deletes a number of messages from the text channel
    @commands.hybrid_command(
        name=f"{text['MODERATION_CENSOR_NAME']}",
        description=f"{text['MODERATION_CENSOR_DESC']}")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @not_blacklisted()
    @is_admin()
    async def censor(self, ctx:Context, amount:str=None) -> None:
        if not amount or not amount.isnumeric():
            return await self.responder.respond(ctx, RED, text['ERROR_INVALID_PARAMETERS'])
        await self.responder.respond(ctx, RED, f"{text['MODERATION_CENSOR_EMBED'][0]} `{amount}` {text['MODERATION_CENSOR_EMBED'][1]} `{ctx.channel.name}`")
        await asyncio.sleep(2)
        await ctx.channel.purge(limit=int(amount))

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Moderation(bot))