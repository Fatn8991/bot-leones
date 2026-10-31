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
    print(f"Verificando publicaciones para @{X_USERNAME}...", flush=True)
    
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

        data = response.json()
        contenido_markdown = data.get("data", {}).get("content", "")
        
        if not contenido_markdown:
            print("No se encontró contenido en la respuesta.", flush=True)
            return

        # Tomamos una porción del texto para usarlo como identificador único del tuit actual
        lineas = [l.strip() for l in contenido_markdown.split("\n") if l.strip()]
        if not lineas:
            return
            
        # Buscamos las líneas que parezcan contenido de tuit (evitando cabeceras de perfil)
        tweet_texto = ""
        for linea in lineas:
            if len(linea) > 20 and "Leones del Caracas" not in linea and "(@leones_cbbc)" not in linea:
                tweet_texto = linea
                break

        if not tweet_texto:
            tweet_texto = lineas[0]

        # Usamos el texto como firma de memoria para evitar duplicados
        tweet_id = str(hash(tweet_texto))

        print(f"Identificador de tuit actual: {tweet_id} | Memoria: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Sin nuevos tuits en este ciclo.", flush=True)
            return

        mensaje = f"🦁⚾ <b>¡Actualización de los Leones!</b>\n\n{tweet_texto}\n\n🔗 <a href='https://x.com/{X_USERNAME}'>Ver perfil oficial en X</a>"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            print("¡Tuit enviado con éxito al canal de Telegram!", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)

        ultimo_tweet_id_memoria = tweet_id

    except Exception as e:
        print(f"Excepción al procesar la actualización: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con conector estables de X...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot sincronizado y monitoreando el equipo!</b>")

    while True:
        try:
            verificar_actualizacion()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(60)
