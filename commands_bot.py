import discord
import random
import asyncio
from discord import app_commands
from bot_logic import leave_voice, clear_channel

async def register_bot_commands(bot):
    
    # ROLAR DADO #
    @bot.tree.command(name="rolar_dado", description="Rola um dado de 1 a 6")
    async def rolar_dado(interaction: discord.Interaction):
        resultado = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Você rolou um {resultado}!")
        
    # CLEAR CHAT #
    @bot.tree.command(name="clear", description="Limpa as mensagens do chat")
    async def clear(interaction: discord.Interaction, amount: int = 10):
        await clear_channel(interaction, bot, amount)
    
    # LEAVE BOT #
    @bot.tree.command(name="leave", description="Desconecta o bot do canal de voz")
    async def leave(interaction: discord.Interaction):
        await leave_voice(interaction)

    ## SYNC COMANDO COM PERMISSÃO ##
    @bot.tree.command(name="sync", description="Sincroniza os comandos com a API do Discord")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)  # Evita erro de interação expirada
        try:
            synced = await bot.tree.sync(guild=interaction.guild)
            sync_message = await interaction.followup.send(
                f"✅ {len(synced)} comandos sincronizados com sucesso!",
                ephemeral=True
            )

            await asyncio.sleep(2)
            try:
                await sync_message.delete()
            except discord.NotFound:
                pass  # A mensagem já foi deletada
            except Exception as e:
                print(f"[ERRO AO DELETAR MENSAGEM /sync]: {e}")

        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao sincronizar comandos: {e}",
                ephemeral=True
            )

