import feedparser
import requests
import os
import time

RSS_URL = "https://rss.app/feeds/aYipD5t5Wa5yhqo9.xml"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Variable global en memoria para guardar el último tweet procesado
ultimo_guid_memoria = None

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
    global ultimo_guid_memoria
    print("Verificando nuevas jugadas...", flush=True)
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("El feed RSS está vacío en este momento.", flush=True)
        return

    ultimo_item = feed.entries[0]
    guid_actual = getattr(ultimo_item, "id", ultimo_item.link)
    
    print(f"-> ID actual en el RSS: {guid_actual}", flush=True)
    print(f"-> ID guardado en memoria: {ultimo_guid_memoria}", flush=True)

    # Si es la primera vez que arranca el script en esta sesión
    if ultimo_guid_memoria is None:
        ultimo_guid_memoria = guid_actual
        print("Iniciando estado en memoria: último tweet registrado silenciosamente para evitar duplicados.", flush=True)
        return

    # Si hay un tweet nuevo que no coincide con el de la memoria
    if guid_actual != ultimo_guid_memoria:
        titulo = ultimo_item.title
        link = ultimo_item.link
        
        mensaje = f"🦁 <b>¡Jugada / Tweet de los Leones!</b>\n\n{titulo}\n\n🔗 {link}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            ultimo_guid_memoria = guid_actual
            print("¡Publicado en Telegram al instante!", flush=True)
        else:
            print("Error al publicar en Telegram:", resultado, flush=True)
    else:
        print("Sin novedades recientes (los IDs son idénticos).", flush=True)

if __name__ == "__main__":
    print("Iniciando bot continuo en memoria para Telegram...", flush=True)
    while True:
        try:
            verificar_feed()
        except Exception as e:
            print("Error en la ejecución:", e, flush=True)
        
        # Revisa cada 60 segundos
        time.sleep(60)
