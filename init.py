"""
RinBot v1.7.0 (GitHub release)
made by rin
"""

# Make sure cache dirs exist
import os
folders = ["program/music/cache", "log"]
for folder in folders:
    if not os.path.exists(f"{os.path.realpath(os.path.dirname(__file__))}/{folder}"):
        os.makedirs(f"{os.path.realpath(os.path.dirname(__file__))}/{folder}")
        print(f"[init.py]-[Info]: Created directory '{folder}'")

# Imports
import io, subprocess, shutil, asyncio, json, base64, platform, sys, aiosqlite, exceptions, discord, time
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from program.logger import logger
from program import db_manager
from langchain.llms import KoboldApiLLM
from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
from program.helpers import strtobool

# Load env
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
YOUR_BALLS_WILL_EXPLODE_TARGET = os.getenv('YOUR_BALLS_WILL_EXPLODE_TARGET')
USE_AI = strtobool(os.getenv('USE_AI'))
AI_CHAR = os.getenv('AI_CHAR')
ENDPOINT = os.getenv('ENDPOINT')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHAT_HISTORY_LINE_LIMIT = os.getenv('CHAT_HISTORY_LINE_LIMIT')
STOP_SEQUENCES = os.getenv('STOP_SEQUENCES')
MAX_NEW_TOKENS = os.getenv('MAX_NEW_TOKENS')
AI_LANGUAGE = os.getenv('AI_LANGUAGE')
BOT_PREFIX = os.getenv('BOT_PREFIX')
WELCOME_CHANNEL_ID = os.getenv('WELCOME_CHANNEL_ID')

# Check presence of ffmpeg
if platform.system() == 'Windows':
    if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/ffmpeg.exe"):
        sys.exit("[init.py]-[Error]: 'ffmpeg.exe' not found.")
