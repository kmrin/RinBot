"""
#### RinBot's economy command cog
- commands:
    * /orange rank `Shows the Top 10 server leaderboard for the users with most oranges`
    * /orange transfer `Transfer oranges from you and someone else`
    * /orange store `Shows what items that guild has to offer at the store`
    * /orange create_role `Creates a role to be sold on the server's store`
    * /orange buy `Buys an item from the guild's store`
"""

# Imports
import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog
from discord.app_commands import Group
from rinbot.base.responder import respond
from rinbot.base.helpers import is_hex_color, hex_to_int, format_exception
from rinbot.base.checks import *
from rinbot.base.colors import *
from rinbot.base.db_man import *

# Load verbose
text = load_lang()

# "economy" commands cog
class Economy(Cog, name="economy"):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.store = None
    
    # Updates the store
    async def update_store(self):
        self.store = await get_table("store")
        if not self.store: self.store = {}
    
    # Commands groups
    orange = Group(name=f"{text['ECONOMY_ORANGE_NAME']}", description=f"{text['ECONOMY_ORANGE_DESC']}")

    # Shows the top 10 users with the most oranges
    @orange.command(
        name=text['ECONOMY_RANK_NAME'],
        description=text['ECONOMY_RANK_DESC'])
    @not_blacklisted()
    async def _orange_rank(self, interaction:Interaction) -> None:
        await self.update_store()
        economy = await get_table("currency")
        flattened = [(member_id, data["wallet"]) for member_id, data in economy[str(interaction.guild.id)].items()]
        sorted_data = sorted(flattened, key=lambda x: x[1], reverse=True)
        users = []
        for user in sorted_data[:10]:
            u = await self.bot.fetch_user(user[0])
            users.append(u.name)
        rank_data = [f"{i}. {item[1]}🍊 - `{users[i-1]}`"
                     for i, item in enumerate(sorted_data[:10], start=1)]
        message = "\n".join(rank_data)
        embed = discord.Embed(
            title=text['ECONOMY_RANK_TOP_10'],
            description=f"{message}", color=YELLOW)
        embed.set_footer(text=text['ECONOMY_BANK'])
        await respond(interaction, message=embed)
    
    # Transfer oranges between users
    @orange.command(
        name=text['ECONOMY_TRANSFER_NAME'],
        description=text['ECONOMY_TRANSFER_DESC'])
    @not_blacklisted()
    async def _orange_move(self, interaction:Interaction, member:discord.Member=None, value:str=None) -> None:
        if not member or not value or not value.isnumeric():
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        embed = await self.move_currency(interaction, interaction.user, member, value)
        await interaction.response.send_message(embed=embed)
    
    # Shows items on the store
    @orange.command(
        name=text['ECONOMY_STORE_NAME'],
        description=text['ECONOMY_STORE_DESC'])
    @not_blacklisted()
    async def _orange_store(self, interaction:Interaction) -> None:
        await self.update_store()
        if str(interaction.guild.id) in self.store:
            items = []
            for item in self.store[str(interaction.guild.id)].values():
                items.append(f"**{item['name']}** - `{item['price']}`{text['ECONOMY_CURR_ICON']}")
            data = [f"{item}" for item in items]
            data = "\n".join(data)
            embed = discord.Embed(
                title=text['ECONOMY_STORE_EMBED_TITLE'],
                description=f"{data}", color=YELLOW)
        else:
            embed = discord.Embed(
                description=text['ECONOMY_STORE_NO_ITEMS'],
                color=RED)
        await respond(interaction, message=embed)
    
    # Creates a role
    @orange.command(
        name=text['ECONOMY_ROLE_NAME'],
        description=text['ECONOMY_ROLE_DESC'])
    @app_commands.describe(colour=text['ECONOMY_ROLE_COLOR'])
    @not_blacklisted()
    @is_admin()
    async def _orange_create_new_role(self, interaction:Interaction, name:str=None, colour:str=None, price:str=None) -> None:
        await self.update_store()
        if not name or not colour or not price or not price.isnumeric():
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        if not is_hex_color(colour):
            return await respond(interaction, RED, message=text['ECONOMY_ROLE_INVALID_COLOR'])
        colour = hex_to_int(colour)
        try:
            await interaction.guild.create_role(name=name, colour=colour)
        except Exception as e:
            return await respond(interaction, RED, text['ECONOMY_ROLE_CREATION_ERROR'], f"{format_exception(e)}")
        roles = interaction.guild.roles
        roles_f = {}
        for i in roles:
            roles_f[i.name] = i.id
        if name in roles_f:
            new_role = interaction.guild.get_role(int(roles_f[name]))
        if interaction.guild.id not in self.store:
            self.store[str(interaction.guild.id)] = {}
        self.store[str(interaction.guild.id)][name] = {
            "id": new_role.id, "name": new_role.name,
            "type": "role", "price": int(price)}
        await update_table("store", self.store)
        await respond(interaction, GREEN, text['ECONOMY_ROLE_CREATION_FINISHED'], f"{name} {text['ECONOMY_ROLE_CREATION_FINISHED_DESC']}")
    
    # Command to buy stuff from the store
    @orange.command(
        name=text['ECONOMY_BUY_NAME'],
        description=text['ECONOMY_BUY_DESC'])
    @not_blacklisted()
    async def _orange_buy(self, interaction:Interaction, item:str=None) -> None:
        await self.update_store()
        if not item:
            return await respond(interaction, RED, message=text['ERROR_INVALID_PARAMETERS'])
        if str(interaction.guild.id) not in self.store.keys():
            return await respond(interaction, RED, message=text['ECONOMY_STORE_NO_ITEMS'])
        member = interaction.guild.get_member(str(interaction.user.id)) or await interaction.guild.fetch_member(interaction.user.id)
        for store_item in self.store[str(interaction.guild.id)].values():
            if store_item["name"].lower() == item.lower() or str(store_item["id"]) == item:
                if store_item["type"] == "role":
                    await self.buy_role(interaction, member, store_item)
                else:
                    await respond(interaction, RED, message=f"{text['ECONOMY_BUY_INVALID_TYPE']} `{store_item['type']}`")
            else:
                await respond(interaction, RED, message=f"{text['ECONOMY_BUY_INVALID_ITEM']}")

    # Functions to buy specific item types from the store
    async def buy_role(self, interaction:Interaction, member:discord.Member, item):
        role = discord.utils.get(interaction.guild.roles, id=int(item["id"]))
        if not role:
            return await respond(interaction, RED, message=text['ECONOMY_BUY_NO_ROLE'])
        transaction = await self.remove_currency(interaction, member, int(item["price"]))
        if not transaction[0]:
            embed = discord.Embed(
                title=text['ECONOMY_ERROR_NOT_ENOUGH'],
                description=f"{text['ECONOMY_CURR_BALANCE'][0]} {transaction[1]['wallet']}{text['ECONOMY_CURR_BALANCE'][1]}",
                color=RED)
            return await respond(interaction, message=embed)
        await member.add_roles(role)
        embed = discord.Embed(
            title=text['ECONOMY_BUY_SUCCESS'],
            description=f"{interaction.user.mention} {text['ECONOMY_BUY_SUCCESS_EMBED'][0]} {item['name']} {text['ECONOMY_BUY_SUCCESS_EMBED'][1]} {item['price']}{text['ECONOMY_CURR_ICON']}",
            color=GREEN)
        embed.set_footer(text=f"{text['ECONOMY_BANK']}")
        await respond(interaction, message=embed)
    
    # Removes currency from a user
    async def remove_currency(self, interaction:Interaction, member:discord.Member, value) -> list:
        await self.update_store()
        economy = await get_table("currency")
        customer = economy[str(interaction.guild.id)][str(member.id)]
        if customer["wallet"] < int(value):
            return [False, customer]
        economy[str(interaction.guild.id)][str(member.id)]["wallet"] -= value
        await update_table("currency", economy)
        return [True, customer]
    
    # Exchanges currency between users
    async def move_currency(self, interaction:Interaction, sender:discord.Member, receiver:discord.Member, value) -> discord.Embed:
        await self.update_store()
        economy = await get_table("currency")
        sender_data = economy[str(interaction.guild.id)][str(sender.id)]
        if sender_data["wallet"] < int(value):
            embed = discord.Embed(
                title=text['ECONOMY_ERROR_NOT_ENOUGH'],
                description=f"{text['ECONOMY_CURR_BALANCE'][0]} {sender_data['wallet']}{text['ECONOMY_CURR_BALANCE'][1]}",
                color=RED)
        else:
            economy[str(interaction.guild.id)][str(sender.id)]["wallet"] -= int(value)
            economy[str(interaction.guild.id)][str(receiver.id)]["wallet"] += int(value)
            embed = discord.Embed(
                title=text['ECONOMY_TRANSFER_SUCCESS'],
                description=f"{sender.mention} {text['ECONOMY_TRANSFER_EMBED'][0]} {value}{text['ECONOMY_TRANSFER_EMBED'][1]} {receiver.mention}.",
                color=GREEN)
        embed.set_footer(text=text['ECONOMY_BANK'])
        await update_table("currency", economy)
        return embed

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Economy(bot))