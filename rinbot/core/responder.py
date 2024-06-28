from nextcord import Interaction, Embed, HTTPException, NotFound, InteractionResponded
from nextcord.ext.commands import Context
from nextcord.utils import MISSING
from nextcord.colour import Colour
from nextcord.ui.view import View
from typing import Union

from .loggers import Loggers, log_exception
from .types import ResponseType

logger = Loggers.RESPONDER

async def respond(
    ctx: Union[Context, Interaction],
    colour: int = Colour.gold(),
    message: Union[str, Embed] = None,
    title: str = None,
    view: View = None,
    outside_content: str = None,
    hidden: bool = False,
    resp_type: ResponseType = ResponseType.SEND_MESSAGE
) -> None:
    async def _send(
        ctx: Union[Context, Interaction],
        embed: Embed = MISSING,
        interface: View = MISSING,
        resp_type: int = 0,
        attempted_followup: bool = False,
        attempted_channel: bool = False
    ) -> None:        
        # If it's a modern interaction
        if isinstance(ctx, Interaction):
            try:
                if resp_type == 0:
                    return await ctx.response.send_message(content=outside_content, embed=embed, view=interface, ephemeral=hidden)
                elif resp_type == 1:
                    return await ctx.followup.send(content=outside_content, embed=embed, view=interface, ephemeral=hidden)
                elif resp_type == 2:
                    return await ctx.channel.send(content=outside_content, embed=embed, view=interface)
            
            # Let's try our best to make sure the user receives the message
            except (NotFound, InteractionResponded):
                if not attempted_followup:
                    logger.error('Error sending response, trying to send it again using the followup method')
                    await _send(ctx, embed, interface, resp_type=1, attempted_followup=True)
                
                elif attempted_followup and not attempted_channel:
                    logger.error('Error sending response, trying to send it again using the channel method')
                    await _send(ctx, embed, interface, resp_type=2, attempted_followup=True, attempted_channel=True)
                
                elif attempted_followup and attempted_channel:
                    logger.error('Error sending response')
                    
                    # DRASTIC MEASURES, I HOPE THIS NEVER GOES THROUGH!!!
                    if ctx.user:
                        logger.error('Trying to send response to user directly.')
                        
                        return await ctx.user.send(embed=embed, view=interface)
                    
                    return  # Prevent looping
                    
            except HTTPException as e:
                logger.error(f'An HTTP error occurred while trying to respond: [HTTP CODE: {e.status} | DC CODE: {e.code} | TEXT: {e.text}]')
            except Exception as e:
                log_exception(e, logger)
        
        # If it's a legacy context
        elif isinstance(ctx, Context):
            if hidden:
                logger.error('Interaction type "Context" does not support ephemeral messages.')
                
                if ctx.author:
                    logger.warning('Sending to user directly!')
                    return await ctx.author.send(embed=embed, view=interface)
            
            try:
                await ctx.send(embed=embed, view=interface)
            except HTTPException as e:
                logger.error(f'An HTTP error occurred while trying to respond: [HTTP CODE: {e.status} | DC CODE: {e.code} | TEXT: {e.text}]')
    
    if not isinstance(message, Embed):
        embed = (
            Embed(description=message, colour=colour) if message and not title else
            Embed(title=title, colour=colour) if title and not message else
            Embed(title=title, description=message, colour=colour) if message and title else
            None
        )
    else:
        embed = message
    
    if isinstance(ctx, Context):
        author = ctx.author
    elif isinstance(ctx, Interaction):
        author = ctx.user
    
    guild = ctx.guild
    channel = ctx.channel
    
    if embed and not view:
        await _send(ctx, embed=embed, resp_type=resp_type.value)
        
        if guild:
            logger.info(
                f'Response sent: [TYPE: Embed | GUILD: {guild} (ID: {guild.id}) | '
                f'AUTHOR: {author} (ID: {author.id}) | CH: {channel.name} (ID: {channel.id}) | MSG: {embed.description or embed.title}]')
            return
        
        logger.info(
            f'Response sent: [TYPE: Embed | AUTHOR: {author} (ID: {author.id}) | DMs | MSG: {embed.description or embed.title}]'
        )
    elif not embed and view:
        await _send(ctx, interface=view, resp_type=resp_type.value)
        
        if guild:
            logger.info(
                f'Response sent: [TYPE: View | GUILD: {guild} (ID: {guild.id}) | AUTHOR: {author} (ID: {author.id}) | CH: {channel.name} (ID: {channel.id})')
            return
        
        logger.info(
            f'Response sent: [TYPE: View | AUTHOR: {author} (ID: {author.id}) | DMs]'
        )
    elif embed and view:
        await _send(ctx, embed=embed, interface=view, resp_type=resp_type.value)
        
        if guild:
            logger.info(
                f'Response sent: [TYPE: Embed + View | GUILD: {guild} (ID: {guild.id}) | AUTHOR: {author} (ID: {author.id})'
                f' | CH: {channel.name} (ID: {channel.id}) | MSG: {embed.description or embed.title}]')
            return
        
        logger.info(
            f'Response sent: [TYPE: Embed + View | AUTHOR: {author} (ID: {author.id}) | DMs | MSG: {embed.description or embed.title}]'
        )
