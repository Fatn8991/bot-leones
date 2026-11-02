import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ARCHIVO_MEMORIA = "id_memoria.txt"

def cargar_memoria():
    """Carga el último ID de tuit procesado desde disco para sobrevivir a reinicios de Render."""
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r") as f:
                return f.read().strip()
        except:
            return None
    return None

def guardar_memoria(tweet_id):
    """Guarda el ID del tuit en disco inmediatamente para evitar spam por reintentos."""
    try:
        with open(ARCHIVO_MEMORIA, "w") as f:
            f.write(str(tweet_id))
    except Exception as e:
        print(f"Error al guardar memoria en disco: {e}", flush=True)

def enviar_a_telegram_multimedia(mensaje, lista_multimedia, tipo_multimedia="photo"):
    """
    Envía contenido a Telegram. Si hay múltiples imágenes, usa un álbum (sendMediaGroup);
    si es un solo video o foto, usa sus métodos individuales con soporte de texto (caption).
    """
    try:
        # Caso 1: Múltiples imágenes (Álbum)
        if tipo_multimedia == "photo" and len(lista_multimedia) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
            media_group = []
            for idx, img_url in enumerate(lista_multimedia[:10]): # Telegram permite hasta 10
                item = {
                    "type": "photo",
                    "media": img_url
                }
                # Añadimos el texto en la primera foto del álbum
                if idx == 0:
                    item["caption"] = mensaje
                    item["parse_mode"] = "HTML"
                media_group.append(item)
            
            payload = {
                "chat_id": CHAT_ID,
                "media": media_group
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.json()

        # Caso 2: Un solo video
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

        # Caso 3: Una sola foto
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

        # Caso 4: Solo texto (Jugadas #LEO o reportes sin multimedia)
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
        print(f"Error crítico al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    ultimo_enlace_memoria = cargar_memoria()
    print(f"Buscando actualizaciones para @{X_USERNAME}...", flush=True)
    
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}?t={int(time.time())}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url_api, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Error HTTP del conector Jina: {response.status_code}", flush=True)
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

            # Detectamos cualquiera de las etiquetas clave (#LEO o #CaraquistaSoy en cualquier variante de mayúsculas/minúsculas)
            if any(tag in linea.lower() for tag in ["#leo", "#caraquistasoy"]):
                
                # Rescatamos el bloque de texto completo del tuit mirando hacia arriba
                bloque_texto = []
                for k in range(max(0, i-4), i+1):
                    candidata = lineas[k]
                    if any(x in candidata.lower() for x in ["leones_cbbc", "http://", "https://", "![image"]):
                        continue
                    if re.match(r'^\[\s*\d+[mh]\s*\]', candidata):
                        continue
                    if len(candidata.strip()) > 2:
                        bloque_texto.append(candidata)
                
                if bloque_texto:
                    tweet_candidato = "\n".join(bloque_texto)
                else:
                    tweet_candidato = linea

                # Búsqueda robusta del ID / enlace único del tuit
                for j in range(max(0, i-6), min(len(lineas), i+7)):
                    match_link = re.search(r'https?://(?:x|twitter)\.com/[^/]+/status/(\d+)', lineas[j])
                    if match_link:
                        enlace_candidato = match_link.group(1)
                        break
                
                if not enlace_candidato:
                    for j in range(max(0, i-6), min(len(lineas), i+7)):
                        match_id = re.search(r'/status/(\d+)', lineas[j])
                        if match_id:
                            enlace_candidato = match_id.group(1)
                            break

                # 1. Buscamos si hay un video directo (.mp4)
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    match_vid = re.search(r'(https?://\S+\.mp4\S*)', lineas[j])
                    if match_vid:
                        video_url = match_vid.group(1)
                        break
                
                # 2. Si no hay video, recolectamos TODAS las imágenes oficiales de alta resolución del tuit (para álbumes de 1 o más fotos)
                if not video_url:
                    for j in range(max(0, i-5), min(len(lineas), i+6)):
                        match_img = re.search(r'!\[Image[^\]]*\]\((https?://pbs\.twimg\.com/media/[^)]+)\)', lineas[j])
                        if match_img:
                            img_link = match_img.group(1)
                            if img_link not in lista_imagenes:
                                lista_imagenes.append(img_link)
                break

        if not tweet_candidato:
            print("No se encontraron publicaciones relevantes en este ciclo.", flush=True)
            return

        if not enlace_candidato:
            enlace_candidato = str(hash(tweet_candidato[:50]))

        print(f"ID evaluado: {enlace_candidato} | Memoria previa en disco: {ultimo_enlace_memoria}", flush=True)

        if enlace_candidato == ultimo_enlace_memoria:
            print("Esta publicación ya fue enviada anteriormente (duplicado bloqueado).", flush=True)
            return

        # --- LIMPIEZA INTELIGENTE DE TEXTO ---
        texto_limpio = tweet_candidato
        texto_limpio = re.sub(r'\[\s*\d+[mh]\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'\[Video\s*\d*\]', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'\(blob:[^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'blob:\S+', '', texto_limpio)
        texto_limpio = re.sub(r'!\[Image[^\]]*\]\([^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto_limpio)
        texto_limpio = re.sub(r'@\w+', '', texto_limpio)
        texto_limpio = re.sub(r'https?://\S+', '', texto_limpio)
        texto_limpio = re.sub(r'[\(\)\[\]]', '', texto_limpio)
        texto_limpio = texto_limpio.replace('*', '').replace('  ', ' ').strip()

        if len(texto_limpio) < 3:
            texto_limpio = "¡Acción oficial de los Leones del Caracas!"

        # Formateo de encabezados según el tipo de contenido
        if video_url:
            mensaje = f"🦁🎥 <b>{texto_limpio}</b>"
            tipo_m = "video"
            multimedia_a_enviar = [video_url]
        elif len(lista_imagenes) > 0:
            mensaje = f"🦁🏆 <b>{texto_limpio}</b>"
            tipo_m = "photo"
            multimedia_a_enviar = lista_imagenes
        else:
            # Jugada a jugada (#LEO con rivales variables como #CAR, #TIG, etc.)
            mensaje = f"🦁⚾ <b>{texto_limpio}</b>"
            tipo_m = "photo"
            multimedia_a_enviar = []

        # Guardamos en disco ANTES de enviar para garantizar cero duplicados por reintentos o reinicios de Render
        guardar_memoria(enlace_candidato)

        resultado = enviar_a_telegram_multimedia(mensaje, multimedia_a_enviar, tipo_m)
        if resultado.get("ok"):
            print("¡Publicación procesada y enviada con éxito!", flush=True)
        else:
            print(f"Telegram rechazó el envío multimedia (intentando respaldo de texto plano): {resultado}", flush=True)
            enviar_a_telegram_multimedia(mensaje, [], "photo")

    except Exception as e:
        print(f"Excepción general en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot definitivo para Leones del Caracas...", flush=True)

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error atrapado en el bucle principal: {err}", flush=True)
        time.sleep(15)
