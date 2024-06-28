"""
RinBot's economy command cog
- Commands:
    * /orange rank              - Shows a top 10 leaderboard of the users with the most oranges
    * /orange transfer          - Transfer oranges from you to someone else
    * /orange store show        - Shows all store items the server has to offer
    * /orange store create-item - Creates an item to be sold at the store
    * /orange store buy         - Buys an item from the server's store
"""

import nextcord

from nextcord import Interaction, Locale, Embed, Colour, SlashOption, slash_command
from nextcord.ext.application_checks import bot_has_permissions
from nextcord.ext.commands import Cog

from rinbot.core import RinBot
from rinbot.core import DBTable
from rinbot.core import Loggers
from rinbot.core import StoreCreateRoleModal
from rinbot.core import StoreItem, TransferResult, StorePurchaseStatus
from rinbot.core import get_interaction_locale, get_localized_string
from rinbot.core import not_blacklisted, is_admin, is_guild
from rinbot.core import respond

logger = Loggers.EXTENSIONS

class EconomyManager:
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
    
    @staticmethod
    def parse_store_item(item_data) -> StoreItem:
        item = StoreItem(
            id = item_data[0][1],
            name = item_data[0][2],
            price = item_data[0][3],
            type = item_data[0][4]
        )
        
        return item
    
    async def add_currency(self, guild_id: int, user_id: int, amount: int) -> None:        
        condition = f'guild_id={guild_id} AND user_id={user_id}'
        
        member_data = await self.bot.db.get(DBTable.CURRENCY, condition)
        
        member_wallet = member_data[0][2]
        member_wallet += amount
        
        await self.bot.db.update(DBTable.CURRENCY, {'wallet': member_wallet}, condition)

    async def remove_currency(self, guild_id: int, user_id: int, amount: int) -> TransferResult:        
        condition = f'guild_id={guild_id} AND user_id={user_id}'
        
        member_data = await self.bot.db.get(DBTable.CURRENCY, condition)
        
        member_wallet = member_data[0][2]
        
        if member_wallet < amount:
            return TransferResult(result=False, wallet=member_wallet)
        
        member_wallet -= amount
        
        await self.bot.db.update(DBTable.CURRENCY, {'wallet': member_wallet}, condition)
        
        return TransferResult(result=True, wallet=member_wallet)
    
    async def move_currency(self, guild_id: int, from_id: int, to_id: int, amount: int) -> TransferResult:
        remove = await self.remove_currency(guild_id, from_id, amount)
        if not remove.result:
            return remove
        
        await self.add_currency(guild_id, to_id, amount)
        
        return remove
    
    @staticmethod
    async def buy_item(item: StoreItem, user: nextcord.Member) -> StorePurchaseStatus:
        # Role type
        if item.type == 0:
            role = nextcord.utils.get(
                user.guild.roles, id=item.id
            )
            if not role:
                return StorePurchaseStatus.ROLE_DOESNT_EXIST
            for user_role in user.roles:
                if user_role.id == role.id:
                    return StorePurchaseStatus.ALREADY_HAS_ITEM
            
            await user.add_roles(role)
            
            return StorePurchaseStatus.SUCCESS
            
