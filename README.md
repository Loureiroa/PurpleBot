# PurpleBot 🎵

![PURPLE BOT](https://github.com/user-attachments/assets/a3b885e2-b867-4aa7-a4fe-927c9777f246)

PurpleBot é um bot de música que desenvolvi para meu servidor do Discord. Ele reproduz músicas a partir de URLs do YouTube ou termos de busca, oferecendo uma interface amigável, responsiva e interativa para os usuários.


# Características

## 🎵 Comandos de Música

- /play: Toca música a partir de uma URL do YouTube ou termo de busca
- /pause: Pausa a reprodução atual
- /resume: Continua a reprodução pausada
- /skip: Pula a música atual
- /loop: Define o modo de repetição (off, musica, fila)
- /queue: Exibe a fila de músicas
- /lastplayed: Mostra as últimas 5 músicas tocadas
- /remove: Remove uma música específica da fila
- /stop: Para a reprodução e limpa a fila (apenas Admin)
- /shuffle: Embaralha a fila de músicas
- /nextsong: Mostra a próxima música da fila


## 🤖 Comandos de Utilidade

- /rolar_dado: Rola um dado aleatório de 1 a 6
- /clear: Limpa mensagens do chat (apenas Admin)
-/leave: Desconecta o bot do canal de voz (apenas Admin)


## ⚙️ Tecnologias

- Python 3.8
- FFmpeg 

### 📚 Bibliotecas utilizadas:

- discord.py
- discord.py[voice]
- PyNaCL
- yt-dlp
- python-dotenv
- eventlet
- flask
flask-socketio


## 🎮 Uso

1. Entre em um canal de voz
2. Use o comando /play seguido do nome da música ou URL do YouTube, como:
   - /play https://youtube.com/...
- ou
   - /play Never Gonna Give You Up
3. Controle a reprodução utilizando os comandos disponíveis!


## 🔐 Recursos de Administração
Alguns comandos exigem permissões administrativas:

- /stop: Parar reprodução e limpar fila
- /clear: Limpar mensagens do chat
- /leave: Forçar saída do bot do canal de voz

  
## 📈 Monitoramento
O bot inclui um servidor web para monitoramento de logs:

- Executa log_server.py
- Acessa http://localhost:8765 no navegador
- Visualiza os logs em tempo real enquanto o bot opera
