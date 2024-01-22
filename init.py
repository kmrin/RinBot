"""
RinBot v3.1.0
made by rin
"""

# Imports
import os, sys, json, platform, subprocess, asyncio, discord, random, pytz, wavelink
from discord import app_commands
from discord.ext import tasks
from discord.ext.commands import Bot
from rinbot.base.db_man import *
from rinbot.base.errors import Exceptions as E
from rinbot.base.helpers import load_lang, format_exception, format_millsec
from rinbot.base.loader import load_extensions
from rinbot.base.colors import *
from rinbot.base.interface import MediaControls
from rinbot.fortnite.daily_shop import show_fn_daily_shop
from rinbot.valorant.daily_shop import show_val_daily_shop
from datetime import datetime

# Load text
text = load_lang()

# Make sure cache dirs exists
try:
    folders = [
        "rinbot/cache", "rinbot/cache/fun", "rinbot/cache/chatlog", "rinbot/cache/stablediffusion",
        "rinbot/assets/images/fortnite/downloaded", "rinbot/assets/images/fortnite/images",
        "rinbot/cache/lavalink", "rinbot/cache/lavalink/log", "rinbot/cache/valorant"]
    for folder in folders:
        path = f"{os.path.realpath(os.path.dirname(__file__))}/{folder}"
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"{text['INIT_CREATED_DIRECTORY']} '{folder}'")
except Exception as e:
    logger.critical(f"{format_exception(e)}")
    sys.exit()

# Check if java is present for lavalink
try:
    output = subprocess.check_output("java -version", stderr=subprocess.STDOUT, shell=True, text=True)
    lines = output.split("\n")
    for line in lines:
        if "version" in line.lower():
            ver = line.split()[2]
            ver = int("".join(c for c in ver if c.isdigit() or c == ".").split(".")[0])
            try:
                if not ver >= 17:
                    logger.error(f"{text['INIT_INVALID_JAVA_VERSION']}: {ver}")
                    sys.exit()
            except:
                logger.error(text['INIT_INVALID_JAVA_VERSION'])
                sys.exit()
except:
    logger.critical(text['INIT_JAVA_NOT_FOUND'])
    sys.exit()

# Load config
CONFIG_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/rinbot/config/config-rinbot.json"
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as c: config = json.load(c)
except Exception as e:
    logger.critical(f"{format_exception(e)}")
    sys.exit()

# Bot intents (many)
intents = discord.Intents.all()
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
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
intents.moderation = True
intents.presences = True
intents.emojis_and_stickers = True
intents.messages = True
intents.emojis = True
intents.reactions = True
intents.typing = True
intents.bans = True

# Values
freshstart = True
message_count = {}
time_window_milliseconds = 5000
max_msg_per_window = 5
author_msg_times = {}
utc = pytz.utc
HOURS = {text['HOURS']}
MINUTES = {text['MINUTES']}
SECONDS = {text['SECONDS']}
OWNER = {text['OWNER']}
ADMIN = {text['ADMIN']}

