import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import subprocess

# 1. Función que corre tu bot y transmite su salida en tiempo real a los logs
def run_bot():
    print("Hilo del bot iniciado, lanzando bot_continuo.py...", flush=True)
    while True:
        try:
            # Usamos Popen y -u para evitar el búfer y ver los logs al instante
            process = subprocess.Popen(
                ["python3", "-u", "bot_continuo.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Lee la salida del bot línea por línea y la muestra en los logs de Render
            for line in process.stdout:
                print(f"[Bot]: {line.strip()}", flush=True)
                
            process.wait()
        except Exception as e:
            print(f"Excepción crítica en el hilo del bot: {e}", flush=True)
            
        print("Reiniciando ciclo del bot en 10 segundos...", flush=True)
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
    print(f"Servidor web escuchando en el puerto {port}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    run()
