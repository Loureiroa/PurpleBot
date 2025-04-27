# Centraliza todas as configurações do bot

FFMPEG_PATH = "F:\\ffmpeg\\ffmpeg.exe"
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -b:a 128k'
}
LOG_SERVER_URL = "http://localhost:8765"
DEFAULT_TIMEOUT = 3  # Tempo padrão para mensagens temporárias (segundos)
QUEUE_DISPLAY_TIME = 10  # Tempo para exibir a fila (segundos)