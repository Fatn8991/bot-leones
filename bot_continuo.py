import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_enlace_memoria = None

def enviar_a_telegram(mensaje, url_imagen=None):
    if url_imagen:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID,
            "photo": url_imagen,
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
        response = requests.post(url, json=payload, timeout=20)
        print(f"Respuesta de Telegram: {response.text}", flush=True)
        return response.json()
    except Exception as err:
        print(f"Error crítico al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    global ultimo_enlace_memoria
    print(f"Buscando publicaciones limpias para @{X_USERNAME}...", flush=True)
    
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
        imagen_candidata = None
        
        for i, linea in enumerate(lineas):
            if "Única cuenta oficial" in linea or "títulos de la LVBP" in linea:
                continue

            if any(tag in linea for tag in ["#LEO", "#leo", "#CaraquistaSoy", "#caraquistasoy"]):
                
                # Extraemos el texto real del tuit ignorando metadatos
                texto_encontrado = ""
                for k in range(max(0, i-3), i+1):
                    candidata = lineas[k]
                    if any(x in candidata.lower() for x in ["leones_cbbc", "http://", "https://", "![image", "video"]):
                        continue
                    if re.match(r'^\[\s*\d+[mh]\s*\]', candidata):
                        continue
                    if len(candidata) > 5:
                        texto_encontrado = candidata
                        break
                
                if not texto_encontrado:
                    texto_encontrado = linea

                tweet_candidato = texto_encontrado
                
                # Obtenemos el identificador/enlace único del tuit para evitar duplicados
                for j in range(max(0, i-5), min(len(lineas), i+6)):
                    match_link = re.search(r'https?://(?:x|twitter)\.com/[^/]+/status/(\d+)', lineas[j])
                    if match_link:
                        enlace_candidato = match_link.group(1)
                        break
                
                # Buscamos la imagen oficial de alta resolución asociada
                for j in range(max(0, i-4), min(len(lineas), i+5)):
                    match_img = re.search(r'!\[Image[^\]]*\]\((https?://pbs\.twimg\.com/media/[^)]+)\)', lineas[j])
                    if match_img:
                        imagen_candidata = match_img.group(1)
                        break
                break

        if not tweet_candidato:
            print("No se encontraron publicaciones relevantes en este ciclo.", flush=True)
            return

        if not enlace_candidato:
            enlace_candidato = tweet_candidato[:30]

        print(f"ID/Enlace evaluado: {enlace_candidato} | Memoria previa: {ultimo_enlace_memoria}", flush=True)

        if enlace_candidato == ultimo_enlace_memoria:
            print("Esta publicación ya fue enviada anteriormente (bloqueado).", flush=True)
            return

        # --- LIMPIEZA PROFUNDA DE TEXTO ---
        texto_limpio = tweet_candidato
        texto_limpio = re.sub(r'\[\s*\d+[mh]\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'\[Video\s*\d*\]', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'\(blob:[^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'blob:\S+', '', texto_limpio)
        texto_limpio = re.sub(r'!\[Image[^\]]*\]\([^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto_limpio)
        texto_limpio = re.sub(r'@\w+', '', texto_limpio)
        texto_limpio = re.sub(r'https?://\S+', '', texto_limpio)
        texto_limpio = re.sub(r'\[\s*\]', '', texto_limpio)
        texto_limpio = re.sub(r'\(\s*\)', '', texto_limpio)
        
        texto_limpio = texto_limpio.replace('*', '').replace('  ', ' ').strip()

        if len(texto_limpio) < 3:
            texto_limpio = "¡Publicación oficial de los Leones del Caracas!"

        if imagen_candidata:
            mensaje = f"🦁🏆 <b>{texto_limpio}</b>"
        else:
            mensaje = f"🦁⚾ <b>{texto_limpio}</b>"

        # Guardamos en memoria ANTES de enviar para prevenir reenvíos en caso de retardo
        ultimo_enlace_memoria = enlace_candidato

        resultado = enviar_a_telegram(mensaje, url_imagen=imagen_candidata)
        if resultado.get("ok"):
            print("¡Publicación enviada y registrada en memoria con éxito!", flush=True)
        else:
            print(f"Telegram rechazó el envío: {resultado}", flush=True)

    except Exception as e:
        print(f"Excepción general en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot en modo silencioso y continuo...", flush=True)
    # Ya no enviamos mensajes de prueba al iniciar para evitar spam en el canal

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error atrapado en el bucle principal: {err}", flush=True)
        time.sleep(15)
