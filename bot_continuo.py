import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None

def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as err:
        print(f"Error al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_feed():
    global ultimo_tweet_id_memoria
    print("Consultando feed mediante lector directo...", flush=True)
    
    # Usamos un servicio de lectura limpia que evita bloqueos de API
    url = f"https://r.jina.ai/https://x.com/{X_USERNAME}"
    
    try:
        headers = {"Accept": "text/plain"}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            contenido = res.text
            
            # Buscamos los IDs de los status en el contenido extraído
            pattern = rf"/{X_USERNAME}/status/(\d+)"
            ids_encontrados = re.findall(pattern, contenido)
            
            if not ids_encontrados:
                print("No se encontraron IDs de tweets en el texto.", flush=True)
                return

            # El primer ID de la lista es el tuit más reciente
            tweet_id = ids_encontrados[0]
            
            print(f"ID detectado en X: {tweet_id} | Memoria: {ultimo_tweet_id_memoria}", flush=True)

            if tweet_id == ultimo_tweet_id_memoria:
                print("Sin nuevos tweets, esperando siguiente ciclo.", flush=True)
                return

            tweet_link = f"https://x.com/{X_USERNAME}/status/{tweet_id}"
            
            # Mensaje directo y limpio al canal
            mensaje = f"🦁⚾ <b>¡Nueva actualización de los Leones en X!</b>\n\n🔗 {tweet_link}"
            
            resultado = enviar_a_telegram(mensaje)
            if resultado.get("ok"):
                print(f"¡Notificación enviada a Telegram con éxito! (ID: {tweet_id})", flush=True)
            else:
                print("Error al enviar a Telegram:", resultado, flush=True)

            ultimo_tweet_id_memoria = tweet_id
        else:
            print(f"Error al consultar la fuente web: {res.status_code}", flush=True)
    except Exception as e:
        print(f"Excepción en la consulta: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con lector directo robusto...", flush=True)
    enviar_a_telegram("🦁🚀 <b>Bot actualizado con sistema de lectura directa y estable.</b>")

    while True:
        try:
            verificar_feed()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