# RinBot class
class RinBot(Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        intents.dm_messages = True
        intents.dm_reactions = True
        intents.dm_typing = True
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
        intents.moderation = True
        intents.presences = True
        intents.emojis_and_stickers = True
        intents.messages = True
        intents.emojis = True
        intents.reactions = True
        intents.typing = True
        intents.bans = True
        super().__init__(command_prefix=config["PREFIX"], intents=intents)
    
    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri=config['LAVALINK_ENDPOINT'], password=config['LAVALINK_PASSWORD'])]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=None)
    
    async def on_wavelink_node_ready(self, payload:wavelink.NodeReadyEventPayload) -> None:
        logger.info(f"{text['INIT_WAVELINK_NODE_CONNECTED'][0]} {payload.node} | {text['INIT_WAVELINK_NODE_CONNECTED'][1]} {payload.resumed} | {text['INIT_WAVELINK_NODE_CONNECTED'][2]} {payload.session_id}")
    
    async def on_wavelink_track_start(self, payload:wavelink.TrackStartEventPayload) -> None:
        logger.info(f"{text['INIT_WAVELINK_TRACK_STARTED'][0]} {payload.track.title} | {text['INIT_WAVELINK_TRACK_STARTED'][1]} {payload.player.guild.name} ({payload.player.guild.id})")
    
        player:wavelink.Player | None = payload.player
        if not player: return
        
        original:wavelink.Playable | None = payload.original
        track:wavelink.Playable = payload.track
        
        # Now Playing embed
        embed = discord.Embed(title=text['INIT_WAVELINK_NOW_PLAYING'][0], color=PURPLE)
        embed.description = f"```{track.title}```"
        embed.set_footer(text=f"{text['INIT_WAVELINK_NOW_PLAYING'][1]} {track.author}")
        
        if track.artwork:
            embed.set_image(url=track.artwork)
        if track.length:
            embed.set_footer(text=f"{embed.footer.text} | {text['INIT_WAVELINK_NOW_PLAYING'][2]} {format_millsec(track.length)}")
        if original and original.recommended:
            embed.set_footer(text=f"{embed.footer.text} | {text['INIT_WAVELINK_NOW_PLAYING'][3]} {track.source}")
        
        # Media controls view
        view = MediaControls(player)
        if track.uri:
            view.add_item(
                discord.ui.Button(
                    label=" 🔗  Link", style=discord.ButtonStyle.link, url=track.uri))
        
        await player.home.send(embed=embed, view=view)
        
    async def on_wavelink_track_end(self, payload:wavelink.TrackEndEventPayload) -> None:
        player:wavelink.Player | None = payload.player
        if not player: return
        
        logger.info(f"{text['INIT_WAVELINK_TRACK_ENDED'][0]} {payload.track.title} | {text['INIT_WAVELINK_TRACK_ENDED'][1]} {player.guild.name} ({player.guild.id})")
        if len(player.queue) == 0 and not player.autoplay.name == "enabled":
            embed = discord.Embed(
                description=text['INIT_WAVELINK_DISCONNECTING'], color=YELLOW)
            await asyncio.sleep(2)
            await player.home.send(embed=embed)
            await player.disconnect()
            player.cleanup()
        elif len(player.queue) == 0 and payload.track.source == "soundcloud" and player.autoplay.name == "enabled":
            embed = discord.Embed(
                description=text['INIT_WAVELINK_DISCONNECTING_SC'], color=RED)
            await asyncio.sleep(2)
            await player.home.send(embed=embed)
            await player.disconnect()
            player.cleanup()

# Client
client = RinBot()
client.val_db = None
client.val_endpoint = None

# Will I use AI?
if config["AI_ENABLED"] and config["AI_CHANNELS"]:
    from langchain.llms.koboldai import KoboldApiLLM
    
    # Specific AI settings
    client.endpoint = str(config["AI_ENDPOINT_KOBOLD"])
    if len(client.endpoint.split("/api")) > 0:
        client.endpoint = client.endpoint.split("/api")[0]
    client.chatlog_dir = "cache/chatlog"
    client.endpoint_connected = False
    client.channel_id = config["AI_CHANNEL"]
    client.num_lines_to_keep = 15
    client.guild_ids = [int(x) for x in config["AI_CHANNEL"].split(",")]
    client.debug = True
    client.char_name = "RinBot"
    client.endpoint_type = "Kobold"
    client.llm = KoboldApiLLM(endpoint=client.endpoint, max_length=800)

# Fortnite daily shop scheduler
async def fortnite_daily_shop_scheduler():
    logger.info(text['INIT_DAILY_SHOP_STARTED'])
    while True and config["FORTNITE_DAILY_SHOP_ENABLED"]:
        time = config["FORTNITE_DAILY_SHOP_UPDATE_TIME"].split(":")
        curr_time = datetime.now(utc).strftime("%H:%M:%S")
        target_time = f"{time[0]}:{time[1]}:{time[2]}"
        if curr_time == target_time:
            await show_fn_daily_shop(client, config["FORTNITE_DAILY_SHOP_FNBR_KEY"])
        await asyncio.sleep(1)

# Valorant daily shop scheduler
async def valorant_daily_shop_scheduler():
    logger.info("Valorant daily shop task started")
    while True and config["VALORANT_DAILY_SHOP_ENABLED"]:
        time = config["VALORANT_DAILY_SHOP_UPDATE_TIME"].split(":")
        curr_time = datetime.now(utc).strftime("%H:%M:%S")
        target_time = f"{time[0]}:{time[1]}:{time[2]}"
        if curr_time == target_time:
            await show_val_daily_shop(client)
        await asyncio.sleep(1)

# Change status every 5 minutes (if there are more than 1)
@tasks.loop(minutes=int(config["ACTIVITY_SWITCH_INTERVAL"]))
async def status_loop():
    chosen = random.choice(text['INIT_ACTIVITY'])
    await client.change_presence(activity=discord.CustomActivity(name=chosen))

