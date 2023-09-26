"""
RinBot v1.4.3
feita por rin
"""

# Imports
import discord, re, urllib, yt_dlp, asyncio, urllib.parse, random, platform
from collections import deque
from discord import app_commands
from discord.utils import get
from discord.app_commands.models import Choice
from discord.ext import commands
from discord.ext.commands import Context
from program.is_url import is_url
from program.checks import *

# Valores iniciais de variáveis
song_queue = deque()
max_history_lenght = 50
current_vc = None
is_paused = False
is_playing = False
is_playlist = False
current_playlist = ''
current_playlist_title = ''
items_added = 0
playlist_index = 0
playlist_count = 0
playlist_available = True
initial_playlist_message_shown = False
manual_dc = False
is_shuffling = 0
from_next = False
shuffle_list = []
query_selected = 0
start_from = 0

# Carregar histórico de músicas por arquivo, gera uma vazia caso o arquivo não exista
try:
    with open('cache/song_history.json', 'r', encoding='utf-8') as f:
        song_history = json.load(f)
except FileNotFoundError:
    song_history = []

# Opções CLI do youtube-dl e do FFMPEG
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': 'in_playlist',
    'nocheckcertificate': True,
    'ignoreerrors': True}
ffmpeg_opts = {
    'options': '-vn -b:a 128k',  # bitrate de 128kbps
    'executable':
        
        # Usar o ffmpeg incluso caso estiver no windows
        './ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg',
    
    # Essas opções evitam que o ffmpeg morra em conexões instáveis
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

# Bloco de comandos 'music'
class Music(commands.Cog, name='music'):
    def __init__(self, bot):
        self.bot = bot

    # Funções de controle multimídia geral
    async def pause(self, ctx: Context):
        global is_paused
        client = ctx.voice_client
        if client and client.is_playing() and not is_paused:
            client.pause()
            is_paused = True
    async def resume(self, ctx: Context):
        global is_paused
        client = ctx.voice_client
        if client and client.is_paused() and is_paused:
            client.resume()
            is_paused = False
    async def skip(self, ctx: Context):
        client = ctx.voice_client
        if client and client.is_playing():
            client.stop()
        else:
            embed = discord.Embed(
                description=" ❌ Nenhuma música tocando.",
                color=0xd81313)
            await ctx.send(embed=embed)
    
    # Alterna o status da bot caso ela esteja tocando música ou não
    async def updateStatus(self, playing:bool):
        if not playing:
            await self.bot.change_presence(
                status=discord.Status.online, activity=discord.Game("Disponível! ✅"))
        else:
            await self.bot.change_presence(
                status=discord.Status.online, activity=discord.Game("Ocupadinha! ❌"))
    
    # Formata segundos no formato de tempo MM:SS
    async def formatTime(self, time:int):
        m, s = time // 60, time % 60
        time = f"{m:02d}:{s:02d}"
        return time
    
    # Remove items duplicados de uma lista
    async def removeListDuplicates(self, list):
        nodupe = []
        for i in list:
            if i not in nodupe:
                nodupe.append(i)
        return nodupe
    
    # Seleciona uma música do histórico, retorna a URL e a deleta
    async def pickFromHistory(self, entry:int):
        global song_history
        try:
            song = song_history[entry - 1]['url']
            song_history.remove(song_history[entry -1])  # Remover para evitar duplicação
            await self.updateHistoryCache(song_history)  # Atualizar histórico com os novos dados
            return song
        
        # Caso ocorra erros, retorna-se embeds, tratamento feito no comando 'tocar'
        except IndexError:
            embed = discord.Embed(
                title=' ❌ Erro',
                description=f"Item não encontrado no histórico. {entry} está fora de alcance.",
                color=0xD81313)
            return embed
    
    # Realiza uma pesquisa no youtube e retorna os 4 primeiros resultados em uma lista
    async def processYoutubeSearch(self, search):
        try:
            query_data = []
            query = urllib.parse.quote(search)
            html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={query}')
            video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
            video_ids = await self.removeListDuplicates(video_ids)
            video_urls = []
            for i in video_ids[:4]:
                video_urls.append('https://www.youtube.com/watch?v=' + i)
            for i in video_urls:
                video = await self.processYoutubeLink(i)
                query_data.append(video)
            return query_data
        
        # Caso ocorra erros, retorna-se embeds, tratamento feito no comando 'tocar'
        except Exception as e:
            embed = discord.Embed(
                title=" ❌ Erro ao realizar a busca",
                description=f"`{e}`",
                color=0xD81313)
            return embed
    
    # Processa links de playlist do youtube e retorna os dados necessários para o player
    async def processYoutubePlaylist(self, ctx: Context, entry:int, link:str, shuffle:bool):
        global is_playlist, current_playlist, current_playlist_title, is_shuffling, shuffle_list, items_added, initial_playlist_message_shown, playlist_available, playlist_count, playlist_index
        
        items_added = 0  # Ter certeza de que o contador começa zerado
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                
                # Mostrar mensagem de que a playlist está sendo carregada (apenas uma vez)
                if not initial_playlist_message_shown:
                    embed = discord.Embed(
                        description=" ⏳  Carregando dados da playlist. Aguarde.",
                        color=0xF7C50C)
                    await ctx.send(embed=embed)
                    initial_playlist_message_shown = True
                
                # Processar playlist apenas se a variavél de disponibilidade estiver como true
                if playlist_available:
                    playlist_available = False  # Cortar processamento de playlists futuras enquanto essa está ativa
                    playlist_info = ydl.extract_info(link, download=False)
                    playlist_count = len(playlist_info.get('entries', []))  # Número de músicas na playlist
                    
                    # Gerar lista para randomização
                    if is_shuffling != 1:
                        shuffle_list = list(range(playlist_count))
                    
                    # Selecionar uma música aleatória caso a randomização esteja ativa
                    if shuffle:
                        is_shuffling = 1
                        shuffle_song = random.choice(shuffle_list)
                        shuffle_list.remove(shuffle_song)
                        entry = shuffle_song
                    
                    # Extrair informações
                    entries = playlist_info['entries']
                    entry = entries[entry]
                    entry_info = await self.processYoutubeLink(entry['url'])
                    
                    # Atualizar valores e retornar
                    is_playlist = True
                    current_playlist = link
                    playlist_index += 1
                    current_playlist_title = playlist_info['title']
                    return entry_info
                
                # Caso outra playlist já esteja tocando
                else:
                    embed = discord.Embed(
                        description=" ❌ Tem outra playlist tocando. Cancele-a e tente novamente.",
                        color=0xD81313)
                    await ctx.send(embed=embed)
        
        # Caso ocorra erros, retorna-se embeds, tratamento feito no comando 'tocar'
        except yt_dlp.DownloadError as e:
            embed = discord.Embed(
                title=" ❌ Erro no YDL:",
                description=f"``{e}``",
                color=0xD81313)
            return embed

    # Processa links únicos do youtube e retorna dados necessários para o player
    async def processYoutubeLink(self, link):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                duration = await self.formatTime(info['duration'])
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
        
        # Caso ocorra erros, retorna-se embeds, tratamento feito no comando 'tocar'
                else:
                    embed = discord.Embed(
                        title='Erro',
                        description=" ❌ Erro no YT-DLP, não foi possível adquirir os metadados da música :(",
                        color=0xD81313)
                    return embed
        except yt_dlp.DownloadError as e:
            embed = discord.Embed(
                title=" ❌ Erro no YDL:",
                description=f"``{e}``",
                color=0xD81313)
            return embed
    
    # Verifica e tenta tocar a próxima música da fila
    async def play_next(self, ctx: Context, client):
        global from_next, song_history, playlist_available, start_from, manual_dc
        
        from_next = True  # Estamos na 'play_next', então né? Faz sentido :p
        
        if len(song_queue) > 0:
            
            # Pegar próxima música da fila
            next_song = song_queue.popleft()
            
            # Tocar próxima música e depois rodar a função playnext novamente, até o fim da fila
            client.play(next_song['source'], after=lambda e: self.bot.loop.create_task(
                self.play_next(ctx, client)))

            # Adicionar música que começou a tocar no histórico e atualizá-lo
            history_data = {
                'title': next_song['title'], 'duration': next_song['duration'],
                'uploader': next_song['uploader'], 'url': next_song['url']}
            song_history.append(history_data)
            await self.updateHistoryCache(song_history)
            
            # Embed de informações para o usuário
            embed = discord.Embed(
                title=" 🎵  Tocando:",
                description=f"```{next_song['title']}```",
                color=0x25d917)
            embed.set_footer(text=f"Duração: {next_song['duration']}  |  Por: {next_song['uploader']}")
            embed.set_image(url=next_song['thumb'])
            
            # Interface
            view = MediaControls(ctx, self.bot)
            view.add_item(discord.ui.Button(label='🔗 Link', style=discord.ButtonStyle.link, url=next_song['url']))

            # Mostrar
            await ctx.send(embed=embed, view=view)
            
            # Tratamento caso seja uma playlist
            if is_playlist:
                # Definir temporariamente essa variável como true para que a 
                # função de aquisição de dados de playlist funcione corretamente
                playlist_available = True
                
                if playlist_index <= playlist_count:
                    # Atualizar index de playlist
                    start_from=playlist_index
                    await self.play(ctx, current_playlist, randomizar=is_shuffling)
                
                # Fim da playlist
                else:
                    await asyncio.sleep(2)
                    await client.disconnect()
                    await self.resetValues()
                    await self.updateStatus(False)
                    if not manual_dc:
                        embed = discord.Embed(
                            description=" 👋  Desconectando. Fim da fila.",
                            color=0x25d917)
                        await ctx.send(embed=embed)
                    manual_dc = False
        
        # Fim da fila geral
        else:
            if not client.is_playing() and not is_paused:
                await asyncio.sleep(2)
                await client.disconnect()
                await self.cancelPlaylist(ctx, fromdc=True)
                await self.resetValues()
                await self.updateStatus(False)
                if not manual_dc:
                    embed = discord.Embed(
                        description=' 👋  Desconectando. Fim da fila.',
                        color=0x25d917)
                    await ctx.send(embed=embed)
                manual_dc = False
    
    # Desconecta a bot do canal de voz e reseta todos os valores
    async def disconnect(self, ctx: Context):
        global manual_dc
        manual_dc = True
        client = get(self.bot.voice_clients, guild=ctx.guild)
        if client:
            await self.cancelPlaylist(self, ctx, fromdc=True)
            if client.is_playing() or is_paused:
                client.stop()
            await client.disconnect()
            await self.updateStatus(False)
            await self.resetValues()
        else:
            embed = discord.Embed(
            description=" ❌ Parar o que animal?",
            color=0xD81313)
            await ctx.send(embed=embed)

    # Reseta todas as variáveis de fluxo para o valor original
    async def resetValues(self):
        global song_queue, song_history, is_playlist, current_playlist, current_playlist_title, items_added, playlist_index, playlist_count, playlist_available, initial_playlist_message_shown, is_shuffling, shuffle_list, from_next, start_from
        
        song_queue.clear()
        is_playlist = False
        current_playlist = ''
        current_playlist_title = ''
        items_added = 0
        playlist_index = 0
        playlist_count = 0
        playlist_available = True
        initial_playlist_message_shown = False
        is_shuffling = 0
        shuffle_list = []
        from_next = False
        start_from = 0
        
        # O histórico é lido pelo arquivo, ou regenerado
        try:
            with open('cache/song_history.json', 'r', encoding='utf-8') as f:
                song_history = json.load(f)
        except FileNotFoundError:
            song_history = []
    
    # Atualiza o arquivo de histórico com o conteúdo atual na memória
    async def updateHistoryCache(self, new_data):
        try:
            with open('cache/song_history.json', 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4)
        except Exception as e:
            self.bot.logger.error(f'Erro ao atualizar cache de histórico: {e}')

    # Comando principal, para começar a tocar por URL ou queries do youtube
    @commands.hybrid_command(name='tocar', description='Toca músicas / playlists do youtube')
    @app_commands.describe(musica='Link da música ou playlist / Query de pesquisa')
    @app_commands.describe(randomizar='Ativa a randomização (opcional) (para playlists)')
    @app_commands.describe(historico='Toca uma música do histórico (pela ID)')
    @app_commands.choices(
        randomizar=[
            Choice(name='Sim', value=1)])
    @not_blacklisted()
    async def play(self, ctx: Context, musica:str=None, randomizar:Choice[int]=0, historico:int=0) -> None:
        global from_next, query_selected
        
        # Não utilizar o defer caso a função 'play' seja chamada pela 'play_next'
        if not from_next:
            await ctx.defer()
        from_next = False
        
        # Tentar se conectar no canal de voz do autor
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            client = get(self.bot.voice_clients, guild=ctx.guild)
            if client and client.is_connected():
                await client.move_to(channel)
            else:
                client = await channel.connect()
                await self.updateStatus(True)
        else:
            embed = discord.Embed(
                description=" ❌ Você está em um canal de voz inválido, ou eu não tenho permissões suficientes.",
                color=0xD81313)
            await ctx.send(embed=embed)
            return
        
        # Caso o usuário selecione uma música de histórico
        if historico != 0:
            musica = await self.pickFromHistory(historico)
            
            # Tratamento de erro
            if isinstance(musica, discord.Embed):
                await ctx.send(embed=musica)
                return

        # Realiza uma query de busca caso o usuário não tenha providenciado um link
        if not is_url(musica):
            query_data = await self.processYoutubeSearch(musica)
            
            # Tratamento de erro
            if isinstance(query_data, discord.Embed):
                await ctx.send(embed=query_data)
                return
            
            # Mostrar os resultados da busca para o usuário
            query_list = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                          in enumerate(query_data)]
            message = '\n'.join(query_list)
            embed = discord.Embed(
                title=f' 🌐  Resultados de busca para `"{musica}"`:',
                description=f"```{message}```",
                color=0x25d917)
            view = SearchSelector(ctx, self.bot)
            await ctx.send(embed=embed, view=view)
            
            # Aguardar por entrada do usuário
            while query_selected == 0:
                await asyncio.sleep(1)
            
            musica = query_data[query_selected - 1]['url']
            query_selected = 0
        
        # Verificar se a URL é uma playlist
        if "playlist?" in musica:
            song = await self.processYoutubePlaylist(ctx, playlist_index, musica, 
                                                     shuffle=(True if randomizar != 0 else False))
        else:
            song = await self.processYoutubeLink(musica)
        
        # Tratamento de erro
        if isinstance(song, discord.Embed):
            await ctx.send(embed=embed)
            return
        
        # Adicionar a fila
        song_queue.append(song)
        
        # Mostrar mensagem caso seja uma música individual
        if not is_playlist:
            embed = discord.Embed(
                title=" 🎵  Adicionada a fila:",
                description=f"```{song['title']}```",
                color=0x25d917)
            embed.set_thumbnail(url=song['thumb'])
            embed.set_footer(text=f"Requisitado por: {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        
        # Começar a tocar caso nada esteja tocando
        if not client.is_playing() and not is_paused:
            await self.play_next(ctx, client)

        # Enquanto estiver tocando, esperar
        while client.is_playing() or is_paused:
            await asyncio.sleep(1)
        
        # Quando a reprodução acabar, desligar
        await asyncio.sleep(2)  # Delay para não desconectar abruptamente
        await client.disconnect()
        await self.updateStatus(False)

    # Comando para manipular a fila de músicas (queue)
    @commands.hybrid_command(name='fila', description='Manipula a fila de músicas')
    @app_commands.describe(limpar='Limpa a fila de músicas')
    @app_commands.describe(limpar_id='Limpa uma música específica por ID (número)')
    @app_commands.describe(url='Mostrar URLs invés de títulos')
    @app_commands.choices(
        url=[Choice(name='Sim', value=1)],
        limpar=[Choice(name='Sim', value=1)])
    @not_blacklisted()
    async def queue(self, ctx: Context, limpar: Choice[int] = 0, limpar_id: int = 0, url: Choice[int] = 0) -> None:
        if not song_queue and limpar == 0:
            embed = discord.Embed(
                description=" ❌ A fila está vazia",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif not song_queue and limpar.value == 1:
            embed = discord.Embed(
                description=" ❌ A fila está vazia",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif song_queue and limpar == 0:
            if url == 0:
                queue_data = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                              in enumerate(song_queue)]
            else:
                queue_data = [f'{index + 1}. {item["url"]}' for index, item
                              in enumerate(song_queue)]
            message = '\n'.join(queue_data)
            embed = discord.Embed(
                title=" 📋  Fila atual:",
                description=f"```{message}```",
                color=0x25D917)
            await ctx.send(embed=embed)
        elif song_queue and limpar.value == 1 and limpar_id == 0:
            song_queue.clear()
            if not song_queue:
                embed = discord.Embed(
                    description=" ✅  Fila limpa!",
                    color=0x25D917)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=' ❌ Erro',
                    description="Por algum motivo a fila não limpou, e não, a dev não sabe o porque.",
                    color=0xD81313)
                await ctx.send(embed=embed)
        elif song_queue and limpar.value == 1 and limpar_id != 0:
            try:
                if limpar_id <= 0 or limpar_id > len(song_queue):
                    embed = discord.Embed(
                        title=' ❌ Erro',
                        description=f'``ID fora de alcance da fila``',
                        color=0xD81313)
                    await ctx.send(embed=embed)
                    return
                removed_song = song_queue[limpar_id - 1]
                song_queue.remove(removed_song)
                embed = discord.Embed(
                    title=' ✅  Removido da fila',
                    description=f"``{removed_song['title']}``",
                    color=0x25D917)
                embed.set_footer(text=f"Requisitado por: {ctx.author}", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)
            except ValueError:
                embed = discord.Embed(
                    title=' ❌ Erro',
                    description="Item não encontrado na fila.",
                    color=0xD81313)
                await ctx.send(embed=embed)

    # Comando para manipular o histórico de músicas
    @commands.hybrid_command(name='historico', description='Mostra ou manipula o histórico de músicas tocadas')
    @app_commands.describe(limpar='Limpa o histórico')
    @app_commands.describe(url='Mostrar URLs invés de títulos')
    @app_commands.choices(
        limpar=[Choice(name='Sim', value=1)],
        url=[Choice(name='Sim', value=1)])
    @not_blacklisted()
    async def history(self, ctx: Context, limpar: Choice[int] = 0, url: Choice[int] = 0) -> None:
        if not song_history and limpar == 0:
            embed = discord.Embed(
                description = " ❌ O histórico está vazio",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif not song_history and limpar.value == 1:
            embed = discord.Embed(
                description = " ❌ O histórico está vazio",
                color=0xd91313)
            await ctx.send(embed=embed)
        elif song_history and limpar == 0:
            if url == 0:
                history_data = [f'{index + 1}. [{item["duration"]}] - {item["title"]}' for index, item
                                in enumerate(song_history)]
            else:
                history_data = [f'{index + 1}. {item["url"]}' for index, item
                                in enumerate(song_history)]
            message = '\n'.join(history_data)
            embed = discord.Embed(
                title=" 🕒  Histórico:",
                description=f"```{message}```",
                color=0x25D917)
            await ctx.send(embed=embed)
        elif song_history and limpar.value == 1:
            song_history.clear()
            await self.updateHistoryCache(song_history)
            if not song_history:
                embed = discord.Embed(
                    description=" ✅  Histórico limpo!",
                    color=0x25D917)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=' ❌ Erro',
                    description="Por algum motivo o histórico não limpou, e não, a dev não sabe o porque.",
                    color=0xD81313)
                await ctx.send(embed=embed)

    # Comando para cancelar a reprodução de uma playlist em andamento
    @commands.hybrid_command(name='cancelarplaylist', description='Cancela a playlist em andamento')
    @not_blacklisted()
    async def cancelPlaylist(self, ctx: Context, fromdc=False):
        global playlist_available, is_playlist, current_playlist_title, initial_playlist_message_shown
        if playlist_available and not fromdc:
            embed = discord.Embed(
                description=' ❌  Nenhuma playlist ativa',
                color=0xd81313)
            await ctx.send(embed=embed)
            await self.resetValues()
        else:
            playlist_available = True
            is_playlist = False
            initial_playlist_message_shown = False
            if not fromdc:
                embed = discord.Embed(
                    title=" 🛑  Playlist cancelada:",
                    description=f"```{current_playlist_title}```",
                    color=0x25D917)
                await ctx.send(embed=embed)

    # Comando para mostrar a interface de usuário dos controles de multimídia
    @commands.hybrid_command(name='mostrarcontroles', description='Mostra os controles de multimídia')
    @not_blacklisted()
    async def showControls(self, ctx: Context):
        client = get(self.bot.voice_clients, guild=ctx.guild)
        if client and client.is_connected():
            if client.is_playing() or is_paused:
                view = MediaControls(ctx, self.bot)
                await ctx.send(view=view)
            else:
                embed = discord.Embed(
                    description=" ❌ Nenhuma mídia tocando",
                    color=0xD81313)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description=" ❌ Nenhuma mídia tocando",
                color=0xD81313)
            await ctx.send(embed=embed)

