import requests
from bs4 import BeautifulSoup
import os
import time

# Usuario exacto de X/Twitter sin el @
X_USERNAME = "leones_cbbc"

# Variables traídas desde Render
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
    # Lista ampliada de instancias espejo públicas para mayor estabilidad
    instancias = [
        f"https://nitter.poast.org/{X_USERNAME}",
        f"https://nitter.privacydev.net/{X_USERNAME}",
        f"https://nitter.catsarch.com/{X_USERNAME}",
        f"https://nitter.perennialte.ch/{X_USERNAME}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for url in instancias:
        try:
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                tweet_container = soup.find("div", class_="timeline-item")
                if tweet_container:
                    link_tag = tweet_container.find("a", class_="tweet-link")
                    content_tag = tweet_container.find("div", class_="tweet-content")
                    
                    if link_tag and content_tag:
                        path = link_tag.get("href", "")
                        tweet_id = path.split("/")[-1].replace("#m", "")
                        tweet_link = f"https://x.com/{X_USERNAME}/status/{tweet_id}"
                        tweet_texto = content_tag.get_text().strip()
                        
                        return {
                            "id": tweet_id,
                            "texto": tweet_texto,
                            "link": tweet_link
                        }
        except Exception:
            continue

    return None

def verificar_cuenta():
    global ultimo_guid_memoria
    print("Escaneando la cuenta de los Leones en tiempo real...", flush=True)
    
    tweet = obtener_ultimo_tweet_directo()
    
    if not tweet:
        print("No se pudo obtener la información de X en este intento (instancias ocupadas). Reintentando...", flush=True)
        return

    guid_actual = tweet["id"]
    print(f"-> ID extraído de X: {guid_actual}", flush=True)
    print(f"-> ID guardado en memoria: {ultimo_guid_memoria}", flush=True)

    if ultimo_guid_memoria is None:
        ultimo_guid_memoria = guid_actual
        print("Iniciando estado en memoria: último tweet anclado silenciosamente.", flush=True)
        return

    if guid_actual != ultimo_guid_memoria:
        mensaje = f"🦁 <b>¡Jugada / Tweet de los Leones!</b>\n\n{tweet['texto']}\n\n🔗 {tweet['link']}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            ultimo_guid_memoria = guid_actual
            print("¡Publicado en Telegram al instante sin intermediarios!", flush=True)
        else:
            print("Error al publicar en Telegram:", resultado, flush=True)
    else:
        print("Sin novedades recientes en X.", flush=True)

if __name__ == "__main__":
    print("Iniciando motor de rastreo directo para Telegram...", flush=True)
    while True:
        try:
            verificar_cuenta()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
