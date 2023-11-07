"""
RinBot v1.8.0 (GitHub Release)
made by rin
"""

# Imports
import discord, os, sys, json
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Bot
from discord.app_commands.models import Choice
from program.helpers import isHexColor, hexToInt
from program.db_manager import *
from program.checks import *

# 'economy' command Cog
class Economy(commands.Cog, name='economy'):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.updateStore()
    
    # Updates the store
    def updateStore(self):
        if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/../store.json"):
            sys.exit("[economy.py]-[ERROR]: 'store.json' not found.")
        else:
            with open('store.json', 'r', encoding='utf-8') as f:
                self.store = json.load(f)
    
    # Shows the top 10 members with the most oranges
    @commands.hybrid_command(
        name='orange_rank',
        description='Shows the top 10 members with the most oranges')
    @not_blacklisted()
    async def orangerank(self, ctx:Context) -> None:
        rank = await db_manager.get_leaderboard(ctx.guild.id)
        users = []
        for _, (id,_) in enumerate(rank, start=1):
            u = await self.bot.fetch_user(id)
            users.append(u.name)
        rank_data = [f'{i}. {oranges}🍊 - `{users[i-1]}`'
                    for i, (_, oranges) in enumerate(rank, start=1)]
        message = '\n'.join(rank_data)
        embed = discord.Embed(
            title=" 🍊 **TOP 10 Oranges**",
            description=f"{message}",
            color=0xe3a01b)
        embed.set_footer(text=" 🍊  The Orange Bank")
        await ctx.send(embed=embed)
    
    # Transfer oranges between users
    @commands.hybrid_command(
        name='orange_transfer',
        description='Transfer oranges between users')
    @app_commands.describe(user='Who will receive')
    @app_commands.describe(value='The value')
    @not_blacklisted()
    async def orangemove(self, ctx:Context, user:discord.User=None, value:str=None) -> None:
        
        # If no user if given or the value is invalid
        if not user or not value or not value.isnumeric():
            embed = discord.Embed(
                description=" ❌  Invalid attributes.",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        
        # Try to transfer
        transaction = await db_manager.move_currency(
            ctx.author.id, user.id, ctx.guild.id, int(value))
        author_oranges = await db_manager.get_user_currency(ctx.author.id, ctx.guild.id)
        if not transaction:
            embed = discord.Embed(
                title=" ❌  You don't have enough 🍊.",
                description=f"**Current balance:** {author_oranges}🍊",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        else:
            embed = discord.Embed(
                title=" ✅ Transfer complete",
                description=f"{ctx.author.mention} transfered {value}🍊 to {user.mention}.",
                color=0x25d917)
            embed.set_footer(text=" 🍊  The Orange Bank")
            await ctx.send(embed=embed)

    # Shows items on the store
    @commands.hybrid_command(
        name='orange_store',
        description='Shows items on the store')
    @not_blacklisted()
    async def oranjeshow(self, ctx:Context) -> None:
        self.updateStore()
        if str(ctx.guild.id) in self.store:
            items = []
            for item in self.store[str(ctx.guild.id)].values():
                items.append(f"**{item['name']}** - `{item['price']}🍊`")
            data = [f"{item}" for item in items]
            data = '\n'.join(data)
            embed = discord.Embed(
                title=" :department_store:  Orange shop",
                description=f"{data}",
                color=0x25d917)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=f" ❌  This server does't have any store items :(",
                color=0xd91313)
            await ctx.send(embed=embed)

    # Creates a role to be sold on the store
    @commands.hybrid_command(
        name='orange_new_role',
        description='Adds a role item to be sold on the store')
    @app_commands.describe(name='O name do cargo')
    @app_commands.describe(color='The color in a HEX value (Ex: #FFFFFF)')
    @app_commands.describe(price='The value in 🍊')
    @not_blacklisted()
    @is_admin()
    async def orangeCreateNewRole(self, ctx:Context, name:str=None, color:str=None, price:str=None) -> None:
        self.updateStore()
        if not name or not color or not price:
            embed = discord.Embed(
                description=f" ❌  Invalid attributes",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        if not isHexColor(color):
            embed = discord.Embed(
                description=f" ❌  Invalid color, please use a HEX color format like #FFFFFF",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        color = hexToInt(color)
        try:
            await ctx.guild.create_role(name=name, color=color)
        except Exception as e:
            embed = discord.Embed(
                title='Error creating role:',
                description=f" ❌  {e}",
                color=0xd91313)
            await ctx.send(embed=embed)
            return
        roles = ctx.guild.roles
        roles_f = {}
        for i in roles:
            roles_f[i.name] = i.id
        if name in roles_f:
            new_role = ctx.guild.get_role(int(roles_f[name]))
        if str(ctx.guild.id) not in self.store:
            self.store[str(ctx.guild.id)] = {}
        self.store[str(ctx.guild.id)][name] = {
            "id": new_role.id,
            "name": new_role.name,
            "type": "role",
            "price": int(price)}
        with open('store.json', 'w', encoding='utf-8') as f:
            json.dump(self.store, f, indent=4)
        embed = discord.Embed(
            title=" ✅ Finished",
            description=f"Role {name} created and added to the store!",
            color=0x25d917)
        self.bot.logger.info(f"Store updated")
        self.updateStore()
        await ctx.send(embed=embed)

    # Command to buy stuff from the store
    @commands.hybrid_command(
        name='orange_buy',
        description='Buys something with 🍊')
    @app_commands.describe(item='The item to be bought')
    @not_blacklisted()
    async def orangebuy(self, ctx:Context, item:str=None) -> None:
        self.updateStore()
        member = ctx.guild.get_member(ctx.author.id)
        if str(ctx.guild.id) in self.store:
            for store_item in self.store[str(ctx.guild.id)].values():
                if store_item["name"].lower() == item.lower() or str(store_item["id"]) == item:
                    if store_item["type"] == "role":
                        role = discord.utils.get(ctx.guild.roles, id=int(store_item["id"]))
                        if role:
                            transaction = await db_manager.remove_currency(
                                ctx.author.id, ctx.guild.id, int(store_item["price"]))
                            author_oranges = await db_manager.get_user_currency(ctx.author.id, ctx.guild.id)
                            if not transaction:
                                embed = discord.Embed(
                                    title=" ❌  You don't have enough 🍊.",
                                    description=f"**Current balance:** {author_oranges}🍊",
                                    color=0xd91313)
                                await ctx.send(embed=embed)
                                return
                            else:
                                await member.add_roles(role)
                                embed = discord.Embed(
                                    title=" ✅ Purchase successfull",
                                    description=f"{ctx.author.mention} bought {store_item['name']} for {store_item['price']}🍊",
                                    color=0x25d917)
                                embed.set_footer(text=" 🍊  The Orange Bank")
                                await ctx.send(embed=embed)
                                return
                        else:
                            embed = discord.Embed(
                                description=f" ❌ An error ocurred :(",
                                color=0xd91313)
                            await ctx.send(embed=embed)
                            return
                    else:
                        embed = discord.Embed(
                            description=f" ❌ Store error, invalid item type `{store_item['type']}`.",
                            color=0xd91313)
                        await ctx.send(embed=embed)
                        return

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Economy(bot))