# Interface de usuário (botões) de controle multimídia
class MediaControls(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = Music(bot)
        self.id = 'MediaControls'
        self.is_persistent = True
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.green, custom_id='playbutton')
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.resume(self.ctx)
    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.secondary, custom_id='pausebutton')
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.pause(self.ctx)
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.blurple, custom_id='skipbutton')
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.skip(self.ctx)
    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger, custom_id='stopbutton')
    async def disconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.player.disconnect(self.ctx)

# Interface de usuário (botões) do seletor de busca
class SearchSelector(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.bot = bot
        self.player = Music(bot)
        self.id = 'SearchSelector'
        self.is_persistent = False
    
    @discord.ui.button(label="1️⃣", style=discord.ButtonStyle.secondary, custom_id='one')
    async def one(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 1
        await interaction.response.defer()
    @discord.ui.button(label="2️⃣", style=discord.ButtonStyle.secondary, custom_id='two')
    async def two(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 2
        await interaction.response.defer()
    @discord.ui.button(label="3️⃣", style=discord.ButtonStyle.secondary, custom_id='three')
    async def three(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 3
        await interaction.response.defer()
    @discord.ui.button(label="4️⃣", style=discord.ButtonStyle.secondary, custom_id='four')
    async def four(self, interaction: discord.Interaction, button: discord.ui.button):
        global query_selected
        query_selected = 4
        await interaction.response.defer()

# SETUP
async def setup(bot):
    await bot.add_cog(Music(bot))