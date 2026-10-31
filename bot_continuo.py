import feedparser
import requests
import os
import time
from bs4 import BeautifulSoup

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# URL de RSSHub optimizada para extraer el feed de X de forma estable
RSS_URL = f"https://rsshub.app/twitter/user/{X_USERNAME}"

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

def verificar_rss():
    global ultimo_tweet_id_memoria
    print(f"Consultando RSSHub para @{X_USERNAME}...", flush=True)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error al obtener el feed RSS. Código HTTP: {response.status_code}", flush=True)
            return

        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            print("No se encontraron entradas en el RSS.", flush=True)
            return

        entrada = feed.entries[0]
        tweet_link = entrada.link
        tweet_id = entrada.get("id", tweet_link)
        
        if tweet_id == ultimo_tweet_id_memoria:
            print("Sin nuevas publicaciones.", flush=True)
            return

        print(f"¡Nuevo tuit detectado! ID: {tweet_id}", flush=True)

        raw_content = entrada.get("summary", entrada.get("description", ""))
        soup = BeautifulSoup(raw_content, "html.parser")
        
        # Extraer imagen adjunta si la publicación la incluye
        img_tag = soup.find("img")
        foto_url = None
        if img_tag and img_tag.get("src"):
            foto_url = img_tag["src"]

        for img in soup.find_all("img"):
            img.decompose()
            
        tweet_texto = soup.get_text().strip()

        mensaje = f"🦁⚾ <b>¡Actualización de los Leones!</b>\n\n{tweet_texto}\n\n🔗 <a href='{tweet_link}'>Ver publicación en X</a>"
        
        resultado = enviar_a_telegram(mensaje, foto_url=foto_url)
        if resultado.get("ok"):
            print("¡Enviado con éxito al canal de Telegram!", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)

        ultimo_tweet_id_memoria = tweet_id

    except Exception as e:
        print(f"Excepción al procesar el feed: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con motor RSSHub estable...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot actualizado con el nuevo motor RSS estable!</b>")

    while True:
        try:
            verificar_rss()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
