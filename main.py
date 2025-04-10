import discord
import os
from discord import app_commands
from collections import deque  
from registro import setup_commands
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do .env
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class MeuPrimeiroBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.music_queue = deque()  # Fila para as músicas

    async def setup_hook(self):
        await setup_commands(self)
        await self.tree.sync()
        print(f"✅ {len(self.tree.get_commands())} comandos sincronizados com sucesso!")

    async def on_ready(self):
        print(f"🚀 O Bot {self.user} foi ligado com sucesso!")
        print("📌 Comandos registrados:", [cmd.name for cmd in self.tree.get_commands()])

bot = MeuPrimeiroBot()

bot.run(TOKEN)
