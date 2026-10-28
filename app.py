import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import subprocess

# Servidor web falso para que Render esté contento con el puerto
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Leones del Caracas activo 24/7!")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Arrancar el servidor web en segundo plano
threading.Thread(target=run_web, daemon=True).start()

# Arrancar tu bot continuo de Telegram
subprocess.run(["python3", "bot_continuo.py"])
