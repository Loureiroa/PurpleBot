import logging
from flask import copy_current_request_context

class WebSocketLogHandler(logging.Handler):
    def __init__(self, socketio, app):
        super().__init__()
        self.socketio = socketio
        self.app = app

    def emit(self, record):
        log_entry = self.format(record)

        # Ignora logs internos que causam recursão
        if record.name.startswith("werkzeug") or record.name.startswith("engineio"):
            return

        with self.app.app_context():
            self.socketio.emit('log_message', {'message': log_entry})
