import discord
import os
import logging
import requests
from discord import app_commands
from collections import deque  
from registro import setup_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Configuração básica de logs
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# Adiciona um handler HTTP para enviar logs ao servidor Flask
class WebSocketHTTPHandler(logging.Handler):
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def emit(self, record):
        log_entry = self.format(record)
        try:
            requests.post(
                f"{self.url}/send_log", 
                json={"message": log_entry}, 
                timeout=0.5  # Timeout curto para não bloquear o bot
            )
        except Exception:
            pass  # Silenciosamente ignora erros para não afetar o bot

# Adicionar handler ao logger root
handler = WebSocketHTTPHandler("http://localhost:8765")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

class MeuPrimeiroBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.music_queue = deque()

    async def setup_hook(self):
        await setup_commands(self)
        await self.tree.sync()
        logging.info(f"✅ {len(self.tree.get_commands())} comandos sincronizados com sucesso!")

    async def on_ready(self):
        logging.info(f"🚀 O Bot {self.user} foi ligado com sucesso!")
        logging.info(f"📌 Comandos registrados: {[cmd.name for cmd in self.tree.get_commands()]}")

if __name__ == "__main__":
    bot = MeuPrimeiroBot()
    bot.run(TOKEN)