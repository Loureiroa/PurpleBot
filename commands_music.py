import discord
import yt_dlp as youtube_dl
import asyncio
from collections import deque
from discord import app_commands
from discord.app_commands import checks
from bot_logic import send_embed_now_playing

ffmpeg_path = "F:\\ffmpeg\\ffmpeg.exe"  # Caminho do FFmpeg

async def register_music_commands(bot):
    bot.music_queue = deque()
    bot.current_song_message = None
    bot.song_cache = {}
    bot.loop_current = False
    bot.current_song = None
    bot.last_played = deque(maxlen=5)  # Histórico de músicas

    async def get_song_info(url):
        if url in bot.song_cache:
            return bot.song_cache[url]

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'extract_flat': False,
            'default_search': 'auto',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url') or info['formats'][0]['url']
            title = info.get('title', 'Título desconhecido')
            song_data = {'url': audio_url, 'title': title}
            bot.song_cache[url] = song_data
            return song_data

    async def play_next(bot, voice_client):
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
            return

        song = bot.music_queue.popleft()
        bot.current_song = song
        bot.last_played.append(song['title'])
        song_info = await get_song_info(song['url'])

        def after_callback(error):
            if error:
                print(f"[ERRO AO TOCAR] {error}")
            else:
                print("[INFO] Música finalizada.")
            bot.loop.call_soon_threadsafe(asyncio.create_task, play_next(bot, voice_client))

        ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -b:a 192k'
        }

        source = discord.FFmpegPCMAudio(
            source=song_info['url'],
            executable=ffmpeg_path,
            **ffmpeg_options
        )

        voice_client.stop()
        voice_client.play(source, after=after_callback)

        if bot.current_song_message:
            try:
                await bot.current_song_message.delete()
            except discord.NotFound:
                pass

        bot.current_song_message = await send_embed_now_playing(song['interaction'].channel, song_info['title'])

    # COMANDO PLAY #
    
    @bot.tree.command(name="play", description="Toca uma música do YouTube")
    async def play(interaction: discord.Interaction, url: str):
        try:
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            channel = interaction.user.voice.channel

            if not interaction.guild.voice_client:
                await channel.connect()

            voice_client = interaction.guild.voice_client
            song_info = await get_song_info(url)

            bot.music_queue.append({
                'url': url,
                'title': song_info['title'],
                'interaction': interaction
            })

            if not voice_client.is_playing():
                await play_next(bot, voice_client)

            try:
                response = await interaction.followup.send(f"🎵 **{song_info['title']}** adicionada à fila!")
                await asyncio.sleep(2)
                await response.delete()
            except discord.NotFound:
                pass

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)

    # COMANDO PAUSE #
    
    @bot.tree.command(name="pause", description="Pausa a música atual")
    async def pause(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            try:
                message = await interaction.followup.send("⏸️ Música pausada!")
                await asyncio.sleep(3)
                await message.delete()
            except discord.NotFound:
                pass
        else:
            try:
                message = await interaction.followup.send("❌ Nenhuma música tocando.")
                await asyncio.sleep(2)
                await message.delete()
            except discord.NotFound:
                pass

    # COMANDO RESUME #
    
    @bot.tree.command(name="resume", description="Continua a música pausada")
    async def resume(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            try:
                message = await interaction.followup.send("▶️ Música retomada!")
                await asyncio.sleep(3)
                await message.delete()
            except discord.NotFound:
                pass
        else:
            try:
                message = await interaction.followup.send("❌ Nenhuma música pausada.")
                await asyncio.sleep(2)
                await message.delete()
            except discord.NotFound:
                pass

    # COMANDO SKIP #
    
    @bot.tree.command(name="skip", description="Pula a música atual")
    async def skip(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        await interaction.response.defer(ephemeral=False)

        if voice_client and voice_client.is_playing():
            voice_client.stop()
            message = await interaction.followup.send("⏭️ Música pulada!")
        else:
            message = await interaction.followup.send("❌ Nenhuma música tocando.", ephemeral=True)

        await asyncio.sleep(3)
        try:
            await message.delete()
        except discord.NotFound:
            pass

    # COMANDO LOOP #

    # Comando principal
    @bot.tree.command(name="loop", description="Define o modo de repetição: off, musica ou fila")
    @app_commands.describe(modo="Modo de repetição desejado (off, musica, fila)")
    async def loop(interaction: discord.Interaction, modo: str):
        await interaction.response.defer(ephemeral=True)
        modo = modo.lower()
        if modo not in ["off", "musica", "fila"]:
            await interaction.followup.send("❌ Modo inválido. Use: `off`, `musica` ou `fila`.")
            return

        bot.loop_mode = modo
        emoji = {"off": "❎", "musica": "🔂", "fila": "🔁"}[modo]
        message = await interaction.followup.send(f"{emoji} Modo de repetição definido para: **{modo}**")
        await asyncio.sleep(3)
        await message.delete()
        
        
     # Função de autocomplete
    @loop.autocomplete('modo')
    async def autocomplete_loop_modo(interaction: discord.Interaction, current: str):
        modos = ["off", "musica", "fila"]
        return [
            app_commands.Choice(name=modo, value=modo)
            for modo in modos
            if current.lower() in modo
        ]

     # COMANDO QUEUE #
     
    @bot.tree.command(name="queue", description="Mostra a fila de músicas")
    async def queue(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not bot.music_queue:
            msg = await interaction.followup.send("🎵 A fila está vazia!", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
            return

        queue_text = "\n".join(f"{i+1}. {song['title']}" for i, song in enumerate(bot.music_queue, 1))
        loop_display = {
            "off": "❎ Nenhum",
            "musica": "🔂 Música atual",
            "fila": "🔁 Toda a fila"
        }[bot.loop_mode]

        response = await interaction.followup.send(f"💿 **Fila:**\n{queue_text}\n\n🔁 **Loop atual:** {loop_display}")
        await asyncio.sleep(10)
        try:
            await response.delete()
        except discord.NotFound:
            pass
        
    # COMANDO ÚLTIMAS TOCADAS #
       
    @bot.tree.command(name="lastplayed", description="Mostra as últimas 5 músicas tocadas")
    async def lastplayed(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not bot.last_played:
            message = await interaction.followup.send("🔇 Nenhuma música foi tocada ainda.", ephemeral=True)
            await asyncio.sleep(3)
            await message.delete()
            return

        history_text = "\n".join(f"{i+1}. {title}" for i, title in enumerate(reversed(bot.last_played)))
        message = await interaction.followup.send(f"📜 **Últimas tocadas:**\n{history_text}")
        await asyncio.sleep(10)
        try:
            await message.delete()
        except discord.NotFound:
            pass

    # COMANDO REMOVER DA FILA #
    
    @bot.tree.command(name="remove", description="Remove uma música da fila pela posição")
    @app_commands.describe(posicao="A posição da música na fila (1, 2, 3, ...)")
    async def remove(interaction: discord.Interaction, posicao: int):
        await interaction.response.defer(ephemeral=True)

        if posicao < 1 or posicao > len(bot.music_queue):
            message = await interaction.followup.send("❌ Posição inválida na fila.")
            await asyncio.sleep(2)
            await message.delete()
            return

        removida = bot.music_queue[posicao - 1]['title']
        del bot.music_queue[posicao - 1]

        message = await interaction.followup.send(f"🗑️ Música removida da fila: **{removida}**")
        await asyncio.sleep(3)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        
    @remove.autocomplete('posicao') # AUTOCOMPLETE
    async def autocomplete_remove_posicao(interaction: discord.Interaction, current: str):
        suggestions = []
        for i, song in enumerate(bot.music_queue, 1):
            if current.isdigit() and not str(i).startswith(current):
                continue
            title = song["title"]
            suggestions.append(app_commands.Choice(name=f"{i}. {title[:80]}", value=i))
            if len(suggestions) >= 25:
                break
        return suggestions


    # COMANDO STOP #
    
    @checks.has_permissions(administrator=True)
    @bot.tree.command(name="stop", description="Para a música atual e limpa a fila")
    async def stop(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        voice_client = interaction.guild.voice_client

        # Para a música atual
        if voice_client and voice_client.is_playing():
            voice_client.stop()

        # Limpa a fila, a música atual e a mensagem
        bot.music_queue.clear()
        bot.current_song = None

        if bot.current_song_message:
            try:
                await bot.current_song_message.delete()
            except discord.NotFound:
                pass
            bot.current_song_message = None

        message = await interaction.followup.send("🛑 Música parada e fila limpa!")
        await asyncio.sleep(3)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        # COMANDO SHUFFLE #
    
    @bot.tree.command(name="shuffle", description="Embaralha a fila de músicas")
    async def shuffle(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        if not bot.music_queue or len(bot.music_queue) < 2:
            message = await interaction.followup.send("❌ Não há músicas suficientes na fila para embaralhar.", ephemeral=True)
            await asyncio.sleep(3)
            await message.delete()
            return
        
        # Convertendo para lista para embaralhar e depois de volta para deque
        queue_list = list(bot.music_queue)
        import random
        random.shuffle(queue_list)
        bot.music_queue = deque(queue_list)
        
        # Exibe primeiras 5 músicas da fila embaralhada (ou menos se a fila for menor)
        preview_size = min(5, len(bot.music_queue))
        preview = "\n".join(f"{i+1}. {song['title']}" for i, song in enumerate(list(bot.music_queue)[:preview_size]))
        
        message = await interaction.followup.send(f"🔀 **Fila embaralhada!**\nPrimeiras {preview_size} músicas:\n{preview}")
        await asyncio.sleep(5)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        
        
    # COMANDO NEXTSONG #

    @bot.tree.command(name="nextsong", description="Mostra a próxima música na fila")
    async def nextsong(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        
        if not bot.music_queue:
            message = await interaction.followup.send("❌ Não há músicas na fila.", ephemeral=True)
            await asyncio.sleep(3)
            await message.delete()
            return
        
        # Obtém a próxima música
        next_song = bot.music_queue[0]['title']
        
        # Verifica se há música atual tocando
        current_status = ""
        if bot.current_song:
            current_status = f"🎵 **Tocando agora:** {bot.current_song['title']}\n"
        
        message = await interaction.followup.send(
            f"{current_status}🔜 **Próxima música:** {next_song}"
        )
        
        # A mensagem ficará visível por 7 segundos
        await asyncio.sleep(7)
        try:
            await message.delete()
        except discord.NotFound:
            pass