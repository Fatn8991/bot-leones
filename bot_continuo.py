import feedparser
import os
import time

# Usamos RSSHub para obtener el feed directo de la cuenta sin bloqueos
RSS_URL = "https://rsshub.app/twitter/user/leones_cbbc"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_guid_memoria = None

def enviar_a_telegram(mensaje):
    import requests
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
    global ultimo_guid_memoria
    print("Consultando el feed en tiempo real vía RSSHub...", flush=True)
    
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("El feed está cargando o no devolvió entradas todavía. Reintentando...", flush=True)
        return

    ultimo_item = feed.entries[0]
    guid_actual = getattr(ultimo_item, "id", ultimo_item.link)
    
    print(f"-> ID actual: {guid_actual}", flush=True)
    print(f"-> ID en memoria: {ultimo_guid_memoria}", flush=True)

    if ultimo_guid_memoria is None:
        ultimo_guid_memoria = guid_actual
        print("Estado inicial anclado en memoria silenciosamente.", flush=True)
        return

    if guid_actual != ultimo_guid_memoria:
        titulo = ultimo_item.title
        link = ultimo_item.link
        
        mensaje = f"🦁 <b>¡Nuevo Tweet de los Leones!</b>\n\n{titulo}\n\n🔗 {link}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            ultimo_guid_memoria = guid_actual
            print("¡Publicado en Telegram al instante!", flush=True)
        else:
            print("Error al enviar a Telegram:", resultado, flush=True)
    else:
        print("Sin nuevos tweets por ahora.", flush=True)

if __name__ == "__main__":
    print("Iniciando bot definitivo con RSSHub...", flush=True)
    while True:
        try:
            verificar_feed()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
