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

def verificar_fxtwitter_inteligente():
    global ultimo_tweet_id_memoria
    print("Consultando tweets oficiales y jugadas de los Leones...", flush=True)
    url = f"https://api.fxtwitter.com/{X_USERNAME}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            tweets = []
            if isinstance(data, dict):
                raw_tweets = data.get("tweets")
                if isinstance(raw_tweets, list):
                    tweets = raw_tweets

            for tweet in tweets:
                if not isinstance(tweet, dict):
                    continue
                
                tweet_id = str(tweet.get("id", ""))
                if not tweet_id:
                    continue

                # Evitamos procesar tweets ya leídos
                if tweet_id == ultimo_tweet_id_memoria:
                    break

                if ultimo_tweet_id_memoria is None:
                    ultimo_tweet_id_memoria = tweet_id
                    print(f"ID inicial anclado en memoria: {tweet_id}", flush=True)
                    return

                # Analizamos el contenido del tweet
                tweet_texto = tweet.get("text", "")
                media = tweet.get("media", {})
                tiene_multimedia = bool(media and (media.get("photos") or media.get("videos") or media.get("mosaic")))
                
                # Palabras clave amplias enfocadas estrictamente en incidencias de juego y reportes
                texto_lower = tweet_texto.lower()
                es_jugada_o_marcador = any(palabra in texto_lower for palabra in [
                    "jonrón", "hr", "hit", "doble", "triple", "carrera", "anota", 
                    "out", "inning", "ponche", "pitcher", "lanzador", "marcador", 
                    "ganando", "en vivo", "playball", "alineación", "final", "victoria"
                ])

                # Filtro optimizado: Publicamos si tiene contenido visual O si reporta una jugada/incidencia del juego
                if tiene_multimedia or es_jugada_o_marcador:
                    tweet_link = tweet.get("url", f"https://x.com/{X_USERNAME}/status/{tweet_id}")
                    
                    icono = "🦁📺" if tiene_multimedia else "⚾📊"
                    mensaje = f"{icono} <b>Reporte de los Leones:</b>\n\n{tweet_texto}\n\n🔗 {tweet_link}"
                    
                    resultado = enviar_a_telegram(mensaje)
                    if resultado.get("ok"):
                        print(f"¡Publicado en Telegram con éxito! (ID: {tweet_id})", flush=True)
                    else:
                        print("Error al enviar a Telegram:", resultado, flush=True)
                else:
                    print(f"Tweet {tweet_id} omitido por filtro antispam.", flush=True)

                # Actualizamos la memoria con el tweet más reciente procesado
                ultimo_tweet_id_memoria = tweet_id
                break
                
        else:
            print("La API respondió pero está sincronizando...", flush=True)
    except Exception as e:
        print(f"Error consultando FxTwitter: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot definitivo (X Multimedia + Jugadas Oficiales)...", flush=True)
    while True:
        try:
            verificar_fxtwitter_inteligente()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30)
