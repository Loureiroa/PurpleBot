# music/playback.py - Funcionalidades de reprodução de música 

import discord
import asyncio
import logging
from collections import deque
from utils.audio_utils import get_song_info, create_audio_source
from bot_logic import send_embed_now_playing

logger = logging.getLogger("music.playback")


class MusicPlayer:
    """Gerenciador de reprodução de música para um servidor"""
    
    def __init__(self, bot):
        self.bot = bot
        self.guild_players = {}  # Armazena players por servidor
    
    def get_guild_player(self, guild_id):
        """Obtém ou cria um player para o servidor"""
        if guild_id not in self.guild_players:
            self.guild_players[guild_id] = GuildPlayer(self.bot)
        return self.guild_players[guild_id]
        
    def clean_up(self, guild_id):
        """Remove player de um servidor quando o bot se desconecta"""
        if guild_id in self.guild_players:
            del self.guild_players[guild_id]

class GuildPlayer:
    """Player de música para um servidor específico"""
    
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = deque()
        self.current_song = None
        self.current_song_message = None
        self.loop_mode = "off"  # "off", "musica", "fila"
        self.last_played = deque(maxlen=5)  # Histórico limitado
        self.inactive_timer = None  # Timer para desconectar após inatividade
    
    async def play_next(self, voice_client):
        """Toca a próxima música da fila"""
        from bot_logic import send_embed_now_playing
        
        # Implementa lógica de loop
        if self.loop_mode == "musica" and self.current_song:
            self.music_queue.appendleft(self.current_song)
        elif self.loop_mode == "fila" and self.current_song:
            self.music_queue.append(self.current_song)

        # Se não há mais músicas na fila, limpa a mensagem atual e sai
        if not self.music_queue:
            self.current_song = None
            # Apaga a mensagem "Tocando agora" quando a fila acabar
            if self.current_song_message:
                try:
                    logger.info("Nenhuma música na fila. Removendo mensagem 'Tocando agora'.")
                    await self.current_song_message.delete()
                except discord.NotFound:
                    logger.info("Mensagem já foi removida.")
                    pass
                except Exception as e:
                    logger.error(f"Erro ao deletar mensagem 'Tocando agora': {e}")
                finally:
                    self.current_song_message = None
            return

        song = self.music_queue.popleft()
        self.current_song = song
        self.last_played.append(song['title'])

        try:
            song_info = await get_song_info(song['url'], self.bot.song_cache)

            # Configurar callback para quando a música terminar
            def after_callback(error):
                if error:
                    logger.error(f"Erro ao tocar música: {error}")
                    if not self.bot.loop.call_soon_threadsafe(asyncio.create_task,
                        self.handle_playback_error(voice_client, error, song)):
                        self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(voice_client))
                else:
                    logger.info("Música finalizada.")
                    self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(voice_client))

            # Se já existe uma mensagem, edite-a. Caso contrário, crie uma nova.
            if self.current_song_message:
                try:
                    # Criar um novo embed
                    embed = discord.Embed(
                        title="🎶 Tocando agora",
                        description=song_info['title'],
                        color=discord.Color.dark_purple()
                    )
                    embed.set_footer(text="Use /pause, /resume, /skip ou /stop para controlar")
                    
                    # Editar a mensagem existente em vez de criar uma nova
                    await self.current_song_message.edit(embed=embed)
                    
                    # Garanta que as reações estejam presentes
                    if not self.current_song_message.reactions:
                        await self.current_song_message.add_reaction("⏯️")
                        await self.current_song_message.add_reaction("⏩")
                except discord.NotFound:
                    # Se a mensagem não for encontrada, envie uma nova
                    self.current_song_message = await send_embed_now_playing(song['interaction'].channel, song_info['title'])
                except Exception as e:
                    logger.error(f"Erro ao editar mensagem: {e}")
                    # Se editar falhar, tente criar uma nova
                    self.current_song_message = await send_embed_now_playing(song['interaction'].channel, song_info['title'])
            else:
                # Se não houver mensagem atual, crie uma nova
                self.current_song_message = await send_embed_now_playing(song['interaction'].channel, song_info['title'])

            source = create_audio_source(song_info)

            voice_client.stop()
            voice_client.play(source, after=after_callback)

        except Exception as e:
            logger.error(f"Erro grave ao tocar música: {e}")
            await self.play_next(voice_client)
        
    async def handle_playback_error(self, voice_client, error, song):
        """Manipula erros de reprodução e tenta reconectar"""
        if isinstance(error, discord.ClientException) or "Error from FFmpeg" in str(error):
            logger.warning(f"Erro de rede, tentando reproduzir novamente: {error}")
            await asyncio.sleep(2)
            try:
                song_info = await get_song_info(song['url'], self.bot.song_cache)
                source = create_audio_source(song_info)

                voice_client.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self.play_next(voice_client) if not e else self.handle_playback_error(voice_client, e, song)
                ))
                return True
            except Exception as e:
                logger.error(f"Tentativa de reprodução falhou: {e}")
                return False
        return False