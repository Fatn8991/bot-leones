import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_guid_memoria = None

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

def obtener_ultimo_tweet_directo():
    # Usamos la API de lectura directa optimizada para extraer contenido web sin bloqueos
    url_lector = f"https://r.jina.ai/https://x.com/{X_USERNAME}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        res = requests.get(url_lector, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            content = data.get("data", {}).get("content", "")
            
            # Buscamos el ID del último tweet analizando los enlaces de estado en el contenido
            match_id = re.search(r'status/(\d+)', content)
            if match_id:
                tweet_id = match_id.group(1)
                tweet_link = f"https://x.com/{X_USERNAME}/status/{tweet_id}"
                
                return {
                    "id": tweet_id,
                    "link": tweet_link
                }
    except Exception as e:
        print(f"Error consultando el lector directo: {e}", flush=True)
        
    return None

def verificar_cuenta():
    global ultimo_guid_memoria
    print("Escaneando X mediante lector directo en tiempo real...", flush=True)
    
    tweet = obtener_ultimo_tweet_directo()
    
    if not tweet:
        print("Reintentando conexión en el próximo ciclo...", flush=True)
        return

    guid_actual = tweet["id"]
    print(f"-> ID extraído: {guid_actual}", flush=True)
    print(f"-> ID en memoria: {ultimo_guid_memoria}", flush=True)

    if ultimo_guid_memoria is None:
        ultimo_guid_memoria = guid_actual
        print("Estado inicial anclado en memoria silenciosamente.", flush=True)
        return

    if guid_actual != ultimo_guid_memoria:
        mensaje = f"🦁 <b>¡Nuevo Tweet de los Leones!</b>\n\n🔗 {tweet['link']}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            ultimo_guid_memoria = guid_actual
            print("¡Publicado en Telegram al instante!", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)
    else:
        print("Sin nuevos tweets por ahora.", flush=True)

if __name__ == "__main__":
    print("Iniciando motor maestro de rastreo en tiempo real...", flush=True)
    while True:
        try:
            verificar_cuenta()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
