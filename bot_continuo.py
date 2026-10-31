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
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()
    except Exception as err:
        print(f"Error al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_actualizacion():
    global ultimo_tweet_id_memoria
    print(f"Buscando jugadas en tiempo real para @{X_USERNAME}...", flush=True)
    
    url_api = f"https://r.jina.ai/https://x.com/{X_USERNAME}?t={int(time.time())}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        response = requests.get(url_api, headers=headers, timeout=15)
        
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
                    texto_jugada = f"{lineas[i-1]}\n{linea}"
                
                tweet_candidato = texto_jugada
                break

        if not tweet_candidato:
            print("Sin nuevas jugadas en este ciclo.", flush=True)
            return

        # --- LIMPIEZA PROFUNDA DE TEXTO ---
        # 1. Eliminar etiquetas de imágenes Markdown completas: [![Image...]...]
        tweet_candidato = re.sub(r'\[\s*!\[Image[^\]]*\]\([^)]+\)\]\([^)]+\)', '', tweet_candidato)
        tweet_candidato = re.sub(r'!\[Image[^\]]*\]\([^)]+\)', '', tweet_candidato)
        
        # 2. Eliminar menciones al usuario de X
        tweet_candidato = re.sub(r'@leones_cbbc', '', tweet_candidato, flags=re.IGNORECASE)
        
        # 3. Limpiar enlaces web sueltos
        tweet_candidato = re.sub(r'https?://\S+', '', tweet_candidato)
        
        # 4. Limpiar fechas basura o textos institucionales
        tweet_candidato = re.sub(r'Born\s+[A-Za-z]+\s+\d+,\s+\d{4}', '', tweet_candidato)

        # 5. Formatear enlaces tipo [Texto](URL) dejando solo el texto visible
        tweet_candidato = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', tweet_candidato)

        # 6. Quitar asteriscos sueltos o símbolos de lista de Markdown y espacios dobles
        tweet_candidato = tweet_candidato.replace('*', '').replace('  ', ' ').strip()

        if len(tweet_candidato) < 10:
            return

        tweet_id = str(hash(tweet_candidato))
        print(f"ID evaluado: {tweet_id} | Memoria previa: {ultimo_tweet_id_memoria}", flush=True)

        if tweet_id == ultimo_tweet_id_memoria:
            print("Esta jugada ya fue publicada.", flush=True)
            return

        mensaje = f"🦁⚾ <b>¡Jugada en vivo!</b>\n\n{tweet_candidato}"
        
        resultado = enviar_a_telegram(mensaje)
        if resultado.get("ok"):
            print("¡Jugada ultra limpia enviada al canal!", flush=True)
            ultimo_tweet_id_memoria = tweet_id
        else:
            print("Telegram rechazó el envío.", flush=True)

    except Exception as e:
        print(f"Excepción en la verificación: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con formato ultra limpio y sin ruido...", flush=True)
    enviar_a_telegram("🦁🚀 <b>¡Bot optimizado y limpio de metadatos!</b>")

    while True:
        verificar_actualizacion()
        time.sleep(10)
