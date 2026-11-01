import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None

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
    global ultimo_tweet_id_memoria
    print(f"Buscando jugadas y multimedia de alta calidad para @{X_USERNAME}...", flush=True)
    
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
        imagen_candidata = None
        
        for i, linea in enumerate(lineas):
            # Ampliamos el filtro para detectar #LEO o #CaraquistaSoy
            if any(tag in linea for tag in ["#LEO", "#leo", "#CaraquistaSoy", "#caraquistasoy"]):
                texto_jugada = linea
                if i > 0 and len(lineas[i-1]) > 5:
                    texto_jugada = f"{lineas[i-1]}\n{linea}"
                
                tweet_candidato = texto_jugada
                
                # Búsqueda mejorada de la imagen principal del tuit (excluyendo avatares pequeños de perfil)
                for j in range(max(0, i-4), min(len(lineas), i+5)):
                    # Buscamos URLs de imágenes de X que suelen venir en formato pbs.twimg.com/media
                    match_img = re.search(r'!\[Image[^\]]*\]\((https?://pbs\.twimg\.com/media/[^)]+)\)', lineas[j])
                    if match_img:
                        imagen_candidata = match_img.group(1)
                        break
                break

        if not tweet_candidato:
            print("No se encontraron tuits relevantes en este ciclo.", flush=True)
            return

        # Limpieza de texto manteniendo los datos impecables
        texto_limpio = re.sub(r'\[\s*!\[Image[^\]]*\]\([^)]+\)\]\([^)]+\)', '', tweet_candidato)
        texto_limpio = re.sub(r'!\[Image[^\]]*\]\([^)]+\)', '', texto_limpio)
        texto_limpio = re.sub(r'@leones_cbbc', '', texto_limpio, flags=re.IGNORECASE)
        texto_limpio = re.sub(r'https?://\S+', '', texto_limpio)
        texto_limpio = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}', '', texto_limpio)
        texto_limpio = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto_limpio)
        texto_limpio = texto_limpio.replace('*', '').replace('  ', ' ').strip()

        if len(texto_limpio) < 5:
            return

        tweet_id = str(hash(texto_limpio))
        print(f"ID evaluado: {tweet_id} | Memoria previa: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Esta publicación ya fue enviada anteriormente.", flush=True)
            return

        # Formateamos el mensaje según si trae la imagen oficial de alta resolución
        if imagen_candidata:
            mensaje = f"🦁🏆 <b>¡Publicación oficial / Victoria!</b>\n\n{texto_limpio}"
            print(f"¡Imagen oficial de alta calidad detectada: {imagen_candidata}", flush=True)
        else:
            mensaje = f"🦁⚾ <b>¡Jugada en vivo!</b>\n\n{texto_limpio}"

        resultado = enviar_a_telegram(mensaje, url_imagen=imagen_candidata)
        if resultado.get("ok"):
            print("¡Enviado con éxito al canal de Telegram!", flush=True)
            ultimo_tweet_id_memoria = tweet_id
        else:
            print(f"Telegram rechazó el envío: {resultado}", flush=True)

    except Exception as e:
        print(f"Excepción general en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con filtro de imágenes oficiales de alta calidad...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot sintonizado con filtro optimizado para imágenes oficiales!</b>")

    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error atrapado en el bucle principal: {err}", flush=True)
        time.sleep(10)
