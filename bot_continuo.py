import requests
import os
import time
from bs4 import BeautifulSoup

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

def obtener_ultimo_tweet_widget():
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{X_USERNAME}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Buscamos enlaces directos a los status del usuario en el widget oficial
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if f"/{X_USERNAME}/status/" in href:
                    parts = href.split("/status/")
                    if len(parts) > 1:
                        tweet_id = parts[1].split("?")[0].split("/")[0]
                        tweet_link = f"https://x.com/{X_USERNAME}/status/{tweet_id}"
                        
                        # Extraemos el texto del tweet si está disponible en el contenedor
                        tweet_container = link.find_parent("article") or link.find_parent("div")
                        tweet_texto = tweet_container.get_text().strip() if tweet_container else "Nuevo tweet de los Leones del Caracas"
                        
                        return {
                            "id": tweet_id,
                            "link": tweet_link,
                            "texto": tweet_texto
                        }
        print("La API del widget respondió pero no arrojó elementos todavía. Reintentando...", flush=True)
    except Exception as e:
        print(f"Error consultando el widget oficial: {e}", flush=True)
        
    return None

def verificar_cuenta():
    global ultimo_guid_memoria
    print("Consultando el widget oficial de X en tiempo real...", flush=True)
    
    tweet = obtener_ultimo_tweet_widget()
    
    if not tweet:
        return

    guid_actual = tweet["id"]
    print(f"-> ID actual: {guid_actual}", flush=True)
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
    print("Iniciando motor oficial de widgets...", flush=True)
    while True:
        try:
            verificar_cuenta()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
