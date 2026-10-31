import feedparser
import requests
import os
import time
from bs4 import BeautifulSoup

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

def verificar_nitter_rss():
    global ultimo_tweet_id_memoria
    print("Consultando el feed RSS de Nitter...", flush=True)
    
    url_rss = f"https://nitter.privacydev.net/{X_USERNAME}/rss"
    
    try:
        feed = feedparser.parse(url_rss)
        
        if not feed.entries:
            print("No se encontraron entradas en el RSS de Nitter.", flush=True)
            return

        entrada = feed.entries[0]
        tweet_link = entrada.link
        
        # Extraemos el ID numérico del enlace para la memoria
        tweet_id = tweet_link.split("/")[-1].split("#")[0]
        
        if not tweet_id:
            return

        print(f"ID detectado via Nitter RSS: {tweet_id} | Memoria: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Sin nuevos tweets en Nitter.", flush=True)
            return

        raw_content = entrada.get("summary", "")
        soup = BeautifulSoup(raw_content, "html.parser")
        tweet_texto = soup.get_text()

        # Ocultamos la URL de Nitter detrás de un texto limpio usando HTML de Telegram
        mensaje = f"🦁⚾ <b>¡Nuevo Tweet de los Leones!</b>\n\n{tweet_texto}\n\n🔗 <a href='{tweet_link}'>Ver publicación original en X</a>"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            print(f"¡Enviado a Telegram con éxito! (ID: {tweet_id})", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)

        ultimo_tweet_id_memoria = tweet_id

    except Exception as e:
        print(f"Excepción al leer Nitter RSS: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con formato limpio...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot actualizado con formato de mensajes limpios!</b>")

    while True:
        try:
            verificar_nitter_rss()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
