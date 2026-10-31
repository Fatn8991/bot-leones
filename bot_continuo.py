import feedparser
import requests
import os
import time
from bs4 import BeautifulSoup

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None

def enviar_a_telegram(mensaje, foto_url=None):
    # Si el tuit trae una imagen adjunta, usamos sendPhoto para que luzca profesional
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
    print("Consultando jugadas y multimedia en Nitter RSS...", flush=True)
    
    url_rss = f"https://nitter.privacydev.net/{X_USERNAME}/rss"
    
    try:
        feed = feedparser.parse(url_rss)
        
        if not feed.entries:
            print("No se encontraron entradas en el RSS.", flush=True)
            return

        entrada = feed.entries[0]
        tweet_link = entrada.link
        
        tweet_id = tweet_link.split("/")[-1].split("#")[0]
        
        if not tweet_id:
            return

        print(f"ID detectado: {tweet_id} | Memoria: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Sin nuevas jugadas o multimedia.", flush=True)
            return

        raw_content = entrada.get("summary", "")
        soup = BeautifulSoup(raw_content, "html.parser")
        
        # Buscamos si el tuit contiene alguna imagen adjunta
        img_tag = soup.find("img")
        foto_url = None
        if img_tag and img_tag.get("src"):
            foto_url = img_tag["src"]
            # Si la URL de la imagen es relativa a nitter, la completamos
            if foto_url.startswith("/"):
                foto_url = f"https://nitter.privacydev.net{foto_url}"

        # Limpiamos el texto removiendo las etiquetas de imágenes del cuerpo para que no ensucie
        for img in soup.find_all("img"):
            img.decompose()
            
        tweet_texto = soup.get_text().strip()

        # Armamos el mensaje para el canal
        mensaje = f"🦁⚾ <b>¡Actualización de los Leones!</b>\n\n{tweet_texto}\n\n🔗 <a href='{tweet_link}'>Ver jugada completa en X</a>"
        
        resultado = enviar_a_telegram(mensaje, foto_url=foto_url)
        if resultado.get("ok"):
            print(f"¡Multimedia/Jugada enviada con éxito! (ID: {tweet_id})", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)

        ultimo_tweet_id_memoria = tweet_id

    except Exception as e:
        print(f"Excepción al procesar multimedia: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con soporte de multimedia y jugadas...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot actualizado con captura de fotos y jugadas en tiempo real!</b>")

    while True:
        try:
            verificar_nitter_rss()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
