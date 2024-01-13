"""
#### RinBot's extension loading funcions
"""

import os
from discord.ext.commands import Bot
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang, format_exception

text = load_lang()

async def load_extension(client:Bot, ext, ai=False):
    if not ai:
        try:
            await client.load_extension(f"rinbot.extensions.{ext}")
            logger.info(f"{text['LOADER_EXTENSION_LOADED']} '{ext}'")
        except Exception as e:
            logger.error(f"{format_exception(e)}")
    else:
        try:
            await client.load_extension(f"rinbot.kobold.cogs.{ext}")
            if ext == "languagemodel":
                client.endpoint_connected = True
            logger.info(f"{text['LOADER_EXTENSION_LOADED']} {ext}")
        except Exception as e:
            logger.error(f"{format_exception(e)}")

async def load_extensions(client, config):
    if config["AI_ENABLED"]:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/../kobold/cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                await load_extension(client, extension, True)
    booru_ext = ["booru"]
    rule34_ext = ["rule34"]
    sum = booru_ext + rule34_ext
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/../extensions"):
        if file.endswith(".py"):
            extension = file[:-3]
            if config["BOORU_ENABLED"] and extension in booru_ext:
                await load_extension(client, extension)
            elif config["RULE34_ENABLED"] and extension in rule34_ext:
                await load_extension(client, extension)
            if all(extension not in sl for sl in sum):
                await load_extension(client, extension)