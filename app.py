import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import subprocess

# 1. Función que corre tu bot en segundo plano de forma independiente
def run_bot():
    while True:
        try:
            subprocess.run(["python3", "bot_continuo.py"])
        except Exception as e:
            print(f"Error en el bot: {e}")
        time.sleep(10)

# Iniciar el bot en un hilo secundario
threading.Thread(target=run_bot, daemon=True).start()

# 2. Servidor web obligatorio para Render en el hilo principal
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Leones del Caracas activo 24/7!")

def run():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Servidor web escuchando en el puerto {port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
