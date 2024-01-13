"""
#### RinBot's responder
Automatically determines the context type (ctx or interaction) and sends
an embed, view, or both to the channel
"""

# Imports
import discord
from discord.ext.commands import Context
from rinbot.base.colors import *
from rinbot.base.helpers import load_lang, format_exception
from rinbot.base.logger import logger

# Load text
text = load_lang()

async def respond(context, color=None, title=None, message=None, view=None, response_type=0):
    """
    #### Responds to the current context or interaction with an embed or view
    - context: `discord.Interaction or Context object`
    - color: `HEX color value for embed (optional)`
    - message: `str message for embed description`
    - title: `str title for embed title (optional)`
    - view: `A view for the interaction (optional)`
    - response_type:
        * default = `0 (uses response.send_message)`
        * followup = `1 (uses followup.send)`
        * channel = `2 (uses channel.send)`
    #### NOTE: If a ready embed is sent through the message argument, 
    #### that embed will be parsed directly and the other embed arguments will be ignored.
    """
    
    async def _send_response(context, embed=None, view=None, response_type=0):
        if isinstance(context, discord.Interaction):
            if response_type == 0:
                if not view: await context.response.send_message(embed=embed)
                else: await context.response.send_message(embed=embed, view=view)
            elif response_type == 1:
                if not view: await context.followup.send(embed=embed)
                else: await context.followup.send(embed=embed, view=view)
            elif response_type == 2:
                if not view: await context.channel.send(embed=embed)
                else: await context.channel.send(embed=embed, view=view)
        elif isinstance(context, Context):
            if not view: await context.send(embed=embed)
            else: await context.send(embed=embed, view=view)
    
    try:
        if not isinstance(message, discord.Embed):
            embed = (
                discord.Embed(description=message, color=color) if message and not title
                else discord.Embed(title=title, color=color) if title and not message
                else discord.Embed(title=title, description=message, color=color) if message and title
                else None)
        else:
            embed = message

        if embed and not view:
            await _send_response(context, embed, response_type=response_type)
            logger.info(f"{text['RESPONDER_RESPONSE_SENT']} (Embed) | GUILD ID {context.guild.id} | MSG: {embed.description}")
        elif not embed and view:
            await _send_response(context, view=view, response_type=response_type)
            logger.info(f"{text['RESPONDER_RESPONSE_SENT']} (View) | GUILD ID {context.guild.id}")
        elif embed and view:
            await _send_response(context, embed, view, response_type)
            logger.info(f"{text['RESPONDER_RESPONSE_SENT']} (Embed + View) | GUILD ID {context.guild.id} | MSG: {embed.description}")

    except Exception as e: logger.error(f"{format_exception(e)}")