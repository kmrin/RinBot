# Imports
import os, yt_dlp, platform, discord, re
from program.base.colors import *
from program.base.helpers import formatTime, format_exception, load_lang, is_url
from youtubesearchpython.__future__ import *
from dotenv import load_dotenv

# Verbose
text = load_lang()

# Load bitrate
load_dotenv()
bitrate = os.getenv('MUSIC_AUDIO_BITRATE')

# Youtube-DL and FFMPEG settings
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': 'in_playlist',
    'nocheckcertificate': True,
    'ignoreerrors': True}
ffmpeg_opts = {
    'options': f'-vn -b:a {bitrate}k',
    'executable': 
        
        # Use included ffmpeg executable if on windows
        f'{os.path.realpath(os.path.dirname(__file__))}/../bin/ffmpeg.exe' 
        if platform.system() == 'Windows' else 'ffmpeg',
    
    # These options make sure ffmpeg doesn't unalive itself on unstable networks
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

# Get thumbnail and audio source from a link
async def get_media(link):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            thumbnail = info.get("thumbnail", "")
            if "formats" in info and info["formats"]:
                audio = next((format for format in info["formats"]
                              if format.get("acodec") == "opus"), None)
                source = discord.FFmpegOpusAudio(audio["url"], **ffmpeg_opts)
            return {"thumb": thumbnail, "source_url": audio["url"], "source": source}
    except Exception as e:
        e = format_exception(e)
        return discord.Embed(    
            title = f"{text['YOUTUBE_ERROR_EXTRACT_MEDIA']} `{link}`",
            description=f"{e}", color=RED)

# Processes a youtube link and returns necessary data
async def process_link(link):
    data = {"title": None, "url": None, "duration": None, "uploader": None}
    try:
        video = await Video.getInfo(link)
        try: duration = formatTime(video["duration"]["secondsText"])
        except: duration = "N/A"
        data["title"] = video["title"]
        data["url"] = link
        data["duration"] = duration
        data["uploader"] = video["channel"]["name"]
        return data
    except Exception as e:
        e = format_exception(e)
        return discord.Embed(    
            title = f"{text['YOUTUBE_ERROR_EXTRACT_INFO']} `{link}`",
            description=f"{e}", color=RED)

# Processes a youtube playlist and returns the necessary data
async def process_playlist(link):
    try:
        data = {"title": None, "count": None, 
                "titles": [], "urls": [], "durations": [], "uploaders": []}
        playlist = await Playlist.get(link)
        data["title"] = playlist["info"]["title"]
        data["count"] = playlist["info"]["videoCount"]
        for v in playlist["videos"]:
            data["titles"].append(v["title"])
            data["urls"].append(v["link"].split("&list")[0])
            data["durations"].append(v["duration"])
            data["uploaders"].append(v["channel"]["name"])
        return data
    except Exception as e:
        e = format_exception(e)
        return discord.Embed(    
            title = f"{text['YOUTUBE_ERROR_EXTRACT_INFO']} `{link}`",
            description=f"{e}", color=RED)

# Processes a youtube video-only search and returns the necessary data
async def process_video_search(search):
    try:
        data = {"titles": [], "urls": [], "durations": [], "uploaders": []}
        query = await VideosSearch(search, limit=25).next()
        if not query["result"]:
            return discord.Embed(
                description=f"{text['YOUTUBE_ERROR_NO_RESULTS']} ``{search}``", color=RED)
        for v in query["result"]:
            data["urls"].append(v["link"])
            data["titles"].append(v["title"])
            data["durations"].append(v["duration"])
            data["uploaders"].append(v["channel"]["name"])
        return data
    except Exception as e:
        e = format_exception(e)
        return discord.Embed(    
            title = f"{text['YOUTUBE_ERROR_SEARCH']}",
            description=f"{e}", color=RED)

# Processes a youtube playlist-only search and returns the necessary data
async def process_playlist_search(search):
    try:
        data = {"titles": [], "urls": []}
        query = await PlaylistsSearch(search, limit=25).next()
        if not query["result"]:
            return discord.Embed(
                description=f"{text['YOUTUBE_ERROR_NO_RESULTS']} ``{search}``", color=RED)
        for p in query["result"]:
            data["titles"].append(p["title"])
            data["urls"].append(p["link"])
        return data
    except Exception as e:
        e = format_exception(e)
        return discord.Embed(    
            title = f"{text['YOUTUBE_ERROR_SEARCH']}",
            description=f"{e}", color=RED)

# Receives a list of youtube links, and gives back another list with them formatted
async def format_links(links):
    links = links.split("http")
    links.pop(0)
    for index, link in enumerate(links):
        if not is_url("http" + link):
            links.pop(index)
            continue
        elif "spotify" in link or "soundcloud" in link or "embed" in link:
            links.pop(index)
            continue
        elif "playlist?" in link:
            continue
        if "player_embedded&v=" in link:
            link = link.split("player_embedded&v=")[1]
        elif "desktop&v=" in link:
            link = link.split("desktop&v=")[1]
        elif "/v/" in link and not "?version" in link:
            link = link.split("/v/")[1]
        elif "/v/" in link and "?version" in link:
            link = link.split("?version")[0]
            link = link.split("/v/")[1]
        elif "/v/" in link and "?fs=" in link:
            link = link.split("?fs=")[0]
            link = link.split("/v/")[1]
        elif "&feature" in link:
            link = link.split("&feature")[0]
            link = link.split("?v=")[1]
        elif "/v/" in link and "?feature" in link:
            link = link.split("?feature")[0]
            link = link.split("/v/")[1]
        elif "#t=" in link:
            link = link.split("#t=")[0]
            link = link.split("?v=")[1]
        elif "&playnext_from=" in link:
            link = link.split("&playnext_from=")[0]
            link = link.split("?v=")[1]
        elif ".be/" in link and "?si=" in link:
            link = link.split(".be/")[1]
            link = link.split("?si=")[0]
        elif "?si=" in link and not "shorts/" in link and not ".be/":
            link = link.split(".be/")
            link = link[1].split("?si=")[0]
        elif "shorts" in link and not "?si=" in link:
            link = link.split("shorts/")[1]
        elif "shorts" in link and "?si=" in link:
            link = link.split("?si=")[0]
            link = link.split("shorts/")[1]
        elif "&list" in link:
            link = link.split("&list")[0]
            link = link.split("watch?v=")[1]
        else:
            link = link.split("watch?v=")[1]
        if not "playlist?" in link:
            link = f"s://youtube.com/watch?v={link}"
        links[index] = links[index].replace(" ", "").replace(",", "").replace(", ", "").replace("|", "").replace("/", "")
        links[index] = "http" + link
    if not links:
        return discord.Embed(
            description=f"{text['YOUTUBE_NO_VALID_LINKS']}", color=RED)
    return links