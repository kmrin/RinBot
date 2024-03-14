"""
#### RinBot's extension loading functions
"""

import os
from rinbot.base.logger import logger
from rinbot.base.helpers import load_config, load_lang, format_exception, get_path

config = load_config()
text = load_lang()

async def load_extensions(bot):
    async def load_extension(bot, ext, ai=False):
        try:
            if ai:
                await bot.load_extension(f"rinbot.kobold.cogs.{ext}")
                if ext == "languagemodel":
                    bot.endpoint_connected = True
                logger.info(f"{text['LOADER_EXTENSION_LOADED']} {ext} (AI)")
            else:
                await bot.load_extension(f"rinbot.extensions.{ext}")
                logger.info(f"{text['LOADER_EXTENSION_LOADED']} '{ext}'")
        except Exception as e:
            logger.error(format_exception(e))

    if config["AI_ENABLED"]:
        for file in os.listdir(get_path("kobold/cogs")):
            if file.endswith(".py"):
                extension = file[:-3]
                await load_extension(bot, extension, True)

    booru_ext = ["booru"]
    rule34_ext = ["rule34"]

    sum = booru_ext + rule34_ext

    for file in os.listdir(get_path("extensions")):
        if file.endswith(".py"):
            extension = file[:-3]

            if config["BOORU_ENABLED"] and extension in booru_ext:
                await load_extension(bot, extension)
            elif config["RULE34_ENABLED"] and extension in rule34_ext:
                await load_extension(bot, extension)

            if all(extension not in sl for sl in sum):
                await load_extension(bot, extension)