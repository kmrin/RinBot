"""
RinBot v1.9.0 (GitHub release)
made by rin
"""

# Imports
import discord, os
from discord import app_commands
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Bot, Context
from program.checks import *
from program import db_manager
from dotenv import load_dotenv

# Carregar configurações
load_dotenv()
WARNING_BAN_LIMIT = os.getenv('MOD_WARNING_BAN_LIMIT')

# 'moderation' command cog
class Moderation(commands.Cog, name='moderation'):
    def __init__(self, bot):
        self.bot:Bot = bot
    
    # Manupulates the admins class
    @commands.hybrid_command(
        name="admins",
        description="Manipulates the admins class")
    @app_commands.describe(action="The action to be taken")
    @app_commands.describe(user="The user to be manipulated")
    @app_commands.choices(
        action=[
            Choice(name='add', value=0),
            Choice(name='remove', value=1)])
    @not_blacklisted()
    @is_owner()
    async def admins(self, ctx: Context, action: Choice[int], user: discord.User = None) -> None:
        # Adds a user to the admin class
        if action.value == 0 and user is not None:
            user_id = user.id
            if await db_manager.is_admin(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is already an admin.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.add_user_to_admins(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** was added to the admin class.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Removes a user from the admins class
        elif action.value == 1 and user is not None:
            user_id = user.id
            if not await db_manager.is_admin(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is not an admin.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            await db_manager.remove_user_from_admins(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** lost the admin hat.",
                color=0x9C84EF)
            await ctx.send(embed=embed)
        
        # Invalid action / user
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid action / user",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Manipulates the blacklist
    @commands.hybrid_command(
        name="blacklist",
        description="Manipulates the blacklist")
    @app_commands.describe(action="The action to be taken")
    @app_commands.describe(user="The user to be manipulates")
    @app_commands.choices(
        action=[
            Choice(name='show', value=0),
            Choice(name='add', value=1),
            Choice(name='remove', value=2)])
    @not_blacklisted()
    @is_admin()
    async def blacklist(self, ctx: Context, action: Choice[int], user: discord.User = None) -> None:
        # Shows users on the blacklist
        if action.value == 0:
            blacklisted_users = await db_manager.get_blacklisted_users()
            if len(blacklisted_users) == 0:
                embed = discord.Embed(
                    description="YaY! There are no users on the blacklist", color=0x9C84EF)
                await ctx.send(embed=embed)
                return
            embed = discord.Embed(title="Blocked users:", color=0x9C84EF)
            users = []
            for bluser in blacklisted_users:
                user = self.bot.get_user(int(bluser[0])) or await self.bot.fetch_user(
                    int(bluser[0]))
                users.append(f" • {user.mention} ({user}) - Blacklisted <t:{bluser[1]}>")
            embed.description = "\n".join(users)
            await ctx.send(embed=embed)
        
        # Adds a user to the blacklist
        elif action.value == 1 and user is not None:
            user_id = user.id
            if await db_manager.is_blacklisted(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is already blacklisted.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            total = await db_manager.add_user_to_blacklist(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** oOoOOOOooOoo you can't use me now",
                color=0x9C84EF)
            embed.set_footer(
                text=f"Total users on the blacklist: {total} {'user' if total == 1 else 'users'}.")
            await ctx.send(embed=embed)
        
        # Remove a user from the blacklist
        elif action.value == 2 and user is not None:
            user_id = user.id
            if not await db_manager.is_blacklisted(user_id):
                embed = discord.Embed(
                    description=f"**{user.name}** is not on the blacklist.",
                    color=0xE02B2B,)
                await ctx.send(embed=embed)
                return
            total = await db_manager.remove_user_from_blacklist(user_id)
            embed = discord.Embed(
                description=f"**{user.name}** can use me now!",
                color=0x9C84EF)
            embed.set_footer(
                text=f"Total users on the blacklist: {total} {'user' if total == 1 else 'users'}.")
            await ctx.send(embed=embed)
        
        # Invalid action / user
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid action / user",
                color=0xE02B2B)
            await ctx.send(embed=embed)
    
    # Manipulates / shows warning data inside the database
    @commands.hybrid_command(
        name='warnings',
        description='Manipulates / shows warning data inside the database')
    @app_commands.describe(action='The action to be taken')
    @app_commands.describe(user='The user to be manipulated')
    @app_commands.describe(warn='The warn')
    @app_commands.choices(
        action=[
            Choice(name='show', value=0),
            Choice(name='add', value=1),
            Choice(name='remove', value=2)])
    @not_blacklisted()
    @is_admin()
    async def warning(self, ctx: Context, action: Choice[int], user: discord.User = None, warn: str = None, warn_id: int = None) -> None:
        # Shows a user's warnings
        if action.value == 0 and user is not None:
            warnings_list = await db_manager.get_warnings(user.id, ctx.guild.id)
            embed = discord.Embed(title=f"{user} warnings:", color=0x9C84EF)
            description = " ❌ Database read error :c"
            if len(warnings_list) == 0:
                description = "YaY! This user doesn't have any warnings!"
            else:
                for warning in warnings_list:
                    description += f" • Warned by <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - warning ID #{warning[5]}\n"
            embed.description = description
            await ctx.send(embed=embed)
        
        # Gives a warning to a user
        elif action.value == 1 and user != None and warn != None and warn != 0:
            member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(
                user.id)
            total = await db_manager.add_warn(
                user.id, ctx.guild.id, ctx.author.id, warn)
            embed = discord.Embed(
                description=f"**{member}** was warned by **{ctx.author}**!\nUser total warnings: {total}",
                color=0x9C84EF,)
            embed.add_field(name="Aviso:", value=warn)
            await ctx.send(embed=embed)
            try:
                await member.send(
                    f"You were warned by **{ctx.author}** in **{ctx.guild.name}**!\nReason: {warn}")
            except:
                await ctx.send(
                    f"{member.mention}, You were warned by **{ctx.author}**!\nReason: {warn}")
            warnings_list = await db_manager.get_warnings(user.id, ctx.guild.id)
            if WARNING_BAN_LIMIT.isnumeric():
                if len(warnings_list) >= int(WARNING_BAN_LIMIT):
                    await member.kick(reason=f'Limite de avisos atingido: {WARNING_BAN_LIMIT}.')
                    embed = discord.Embed(
                        description=f"{user.name} kickado(a) do servidor por excesso de avisos.",
                        color=0x25D917)
                    await ctx.send(embed=embed)
        
        # Removes a warning from a user
        elif action.value == 2 and user is not None and warn_id is not None:
            member = ctx.guild.get_member(user.id) or await ctx.guild.fetch_member(
                user.id)
            total = await db_manager.remove_warn(warn_id, user.id, ctx.guild.id)
            embed = discord.Embed(
                description=f"I removed the warning ID **#{warn_id}** from **{member}**!\nUser total warnings: {total}",
                color=0x9C84EF,)
            await ctx.send(embed=embed)
        
        # Invalid action / user
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid action / user",
                color=0xE02B2B,)
            await ctx.send(embed=embed)
    
    # Deletes a number of messages from a text channel
    @commands.hybrid_command(
        name='censor',
        description='Deletes a number of messages from this text channel')
    
    # Check if the bot has necessary permissions
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to be deleted.")
    @not_blacklisted()
    @is_admin()
    async def sensor(self, ctx: Context, amount: int) -> None:
        embed = discord.Embed(
            description=f"WE'RE BEING CENSORED! {ctx.author} decided to clear {amount} messages!",
            color=0x9C84EF)
        await ctx.send(embed=embed)
        await ctx.channel.purge(limit=amount + 1)
        embed = discord.Embed(
            description=f"**{ctx.author}** cleared **{amount}** messages!",
            color=0x9C84EF)
        await ctx.channel.send(embed=embed)
        embed = discord.Embed(
            description=f"You cleared **{amount}** messages from **{ctx.channel.name}** in **{ctx.guild.name}**!",
            color=0x9C84EF)
        await ctx.author.send(embed=embed)

    # Changes a member's nickname
    @commands.hybrid_command(
        name='nickname',
        description="Changes someone's nickname on the server")
    @app_commands.describe(user='The user')
    @app_commands.describe(nick='The new nickname')
    @not_blacklisted()
    @is_admin()
    async def nickname(self, ctx:Context, user:discord.Member=None, nick:str=None) -> None:
        if not nick or not user:
            embed = discord.Embed(
                description = " ❌ Check your arguments.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            try:
                await user.edit(nick=nick)
                embed = discord.Embed(
                    description=f" ✅  {user.mention}'s new nickname: {nick}",
                    color=0x25D917)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    description = " ❌ No permissions.",
                    color=0xd91313)
                await ctx.send(embed=embed)
            except discord.HTTPException:
                embed = discord.Embed(
                    description = " ❌ HTTP API Error :(",
                    color=0xd91313)
                await ctx.send(embed=embed)

    # Kicks someone from the server
    @commands.hybrid_command(
        name='kick',
        description='Kicks someone from the server')
    @app_commands.describe(user='The user')
    @app_commands.describe(reason='Should I explain?')
    @not_blacklisted()
    @is_admin()
    async def kick(self, ctx:Context, user:discord.Member=None, reason:str=None) -> None:
        if not user:
            embed = discord.Embed(
                description = " ❌ Check your arguments.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            try:
                await user.kick(reason='Not specified' if not reason else reason)
                embed = discord.Embed(
                    description=f"{user.name} was kicked."
                                if not reason else
                                f"{user.name} was kicked, reason: {reason}",
                    color=0x25D917)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    description = " ❌ No permissions.",
                    color=0xd91313)
                await ctx.send(embed=embed)
            except discord.HTTPException:
                embed = discord.Embed(
                    description = " ❌ HTTP API Error :(",
                    color=0xd91313)
                await ctx.send(embed=embed)

    # Bans someone from the server
    @commands.hybrid_command(
        name='ban',
        description='Bans someone from the server')
    @app_commands.describe(user='The user to be banned')
    @app_commands.describe(reason='Should I explain?')
    @not_blacklisted()
    @is_admin()
    async def ban(self, ctx:Context, user:discord.Member=None, reason:str=None) -> None:
        if not user:
            embed = discord.Embed(
                description = " ❌ Check your arguments.",
                color=0xd91313)
            await ctx.send(embed=embed)
        else:
            try:
                await user.ban(reason='Not specified.' if not reason else reason)
                embed = discord.Embed(
                    description=f"{user.name} was banned."
                                if not reason else
                                f"{user.name} was banned, reason: {reason}",
                    color=0x25D917)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    description = " ❌ No permissions.",
                    color=0xd91313)
                await ctx.send(embed=embed)
            except discord.HTTPException:
                embed = discord.Embed(
                    description = " ❌ HTTP API Error :(",
                    color=0xd91313)
                await ctx.send(embed=embed)

# SETUP
async def setup(bot):
    await bot.add_cog(Moderation(bot))