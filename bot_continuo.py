import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_enlace_memoria = None

def enviar_a_telegram(mensaje, url_multimedia=None, tipo_multimedia="photo"):
    """
    Envía contenido a Telegram manejando texto, fotos o videos nativos.
    """
    if url_multimedia:
        if tipo_multimedia == "video":
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": CHAT_ID,
                "video": url_multimedia,
                "caption": mensaje,
                "parse_mode": "HTML"
            }
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "photo": url_multimedia,
                "caption": mensaje,
                "parse_mode": "HTML"
            }
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Respuesta de Telegram: {response.text}", flush=True)
        return response.json()
    except Exception as err:
        print(f"Error crítico al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    global ultimo_enlace_memoria
    print(f"Buscando publicaciones, fotos y videos para @{X_USERNAME}...", flush=True)
    
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
        multimedia_url = None
        tipo_multimedia = "photo"
        
        for i, linea in enumerate(lineas):
            if "Única cuenta oficial" in linea or "títulos de la LVBP" in linea:
                continue

            if any(tag in linea for tag in ["#LEO", "#leo", "#CaraquistaSoy", "#caraquistasoy"]):
                
                # Capturamos el bloque de texto del tuit
                bloque_completo = []
                for k in range(max(0, i-3), min(len(lineas), i+2)):
                    candidata = lineas[k]
                    if "Única cuenta" in candidata or "![image" in candidata and "pbs.twimg.com" not in candidata:
                        continue
                    bloque_completo.append(candidata)
                
                tweet_candidato = "\n".join(bloque_completo)
                
                # Obtenemos el enlace único del tuit para evitar duplicados
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    match_link = re.search(r'https?://(?:x|twitter)\.com/[^/]+/status/(\d+)', lineas[j])
                    if match_link:
                        enlace_candidato = match_link.group(1)
                        break
                
                # 1. Buscamos si hay un video directo o enlace mp4 en el entorno del tuit
                for j in range(max(0, i-4), min(len(lineas), i+5)):
                    match_vid = re.search(r'(https?://\S+\.mp4\S*)', lineas[j])
                    if match_vid:
                        multimedia_url = match_vid.group(1)
                        tipo_multimedia = "video"
                        break
                
                # 2. Si no hay video directo, buscamos la foto oficial de alta resolución
                if not multimedia_url:
                    for j in range(max(0, i-4), min(len(lineas), i+5)):
                        match_img = re.search(r'!\[Image[^\]]*\]\((https?://pbs\.twimg\.com/media/[^)]+)\)', lineas[j])
                        if match_img:
                            multimedia_url = match_img.group(1)
                            tipo_multimedia = "photo"
                            break
                break

        if not tweet_candidato:
            print("No se encontraron publicaciones relevantes en este ciclo.", flush=True)
            return

        if not enlace_candidato:
            enlace_candidato = tweet_candidato[:30]

        print(f"ID/Enlace evaluado: {enlace_candidato} | Memoria previa: {ultimo_enlace_memoria}", flush=True)

        if enlace_candidato == ultimo_enlace_memoria:
            print("Esta publicación ya fue enviada (bloqueada).", flush=True)
            return

        # --- LIMPIEZA INTELIGENTE DE TEXTO ---
        texto_limpio = tweet_candidato
        lineas_finales = []
        for l in texto_limpio.split("\n"):
            l_lower = l.lower()
            if any(x in l_lower for x in ["leones_cbbc", "http://", "https://", "blob:", "video", "![image"]):
                continue
            if re.match(r'^\[\s*\d+[mh]\s*\]', l):
                continue
            if len(l.strip()) > 0:
                lineas_finales.append(l)

        texto_limpio = "\n".join(lineas_finales)
        texto_limpio = re.sub(r'\[Video\s*\d*\]', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto_limpio)
        texto_limpio = re.sub(r'@\w+', '', texto_limpio)
        texto_limpio = re.sub(r'[\(\)\[\]]', '', texto_limpio)
        texto_limpio = texto_limpio.replace('*', '').replace('  ', ' ').strip()

        if len(texto_limpio) < 3:
            texto_limpio = "¡Publicación oficial de los Leones del Caracas!"

        # Formateamos el mensaje según el tipo de contenido multimedia
        if multimedia_url:
            if tipo_multimedia == "video":
                mensaje = f"🦁🎥 <b>{texto_limpio}</b>"
            else:
                mensaje = f"🦁🏆 <b>{texto_limpio}</b>"
        else:
            mensaje = f"🦁⚾ <b>{texto_limpio}</b>"

        ultimo_enlace_memoria = enlace_candidato

        resultado = enviar_a_telegram(mensaje, url_multimedia=multimedia_url, tipo_multimedia=tipo_multimedia)
        if resultado.get("ok"):
            print(f"¡Publicación con {tipo_multimedia} enviada con éxito!", flush=True)
        else:
            print(f"Telegram rechazó el envío (probando respaldo en texto): {resultado}", flush=True)
            # Respaldo de seguridad si el enlace del video presenta restricciones de plataforma
            enviar_a_telegram(mensaje)

    except Exception as e:
        print(f"Excepción general en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con soporte integrado para fotos y videos nativos...", flush=True)

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error atrapado en el bucle principal: {err}", flush=True)
        time.sleep(15)
