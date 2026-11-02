import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_enlace_memoria = None

def enviar_a_telegram(mensaje, url_multimedia=None, tipo_multimedia="photo"):
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
    print(f"Buscando jugadas y publicaciones oficiales para @{X_USERNAME}...", flush=True)
    
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

            # Detectamos tanto las jugadas (#LEO / #leo) como las publicaciones oficiales (#CaraquistaSoy)
            if any(tag in linea for tag in ["#LEO", "#leo", "#CaraquistaSoy", "#caraquistasoy"]):
                
                # Rescatamos el texto real tomando la línea del hashtag y la línea inmediatamente superior si existe
                texto_tuit = linea
                if i > 0 and len(lineas[i-1]) > 3 and "Única cuenta" not in lineas[i-1] and "![image" not in lineas[i-1]:
                    texto_tuit = f"{lineas[i-1]}\n{linea}"
                
                tweet_candidato = texto_tuit
                
                # Buscamos el enlace único del tuit para el control anti-duplicados
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    match_link = re.search(r'https?://(?:x|twitter)\.com/[^/]+/status/(\d+)', lineas[j])
                    if match_link:
                        enlace_candidato = match_link.group(1)
                        break
                
                # Buscamos si hay un video directo (.mp4)
                for j in range(max(0, i-4), min(len(lineas), i+5)):
                    match_vid = re.search(r'(https?://\S+\.mp4\S*)', lineas[j])
                    if match_vid:
                        multimedia_url = match_vid.group(1)
                        tipo_multimedia = "video"
                        break
                
                # Si no hay video, buscamos la foto oficial de alta resolución
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

        # --- LIMPIEZA LIMPIA Y SEGURA DEL TEXTO ---
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
            texto_limpio = "¡Acción de los Leones del Caracas!"

        # Formato de mensaje adaptado
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
            print("¡Publicación enviada con éxito conservando su texto!", flush=True)
        else:
            print(f"Telegram rechazó el envío multimedia (intentando por texto plano): {resultado}", flush=True)
            enviar_a_telegram(mensaje)

    except Exception as e:
        print(f"Excepción general en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con recuperación de texto y soporte multimedia...", flush=True)

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error atrapado en el bucle principal: {err}", flush=True)
        time.sleep(15)
