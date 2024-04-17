"""
Responder
"""

import discord

from discord import Interaction
from discord.ext.commands import Context
from typing import Literal, Union

from .exception_handler import log_exception
from .json_loader import get_lang
from .logger import logger

text = get_lang()

async def respond(
    context: Union[Context, Interaction],
    colour: int=None,
    message: Union[str, discord.Embed]=None,
    title: str=None,
    view: discord.ui.View=None,
    hidden: bool=False,
    response_type: Literal[0, 1, 2]=0
) -> None:
    """
    Respond to the current context or interaction with an embed or view

    Args:
        context (Union[Context, Interaction]): discord.Interaction or discord.ext.commands.Context obj
        colour (int, optional): HEX colour value for embed. Defaults to None.
        message (Union[str, discord.Embed], optional): Message for embed description. Defaults to None.
        title (str, optional): Title for embed title. Defaults to None.
        view (discord.ui.View, optional): A view for the interaction. Defaults to None.
        hidden (bool, optional): False = normal message (default), True = ephemeral message. Defaults to False.
        response_type (Literal[0, 1, 2], optional): 0 = send_message, 1 = followup.send, 2 = channel.send. Defaults to 0.
    """
    
    async def __send(ctx, embed=None, interface=None):
        try:
            if isinstance(ctx, Interaction):
                if response_type == 0:
                    if not interface:
                        await ctx.response.send_message(embed=embed, ephemeral=hidden)
                    else:
                        await ctx.response.send_message(embed=embed, view=interface, ephemeral=hidden)
                elif response_type == 1:
                    if not interface:
                        await ctx.followup.send(embed=embed, ephemeral=hidden)
                    else:
                        await ctx.followup.send(embed=embed, view=interface, ephemeral=hidden)
                elif response_type == 2:
                    if not interface:
                        await ctx.channel.send(embed=embed)
                    else:
                        await ctx.channel.send(embed=embed, view=interface)
            elif isinstance(ctx, Context):
                if not interface:
                    await ctx.send(embed=embed, ephemeral=hidden)
                else:
                    await ctx.send(embed=embed, view=interface, ephemeral=hidden)
        except Exception as e:
            log_exception(e)
    
    try:
        if not isinstance(message, discord.Embed):
            embed = (
                discord.Embed(description=message, colour=colour) if message and not title
                else discord.Embed(title=title, colour=colour) if title and not message
                else discord.Embed(title=title, description=message, colour=colour) if message and title
                else None)
        else:
            embed = message

        if isinstance(context, Context):
            author = context.author
        elif isinstance(context, Interaction):
            author = context.user
        
        if embed and not view:
            await __send(context, embed=embed)
            logger.info(
                text['RESPONDER_SENT'].format(
                    type="(Embed)",
                    guild_id=context.guild.id if context.guild else author.id,
                    msg=embed.description if embed.description else embed.title
                ))
        elif not embed and view:
            await __send(context, interface=view)
            logger.info(
                text['RESPONDER_SENT'].format(
                    type="(View)",
                    guild_id=context.guild.id if context.guild else author.id,
                    msg=None
                ))
        elif embed and view:
            await __send(context, embed=embed, interface=view)
            logger.info(
                text['RESPONDER_SENT'].format(
                    type="(Embed + View)",
                    guild_id=context.guild.id if context.guild else author.id,
                    msg=embed.description if embed.description else embed.title
                ))
    except Exception as e:
        log_exception(e)
