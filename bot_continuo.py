import requests
import os
import time

X_USERNAME = "leones_cbbc"
GAME_ID = "870056"  # ID del partido activo
TUJONRON_API_URL = f"https://gameday.tujonron.com/live/game/{GAME_ID}.json"

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
                        ultimo_tweet_id_memoria = tweet_id
                        break
    except Exception as e:
        print(f"Error en FxTwitter multimedia: {e}", flush=True)

def verificar_jugada_jugada():
    global ultima_jugada_id_memoria
    print("Consultando jugada a jugada en vivo...", flush=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    try:
        res = requests.get(TUJONRON_API_URL, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            
            # Buscamos la lista de jugadas en la respuesta JSON
            jugadas = data.get("plays") or data.get("playByPlay") or data.get("plays_list") or []
            
            if isinstance(data, list):
                jugadas = data

            if jugadas and isinstance(jugadas, list):
                ultima_jugada = jugadas[0] # La jugada más reciente
                
                # Extraemos el identificador y texto de la jugada
                jugada_id = str(ultima_jugada.get("id") or ultima_jugada.get("play_id") or hash(str(ultima_jugada)))
                descripcion = ultima_jugada.get("description") or ultima_jugada.get("text") or ultima_jugada.get("title") or str(ultima_jugada)
                inning = ultima_jugada.get("inning", "")
                
                if jugada_id != ultima_jugada_id_memoria:
                    if ultima_jugada_id_memoria is None:
                        ultima_jugada_id_memoria = jugada_id
                        print(f"ID inicial de jugada anclado: {jugada_id}", flush=True)
                        return
                    
                    mensaje = f"⚾ <b>¡JUGADA EN VIVO!</b> ({inning})\n\n{descripcion}"
                    resultado = enviar_a_telegram(mensaje)
                    
                    if resultado.get("ok"):
                        ultima_jugada_id_memoria = jugada_id
                        print("¡Jugada reportada a Telegram!", flush=True)
                else:
                    print("Sin nuevas jugadas por ahora.", flush=True)
    except Exception as e:
        print(f"Error consultando API TuJonron: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando bot con motor doble (Multimedia X + Jugada a Jugada TuJonrón)...", flush=True)
    while True:
        try:
            verificar_fxtwitter_multimedia()
            verificar_jugada_jugada()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(30) # 30 segundos para mayor velocidad durante los juegos
