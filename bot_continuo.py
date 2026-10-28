import feedparser
import requests
import os
import time

RSS_URL = "https://rss.app/feeds/aYipD5t5Wa5yhqo9.xml"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
STATE_FILE = "ultimo_tweet.txt"

def obtener_ultimo_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None

def guardar_ultimo_id(guid):
    with open(STATE_FILE, "w") as f:
        f.write(guid)

def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload)
    return response.json()

def verificar_feed():
    print("Verificando nuevas jugadas...", flush=True)
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("El feed RSS está vacío en este momento.", flush=True)
        return

    ultimo_item = feed.entries[0]
    guid_actual = getattr(ultimo_item, "id", ultimo_item.link)
    
    ultimo_guardado = obtener_ultimo_id()

    # Imprimimos ambos en los logs para comparar qué está pasando
    print(f"-> ID actual en el RSS: {guid_actual}", flush=True)
    print(f"-> ID guardado en archivo: {ultimo_guardado}", flush=True)

    if ultimo_guardado is None:
        guardar_ultimo_id(guid_actual)
        print("Iniciando estado: último tweet registrado silenciosamente.", flush=True)
        return

    if guid_actual != ultimo_guardado:
        titulo = ultimo_item.title
        link = ultimo_item.link
        
        mensaje = f"🦁 <b>¡Jugada / Tweet de los Leones!</b>\n\n{titulo}\n\n🔗 {link}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            guardar_ultimo_id(guid_actual)
            print("¡Publicado en Telegram al instante!", flush=True)
        else:
            print("Error al publicar en Telegram:", resultado, flush=True)
    else:
        print("Sin novedades recientes (los IDs son idénticos).", flush=True)

if __name__ == "__main__":
    print("Iniciando bot continuo para Telegram...", flush=True)
    while True:
        try:
            verificar_feed()
        except Exception as e:
            print("Error en la ejecución:", e, flush=True)
        
        time.sleep(60)
