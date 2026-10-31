import requests
import os
import time
import re

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None

def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": True  # <-- Esto elimina la tarjeta grande de vista previa del enlace
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"Respuesta de Telegram: {response.text}", flush=True)
        return response.json()
    except Exception as err:
        print(f"Error al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    global ultimo_tweet_id_memoria
    print(f"Buscando jugadas con #LEO para @{X_USERNAME}...", flush=True)
    
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        response = requests.get(url_api, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Error HTTP del conector: {response.status_code}", flush=True)
            return

        data = response.json()
        contenido_markdown = data.get("data", {}).get("content", "")
        
        if not contenido_markdown:
            return

        lineas = [l.strip() for l in contenido_markdown.split("\n") if l.strip()]
        
        tweet_candidato = None
        for i, linea in enumerate(lineas):
            if "#LEO" in linea or "#leo" in linea:
                texto_jugada = linea
                if i > 0 and len(lineas[i-1]) > 10:
                    texto_jugada = f"{lineas[i-1]}\n\n{linea}"
                
                tweet_candidato = texto_jugada
                break

        if not tweet_candidato:
            print("No se encontraron jugadas nuevas con #LEO en este ciclo.", flush=True)
            return

        # Limpiamos URLs, etiquetas de imágenes y textos basura como fechas extrañas
        tweet_candidato = re.sub(r'https?://\S+', '', tweet_candidato)
        tweet_candidato = re.sub(r'\[Image[^\]]*\]\([^)]+\)', '', tweet_candidato)
        tweet_candidato = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}', '', tweet_candidato).strip()

        if len(tweet_candidato) < 10:
            return

        tweet_id = str(hash(tweet_candidato))
        print(f"ID evaluado: {tweet_id} | Memoria previa: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Esta jugada ya fue publicada anteriormente.", flush=True)
            return

        # Mensaje limpio sin enlaces para evitar tarjetas de vista previa
        mensaje = f"🦁⚾ <b>¡Jugada en vivo!</b>\n\n{tweet_candidato}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            print("¡Jugada limpia enviada con éxito al canal!", flush=True)
            ultimo_tweet_id_memoria = tweet_id
        else:
            print("Telegram rechazó el envío.", flush=True)

    except Exception as e:
        print(f"Excepción en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con formato ultra limpio...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot optimizado: solo texto de jugadas en vivo!</b>")

    while True:
        verificar_actualizacion()
        time.sleep(30)
