import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import subprocess

# 1. Función que corre tu bot en segundo plano y muestra errores si ocurren
def run_bot():
    print("Hilo del bot iniciado, esperando para ejecutar bot_continuo.py...")
    while True:
        try:
            print("Ejecutando bot_continuo.py...")
            # Ejecutamos y capturamos la salida y errores para verlos en los logs
            proceso = subprocess.run(
                ["python3", "bot_continuo.py"], 
                capture_output=True, 
                text=True
            )
            
            # Si el bot imprimió algo en la salida estándar
            if proceso.stdout:
                print(f"[Salida del bot]: {proceso.stdout}")
                
            # Si el bot dio algún error, lo mostramos en los logs de Render
            if proceso.returncode != 0:
                print(f"[Error en el bot (código {proceso.returncode})]: {proceso.stderr}")
                
        except Exception as e:
            print(f"Excepción crítica al intentar ejecutar el bot: {e}")
            
        print("Reiniciando ciclo del bot en 10 segundos...")
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
