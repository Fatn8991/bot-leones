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
        "disable_web_page_preview": False
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
    print(f"Buscando actualizaciones reales para @{X_USERNAME}...", flush=True)
    
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
        for linea in lineas:
            # Lista negra estricta: si la línea contiene cualquiera de estas frases, se descarta de inmediato
            texto_minus = linea.lower()
            if any(palabra in texto_minus for palabra in [
                "única cuenta oficial", 
                "títulos de la lvbp", 
                "series del caribe", 
                "x (formerly twitter)", 
                "on x", 
                "following", 
                "followers",
                "joined",
                "http",
                "[image"
            ]):
                continue
                
            # Validamos que sea un texto sustancial y limpio
            if len(linea) > 20:
                # Limpiamos cualquier residuo de formato Markdown
                linea_limpia = re.sub(r'\[Image[^\]]*\]\([^)]+\)', '', linea).strip()
                if len(linea_limpia) > 20:
                    tweet_candidato = linea_limpia
                    break

        if not tweet_candidato:
            print("No hay tuits nuevos de juego en este ciclo (todo lo demás fue filtrado).", flush=True)
            return

        tweet_id = str(hash(tweet_candidato))
        print(f"ID evaluado: {tweet_id} | Memoria previa: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("El tuit ya fue procesado anteriormente.", flush=True)
            return

        mensaje = f"🦁⚾ <b>¡Actualización de los Leones!</b>\n\n{tweet_candidato}\n\n🔗 <a href='https://x.com/{X_USERNAME}'>Ver en X</a>"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            print("¡Tuit real de juego enviado con éxito al canal!", flush=True)
            ultimo_tweet_id_memoria = tweet_id
        else:
            print("Telegram rechazó el envío.", flush=True)

    except Exception as e:
        print(f"Excepción en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con filtro estricto anti-perfil...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Filtro estricto activado! Esperando nuevas jugadas...</b>")

    while True:
        verificar_actualizacion()
        time.sleep(45)
