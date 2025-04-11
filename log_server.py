import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from logger_websocket import WebSocketLogHandler
import logging

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Logger que envia logs para o WebSocket
handler = WebSocketLogHandler(socketio, app)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

@app.route("/")
def index():
    return render_template("index.html")

# Rota para receber logs via HTTP do bot
@app.route("/send_log", methods=["POST"])
def receive_log():
    data = request.json
    if data and "message" in data:
        # Encaminhar diretamente para o socket sem passar pelo logger
        with app.app_context():
            socketio.emit('log_message', {'message': data["message"]})
    return jsonify({"status": "ok"})

# Recebe log de teste do botão
@socketio.on('log_message')
def handle_log_message(data):
    message = data.get('message', '')
    logging.info(f"[CLIENTE] {message}")

if __name__ == "__main__":
    print("[FLASK] Servidor de log iniciado em http://localhost:8765")
    socketio.run(app, host="0.0.0.0", port=8765)