class Economy(Cog, name='economy'):
    def __init__(self, bot: RinBot) -> None:
        self.bot = bot
        self.manager = EconomyManager(bot)

    # /orange
    @slash_command(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_ROOT_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _orange_root(self, interaction: Interaction) -> None:
        pass
    
    # /orange rank
    @_orange_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_RANK_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_RANK_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_RANK_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_RANK_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _orange_rank(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        currency = await self.bot.db.get(
            DBTable.CURRENCY,
            f'guild_id={interaction.guild.id}'
        )
        
        flattened = [(row[1], row[2]) for row in currency]
        sorted_data = sorted(flattened, key=lambda x: x[1], reverse=True)
        users = []
        
        for user in sorted_data[:10]:
            u = self.bot.get_user(user[0]) or await self.bot.fetch_user(user[0])
            users.append(u)
        
        rank_data = [
            f'{i}. {item[1]}🍊 - `{users[i-1]}`'
            for i, item in enumerate(sorted_data[:10], start=1)
        ]
        
        embed = Embed(
            title=get_localized_string(locale, 'ECONOMY_ORANGE_RANK_TITLE'),
            description='\n'.join(rank_data),
            colour=Colour.gold()
        )
        embed.set_footer(text=' 🍊  The Orange Bank')
        
        await respond(interaction, message=embed)
    
    # /orange transfer
    @_orange_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_TRANSFER_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_TRANSFER_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_TRANSFER_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_TRANSFER_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _orange_transfer(
        self, interaction: Interaction,
        to: nextcord.Member = SlashOption(
            name=get_localized_string('en-GB', 'ECONOMY_ORANGE_MEMBER_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_MEMBER_NAME')
            },
            description=get_localized_string('en-GB', 'ECONOMY_ORANGE_MEMBER_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_MEMBER_DESC')
            },
            required=True
        ),
        amount: int = SlashOption(
            name=get_localized_string('en-GB', 'ECONOMY_ORANGE_AMOUNT_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_AMOUNT_NAME')
            },
            description=get_localized_string('en-GB', 'ECONOMY_ORANGE_AMOUNT_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_AMOUNT_DESC')
            },
            required=True,
            min_value=1
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        if to == interaction.user:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_TRANSFER_SAME_USER'
                )
            )
        
        move = await self.manager.move_currency(
            interaction.guild.id, interaction.user.id, to.id, amount
        )
        
        if not move.result:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_NOT_ENOUGH',
                    wallet = move.wallet
                ),
                hidden = True
            )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'ECONOMY_TRANSFER_SUCCESS',
                amount = amount,
                to_user = to.display_name,
                wallet = move.wallet
            ),
            hidden = True
        )
    
    # /orange store
    @_orange_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_ROOT_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_ROOT_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_ROOT_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_ROOT_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _orange_store_root(self, interaction: Interaction) -> None:
        pass
    
    # /orange store show
    @_orange_store_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_SHOW_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_SHOW_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_SHOW_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_SHOW_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    async def _orange_store_show(self, interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        store = await self.bot.db.get(
            DBTable.STORE, f'guild_id={interaction.guild.id}'
        )
        
        if not store:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_STORE_NO_ITEMS'
                )
            )
        
        items = []
        for row in store:
            items.append(f'**{row[3]}**🍊 - `{row[2]}`')
        
        data = [f'{item}' for item in items]
        data = '\n'.join(data)
        
        await respond(
            interaction, Colour.yellow(),
            data, get_localized_string(
                locale, 'ECONOMY_STORE_TITLE',
                name = interaction.guild.name
            )
        )
    
    # /orange store create-item
    @_orange_store_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_DESC')
        }
    )
    @is_admin()
    @is_guild()
    @not_blacklisted()
    @bot_has_permissions(manage_roles=True)
    async def _orange_store_create(
        self, interaction: Interaction,
        item_type: int = SlashOption(
            name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_TYPE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_TYPE_NAME')
            },
            description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_TYPE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_TYPE_DESC')
            },
            choices={
                'Role': 0
            },
            choice_localizations={
                'Role': {
                    Locale.pt_BR: 'Cargo'
                }
            },
            required=True
        ),
        item_price: int = SlashOption(
            name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_PRICE_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_PRICE_NAME')
            },
            description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_CREATE_PRICE_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_CREATE_PRICE_DESC')
            },
            min_value=1,
            required=True
        )
    ) -> None:        
        # Role type
        if item_type == 0:
            await interaction.response.send_modal(StoreCreateRoleModal(self.bot, interaction, item_price))
        
    # /orange store buy
    @_orange_store_root.subcommand(
        name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_BUY_NAME'),
        name_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_BUY_NAME')
        },
        description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_BUY_DESC'),
        description_localizations={
            Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_BUY_DESC')
        }
    )
    @is_guild()
    @not_blacklisted()
    @bot_has_permissions(manage_roles=True)
    async def _orange_store_buy(
        self, interaction: Interaction,
        item_name: str = SlashOption(
            name=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_BUY_ITEM_NAME'),
            name_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_BUY_ITEM_NAME')
            },
            description=get_localized_string('en-GB', 'ECONOMY_ORANGE_STORE_BUY_ITEM_DESC'),
            description_localizations={
                Locale.pt_BR: get_localized_string('pt-BR', 'ECONOMY_ORANGE_STORE_BUY_ITEM_DESC')
            },
            min_length=1,
            max_length=32,
            required=True
        )
    ) -> None:
        locale = get_interaction_locale(interaction)
        
        # Get item data
        store = await self.bot.db.get(DBTable.STORE, f'guild_id={interaction.guild.id}')
        items = [
            StoreItem(
                id = row[1],
                name = row[2],
                price = row[3],
                type = row[4]
            )
            for row in store
        ]
        
        item_to_process: StoreItem = None
        
        for item in items:
            if item.name == item_name:
                item_to_process = item

        # If item doesn't exist
        if not item_to_process:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_BUY_NOT_FOUND',
                    name = item_name
                )
            )
                
        # Take the money
        transaction = await self.manager.remove_currency(
            interaction.guild.id, interaction.user.id, item_to_process.price
        )
        
        # If the user doesn't have enough
        if not transaction.result:
            return await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_NOT_ENOUGH',
                    wallet = transaction.wallet
                ),
                hidden = True
            )
        
        # Try to give the item to the user
        buy = await self.manager.buy_item(item_to_process, interaction.user)
        
        # If the user already has the item
        if buy == StorePurchaseStatus.ALREADY_HAS_ITEM:
            await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_BUY_ERROR_HAS_ITEM'
                ),
                hidden = True
            )
            
            # Return money
            return await self.manager.add_currency(
                interaction.guild.id, interaction.user.id, item_to_process.price
            )
        
        # If the user is trying to buy a role but the server owner removed it
        elif buy == StorePurchaseStatus.ROLE_DOESNT_EXIST:
            await respond(
                interaction, Colour.red(),
                get_localized_string(
                    locale, 'ECONOMY_BUY_ERROR_ROLE_NOT_EXISTS',
                    name = item_name
                ),
                hidden = True
            )
            
            # Return money
            return await self.manager.add_currency(
                interaction.guild.id, interaction.user.id, item_to_process.price
            )
        
        await respond(
            interaction, Colour.green(),
            get_localized_string(
                locale, 'ECONOMY_BUY_SUCCESS',
                item = item_to_process.name,
                price = item_to_process.price
            )
        )
        
# SETUP
def setup(bot: RinBot) -> None:
    bot.add_cog(Economy(bot))
