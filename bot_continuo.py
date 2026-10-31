import feedparser
import requests
import os
import time
from bs4 import BeautifulSoup

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Lista de instancias públicas de Nitter para que el bot salte a otra si una falla
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.unixlooters.xyz"
]

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

def verificar_nitter_rss():
    global ultimo_tweet_id_memoria
    
    feed = None
    instancia_activa = ""
    
    # Probamos las instancias hasta que una responda con éxito
    for base_url in NITTER_INSTANCES:
        url_rss = f"{base_url}/{X_USERNAME}/rss"
        try:
            print(f"Probando instancia: {base_url}...", flush=True)
            temp_feed = feedparser.parse(url_rss)
            if temp_feed.entries:
                feed = temp_feed
                instancia_activa = base_url
                break
        except Exception:
            continue

    if not feed or not feed.entries:
        print("Ninguna instancia de Nitter devolvió entradas en este ciclo.", flush=True)
        return

    try:
        entrada = feed.entries[0]
        tweet_link = entrada.link
        tweet_id = tweet_link.split("/")[-1].split("#")[0]
        
        if not tweet_id:
            return

        print(f"ID detectado: {tweet_id} (Instancia: {instancia_activa}) | Memoria: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Sin nuevas publicaciones.", flush=True)
            return

        raw_content = entrada.get("summary", "")
        soup = BeautifulSoup(raw_content, "html.parser")
        
        img_tag = soup.find("img")
        foto_url = None
        if img_tag and img_tag.get("src"):
            foto_url = img_tag["src"]
            if foto_url.startswith("/"):
                foto_url = f"{instancia_activa}{foto_url}"

        for img in soup.find_all("img"):
            img.decompose()
            
        tweet_texto = soup.get_text().strip()

        # Ajustamos el enlace para que apunte directo a x.com en lugar de nitter si lo prefieres
        x_real_link = tweet_link.replace(instancia_activa, "https://x.com")

        mensaje = f"🦁⚾ <b>¡Actualización de los Leones!</b>\n\n{tweet_texto}\n\n🔗 <a href='{x_real_link}'>Ver publicación en X</a>"
        
        resultado = enviar_a_telegram(mensaje, foto_url=foto_url)
        if resultado.get("ok"):
            print(f"¡Enviado con éxito al canal! (ID: {tweet_id})", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)

        ultimo_tweet_id_memoria = tweet_id

    except Exception as e:
        print(f"Excepción al procesar el feed: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con rotación de instancias Nitter...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot reiniciado y escaneando con respaldo de múltiples instancias!</b>")

    while True:
        try:
            verificar_nitter_rss()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
