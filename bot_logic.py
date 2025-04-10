import discord
import asyncio
from discord import app_commands
from discord.app_commands import checks

## RECONEXAO AUTO ##
async def reconnect_voice(client, channel):
    """ Tenta reconectar o bot automaticamente ao canal de voz """
    while not client.is_closed():
        try:
            await channel.connect()
            break
        except discord.errors.ConnectionClosed:
            print("Conexão fechada. Tentando reconectar...")
            await asyncio.sleep(5)

## DEIXAR CANAL ##
@checks.has_permissions(administrator=True)
async def leave_voice(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.followup.send("🔌 Bot desconectado do canal de voz.", ephemeral=False)
    else:
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.followup.send("❌ O bot não está em um canal de voz.", ephemeral=True)

    await asyncio.sleep(2)
    try:
        await msg.delete()
    except discord.NotFound:
        pass  # A mensagem já foi deletada ou não existe

## LIMPAR CHANNEL ##

#  DESCRIÇÃO #
@app_commands.describe(amount="Quantidade de mensagens a apagar (padrão: 10, máximo: 50)")
@checks.has_permissions(administrator=True)
async def clear_channel(interaction: discord.Interaction, bot, amount: int = 10):
    amount = min(amount, 50)  # Garante que não ultrapasse 50

    await interaction.response.defer(ephemeral=True)

    try:
        # Informa se o valor padrão foi usado
        if amount == 10:
            aviso = await interaction.followup.send("ℹ️ Nenhuma quantidade especificada. Usando o padrão: **10 mensagens**.", ephemeral=True)
            await asyncio.sleep(2)
            await aviso.delete()

        deleted_messages = await interaction.channel.purge(limit=amount)

        confirmation_message = await interaction.followup.send(
            f"🧹 {len(deleted_messages)} mensagens apagadas!", ephemeral=True
        )
        await asyncio.sleep(2)
        await confirmation_message.delete()

    except discord.errors.Forbidden:
        await interaction.followup.send("❌ Eu não tenho permissão para apagar mensagens!", ephemeral=True)

    except discord.errors.HTTPException:
        await interaction.followup.send("❌ Algo deu errado ao tentar apagar as mensagens.", ephemeral=True)


## MENSAGEM DE MÚSICA ATUAL COM EMBED E REAÇÕES ##

async def send_embed_now_playing(channel, song_title):
    embed = discord.Embed(
        title="🎶 Tocando agora",
        description=song_title,
        color=discord.Color.dark_purple()
    )
    embed.set_footer(text="Use /pause, /resume, /skip ou /stop para controlar")
    message = await channel.send(embed=embed)
    await message.add_reaction("⏯️")  # play/pause
    await message.add_reaction("⏩")  # skip
    return message
