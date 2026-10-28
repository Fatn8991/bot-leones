import requests
import os
import time

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN import requests
import os
import time

X_USERNAME = "leones_cbbc"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_guid_memoria = None

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

def verificar_fxtwitter():
    global ultimo_guid_memoria
    print("Consultando la API de FxTwitter...", flush=True)
    url = f"https://api.fxtwitter.com/{X_USERNAME}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            
            # Verificamos de forma segura el formato de la respuesta
            tweets = []
            if isinstance(data, dict):
                raw_tweets = data.get("tweets")
                if isinstance(raw_tweets, list):
                    tweets = raw_tweets
                elif "user" in data and isinstance(data["user"], dict):
                    user_tweets = data["user"].get("tweets")
                    if isinstance(user_tweets, list):
                        tweets = user_tweets
                elif "tweet" in data and isinstance(data["tweet"], dict):
                    tweets = [data["tweet"]]

            if tweets:
                ultimo_tweet = tweets[0]
                if isinstance(ultimo_tweet, dict):
                    tweet_id = str(ultimo_tweet.get("id", ""))
                    tweet_texto = ultimo_tweet.get("text", "")
                    tweet_link = ultimo_tweet.get("url", f"https://x.com/{X_USERNAME}/status/{tweet_id}")
                    
                    if not tweet_id:
                        return

                    print(f"-> ID actual encontrado: {tweet_id}", flush=True)
                    print(f"-> ID en memoria: {ultimo_guid_memoria}", flush=True)

                    if ultimo_guid_memoria is None:
                        ultimo_guid_memoria = tweet_id
                        print("Estado inicial anclado en memoria silenciosamente.", flush=True)
                        return

                    if tweet_id != ultimo_guid_memoria:
                        mensaje = f"🦁 <b>¡Nuevo Tweet de los Leones!</b>\n\n{tweet_texto}\n\n🔗 {tweet_link}"
                        resultado = enviar_a_telegram(mensaje)
                        if resultado.get("ok"):
                            ultimo_guid_memoria = tweet_id
                            print("¡Publicado en Telegram al instante!", flush=True)
                        else:
                            print("Error al enviar a Telegram:", resultado, flush=True)
                    else:
                        print("Sin nuevos tweets por ahora.", flush=True)
                    return
                
        print("La API respondió pero está sincronizando. Reintentando...", flush=True)
    except Exception as e:
        print(f"Error consultando FxTwitter: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando motor FxTwitter blindado...", flush=True)
    while True:
        try:
            verificar_fxtwitter()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)= os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

ultimo_guid_memoria = None

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

def verificar_fxtwitter():
    global ultimo_guid_memoria
    print("Consultando la API de FxTwitter...", flush=True)
    url = f"https://api.fxtwitter.com/{X_USERNAME}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            
            # Verificamos de forma segura el formato de la respuesta
            tweets = []
            if isinstance(data, dict):
                raw_tweets = data.get("tweets")
                if isinstance(raw_tweets, list):
                    tweets = raw_tweets
                elif "user" in data and isinstance(data["user"], dict):
                    user_tweets = data["user"].get("tweets")
                    if isinstance(user_tweets, list):
                        tweets = user_tweets
                elif "tweet" in data and isinstance(data["tweet"], dict):
                    tweets = [data["tweet"]]

            if tweets:
                ultimo_tweet = tweets[0]
                if isinstance(ultimo_tweet, dict):
                    tweet_id = str(ultimo_tweet.get("id", ""))
                    tweet_texto = ultimo_tweet.get("text", "")
                    tweet_link = ultimo_tweet.get("url", f"https://x.com/{X_USERNAME}/status/{tweet_id}")
                    
                    if not tweet_id:
                        return

                    print(f"-> ID actual encontrado: {tweet_id}", flush=True)
                    print(f"-> ID en memoria: {ultimo_guid_memoria}", flush=True)

                    if ultimo_guid_memoria is None:
                        ultimo_guid_memoria = tweet_id
                        print("Estado inicial anclado en memoria silenciosamente.", flush=True)
                        return

                    if tweet_id != ultimo_guid_memoria:
                        mensaje = f"🦁 <b>¡Nuevo Tweet de los Leones!</b>\n\n{tweet_texto}\n\n🔗 {tweet_link}"
                        resultado = enviar_a_telegram(mensaje)
                        if resultado.get("ok"):
                            ultimo_guid_memoria = tweet_id
                            print("¡Publicado en Telegram al instante!", flush=True)
                        else:
                            print("Error al enviar a Telegram:", resultado, flush=True)
                    else:
                        print("Sin nuevos tweets por ahora.", flush=True)
                    return
                
        print("La API respondió pero está sincronizando. Reintentando...", flush=True)
    except Exception as e:
        print(f"Error consultando FxTwitter: {e}", flush=True)

if __name__ == "__main__":
    print("Iniciando motor FxTwitter blindado...", flush=True)
    while True:
        try:
            verificar_fxtwitter()
        except Exception as e:
            print("Error en el ciclo principal:", e, flush=True)
        
        time.sleep(45)
