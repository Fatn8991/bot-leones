import requests
import os
import time
import hashlib
import re

X_USERNAME = "leones_cbbc"
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ARCHIVO_MEMORIA = "id_memoria.txt"
HISTORIAL_ENVIADOS = set()

def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
                for linea in f:
                    limpia = linea.strip()
                    if limpia:
                        HISTORIAL_ENVIADOS.add(limpia)
        except:
            pass

cargar_memoria()

def guardar_memoria(identificador):
    try:
        if identificador and identificador not in HISTORIAL_ENVIADOS:
            HISTORIAL_ENVIADOS.add(identificador)
            with open(ARCHIVO_MEMORIA, "a", encoding="utf-8") as f:
                f.write(identificador + "\n")
    except Exception as e:
        print("Error al guardar en disco: " + str(e), flush=True)

def obtener_user_id():
    url = f"https://api.twitter.com/2/users/by/username/{X_USERNAME}"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get("data", {}).get("id")
        else:
            print(f"Error al obtener User ID: {res.status_code} - {res.text}", flush=True)
    except Exception as e:
        print("Error de conexión obteniendo User ID de X: " + str(e), flush=True)
    return None

def enviar_a_telegram(mensaje, imagenes):
    try:
        # Si hay varias imágenes, envía un álbum de fotos
        if len(imagenes) > 1:
            url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
            media_group = []
            for idx, img_url in enumerate(imagenes[:10]):
                item = {"type": "photo", "media": img_url}
                if idx == 0:
                    item["caption"] = mensaje
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            res = requests.post(url_tg, json={"chat_id": CHAT_ID, "media": media_group}, timeout=30)
            if res.json().get("ok"):
                return res.json()

        # Si hay una sola imagen, se descarga localmente y se envía de forma segura
        if len(imagenes) == 1:
            img_resp = requests.get(imagenes[0], timeout=15)
            if img_resp.status_code == 200:
                url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                files = {'photo': ('image.jpg', img_resp.content, 'image/jpeg')}
                data = {'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'HTML'}
                res = requests.post(url_tg, data=data, files=files, timeout=30)
                if res.json().get("ok"):
                    return res.json()

        # Si no hay imágenes, envía solo texto plano limpio
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID, 
            "text": mensaje, 
            "parse_mode": "HTML", 
            "disable_web_page_preview": True
        }
        res = requests.post(url_tg, json=payload, timeout=30)
        return res.json()
    except Exception as err:
        print("Error en Telegram: " + str(err), flush=True)
        return {}

def verificar_actualizacion(user_id):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": 5,
        "expansions": "attachments.media_keys",
        "media.fields": "url,preview_image_url,type",
        "tweet.fields": "created_at,text"
    }
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        if res.status_code != 200:
            print(f"Error API X: {res.status_code} - {res.text}", flush=True)
            return

        data = res.json()
        tweets = data.get("data", [])
        includes = data.get("includes", {}).get("media", [])
        
        media_map = {m["media_key"]: m.get("url") or m.get("preview_image_url") for m in includes if m.get("url") or m.get("preview_image_url")}

        # Procesamos en orden cronológico (del más antiguo al más nuevo)
        for tweet in reversed(tweets):
            tweet_id = tweet.get("id")
            texto = tweet.get("text", "")
            
            # Verificamos si ya fue enviado usando el ID oficial del tuit
            if tweet_id in HISTORIAL_ENVIADOS:
                continue

            # Extracción de imágenes asociadas
            imagenes = []
            attachments = tweet.get("attachments", {}).get("media_keys", [])
            for key in attachments:
                if key in media_map:
                    imagenes.append(media_map[key])

            # Limpiamos los enlaces web del texto para que quede estético
            texto_limpio = re.sub(r'https?://\S+', '', texto).strip()
            if not texto_limpio:
                texto_limpio = "¡Información oficial de los Leones del Caracas!"

            mensaje = f"🦁⚾ <b>{texto_limpio}</b>"

            # Registramos el ID oficial inmediatamente en disco y memoria
            guardar_memoria(tweet_id)

            res_tg = enviar_a_telegram(mensaje, imagenes)
            if res_tg.get("ok"):
                print(f"¡Tuit oficial {tweet_id} enviado con éxito!", flush=True)
            else:
                print(f"Error al enviar tuit {tweet_id} a Telegram: {res_tg}", flush=True)
            
            time.sleep(2)

    except Exception as e:
        print("Error general en bucle de API X: " + str(e), flush=True)

if __name__ == "__main__":
    print("Iniciando bot con API Oficial de X...", flush=True)
    user_id = None
    while not user_id:
        user_id = obtener_user_id()
        if not user_id:
            print("Reintentando obtener User ID de X en 10 segundos...", flush=True)
            time.sleep(10)
    
    print(f"¡User ID de @{X_USERNAME} obtenido ({user_id})! Iniciando monitoreo oficial...", flush=True)
    while True:
        verificar_actualizacion(user_id)
        time.sleep(30)
