import requests
import os
import time
import hashlib
import re
import xml.etree.ElementTree as ET

X_USERNAME = "leones_cbbc"
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
        print("Error al guardar memoria en disco: " + str(e), flush=True)

def enviar_a_telegram(mensaje, imagenes, videos):
    try:
        # Si hay videos, priorizamos enviar el video con su texto/caption
        if videos:
            url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": CHAT_ID,
                "video": videos[0],
                "caption": mensaje,
                "parse_mode": "HTML"
            }
            res = requests.post(url_tg, json=payload, timeout=30)
            if res.json().get("ok"):
                return res.json()

        # Filtrar solo URLs válidas de imágenes de Twitter
        imagenes_validas = [img for img in imagenes if "pbs.twimg.com/media" in img]

        # Enviar grupo de medios (álbum) si hay más de una foto
        if len(imagenes_validas) > 1:
            url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
            media_group = []
            for idx, img_url in enumerate(imagenes_validas[:10]):
                item = {"type": "photo", "media": img_url}
                if idx == 0:
                    item["caption"] = mensaje
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            res = requests.post(url_tg, json={"chat_id": CHAT_ID, "media": media_group}, timeout=30)
            if res.json().get("ok"):
                return res.json()

        # Enviar foto individual con descarga local segura si hay 1 imagen
        if len(imagenes_validas) == 1:
            headers = {'User-Agent': 'Mozilla/5.0'}
            img_resp = requests.get(imagenes_validas[0], headers=headers, timeout=15)
            if img_resp.status_code == 200:
                url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                files = {'photo': ('image.jpg', img_resp.content, 'image/jpeg')}
                data = {'chat_id': CHAT_ID, 'caption': mensaje, 'parse_mode': 'HTML'}
                res = requests.post(url_tg, data=data, files=files, timeout=30)
                if res.json().get("ok"):
                    return res.json()

        # Respaldo en texto plano si no hay multimedia
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
        print("Error crítico en Telegram: " + str(err), flush=True)
        return {}

def verificar_actualizacion():
    instancias_rss = [
        f"https://nitter.net/{X_USERNAME}/rss",
        f"https://rss.app/feeds/twitter/{X_USERNAME}.xml",
        f"https://nitter.cz/{X_USERNAME}/rss"
    ]
    
    contenido_xml = None
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for url in instancias_rss:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200 and ("<rss" in res.text or "<feed" in res.text):
                contenido_xml = res.text
                break
        except:
            continue

    if not contenido_xml:
        return

    try:
        root = ET.fromstring(contenido_xml)
        items = root.findall(".//item")
        
        for item in reversed(items[:5]):
            title = item.find("title").text if item.find("title") is not None else ""
            description = item.find("description").text if item.find("description") is not None else ""
            guid = item.find("guid").text if item.find("guid") is not None else title

            # Extracción de imágenes
            imagenes = []
            match_imgs = re.findall(r'<img[^>]+src="([^">]+)"', description)
            for img in match_imgs:
                if "twimg.com" in img:
                    img_limpia = re.sub(r':[a-z]+$', '', img)
                    imagenes.append(img_limpia)

            match_links = re.findall(r'https?://pbs\.twimg\.com/media/[^\s"\'\)<>]+', description + " " + title)
            for link in match_links:
                link_limpio = re.sub(r':[a-z]+$', '', link)
                imagenes.append(link_limpio)

            imagenes = list(dict.fromkeys(imagenes))

            # Extracción de videos (enlaces directos .mp4 o etiquetas de video)
            videos = []
            match_vids = re.findall(r'https?://[^\s"\'\)<>]+?\.mp4[^\s"\'\)<>]*', description + " " + title)
            for v in match_vids:
                videos.append(v)
            
            # Buscar también en atributos de video o enclosures si existen
            for enclosure in item.findall("enclosure"):
                enc_url = enclosure.get("url", "")
                if ".mp4" in enc_url or "video" in enclosure.get("type", ""):
                    videos.append(enc_url)

            videos = list(dict.fromkeys(videos))

            # Limpieza del texto del tuit
            texto_limpio = re.sub(r'<[^>]+>', '', title)
            texto_limpio = re.sub(r'https?://\S+', '', texto_limpio).strip()

            if not texto_limpio:
                texto_limpio = "¡Información oficial de los Leones del Caracas!"

            firma_id = hashlib.md5(guid.encode('utf-8')).hexdigest()

            if firma_id in HISTORIAL_ENVIADOS:
                continue

            guardar_memoria(firma_id)
            mensaje = f"🦁⚾ <b>{texto_limpio}</b>"

            res = enviar_a_telegram(mensaje, imagenes, videos)
            if res.get("ok"):
                print(f"¡Publicación multimedia enviada con éxito! Hash: {firma_id}", flush=True)
            else:
                print(f"Respuesta de Telegram: {res}", flush=True)

            time.sleep(2)

    except Exception as err_xml:
        print("Error parseando XML: " + str(err_xml), flush=True)

if __name__ == "__main__":
    print("Iniciando bot continuo autónomo con soporte de fotos y videos...", flush=True)
    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print("Error en el bucle principal: " + str(err), flush=True)
        time.sleep(30)
