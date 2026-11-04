import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ARCHIVO_MEMORIA = "id_memoria.txt"

def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return None
    return None

def guardar_memoria(tweet_id):
    try:
        with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
            f.write(str(tweet_id))
    except Exception as e:
        print("Error al guardar memoria en disco: " + str(e), flush=True)

def enviar_a_telegram_multimedia(mensaje, lista_multimedia, tipo_multimedia="photo"):
    try:
        if tipo_multimedia == "photo" and len(lista_multimedia) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
            media_group = []
            for idx, img_url in enumerate(lista_multimedia[:10]):
                item = {"type": "photo", "media": img_url}
                if idx == 0:
                    item["caption"] = mensaje
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            payload = {"chat_id": CHAT_ID, "media": media_group}
            response = requests.post(url, json=payload, timeout=30)
            return response.json()

        elif tipo_multimedia == "video" and len(lista_multimedia) > 0:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": CHAT_ID,
                "video": lista_multimedia[0],
                "caption": mensaje,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json()

        elif tipo_multimedia == "photo" and len(lista_multimedia) == 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "photo": lista_multimedia[0],
                "caption": mensaje,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json()

        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json()

    except Exception as err:
        print("Error crítico al conectar con Telegram: " + str(err), flush=True)
        return {}

def verificar_actualizacion():
    ultimo_texto_memoria = cargar_memoria()
    print("Buscando nuevas publicaciones en @" + X_USERNAME + "...", flush=True)
    
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}?t={int(time.time())}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url_api, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print("Error HTTP del conector Jina: " + str(response.status_code), flush=True)
            return

        data = response.json()
        contenido_markdown = data.get("data", {}).get("content", "")
        
        if not contenido_markdown:
            print("El conector devolvió contenido vacío.", flush=True)
            return

        lineas = [l.strip() for l in contenido_markdown.split("\n") if l.strip()]
        
        tweet_candidato = None
        lista_imagenes = []
        video_url = None
        
        for i, linea in enumerate(lineas):
            if "Única cuenta oficial" in linea or "títulos de la LVBP" in linea:
                continue

            if any(tag in linea.lower() for tag in ["#leo", "#caraquistasoy"]):
                
                bloque_texto = []
                for k in range(max(0, i-2), i+1):
                    candidata = lineas[k]
                    c_lower = candidata.lower()
                    
                    if any(x in c_lower for x in ["leones_cbbc", "http://", "https://", "image", "born ", "caracas, venezuela", "joined "]):
                        continue
                    if re.match(r'^\[\s*\d+[mh]\s*\]', candidata):
                        continue
                    if re.match(r'^[\d\s\.,kKmMBb/:-]+$', candidata) and len(candidata) < 15:
                        continue
                        
                    if len(candidata.strip()) > 2:
                        bloque_texto.append(candidata)
                
                if bloque_texto:
                    tweet_candidato = "\n".join(bloque_texto)
                else:
                    tweet_candidato = linea

                for j in range(max(0, i-2), min(len(lineas), i+3)):
                    match_vid = re.search(r'(https?://\S+\.mp4\S*)', lineas[j])
                    if match_vid:
                        video_url = match_vid.group(1)
                        break
                
                if not video_url:
                    for j in range(max(0, i-2), min(len(lineas), i+3)):
                        match_img = re.search(r'(https?://pbs\.twimg\.com/media/[^)]+)', lineas[j])
                        if match_img:
                            img_link = match_img.group(1)
                            if img_link not in lista_imagenes:
                                lista_imagenes.append(img_link)
                break

        if not tweet_candidato:
            print("Monitoreando... No hay tuits nuevos con #LEO o #CaraquistaSoy.", flush=True)
            return

        texto_limpio = tweet_candidato
        texto_limpio = re.sub(r'\[\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'\(\s*\)', '', texto_limpio)
        texto_limpio = re.sub(r'\(blob:[^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'blob:\S+', '', texto_limpio)
        texto_limpio = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'Caracas,\s+Venezuela', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'@\w+', '', texto_limpio)
        texto_limpio = re.sub(r'https?://\S+', '', texto_limpio)
        
        lineas_limpias = []
        for l in texto_limpio.split("\n"):
            l_str = l.strip()
            if re.match(r'^[\d\s\.,kKmMBb]+$', l_str) and len(l_str) < 15:
                continue
            if l_str:
                lineas_limpias.append(l_str)
                
        texto_limpio = "\n".join(lineas_limpias)
        texto_limpio = texto_limpio.replace('*', '').replace('[', '').replace(']', '').replace('  ', ' ').strip()

        if len(texto_limpio) < 3:
            texto_limpio = "¡Información oficial de los Leones del Caracas!"

        print("Texto evaluado: " + texto_limpio[:40] + " | Memoria previa: " + str(ultimo_texto_memoria[:40] if ultimo_texto_memoria else "Ninguna"), flush=True)

        if texto_limpio == ultimo_texto_memoria:
            print("Este tuit exacto ya fue enviado al canal anteriormente (duplicado bloqueado).", flush=True)
            return

        mensaje = f"🦁⚾ <b>{texto_limpio}</b>"

        if video_url:
            tipo_m = "video"
            multimedia_a_enviar = [video_url]
        elif len(lista_imagenes) > 0:
            tipo_m = "photo"
            multimedia_a_enviar = lista_imagenes
        else:
            tipo_m = "photo"
            multimedia_a_enviar = []

        guardar_memoria(texto_limpio)

        resultado = enviar_a_telegram_multimedia(mensaje, multimedia_a_enviar, tipo_m)
        if resultado.get("ok"):
            print("¡Publicación enviada y guardada en memoria con éxito!", flush=True)
        else:
            print("Telegram rechazó el envío multimedia (intentando texto plano): " + str(resultado), flush=True)
            enviar_a_telegram_multimedia(mensaje, [], "photo")

    except Exception as e:
        print("Excepción general en la verificación: " + str(e), flush=True)

if __name__ == "__main__":
    print("Iniciando bot con sintaxis limpia y control anti-duplicados...", flush=True)

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print("Error atrapado en el bucle principal: " + str(err), flush=True)
        time.sleep(15)
