# utils/message_utils.py - Funções para lidar com mensagens

import discord
import asyncio
import logging
from config import DEFAULT_TIMEOUT

logger = logging.getLogger("utils.message")

async def send_temp_message(channel, content, ephemeral=False, delete_after=DEFAULT_TIMEOUT, embed=None):
    """
    Envia uma mensagem temporária que será excluída após um tempo.
    
    Args:
        channel: Canal ou interação para enviar a mensagem
        content: Conteúdo da mensagem
        ephemeral: Se a mensagem deve ser visível apenas para o usuário
        delete_after: Tempo em segundos antes de excluir a mensagem
        embed: Embed opcional para enviar junto com a mensagem
    
    Returns:
        A mensagem enviada
    """
    try:
        if isinstance(channel, discord.Interaction):
            if channel.response.is_done():
                message = await channel.followup.send(content=content, ephemeral=ephemeral, embed=embed)
            else:
                await channel.response.defer(ephemeral=ephemeral)
                message = await channel.followup.send(content=content, embed=embed)
        else:
            message = await channel.send(content=content, embed=embed)
        
        if delete_after > 0:
            await asyncio.sleep(delete_after)
            try:
                await message.delete()
            except discord.NotFound:
                pass  # Mensagem já foi excluída
            except Exception as e:
                logger.error(f"Erro ao deletar mensagem: {e}")
        
        return message
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return None

async def create_embed(title, description, color=discord.Color.dark_purple(), footer=None, thumbnail=None):
    """
    Cria um embed com as configurações especificadas
    
    Args:
        title: Título do embed
        description: Descrição do embed
        color: Cor do embed
        footer: Texto do rodapé
        thumbnail: URL da miniatura
        
    Returns:
        Objeto Embed configurado
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    if footer:
        embed.set_footer(text=footer)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
        
    return embed