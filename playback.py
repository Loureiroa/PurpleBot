import discord
import asyncio
import yt_dlp as youtube_dl

ffmpeg_path = "F:\\ffmpeg\\ffmpeg.exe"

# Configurações globais do FFmpeg
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -b:a 128k'
}

async def get_song_info(query, bot):
    if query in bot.song_cache:
        return bot.song_cache[query]

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

            bot.song_cache[query] = song_data
            return song_data
    except Exception as e:
        print(f"[ERRO AO BUSCAR] {e}")
        raise e

def create_audio_source(song_info):
    """Cria e retorna um FFmpegPCMAudio com configurações padrão"""
    return discord.FFmpegPCMAudio(
        source=song_info['url'],
        executable=ffmpeg_path,
        **FFMPEG_OPTIONS
    )

async def handle_playback_error(bot, voice_client, error, song):
    from playback import play_next  # evitar import circular
    if isinstance(error, discord.ClientException) or "Error from FFmpeg" in str(error):
        print(f"[ERRO DE REDE] Tentando reproduzir novamente: {error}")
        await asyncio.sleep(2)
        try:
            song_info = await get_song_info(song['url'], bot)
            source = create_audio_source(song_info)

            voice_client.play(source, after=lambda e: bot.loop.call_soon_threadsafe(
                asyncio.create_task,
                play_next(bot, voice_client) if not e else handle_playback_error(bot, voice_client, e, song)
            ))
            return True
        except Exception as e:
            print(f"[TENTATIVA FALHOU] {e}")
            return False
    return False

async def play_next(bot, voice_client):
    from bot_logic import send_embed_now_playing
    from playback import get_song_info, handle_playback_error

    if bot.loop_mode == "musica" and bot.current_song:
        bot.music_queue.appendleft(bot.current_song)
    elif bot.loop_mode == "fila" and bot.current_song:
        bot.music_queue.append(bot.current_song)

    if not bot.music_queue:
        bot.current_song = None
        if bot.current_song_message:
            try:
                await bot.current_song_message.delete()
            except discord.NotFound:
                pass
            bot.current_song_message = None
        return

    song = bot.music_queue.popleft()
    bot.current_song = song
    bot.last_played.append(song['title'])

    try:
        song_info = await get_song_info(song['url'], bot)

        def after_callback(error):
            if error:
                print(f"[ERRO AO TOCAR] {error}")
                if not bot.loop.call_soon_threadsafe(asyncio.create_task,
                    handle_playback_error(bot, voice_client, error, song)):
                    bot.loop.call_soon_threadsafe(asyncio.create_task, play_next(bot, voice_client))
            else:
                print("[INFO] Música finalizada.")
                bot.loop.call_soon_threadsafe(asyncio.create_task, play_next(bot, voice_client))

        source = create_audio_source(song_info)

        voice_client.stop()
        voice_client.play(source, after=after_callback)

        if bot.current_song_message:
            try:
                await bot.current_song_message.delete()
            except discord.NotFound:
                pass

        bot.current_song_message = await send_embed_now_playing(song['interaction'].channel, song_info['title'])

    except Exception as e:
        print(f"[ERRO GRAVE] Não foi possível tocar a música: {e}")
        await play_next(bot, voice_client)