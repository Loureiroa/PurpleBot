async def setup_commands(bot):
    from commands_bot import register_bot_commands  # importando corretamente os comandos
    await register_bot_commands(bot)  # Registra os comandos

    from music.commands_music import register_music_commands # imoprtando corretamente os comandos
    await register_music_commands(bot) # Registra os comandos
    bot.loop_mode = "off"  # Modos: 'off', 'musica', 'fila'
