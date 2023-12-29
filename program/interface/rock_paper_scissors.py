import discord, random
from program.base.helpers import load_lang

text = load_lang()

class RockPaperScissors(discord.ui.Select):
    def __init__(self):
        
        options = [
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_SCISSORS'][0]}", description=f"{text['INTERFACE_FUN_SCISSORS'][1]}", emoji="✂"),
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_ROCK'][0]}", description=f"{text['INTERFACE_FUN_ROCK'][1]}", emoji="🪨"),
            discord.SelectOption(
                label=f"{text['INTERFACE_FUN_PAPER'][0]}", description=f"{text['INTERFACE_FUN_PAPER'][1]}", emoji="🧻"),]
        super().__init__(
            placeholder=f"{text['INTERFACE_FUN_TAUNT']}",
            min_values=1,
            max_values=1,
            options=options,)

    async def callback(self, interaction: discord.Interaction):
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2,}
        
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]
        
        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]
        
        result_embed = discord.Embed(color=0x9C84EF)
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.avatar.url)
        if user_choice_index == bot_choice_index:
            result_embed.description = f"**{text['INTERFACE_FUN_DRAW']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0xF59E42
        elif user_choice_index == 0 and bot_choice_index == 2:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 1 and bot_choice_index == 0:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        elif user_choice_index == 2 and bot_choice_index == 1:
            result_embed.description = f"**{text['INTERFACE_FUN_USER_WON']}**\n{text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}."
            result_embed.colour = 0x9C84EF
        else:
            result_embed.description = (
                f"**\n{text['INTERFACE_FUN_I_WON!']}** {text['INTERFACE_FUN_YOU_AND_I'][0]} {user_choice} {text['INTERFACE_FUN_YOU_AND_I'][1]} {bot_choice}.")
            result_embed.colour = 0xE02B2B
        
        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None)

class RockPaperScissorsView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RockPaperScissors())