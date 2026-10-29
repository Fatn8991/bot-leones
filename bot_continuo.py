import requests
import os
import time

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_tweet_id_memoria = None
ultima_jugada_id_memoria = None

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

def verificar_fxtwitter_multimedia():
    global ultimo_tweet_id_memoria
    print("Consultando tweets multimedia de los Leones...", flush=True)
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

                # Verificamos si contiene fotos, videos o galerías
                media = tweet.get("media", {})
                tiene_multimedia = bool(media and (media.get("photos") or media.get("videos") or media.get("mosaic")))

                if tweet_id != ultimo_tweet_id_memoria:
                    if ultimo_tweet_id_memoria is None:
                        ultimo_tweet_id_memoria = tweet_id
                        print(f"ID multimedia inicial fijado: {tweet_id}", flush=True)
                        return

                    if tiene_multimedia:
                        tweet_texto = tweet.get("text", "")
                        tweet_link = tweet.get("url", f"https://x.com/{X_USERNAME}/status/{tweet_id}")
                        
                        mensaje = f"🦁📺 <b>¡Nuevo contenido multimedia de los Leones!</b>\n\n{tweet_texto}\n\n🔗 {tweet_link}"
                        resultado = enviar_a_telegram(mensaje)
                        
                        if resultado.get("ok"):
                            ultimo_tweet_id_memoria = tweet_id
                            print("¡Multimedia publicada en Telegram!", flush=True)
                        break
                    else:
                        # Si es texto plano, avanzamos el puntero para no reevaluarlo
                        ultimo_tweet_id_memoria = tweet_id
                        break
    except Exception as e:
        print(f"Error en FxTwitter multimedia: {e}", flush=True)

def verificar_jugada_jugada():
    global ultima_jugada_id_memoria
    # Nota: Aquí podemos conectar directamente al endpoint de la API de la LVBP 
    # o la fuente de datos que alimenta las jugadas de TuJonrón.
    try:
        # Ejemplo de consulta a una API de jugadas en tiempo real de la LVBP
        # endpoint_lvbp = "https://api.lvbp.com/v1/games/live-feed" (o similar)
        # res = requests.get(endpoint_lvbp, timeout=10)
        # ... procesar jugada nueva ...
        pass
    except Exception as e:
        print(f"Error consultando jugada a jugada: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot híbrido (Multimedia + Jugada a Jugada)...", flush=True)
    while True:
        try:
            verificar_fxtwitter_multimedia()
            verificar_jugada_jugada()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