# When ready
@client.event
async def on_ready() -> None:
    # Initial logger info (splash)
    logger.info("--------------------------------------")
    logger.info(f"  > {config['VER']}")
    logger.info("--------------------------------------")
    logger.info(f" {text['INIT_SPLASH_LOGGED_AS']} {client.user.name}")
    logger.info(f" {text['INIT_SPLASH_API_VER']} {discord.__version__}")
    logger.info(f" {text['INIT_SPLASH_PY_VER']} {platform.python_version()}")
    logger.info(f" {text['INIT_SPLASH_RUNNING_ON']} {platform.system()}-{platform.release()} ({os.name})")
    logger.info("--------------------------------------")
    
    # Check if all members are present in the economy
    logger.info(text['INIT_CHECKING_ECONOMY'])
    economy = await get_table("currency")
    for guild in client.guilds:
        if str(guild.id) not in economy.keys():
            economy[str(guild.id)] = {}
        for member in guild.members:
            if str(member.id) not in economy[str(guild.id)]:
                economy[str(guild.id)][str(member.id)] = {"wallet": 500, "messages": 0}
        logger.info(f"{text['INIT_CURR_GUILD'][0]} {guild.member_count} {text['INIT_CURR_GUILD'][1]} {guild.name} (ID: {guild.id})")
    update = await update_table("currency", economy)
    if update: logger.info(text['INIT_CHECKED_ECONOMY'])
    else: logger.error(text['INIT_ERROR_CHECKING_ECONOMY'])
    
    # Make sure the bot has a history of all joined guilds
    logger.info(text['INIT_CHECKING_GUILDS'])
    joined = await get_table("guilds")
    for guild in client.guilds:
        if str(guild.id) not in joined:
            joined.append(str(guild.id))
    update = await update_table("guilds", joined)
    if update: logger.info(text['INIT_CHECKED_GUILDS'])
    else: logger.error(text['INIT_ERROR_CHECKING_GUILDS'])
    
    # Make sure all members are registered on the valorant stuff
    logger.info("Checking valorant stuff")
    val = await get_table("valorant")
    for guild in client.guilds:
        if str(guild.id) not in val.keys:
            val[str(guild.id)] = {"active": False, "channel_id": 0, "members": {}}
        for member in guild.members:
            if str(member.id) not in val[str(guild.id)].keys:
                val[str(guild.id)]["members"][str(member.id)] = {"active": False, "type": 0}
    update = await update_table("valorant", val)
    if update: logger.info("Checked valorant stuff")
    else: logger.error("Error checking valorant stuff")
    
    # Start client tasks
    status_loop.start()
    
    # Start async tasks
    asyncio.create_task(fortnite_daily_shop_scheduler())
    asyncio.create_task(valorant_daily_shop_scheduler())
    
    # Sync commands
    logger.info(text['INIT_SYNCHING_COMMANDS'])
    await client.tree.sync()

# Save new guild ID's when joining
@client.event
async def on_guild_join(guild:discord.Guild):
    logger.info(f"{text['INIT_JOINED_GUILD']} '{guild.name}'! ID: {guild.id}")
    joined = await get_table("guilds")
    for guild in joined:
        if not guild.id == int(guild):
            joined.append(str(guild.id))
    update = await update_table("guilds", joined)
    if update: logger.info(text['INIT_ADDED_NEW_GUILD'])
    else: logger.error(text['INIT_ERROR_ADDING_NEW_GUILD'])

# Remove guild ID's when leaving
@client.event
async def on_guild_remove(guild:discord.Guild):
    logger.info(f"{text['INIT_LEFT_GUILD']} '{guild.name}'. ID: {guild.id}")
    joined = await get_table("guilds")
    joined.remove(str(guild.id))
    update = await update_table("guilds", joined)
    if update: logger.info(text['INIT_REMOVED_GUILD'])
    else: logger.error(text['INIT_ERROR_REMOVING_GUILD'])

# When members join
@client.event
async def on_member_join(member:discord.Member):
    welcome_channels = await get_table("welcome_channels")
    if str(member.guild.id) in welcome_channels.keys():
        channel:discord.TextChannel = client.get_channel(int(welcome_channels[str(member.guild.id)]["channel_id"])) or await client.fetch_channel(int(welcome_channels[str(member.guild.id)]["channel_id"]))
        is_active = welcome_channels[str(member.guild.id)]["active"]
        custom_msg = welcome_channels[str(member.guild.id)]["custom_message"]
        if channel and is_active:
            embed = discord.Embed(
                title=f"{text['INIT_NEW_MEMBER_TITLE'][0]} {member.name}{text['INIT_NEW_MEMBER_TITLE'][1]}")
            if custom_msg:
                embed.description = f"{custom_msg}"
        await channel.send(embed=embed)

# When members leave
@client.event
async def on_member_remove(member:discord.Member):
    pass  # Got no use for this yet but it's here

