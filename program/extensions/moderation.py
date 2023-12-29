# Imports
import discord, os
from discord.app_commands import Group
from discord.ext.commands import Bot, Cog, Context
from program.base.checks import *
from program.base.helpers import load_lang
from program.base import db_manager
from dotenv import load_dotenv
from program.base.colors import *

# Load verbose
text = load_lang()

# Load env vars
load_dotenv()
WARNING_BAN_LIMIT = os.getenv("MOD_WARNING_BAN_LIMIT")

# Moderation command cog
class Moderation(Cog, name="moderation"):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    warnings_group = Group(name=f"{text['MODERATION_WARNINGS_NAME']}", description=f"{text['MODERATION_WARNINGS_DESC']}")
    admins_group = Group(name=f"{text['MODERATION_ADMINS_NAME']}", description=f"{text['MODERATION_ADMINS_DESC']}")
    blacklist_group = Group(name=f"{text['MODERATION_BL_NAME']}", description=f"{text['MODERATION_BL_DESC']}")
    
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_SHOW_NAME']}",
        description=f"{text['MODERATION_WARNINGS_SHOW_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def warnings_show(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        warnings_list = await db_manager.get_warnings(user.id, interaction.guild.id)
        embed = discord.Embed(title=f"{user} {text['MODERATION_WARNINGS_EMBED_WARN']}", color=GREEN)
        description = ""
        if len(warnings_list) == 0:
            description = f"{text['MODERATION_WARNINGS_NO_WARNINGS']}"
        else:
            for warning in warnings_list:
                description += f"{text['MODERATION_WARNINGS_CREATE_WARNING'][0]} <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - {text['MODERATION_WARNINGS_CREATE_WARNING'][1]}{warning[5]}\n"
        embed.description = description
        await interaction.response.send_message(embed=embed)
    
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_ADD_NAME']}",
        description=f"{text['MODERATION_WARNINGS_ADD_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def warnings_add(self, interaction:discord.Interaction, user:discord.User=None, warn:str=None) -> None:
        if not user or not warn:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
        total = await db_manager.add_warn(
            user.id, interaction.guild.id, interaction.user.id, warn)
        embed = discord.Embed(
            description=f"**{member}** {text['MODERATION_WARNINGS_WAS_WARNED'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_WAS_WARNED'][1]} {total}",
            color=0x9C84EF,)
        embed.add_field(name=f"{text['MODERATION_WARNINGS_WARN']}", value=warn)
        await interaction.response.send_message(embed=embed)
        try:
            await member.send(f"{text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}** {text['MODERATION_WARNINGS_PRIVATE_MSG'][1]} **{interaction.guild.name}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}")
        except:
            await interaction.channel.send(f"{member.mention}, {text['MODERATION_WARNINGS_PRIVATE_MSG'][0]} **{interaction.user}**!\n{text['MODERATION_WARNINGS_PRIVATE_MSG'][2]} {warn}")
        warnings_list = await db_manager.get_warnings(user.id, interaction.guild.id)
        if WARNING_BAN_LIMIT.isnumeric():
            if len(warnings_list) >= int(WARNING_BAN_LIMIT):
                await member.kick(reason=f"{text['MODERATION_WARNINGS_BAN_LIMIT_REACHED']} {WARNING_BAN_LIMIT}.")
                embed = discord.Embed(
                    description=f"{user.name} {text['MODERATION_WARNINGS_WARN_LIMIT_REACHED_EMBED']}",
                    color=RED)
                await interaction.channel.send(embed=embed)
    
    @warnings_group.command(
        name=f"{text['MODERATION_WARNINGS_REM_NAME']}",
        description=f"{text['MODERATION_WARNINGS_REM_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def warnings_remove(self, interaction:discord.Interaction, user:discord.User=None, warn_id:int=None) -> None:
        if not user or not warn_id:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        member = interaction.guild.get_member(user.id) or await interaction.guild.fetch_member(user.id)
        total = await db_manager.remove_warn(warn_id, user.id, interaction.guild.id)
        embed = discord.Embed(
            description=f"{text['MODERATION_WARNINGS_WARN_REMOVED'][0]} **#{warn_id}** {text['MODERATION_WARNINGS_WARN_REMOVED'][1]} **{member}**!\n{text['MODERATION_WARNINGS_WARN_REMOVED'][2]} {total}",
            color=GREEN,)
        await interaction.response.send_message(embed=embed)
    
    @admins_group.command(
        name=f"{text['MODERATION_ADMINS_ADD_NAME']}",
        description=f"{text['MODERATION_ADMINS_ADD_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def admins_add(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.is_admin(user.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ALREADY_ADMIN']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.add_user_to_admins(user.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ADDED'][0]}{user.name} {text['MODERATION_ADMINS_ADDED'][1]}",
                color=GREEN)
        else:
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ERROR_ADDING'][0]}{user.name} {text['MODERATION_ADMINS_ERROR_ADDING'][1]}",
                color=RED)
        await interaction.response.send_message(embed=embed)

    @admins_group.command(
        name=f"{text['MODERATION_ADMINS_REM_NAME']}",
        description=f"{text['MODERATION_ADMINS_REM_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def admins_rem(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if not await db_manager.is_admin(user.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_NOT_ADMIN']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.remove_user_from_admins(user.id):
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_REMOVED'][0]}{user.name} {text['MODERATION_ADMINS_REMOVED'][1]}",
                color=GREEN)
        else:
            embed = discord.Embed(
                description=f"{text['MODERATION_ADMINS_ERROR_REMOVING'][0]}{user.name} {text['MODERATION_ADMINS_ERROR_REMOVING'][1]}",
                color=RED)
        await interaction.response.send_message(embed=embed)
    
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_SHOW_NAME']}",
        description=f"{text['MODERATION_BL_SHOW_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def blacklist_show(self, interaction:discord.Interaction) -> None:
        blacklisted = await db_manager.get_blacklisted()
        if len(blacklisted) == 0:
            embed = discord.Embed(
                description=f"{text['MODERATION_BLACKLIST_NO_USERS']}",
                color=GREEN)
            return await interaction.response.send_message(embed=embed)
        embed = discord.Embed(title=f"{text['MODERATION_BLACKLIST_USER_COUNT']}", color=YELLOW)
        users = []
        for bluser in blacklisted:
            user = self.bot.get_user(int(bluser[0])) or await self.bot.fetch_user(int(bluser[0]))
            users.append(f" • {user.mention} ({user}) {text['MODERATION_BLACKLIST_BLACKLISTED']} <t:{bluser[1]}>")
        embed.description = "\n".join(users)
        await interaction.response.send_message(embed=embed)
    
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_ADD_NAME']}",
        description=f"{text['MODERATION_BL_ADD_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def blacklist_add(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if await db_manager.is_blacklisted(user.id):
            embed = discord.Embed(
                description=f"**{user.name}** {text['MODERATION_BLACKLIST_IS_BLACKLISTED']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        total = await db_manager.add_user_to_blacklist(user.id)
        embed = discord.Embed(
            description=f"**{user.mention}** {text['MODERATION_BLACKLIST_CANT_USE_ME']}",
            color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")
        await interaction.response.send_message(embed=embed)
    
    @blacklist_group.command(
        name=f"{text['MODERATION_BL_REM_NAME']}",
        description=f"{text['MODERATION_BL_REM_DESC']}")
    @not_blacklisted()
    @is_admin()
    async def blacklist_remove(self, interaction:discord.Interaction, user:discord.User=None) -> None:
        if not user:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        if not await db_manager.is_blacklisted(user.id):
            embed = discord.Embed(
                description=f"**{user.name}** {text['MODERATION_BLACKLIST_NOT_ON_BLACKLIST']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        total = await db_manager.remove_user_from_blacklist(user.id)
        embed = discord.Embed(
            description=f"**{user.mention}** {text['MODERATION_BLACKLIST_CAN_USE_ME']}",
            color=GREEN)
        embed.set_footer(text=f"{text['MODERATION_BLACKLIST_TOTAL_USERS']} {total}")
        await interaction.response.send_message(embed=embed)
    
    @commands.hybrid_command(
        name=f"{text['MODERATION_CENSOR_NAME']}",
        description=f"{text['MODERATION_CENSOR_DESC']}")
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @not_blacklisted()
    @is_admin()
    async def censor(self, ctx:Context, amount:str=None) -> None:
        if not amount or not amount.isnumeric():
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await ctx.send(embed=embed)
        embed = discord.Embed(
            description=" ✅  Cleared!",
            color=GREEN)
        await ctx.channel.purge(limit=int(amount))
        await ctx.send(embed=embed)

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Moderation(bot))