elif platform.system() == 'Linux':
    try:
        # Try to execute ffmpeg if on linux
        result = subprocess.run(['ffmpeg', '-version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                text=True)
        if result.returncode != 0:
            sys.exit("[init.py]-[Error]: 'ffmpeg' not found on this system, please install it, or if it is installed, check if it is available in PATH.")
    except FileNotFoundError:
        sys.exit("[init.py]-[Error]: 'ffmpeg' not found on this system, please install it, or if it is installed, check if it is available in PATH.")

# Bot intentions (many)
intents = discord.Intents.all()
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.voice_states = True
intents.webhooks = True
intents.members = True
intents.message_content = True
intents.presences = True
intents.emojis_and_stickers = True
intents.messages = True
intents.reactions = True
intents.typing = True
intents.bans = True

# Bot
bot = Bot(
    command_prefix=commands.when_mentioned_or(BOT_PREFIX),
    intents=intents,
    help_command=None,)
bot.logger = logger

# Vars
freshstart = True

# Will I use AI?
if USE_AI:
    # Load AI environment variables
    load_dotenv()
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    ENDPOINT = str(os.getenv("ENDPOINT"))
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    CHAT_HISTORY_LINE_LIMIT = os.getenv("CHAT_HISTORY_LINE_LIMIT")
    if os.getenv("MAX_NEW_TOKENS") is not None:
        MAX_NEW_TOKENS = os.getenv("MAX_NEW_TOKENS")
    else:
        MAX_NEW_TOKENS = 300

    # Specific AI settings
    bot.endpoint = str(ENDPOINT)
    if len(bot.endpoint.split("/api")) > 0:
        bot.endpoint = bot.endpoint.split("/api")[0]
    bot.chatlog_dir = "log"
    bot.endpoint_connected = False
    bot.channel_id = CHANNEL_ID
    bot.num_lines_to_keep = int(CHAT_HISTORY_LINE_LIMIT)
    bot.guild_ids = [int(x) for x in CHANNEL_ID.split(",")]
    bot.debug = True
    bot.char_name = AI_CHAR
    characters_folder = "ai/Characters"
    cards_folder = "ai/Cards"
    characters = {}
    bot.endpoint_type = "Kobold"
    bot.llm = KoboldApiLLM(endpoint=bot.endpoint, max_length=MAX_NEW_TOKENS)

    # Saves AI characters
    def upload_character(json_file, img, tavern=False):
        json_file = json_file if type(json_file) == str else json_file.decode("utf-8")
        data = json.loads(json_file)
        outfile_name = data["char_name"]
        i = 1
        while Path(f"{characters_folder}/{outfile_name}.json").exists():
            outfile_name = f'{data["char_name"]}_{i:03d}'
            i += 1
        if tavern:
            outfile_name = f"TavernAI-{outfile_name}"
        with open(Path(f"{characters_folder}/{outfile_name}.json"), "w") as f:
            f.write(json_file)
        if img is not None:
            img = Image.open(io.BytesIO(img))
            img.save(Path(f"{characters_folder}/{outfile_name}.png"))
        bot.logger.info(f'New character saved to "{characters_folder}/{outfile_name}.json".')
        return outfile_name

    # Saves AI characters (tavern)
    def upload_tavern_character(img, name1, name2):
        _img = Image.open(io.BytesIO(img))
        _img.getexif()
        decoded_string = base64.b64decode(_img.info["chara"])
        _json = json.loads(decoded_string)
        _json = {
            "char_name": _json["name"],
            "char_persona": _json["description"],
            "char_greeting": _json["first_mes"],
            "example_dialogue": _json["mes_example"],
            "world_scenario": _json["scenario"],}
        _json["example_dialogue"] = (
            _json["example_dialogue"]
            .replace("{{user}}", name1)
            .replace("{{char}}", _json["char_name"]))
        return upload_character(json.dumps(_json), img, tavern=True)
    try:
        for filename in os.listdir(cards_folder):
            if filename.endswith(".png"):
                with open(os.path.join(cards_folder, filename), "rb") as read_file:
                    img = read_file.read()
                    name1 = "User"
                    name2 = "Character"
                    tavern_character_data = upload_tavern_character(img, name1, name2)
                with open(
                    os.path.join(characters_folder, tavern_character_data + ".json")
                ) as read_file:
                    character_data = json.load(read_file)
                    # characters.append(character_data)
                read_file.close()
                if not os.path.exists(f"{cards_folder}/Converted"):
                    os.makedirs(f"{cards_folder}/Converted")
                os.rename(
                    os.path.join(cards_folder, filename),
                    os.path.join(f"{cards_folder}/Converted/", filename),)
    except:
        pass
    for filename in os.listdir(characters_folder):
        if filename.endswith(".json"):
            with open(
                os.path.join(characters_folder, filename), encoding="utf-8"
            ) as read_file:
                character_data = json.load(read_file)
                character_data["char_filename"] = filename
                image_file_jpg = f"{os.path.splitext(filename)[0]}.jpg"
                image_file_png = f"{os.path.splitext(filename)[0]}.png"
                if os.path.exists(os.path.join(characters_folder, image_file_jpg)):
                    character_data["char_image"] = image_file_jpg
                elif os.path.exists(os.path.join(characters_folder, image_file_png)):
                    character_data["char_image"] = image_file_png
                characters[os.path.splitext(filename)[0]] = character_data
    if os.path.exists('ai/chardata.json'):
        with open('ai/chardata.json', encoding='utf-8') as read_file:
            character_data = json.load(read_file)
    else:
        data = characters[AI_CHAR]
        char_name = data['char_name']
        char_filename = os.path.join(characters_folder, data['char_filename'])
        shutil.copyfile(char_filename, "ai/chardata.json")
# Don't even ask me how this works ^

# Start SQL database
async def init_db():
    async with aiosqlite.connect(
        f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
    ) as db:
        with open(
            f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
        ) as file:
            await db.executescript(file.read())

# Checks if the bot has someone on the 'owners' class
async def checkOwners():
    owners = await db_manager.get_owners()
    if len(owners) == 0:
        owner_valid = False
        bot.logger.warning('Fresh database, first start detected, Welcome!')
        bot.logger.info('Please copy and paste your discord user ID so we can add you as a bot owner.')
        while not owner_valid:
            fresh_owner_id:str = input('Your ID: ')
            owner_valid = fresh_owner_id.isnumeric()
            if owner_valid:
                await db_manager.add_user_to_owners(fresh_owner_id)
                bot.logger.info("Thanks! You've been added to the 'owners' class, have fun! :D")
            else:
                bot.logger.error('Invalid ID. Make sure it only contains numbers.')
    else:
        bot.logger.info('Owners class filled, proceeding.')

# When ready
@bot.event
async def on_ready() -> None:
    # Initial logger info (splash)
    bot.logger.info("--------------------------------------")
    bot.logger.info(" >   RinBot v1.7.0 (GitHub release)   ")
    bot.logger.info("--------------------------------------")
    bot.logger.info(f" > Logged as {bot.user.name}")
    bot.logger.info(f" > API Version: {discord.__version__}")
    bot.logger.info(f" > Python Version: {platform.python_version()}")
    bot.logger.info(f" > Running on: {platform.system()}-{platform.release()} ({os.name})")
    bot.logger.info("--------------------------------------")
    
    # Load AI extensions
    if USE_AI:
        bot.logger.info('Usando IA...')
        for items in bot.guild_ids:
            try:
                channel = bot.get_channel(int(items))
                guild = channel.guild
                if isinstance(channel, discord.TextChannel):
                    channel_name = channel.name
                    bot.logger.info(f'AI Text channel: {guild.name} | {channel_name}')
                else:
                    bot.logger.error(f'AI Text channel {bot.channel_id} is not a valid text channel, check your ID or channel settings.')
            except AttributeError:
                bot.logger.error(
                    "Couldn't validate AI text channel, verify the ID, channel settings, and if I have the necessary permissions.")
    
    # Default status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name='to your commands :3'))
        
    # Sync commands with discord
    bot.logger.info("Synching commands globally")
    await bot.tree.sync()

# Member welcome
@bot.event
async def on_member_join(member:discord.Member):
    if WELCOME_CHANNEL_ID.isnumeric():
        channel = bot.get_channel(int(WELCOME_CHANNEL_ID))
        if channel:
            embed = discord.Embed(
                title=' :star:  Alguém chegou!',
                description=f'Bem-vindo(a) à {member.guild.name}, {member.mention}!',
                color=0xf5be0a)
            try:
                embed.set_thumbnail(url=member.avatar.url)
            except AttributeError:
                pass
            await channel.send(embed=embed)

# Save new guild ID's when joining
@bot.event
async def on_guild_join(guild):
    await db_manager.add_guild_id(int(guild.id))
    await db_manager.add_joined_on(str(guild.id))
    bot.logger.info(f'Joined guild ID: {guild.id}')

# Processes standard message commands (not-in-use at the moment)
@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

# Show executed commands on the log
@bot.event
async def on_command_completion(context: Context) -> None:
    full_command_name = context.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if context.guild is not None:
        bot.logger.info(
            f"Comando {executed_command} executado em {context.guild.name} (ID: {context.guild.id}) por {context.author} (ID: {context.author.id})")
    else:
        bot.logger.info(
            f"Comando {executed_command} executado por {context.author} (ID: {context.author.id}) nas DMs.")

# What to do when commands go no-no
@bot.event
async def on_command_error(context: Context, error) -> None:
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            description=f"**Please wait! >-< ** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        embed = discord.Embed(
            description="You are blocked from using RinBot!", color=0xE02B2B)
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command on guild {context.guild.name} (ID: {context.guild.id}), but they're blocked from using RinBot.")
        else:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command on my DMs, but they're blocked from using RinBot.")
    elif isinstance(error, exceptions.UserNotOwner):
        embed = discord.Embed(
            description="You are not on the RinBot `owners` class, kinda SUS!", color=0xE02B2B)
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command of class `owner` {context.guild.name} (ID: {context.guild.id}), but they're not a part of this class")
        else:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command of class `owner` on my DMs, but they're not a part of this class")
    elif isinstance(error, exceptions.UserNotAdmin):
        embed = discord.Embed(
            description="You are not on the RinBot `admins` class, kinda SUS!", color=0xE02B2B)
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command of class `admin` {context.guild.name} (ID: {context.guild.id}), but they're not a part of this class")
        else:
            bot.logger.warning(
                f"{context.author} (ID: {context.author.id}) tried running a command of class `admin` on my DMs, but they're not a part of this class")
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            description="You don't have `"
            + ", ".join(error.missing_permissions)
            + "` permissions, which are necessary to run this command!",
            color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(
            description="I don't have `"
            + ", ".join(error.missing_permissions)
            + "` permissions, which are necessary to run this command!",
            color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            description=str(error).capitalize(),
            color=0xE02B2B,)
        await context.send(embed=embed)
    else:
        raise error

# Loads extensions (command cogs)
async def load_extensions() -> None:
    global USE_AI
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/extensions"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"extensions.{extension}")
                bot.logger.info(f"Extension loaded '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                bot.logger.error(f"Error while loading extension {extension}\n{exception}")
    if USE_AI:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/ai"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await bot.load_extension(f"ai.{extension}")
                    if extension == 'languagemodel':
                        bot.endpoint_connected = True
                    bot.logger.info(f"AI extension '{extension}' loaded.")
                except Exception as e:
                    if extension == 'languagemodel':
                        bot.endpoint_connected = False
                    exception = f"{type(e).__name__}: {e}"
                    bot.logger.error(f"Error on AI extension '{extension}': \n{exception}")

# Wait 5 seconds when coming from a reset
try:
    if sys.argv[1] == 'reset':
        print('Coming from a reset, waiting for previous instance to finish...')
        time.sleep(5)
except:
    pass

# RUN
asyncio.run(init_db())
asyncio.run(checkOwners())
asyncio.run(load_extensions())
bot.run(DISCORD_BOT_TOKEN)