# Process messages
@client.event
async def on_message(message:discord.Message):
    try:
        # Do not interact with self or other bots
        if message.author == client.user or message.author.bot: return
        
        # Anti-spam for economy system
        global author_msg_times
        aid = message.author.id
        ct = datetime.now().timestamp() * 1000
        if not author_msg_times.get(aid, False):
            author_msg_times[aid] = []
        author_msg_times[aid].append(ct)
        et = ct - time_window_milliseconds
        em = [mt for mt in author_msg_times[aid] if mt < et]
        for mt in em: author_msg_times[aid].remove(mt)
        if not len(author_msg_times[aid]) > max_msg_per_window:
            
            # Update user message count and reward after 50 messages
            currency = await get_table("currency")
            user_data = currency[str(message.guild.id)][str(message.author.id)]
            user_data["messages"] += 1
            if user_data["messages"] >= 50:
                user_data["wallet"] += 25
                user_data["messages"] == 0
            currency[str(message.guild.id)][str(message.author.id)] = user_data
            await update_table("currency", currency)

    except AttributeError:
        pass

# Show executed commands on the log
@client.event
async def on_app_command_completion(interaction:discord.Interaction) -> None:
    comm_name = interaction.command.qualified_name.split(" ")
    comm = str(comm_name[0])
    logger.info(f"{text['INIT_COMM_EXECUTED_GUILD'][0]} {comm} {text['INIT_COMM_EXECUTED_GUILD'][1]} (ID: {interaction.guild.id}) {text['INIT_COMM_EXECUTED_GUILD'][2]} {interaction.user} (ID: {interaction.user.id}))"
                if interaction.guild is not None else
                f"{text['INIT_COMM_EXECUTED_DMS'][0]} {comm} {text['INIT_COMM_EXECUTED_DMS'][1]} {interaction.user} (ID: {interaction.user.id}) {text['INIT_COMM_EXECUTED_DMS'][2]}")

# What to do when commands go nuh-uh
@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error) -> None:
    if isinstance(error, app_commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            description=f"{text['INIT_COMM_ERROR_DELAY']} {f'{round(hours)} {HOURS}' if round(hours) > 0 else ''} {f'{round(minutes)} {MINUTES}' if round(minutes) > 0 else ''} {f'{round(seconds)} {SECONDS}' if round(seconds) > 0 else ''}.",
            color=0xE02B2B,)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, E.UserBlacklisted):
        embed = discord.Embed(
            description=f"{text['INIT_BLOCKED']}", color=0xE02B2B)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if interaction.guild:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_COMM_GUILD']} {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_BLOCKED']}")
        else:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM']} {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_BLOCKED']}")
    elif isinstance(error, E.UserNotOwner):
        embed = discord.Embed(
            description=f"{text['INIT_NOT_OWNER']}", color=0xE02B2B)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if interaction.guild:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        else:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{OWNER}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
    elif isinstance(error, E.UserNotAdmin):
        embed = discord.Embed(
            description=f"{text['INIT_NOT_ADMIN']}", color=0xE02B2B)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if interaction.guild:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {interaction.guild.name} (ID: {interaction.guild.id}), {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
        else:
            logger.warning(
                f"{interaction.user} (ID: {interaction.user.id}) {text['INIT_TRIED_COMM_CLASS']} `{ADMIN}` {text['INIT_TRIED_ON_DMS']}, {text['INIT_TRIED_COMM_NOT_IN_CLASS']}")
    elif isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            description=f"{text['INIT_USER_NO_PERMS_1']}"
            + ", ".join(error.missing_permissions)
            + f"{text['INIT_USER_NO_PERMS_2']}",
            color=0xE02B2B,)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        embed = discord.Embed(
            description=f"{text['INIT_BOT_NO_PERMS_1']}"
            + ", ".join(error.missing_permissions)
            + f"{text['INIT_BOT_NO_PERMS_2']}",
            color=0xE02B2B,)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        raise error

# Starts lavalink
async def lavalink():
    logger.info(text['INIT_STARTING_LAVALINK'])
    system = platform.system().lower()
    if system == "windows":
        script_path = r"rinbot\bin\run_lavalink.bat"
    elif system == "linux": return
    process = await asyncio.create_subprocess_shell(
        script_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error(f"{stderr.decode(errors='replace')}")

# Main func, runs everything
async def main() -> None:
    # Start database
    await populate()
    await startup()
    
    # Load extensions
    await load_extensions(client, config)
    
    # Start lavalink
    lavalink_task = asyncio.create_task(lavalink())
    
    # Get token and run bot
    bot = await get_table("bot")
    async with client:
        try:
            await client.start(token=bot["token"], reconnect=True)
        except discord.errors.LoginFailure:
            logger.critical(text['INIT_INVALID_TOKEN'])
    
    # Stop lavalink after bot closes
    logger.info(text['INIT_STOPPING_LAVALINK'])
    lavalink_task.cancel()

# RUN
if __name__ == "__main__":
    asyncio.run(main())