# Imports
import yt_dlp, platform, discord, urllib.parse, re, os
from program.helpers import removeListDuplicates, formatTime
from dotenv import load_dotenv

# Load bitrate settings
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
        './bin/ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg',
    
    # These options make sure ffmpeg doesn't unalive itself on unstable networks
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

# Processes standalone youtube links and returns the necessary data for further processing
def processYoutubeLink(link:str):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            duration = formatTime(info['duration'])
            thumbnail = info.get('thumbnail', '')
            if 'formats' in info and info['formats']:
                audio = next((format for format in info['formats']
                            if format.get('acodec') == 'opus'), None)
            if audio:
                data = {
                    'title': info['title'],
                    'url': link,
                    'thumb': thumbnail,
                    'duration': duration,
                    'uploader': info['uploader'],
                    'source': discord.FFmpegOpusAudio(audio['url'], **ffmpeg_opts)}
                return data
            else:
                embed = discord.Embed(
                    title='Error',
                    description=" ❌ YT-DLP error, could not grab song info :(",
                    color=0xD81313)
                return embed
    except yt_dlp.DownloadError as e:
        embed = discord.Embed(
            title=' ❌ Error on YT-DLP:',
            description=f"``{e}``",
            color=0xd81313)
        return embed

# Processes youtube playlist links and returns the necessary data for further processing
def processYoutubePlaylist(link:str):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            pl_info = ydl.extract_info(link, download=False)
            pl_data = {
                'title': pl_info['title'],
                'url': link,
                'count': len(pl_info.get('entries', [])),  # Number of songs
                'entries': pl_info['entries']}
            return pl_data
    except yt_dlp.DownloadError as e:
        embed = discord.Embed(
            title=" ❌ Error on YT-DLP:",
            description=f"``{e}``",
            color=0xD81313)
        return embed

# Makes a youtube query and returns the first 4 results
def processYoutubeSearch(search:str):
    try:
        query_data = []
        query = urllib.parse.quote(search)
        html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={query}')
        video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
        video_ids = removeListDuplicates(video_ids)
        video_urls = []
        for i in video_ids[:4]:
            video_urls.append('https://www.youtube.com/watch?v=' + i)
        for i in video_urls:
            video = processYoutubeLink(i)
            query_data.append(video)
        return query_data
    except Exception as e:
        embed = discord.Embed(
            title=" ❌ Error during search query:",
            description=f"`{e}`",
            color=0xD81313)
        return embed
