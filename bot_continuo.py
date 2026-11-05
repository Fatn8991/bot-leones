import requests
import os
import time
import re
import hashlib

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
        print("Error al guardar en disco: " + str(e), flush=True)

def enviar_a_telegram(mensaje, multimedia, tipo_m):
    try:
        if tipo_m == "photo" and len(multimedia) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
            media_group = []
            for idx, img in enumerate(multimedia[:10]):
                item = {"type": "photo", "media": img}
                if idx == 0:
                    item["caption"] = mensaje
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            res = requests.post(url, json={"chat_id": CHAT_ID, "media": media_group}, timeout=30)
            return res.json()

        elif tipo_m == "photo" and len(multimedia) == 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            payload = {"chat_id": CHAT_ID, "photo": multimedia[0], "caption": mensaje, "parse_mode": "HTML"}
            res = requests.post(url, json=payload, timeout=30)
            return res.json()

        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": True}
            res = requests.post(url, json=payload, timeout=30)
            return res.json()
    except Exception as err:
        print("Error en Telegram: " + str(err), flush=True)
        return {}

def verificar_actualizacion():
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}?t={int(time.time())}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url_api, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print("Error HTTP Jina: " + str(response.status_code), flush=True)
            return

        data = response.json()
        contenido = data.get("data", {}).get("content", "")
        
        if not contenido:
            return

        lineas = [l.strip() for l in contenido.split("\n") if l.strip()]
        
        for i, linea in enumerate(lineas):
            if "Única cuenta oficial" in linea or "títulos de la LVBP" in linea:
                continue

            if any(tag in linea.lower() for tag in ["#leo", "#caraquistasoy"]):
                
                bloque = []
                for k in range(max(0, i-2), i+1):
                    cand = lineas[k]
                    c_low = cand.lower()
                    
                    if any(x in c_low for x in ["leones_cbbc", "http://", "https://", "image", "born ", "caracas, venezuela", "joined "]):
                        continue
                    if re.match(r'^\d+[mhds]$', cand.strip()):
                        continue
                    if re.match(r'^\[\s*\d+[mh]\s*\]', cand):
                        continue
                    if len(cand.strip()) < 15 and re.match(r'^[\d\s\.,kKmMBb/:-]+$', cand):
                        continue
                        
                    if len(cand.strip()) > 2:
                        bloque.append(cand)
                
                tweet_texto = "\n".join(bloque) if bloque else linea

                # Extracción robusta de imágenes de Twitter (pbs.twimg.com)
                imagenes = []
                for j in range(max(0, i-4), min(len(lineas), i+5)):
                    match_img = re.search(r'(https?://pbs\.twimg\.com/media/[^?\s)]+)', lineas[j])
                    if match_img:
                        img_url = match_img.group(1)
                        if img_url not in imagenes:
                            imagenes.append(img_url)

                # --- LIMPIEZA PROFUNDA ---
                limpio = tweet_texto
                limpio = re.sub(r'\b\d+[mhds]\b', '', limpio)
                limpio = re.sub(r'!?[Ii]mage\s*\d*:?', '', limpio)
                limpio = re.sub(r'\[\s*\]|\(\s*\)|\(blob:[^)]+\)|blob:\S+', '', limpio)
                limpio = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}|Caracas,\s+Venezuela', '', limpio, flags=re.IGNORECASE)
                limpio = re.sub(r'@\w+|https?://\S+', '', limpio)
                
                lineas_L = []
                for l in limpio.split("\n"):
                    l_str = l.strip()
                    if not l_str:
                        continue
                    if re.match(r'^\d+[mhds]$', l_str):
                        continue
                    if len(l_str) < 15 and re.match(r'^[\d\s\.,kKmMBb]+$', l_str):
                        continue
                    lineas_L.append(l_str)
                
                limpio = "\n".join(lineas_L).replace('*', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('  ', ' ').strip()

                if len(limpio) < 3:
                    limpio = "¡Información oficial de los Leones del Caracas!"

                firma_texto = re.sub(r'[^a-zA-Z0-9]', '', limpio.lower())
                hash_id = hashlib.md5(firma_texto.encode('utf-8')).hexdigest()

                if hash_id in HISTORIAL_ENVIADOS:
                    continue

                guardar_memoria(hash_id)

                mensaje = f"🦁⚾ <b>{limpio}</b>"
                
                # Garantizamos el envío fotográfico si existen imágenes capturadas
                if len(imagenes) > 0:
                    tipo_m = "photo"
                    multimedia = imagenes
                else:
                    tipo_m = "text"
                    multimedia = []

                res = enviar_a_telegram(mensaje, multimedia, tipo_m)
                if res.get("ok"):
                    print(f"¡Publicación enviada con éxito! (Multimedia: {tipo_m}) Hash: " + hash_id, flush=True)
                else:
                    print("Reintento en texto plano: " + str(res), flush=True)
                    enviar_a_telegram(mensaje, [], "text")
                
                time.sleep(2)

    except Exception as e:
        print("Error general: " + str(e), flush=True)

if __name__ == "__main__":
    print("Bot definitivo optimizado para texto y fotos iniciado...", flush=True)
    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print("Error en bucle: " + str(err), flush=True)
        time.sleep(15)
