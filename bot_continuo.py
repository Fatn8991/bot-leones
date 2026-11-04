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
            with open(ARCHIVO_MEMORIA, "r") as f:
                return f.read().strip()
        except:
            return None
    return None

def guardar_memoria(tweet_id):
    try:
        with open(ARCHIVO_MEMORIA, "w") as f:
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
    ultimo_enlace_memoria = cargar_memoria()
    print("Buscando actualizaciones para @" + X_USERNAME + "...", flush=True)
    
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
        enlace_candidato = None
        lista_imagenes = []
        video_url = None
        
        for i, linea in enumerate(lineas):
            if "Única cuenta oficial" in linea or "títulos de la LVBP" in linea:
                continue

            # Detectamos las etiquetas oficiales
            if any(tag in linea.lower() for tag in ["#leo", "#caraquistasoy"]):
                
                # BÚSQUEDA ESTRICTA DE ID NUMÉRICO OFICIAL DE X
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    match_link = re.search(r'https?://(?:x|twitter)\.com/[^/]+/status/(\d+)', lineas[j])
                    if match_link:
                        enlace_candidato = match_link.group(1)
                        break
                
                if not enlace_candidato:
                    for j in range(max(0, i-5), min(len(lineas), i+6)):
                        match_id = re.search(r'/status/(\d+)', lineas[j])
                        if match_id:
                            enlace_candidato = match_id.group(1)
                            break

                # Si el tuit no tiene ID numérico oficial de X, lo descartamos de inmediato para evitar duplicados falsos
                if not enlace_candidato:
                    continue

                # Extracción del bloque de texto limpio
                bloque_texto = []
                for k in range(max(0, i-3), i+1):
                    candidata = lineas[k]
                    c_lower = candidata.lower()
                    
                    if any(x in c_lower for x in ["leones_cbbc", "http://", "https://", "![image", "born ", "caracas, venezuela", "joined "]):
                        continue
                    if re.match(r'^\[\s*\d+[mh]\s*\]', candidata):
                        continue
                    if re.match(r'^[\d\s\.,kKmMBb/:-]+\$', candidata) and len(candidata) < 15:
                        continue
                        
                    if len(candidata.strip()) > 2:
                        bloque_texto.append(candidata)
                
                if bloque_texto:
                    tweet_candidato = "\n".join(bloque_texto)
                else:
                    tweet_candidato = linea

                # Búsqueda de video (.mp4)
                for j in range(max(0, i-3), min(len(lineas), i+4)):
                    match_vid = re.search(r'(https?://\S+\.mp4\S*)', lineas[j])
                    if match_vid:
                        video_url = match_vid.group(1)
                        break
                
                # Recolección de imágenes
                if not video_url:
                    for j in range(max(0, i-3), min(len(lineas), i+4)):
                        match_img = re.search(r'!\[Image[^\]]*\]\((https?://pbs\.twimg\.com/media/[^)]+)\)', lineas[j])
                        if match_img:
                            img_link = match_img.group(1)
                            if img_link not in lista_imagenes:
                                lista_imagenes.append(img_link)
                break

        if not tweet_candidato or not enlace_candidato:
            print("No se encontraron publicaciones con ID válido en este ciclo.", flush=True)
            return

        print("ID oficial evaluado: " + str(enlace_candidato) + " | Memoria previa en disco: " + str(ultimo_enlace_memoria), flush=True)

        if enlace_candidato == ultimo_enlace_memoria:
            print("Esta publicación ya fue enviada anteriormente (duplicado bloqueado por ID).", flush=True)
            return

        # --- LIMPIEZA DE TEXTO ---
        texto_limpio = tweet_candidato
        texto_limpio = re.sub(r'\[\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'\(\s*\)', '', texto_limpio)
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto_limpio)
        texto_limpio = re.sub(r'!\[Image[^\]]*\]\([^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'\(blob:[^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'blob:\S+', '', texto_limpio)
        texto_limpio = re.sub(r'\[\s*\d+[mh]\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'Caracas,\s+Venezuela', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'@\w+', '', texto_limpio)
        texto_limpio = re.sub(r'https?://\S+', '', texto_limpio)
        
        lineas_limpias = []
        for l in texto_limpio.split("\n"):
            l_str = l.strip()
            if re.match
