# utils/audio_utils.py - Funções relacionadas a áudio

import discord
import logging
from config import FFMPEG_PATH, FFMPEG_OPTIONS
import yt_dlp as youtube_dl

logger = logging.getLogger("utils.audio")

async def get_song_info(query, cache):
    """
    Obtém informações sobre uma música do YouTube.
    
    Args:
        query: URL ou termo de busca
        cache: Dicionário de cache para armazenar resultados
    
    Returns:
        Dicionário com informações da música
    """
    if query in cache:
        return cache[query]

    is_url = query.startswith('http://') or query.startswith('https://')

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True if is_url else False,
        'default_search': 'ytsearch',
        'nowarning': True,
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            if not is_url:
                query = f"ytsearch1:{query}"
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            audio_url = info.get('url') or info['formats'][0]['url']
            title = info.get('title', 'Título desconhecido')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)

            song_data = {
                'url': audio_url,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration
            }

            cache[query] = song_data
            return song_data
    except Exception as e:
        logger.error(f"Erro ao buscar música: {e}")
        raise RuntimeError(f"Erro ao buscar informações da música: {e}")

def create_audio_source(song_info):
    """Cria e retorna um FFmpegPCMAudio com configurações padrão"""
    return discord.FFmpegPCMAudio(
        source=song_info['url'],
        executable=FFMPEG_PATH,
        **FFMPEG_OPTIONS
    )

def check_ffmpeg_installation():
    """Verifica se o FFmpeg está instalado e acessível"""
    import subprocess
    
    try:
        result = subprocess.run([FFMPEG_PATH, "-version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Erro ao verificar FFmpeg: {e}")
        return False