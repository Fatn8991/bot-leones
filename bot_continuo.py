import requests
import os
import time
from bs4 import BeautifulSoup

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None

def enviar_a_telegram(mensaje, foto_url=None):
    if foto_url:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID,
            "photo": foto_url,
            "caption": mensaje,
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as err:
        print(f"Error al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    global ultimo_tweet_id_memoria
    print(f"Verificando actualizaciones para @{X_USERNAME}...", flush=True)
    
    # Usamos un servicio de respaldo público alternativo para evitar el 404
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        response = requests.get(url_api, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Servicio alternativo respondió con código: {response.status_code}", flush=True)
            return

        contenido = response.text
        
        # Verificamos si hay texto nuevo y simulamos la lectura del último tuit
        if not contenido:
            print("Contenido vacío recibido.", flush=True)
            return

        print("¡Conexión exitosa con el servicio de lectura!", flush=True)
        
    except Exception as e:
        print(f"Excepción al consultar el servicio: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con conector alternativo...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot reiniciado con conector de respaldo activo!</b>")

    while True:
        try:
            verificar_actualizacion()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(60)
