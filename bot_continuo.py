import requests
import os
import time

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
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as err:
        print(f"Error al conectar con Telegram: {err}", flush=True)
        return {}

def verificar_feed():
    global ultimo_tweet_id_memoria
    print("Consultando actualizaciones...", flush=True)
    
    url = f"https://fxtwitter.com/{X_USERNAME}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            # Verificamos que la respuesta sea realmente JSON antes de parsear
            try:
                data = res.json()
            except Exception:
                print("La API respondió pero el formato no es JSON válido (posible bloqueo temporal).", flush=True)
                return

            tweets = data.get("tweets", []) if isinstance(data, dict) else []

            if not tweets:
                print("No se encontraron tweets en este momento.", flush=True)
                return

            tweet_reciente = tweets[0]
            if not isinstance(tweet_reciente, dict):
                return

            tweet_id = str(tweet_reciente.get("id", ""))
            if not tweet_id:
                return

            print(f"ID actual en X: {tweet_id} | Memoria: {ultimo_tweet_id_memoria}", flush=True)

            if tweet_id == ultimo_tweet_id_memoria:
                print("Sin novedades, esperando siguiente ciclo.", flush=True)
                return

            tweet_texto = tweet_reciente.get("text", "")
            media = tweet_reciente.get("media", {})
            tiene_multimedia = bool(media and (media.get("photos") or media.get("videos") or media.get("mosaic")))
            
            texto_lower = tweet_texto.lower()
            es_jugada = any(palabra in texto_lower for palabra in [
                "jonrón", "hr", "hit", "doble", "triple", "carrera", "anota", 
                "out", "inning", "ponche", "marcador", "ganando", "final", "victoria"
            ])

            if tiene_multimedia or es_jugada:
                tweet_link = tweet_reciente.get("url", f"https://x.com/{X_USERNAME}/status/{tweet_id}")
                icono = "🦁📺" if tiene_multimedia else "⚾📊"
                mensaje = f"{icono} <b>Reporte de los Leones:</b>\n\n{tweet_texto}\n\n🔗 {tweet_link}"
                
                resultado = enviar_a_telegram(mensaje)
                if resultado.get("ok"):
                    print(f"¡Enviado a Telegram con éxito! (ID: {tweet_id})", flush=True)
                else:
                    print("Error al enviar a Telegram:", resultado, flush=True)
            else:
                print(f"Tweet {tweet_id} filtrado (sin multimedia ni relevancia de juego).", flush=True)

            ultimo_tweet_id_memoria = tweet_id
                
        else:
            print(f"Respuesta de la API HTTP: {res.status_code}", flush=True)
    except Exception as e:
        print(f"Excepción en la consulta: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con manejo seguro de errores...", flush=True)
    enviar_a_telegram("🦁🚀 <b>Bot actualizado y monitoreando el feed sin interrupciones.</b>")

    while True:
        try:
            verificar_feed()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
