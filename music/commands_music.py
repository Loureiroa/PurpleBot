# music/commands.py - Comandos relacionados a música

import discord
from discord import app_commands
import asyncio
import random
import logging
from collections import deque
from utils.message_utils import send_temp_message
from utils.audio_utils import get_song_info
from music.playback import MusicPlayer
from config import QUEUE_DISPLAY_TIME

logger = logging.getLogger("music.commands")
music_player = None  # Será inicializado no registro dos comandos

async def register_music_commands(bot):
    global music_player
    music_player = MusicPlayer(bot)
    bot.song_cache = {}  # Cache global de músicas

    # Registra evento para limpeza quando o bot é desconectado
    @bot.event
    async def on_voice_state_update(member, before, after):
        # Limpar recursos quando o bot é desconectado
        if member == bot.user and before.channel and not after.channel:
            # Bot foi desconectado
            music_player.clean_up(before.channel.guild.id)
        
        # Auto-desconectar quando ficar sozinho
        elif before.channel and bot.user in before.channel.members:
            # Verificar se o bot está sozinho no canal
            members = [m for m in before.channel.members if not m.bot]
            if not members:
                voice_client = member.guild.voice_client
                if voice_client:
                    await voice_client.disconnect()
                    music_player.clean_up(member.guild.id)

    # COMANDO PLAY
    @bot.tree.command(name="play", description="Toca uma música do YouTube (URL ou nome)")
    @app_commands.describe(pesquisa="URL ou nome da música para tocar")
    async def play(interaction: discord.Interaction, pesquisa: str):
        try:
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            channel = interaction.user.voice.channel

            if not interaction.guild.voice_client:
                await channel.connect()

            voice_client = interaction.guild.voice_client
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            # Determina se é URL ou termo de pesquisa
            is_url = pesquisa.startswith('http://') or pesquisa.startswith('https://')
            search_text = "Buscando..." if not is_url else "Carregando..."
            
            progress_msg = await interaction.followup.send(f"🔍 {search_text}", ephemeral=True)
            
            try:
                song_info = await get_song_info(pesquisa, bot.song_cache)
                
                # Atualiza a mensagem enquanto processa
                await progress_msg.edit(content=f"✅ Encontrado: **{song_info['title']}**")
                
                guild_player.music_queue.append({
                    'url': pesquisa,  # Mantém a pesquisa original para caso de loop
                    'title': song_info['title'],
                    'interaction': interaction,
                    'thumbnail': song_info.get('thumbnail', '')
                })

                if not voice_client.is_playing():
                    await guild_player.play_next(voice_client)

                await asyncio.sleep(1)
                await progress_msg.edit(content=f"🎵 **{song_info['title']}** adicionada à fila!")
                await asyncio.sleep(2)
                await progress_msg.delete()

            except Exception as e:
                logger.error(f"Erro no comando play: {e}")
                await progress_msg.edit(content=f"❌ Erro ao buscar música: {e}")
                await asyncio.sleep(3)
                await progress_msg.delete()

        except Exception as e:
            logger.error(f"Erro crítico no comando play: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ocorreu um erro: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Ocorreu um erro: {e}", ephemeral=True)

    # COMANDO PAUSE
    @bot.tree.command(name="pause", description="Pausa a música atual")
    async def pause(interaction: discord.Interaction):
        try:
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.is_playing():
                voice_client.pause()
                await send_temp_message(interaction, "⏸️ Música pausada!", ephemeral=False)
            else:
                await send_temp_message(interaction, "❌ Nenhuma música tocando.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando pause: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)

    # COMANDO RESUME
    @bot.tree.command(name="resume", description="Continua a música pausada")
    async def resume(interaction: discord.Interaction):
        try:
            voice_client = interaction.guild.voice_client
            if voice_client and voice_client.is_paused():
                voice_client.resume()
                await send_temp_message(interaction, "▶️ Música retomada!", ephemeral=False)
            else:
                await send_temp_message(interaction, "❌ Nenhuma música pausada.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando resume: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)

    # SKIP 
    @bot.tree.command(name="skip", description="Pula a música atual")
    async def skip(interaction: discord.Interaction):
        try:
            voice_client = interaction.guild.voice_client
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if voice_client and voice_client.is_playing():
                # Verifica se a fila está vazia antes de pular
                if not guild_player.music_queue and guild_player.loop_mode == "off":
                    # Se a fila estiver vazia, guarde uma referência à mensagem atual antes de pular
                    current_message = guild_player.current_song_message
                    
                    # Para a reprodução (isso vai disparar o callback que chama play_next)
                    voice_client.stop()
                    
                    await send_temp_message(interaction, "⏭️ Música pulada! Não há mais músicas na fila.", ephemeral=False)
                else:
                    # Se há mais músicas na fila ou modo de loop ativo, apenas pule
                    voice_client.stop()
                    await send_temp_message(interaction, "⏭️ Música pulada!", ephemeral=False)
            else:
                await send_temp_message(interaction, "❌ Nenhuma música tocando.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando skip: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)

    # COMANDO LOOP
    @bot.tree.command(name="loop", description="Define o modo de repetição: off, musica ou fila")
    @app_commands.describe(modo="Modo de repetição desejado (off, musica, fila)")
    async def loop(interaction: discord.Interaction, modo: str):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            modo = modo.lower()
            if modo not in ["off", "musica", "fila"]:
                await send_temp_message(interaction, "❌ Modo inválido. Use: `off`, `musica` ou `fila`.", ephemeral=True)
                return

            guild_player.loop_mode = modo
            emoji = {"off": "❎", "musica": "🔂", "fila": "🔁"}[modo]
            await send_temp_message(interaction, f"{emoji} Modo de repetição definido para: **{modo}**", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando loop: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)
        
    # Função de autocomplete para o loop
    @loop.autocomplete('modo')
    async def autocomplete_loop_modo(interaction: discord.Interaction, current: str):
        modos = ["off", "musica", "fila"]
        return [
            app_commands.Choice(name=modo, value=modo)
            for modo in modos
            if current.lower() in modo
        ]

    # COMANDO QUEUE
    @bot.tree.command(name="queue", description="Mostra a fila de músicas")
    async def queue(interaction: discord.Interaction):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if not guild_player.music_queue:
                await send_temp_message(interaction, "🎵 A fila está vazia!", ephemeral=True)
                return

            queue_text = "\n".join(f"{i+1}. {song['title']}" for i, song in enumerate(guild_player.music_queue))
            loop_display = {
                "off": "❎ Nenhum",
                "musica": "🔂 Música atual",
                "fila": "🔁 Toda a fila"
            }[guild_player.loop_mode]

            await send_temp_message(
                interaction, 
                f"💿 **Fila:**\n{queue_text}\n\n🔁 **Loop atual:** {loop_display}", 
                ephemeral=False, 
                delete_after=QUEUE_DISPLAY_TIME
            )
        except Exception as e:
            logger.error(f"Erro no comando queue: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)
        
    # COMANDO LASTPLAYED
    @bot.tree.command(name="lastplayed", description="Mostra as últimas 5 músicas tocadas")
    async def lastplayed(interaction: discord.Interaction):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if not guild_player.last_played:
                await send_temp_message(interaction, "🔇 Nenhuma música foi tocada ainda.", ephemeral=True)
                return

            history_text = "\n".join(f"{i+1}. {title}" for i, title in enumerate(reversed(guild_player.last_played)))
            await send_temp_message(
                interaction, 
                f"📜 **Últimas tocadas:**\n{history_text}", 
                ephemeral=False,
                delete_after=QUEUE_DISPLAY_TIME
            )
        except Exception as e:
            logger.error(f"Erro no comando lastplayed: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)

    # COMANDO REMOVE
    @bot.tree.command(name="remove", description="Remove uma música da fila pela posição")
    @app_commands.describe(posicao="A posição da música na fila (1, 2, 3, ...)")
    async def remove(interaction: discord.Interaction, posicao: int):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if posicao < 1 or posicao > len(guild_player.music_queue):
                await send_temp_message(interaction, "❌ Posição inválida na fila.", ephemeral=True)
                return

            removida = guild_player.music_queue[posicao - 1]['title']
            del guild_player.music_queue[posicao - 1]

            await send_temp_message(interaction, f"🗑️ Música removida da fila: **{removida}**", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando remove: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)
        
    @remove.autocomplete('posicao')
    async def autocomplete_remove_posicao(interaction: discord.Interaction, current: str):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            suggestions = []
            
            for i, song in enumerate(guild_player.music_queue, 1):
                if current.isdigit() and not str(i).startswith(current):
                    continue
                title = song["title"]
                suggestions.append(app_commands.Choice(name=f"{i}. {title[:80]}", value=i))
                if len(suggestions) >= 25:
                    break
            return suggestions
        except Exception:
            return []

    # COMANDO STOP
    @app_commands.checks.has_permissions(administrator=True)
    @bot.tree.command(name="stop", description="Para a música atual e limpa a fila")
    async def stop(interaction: discord.Interaction):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            voice_client = interaction.guild.voice_client

            # Para a música atual
            if voice_client and voice_client.is_playing():
                voice_client.stop()

            # Limpa a fila, a música atual e a mensagem
            guild_player.music_queue.clear()
            guild_player.current_song = None

            if guild_player.current_song_message:
                try:
                    await guild_player.current_song_message.delete()
                except discord.NotFound:
                    pass
                except Exception as e:
                    logger.error(f"Erro ao deletar mensagem: {e}")
                guild_player.current_song_message = None

            await send_temp_message(interaction, "🛑 Música parada e fila limpa!", ephemeral=False)
        except Exception as e:
            logger.error(f"Erro no comando stop: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)
            
    # COMANDO SHUFFLE
    @bot.tree.command(name="shuffle", description="Embaralha a fila de músicas")
    async def shuffle(interaction: discord.Interaction):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if not guild_player.music_queue or len(guild_player.music_queue) < 2:
                await send_temp_message(interaction, "❌ Não há músicas suficientes na fila para embaralhar.", ephemeral=True)
                return
            
            # Convertendo para lista para embaralhar e depois de volta para deque
            queue_list = list(guild_player.music_queue)
            random.shuffle(queue_list)
            guild_player.music_queue = deque(queue_list)
            
            # Exibe primeiras 5 músicas da fila embaralhada (ou menos se a fila for menor)
            preview_size = min(5, len(guild_player.music_queue))
            preview = "\n".join(f"{i+1}. {song['title']}" for i, song in enumerate(list(guild_player.music_queue)[:preview_size]))
            
            await send_temp_message(
                interaction, 
                f"🔀 **Fila embaralhada!**\nPrimeiras {preview_size} músicas:\n{preview}",
                ephemeral=False,
                delete_after=5
            )
        except Exception as e:
            logger.error(f"Erro no comando shuffle: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)
            
    # COMANDO NEXTSONG
    @bot.tree.command(name="nextsong", description="Mostra a próxima música na fila")
    async def nextsong(interaction: discord.Interaction):
        try:
            guild_player = music_player.get_guild_player(interaction.guild.id)
            
            if not guild_player.music_queue:
                await send_temp_message(interaction, "❌ Não há músicas na fila.", ephemeral=True)
                return
            
            # Obtém a próxima música
            next_song = guild_player.music_queue[0]['title']
            
            # Verifica se há música atual tocando
            current_status = ""
            if guild_player.current_song:
                current_status = f"🎵 **Tocando agora:** {guild_player.current_song['title']}\n"
            
            await send_temp_message(
                interaction,
                f"{current_status}🔜 **Próxima música:** {next_song}",
                ephemeral=False,
                delete_after=7
            )
        except Exception as e:
            logger.error(f"Erro no comando nextsong: {e}")
            await send_temp_message(interaction, f"❌ Erro: {e}", ephemeral=True)