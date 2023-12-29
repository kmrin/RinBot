# Imports
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.app_commands import Group
from program.base.helpers import isHexColor, hexToInt
from program.base.db_manager import *
from program.base.checks import *
from program.base.colors import *

# Load verbose
text = load_lang()

# 'economy' command Cog
class Economy(commands.Cog, name='economy'):
    def __init__(self, bot):
        self.bot:Bot = bot
        self.store = None
    
    # Updates the store
    async def updateStore(self):
        self.store = await db_manager.get_store()
        if not self.store: self.store = {}
    
    orange_group = Group(name=f"{text['ECONOMY_ORANGE_NAME']}", description=f"{text['ECONOMY_ORANGE_DESC']}")
    
    # Shows the top 10 members with the most oranges
    @orange_group.command(
        name=f"{text['ECONOMY_RANK_NAME']}",
        description=f"{text['ECONOMY_RANK_DESC']}")
    @not_blacklisted()
    async def orangerank(self, interaction:discord.Interaction) -> None:
        await self.updateStore()
        rank = await db_manager.get_currency_leaderboard(interaction.guild.id)
        users = []
        for _, (id,_) in enumerate(rank, start=1):
            u = await self.bot.fetch_user(id)
            users.append(u.name)
        rank_data = [f'{i}. {oranges}🍊 - `{users[i-1]}`'
                    for i, (_, oranges) in enumerate(rank, start=1)]
        message = '\n'.join(rank_data)
        embed = discord.Embed(
            title=f"{text['ECONOMY_RANK_TOP_10']}",
            description=f"{message}",
            color=0xe3a01b)
        embed.set_footer(text=f"{text['ECONOMY_BANK']}")
        await interaction.response.send_message(embed=embed)
    
    # Transfer oranges between users
    @orange_group.command(
        name=f"{text['ECONOMY_TRANSFER_NAME']}",
        description=f"{text['ECONOMY_TRANSFER_DESC']}")
    @not_blacklisted()
    async def orangemove(self, interaction:discord.Interaction, user:discord.User=None, value:str=None) -> None:
        await self.updateStore()
        
        if not user or not value or not value.isnumeric():
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        
        # Try to transfer
        transaction = await db_manager.move_currency(interaction.user.id, user.id, interaction.guild.id, int(value))
        author_oranges = await db_manager.get_user_currency(interaction.user.id, interaction.guild.id)
        if not transaction:
            embed = discord.Embed(
                title=f"{text['ECONOMY_ERROR_NOT_ENOUGH']}",
                description=f"{text['ECONOMY_CURR_BALANCE'][0]} {author_oranges}{text['ECONOMY_CURR_BALANCE'][1]}",
                color=0xd91313)
        else:
            embed = discord.Embed(
                title=f"{text['ECONOMY_TRANSFER_SUCCESS']}",
                description=f"{interaction.user.mention} {text['ECONOMY_TRANSFER_EMBED'][0]} {value}{text['ECONOMY_TRANSFER_EMBED'][1]} {user.mention}.",
                color=0x25d917)
            embed.set_footer(text=f"{text['ECONOMY_BANK']}")
        return await interaction.response.send_message(embed=embed)

    # Shows items on the store
    @orange_group.command(
        name=f"{text['ECONOMY_STORE_NAME']}",
        description=f"{text['ECONOMY_STORE_DESC']}e")
    @not_blacklisted()
    async def orangeshow(self, interaction:discord.Interaction) -> None:
        await self.updateStore()
        if str(interaction.guild.id) in self.store:
            items = []
            for item in self.store[str(interaction.guild.id)].values():
                items.append(f"**{item['name']}** - `{item['price']}`{text['ECONOMY_CURR_ICON']}")
            data = [f"{item}" for item in items]
            data = '\n'.join(data)
            embed = discord.Embed(
                title=f"{text['ECONOMY_STORE_EMBED_TITLE']}",
                description=f"{data}",
                color=0x25d917)
        else:
            embed = discord.Embed(
                description=f"{text['ECONOMY_STORE_NO_ITEMS']}",
                color=0xd91313)
        await interaction.response.send_message(embed=embed)
    
    # Creates a role to be sold on the store
    @orange_group.command(
        name=f"{text['ECONOMY_ROLE_NAME']}",
        description=f"{text['ECONOMY_ROLE_DESC']}")
    @app_commands.describe(color=f"{text['ECONOMY_ROLE_COLOR']}")
    @not_blacklisted()
    @is_admin()
    async def orangeCreateNewRole(self, interaction:discord.Interaction, name:str=None, color:str=None, price:str=None) -> None:
        await self.updateStore()
        if not name or not color or not price or not price.isnumeric():
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        if not isHexColor(color):
            embed = discord.Embed(
                description=f"{text['ECONOMY_ROLE_INVALID_COLOR']}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        color = hexToInt(color)
        try:
            await interaction.guild.create_role(name=name, color=color)
        except Exception as e:
            e = format_exception(e)
            embed = discord.Embed(
                title=f"{text['ECONOMY_ROLE_CREATION_ERROR']}",
                description=f"{e}",
                color=0xd91313)
            return await interaction.response.send_message(embed=embed)
        roles = interaction.guild.roles
        roles_f = {}
        for i in roles:
            roles_f[i.name] = i.id
        if name in roles_f:
            new_role = interaction.guild.get_role(int(roles_f[name]))
        if str(interaction.guild.id) not in self.store:
            self.store[str(interaction.guild.id)] = {}
        self.store[str(interaction.guild.id)][name] = {
            "id": new_role.id,
            "name": new_role.name,
            "type": "role",
            "price": int(price)}
        add = await db_manager.update_store(self.store)
        if add:
            embed = discord.Embed(
                title=f"{text['ECONOMY_ROLE_CREATION_FINISHED']}",
                description=f"{name} {text['ECONOMY_ROLE_CREATION_FINISHED_DESC']}",
                color=0x25d917)
        else:
            embed = discord.Embed(
                description=f"{text['ECONOMY_ROLE_FAIL_DB_ERROR']}",
                color=0xd91313)
        await self.updateStore()
        await interaction.response.send_message(embed=embed)

    # Command to buy stuff from the store
    @orange_group.command(
        name=f"{text['ECONOMY_BUY_NAME']}",
        description=f"{text['ECONOMY_BUY_DESC']}")
    @not_blacklisted()
    async def orangebuy(self, interaction:discord.Interaction, item:str=None) -> None:
        if not item:
            embed = discord.Embed(
                description=f"{text['ERROR_INVALID_PARAMETERS']}",
                color=RED)
            return await interaction.response.send_message(embed=embed)
        
        await self.updateStore()
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.guild.id) in self.store:
            for store_item in self.store[str(interaction.guild.id)].values():
                if store_item["name"].lower() == item.lower() or str(store_item["id"]) == item:
                    if store_item["type"] == "role":
                        role = discord.utils.get(interaction.guild.roles, id=int(store_item["id"]))
                        if role:
                            transaction = await db_manager.remove_currency(
                                interaction.user.id, interaction.guild.id, int(store_item["price"]))
                            author_oranges = await db_manager.get_user_currency(interaction.user.id, interaction.guild.id)
                            if not transaction:
                                embed = discord.Embed(
                                    title=f"{text['ECONOMY_ERROR_NOT_ENOUGH']}",
                                    description=f"{text['ECONOMY_CURR_BALANCE'][0]} {author_oranges}{text['ECONOMY_CURR_BALANCE'][1]}",
                                    color=0xd91313)
                                return await interaction.response.send_message(embed=embed)
                            await member.add_roles(role)
                            embed = discord.Embed(
                                title=f"{text['ECONOMY_BUY_SUCCESS']}",
                                description=f"{interaction.user.mention} {text['ECONOMY_BUY_SUCCESS_EMBED'][0]} {store_item['name']} {text['ECONOMY_BUY_SUCCESS_EMBED'][1]} {store_item['price']}{text['ECONOMY_CURR_ICON']}",
                                color=0x25d917)
                            embed.set_footer(text=f"{text['ECONOMY_BANK']}")
                            await interaction.response.send_message(embed=embed)
                        else:
                            embed = discord.Embed(
                                description=f"{text['ECONOMY_BUY_NO_ROLE']}",
                                color=0xd91313)
                            await interaction.response.send_message(embed=embed)
                    #################################################
                    # TODO: Add more store item types on the future #
                    #################################################
                    else:
                        embed = discord.Embed(
                            description=f"{text['ECONOMY_BUY_INVALID_TYPE']} `{store_item['type']}`.",
                            color=0xd91313)
                        await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(
                        description=f"{text['ECONOMY_STORE_INVALID_ITEM']}",
                        color=RED)
                    await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description=f"{text['ECONOMY_STORE_NO_ITEMS']}",
                color=0xd91313)
            await interaction.response.send_message(embed=embed)

# SETUP
async def setup(bot:Bot):
    await bot.add_cog(Economy(bot))