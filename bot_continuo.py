import hashlib
import html
import os
import re
import time
import xml.etree.ElementTree as ET
import requests

X_USERNAME = os.getenv("X_USERNAME", "leones_cbbc")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MEMORIA_FILE = "id_memoria.txt"
INTERVALO_SEGUNDOS = 10


def cargar_memoria():
    if not os.path.exists(MEMORIA_FILE):
        return set()
    with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def guardar_hash(h):
    with open(MEMORIA_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")


def generar_hash(texto_base):
    return hashlib.md5(texto_base.encode("utf-8")).hexdigest()


def limpiar_html(raw_html):
    if not raw_html:
        return ""
    texto = re.sub(r"<br\s*/?>", "\n", raw_html, flags=re.IGNORECASE)
    texto = re.sub(r"</p\s*>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extraer_imagenes(raw_html, base_dominio="https://nitter.jaydenha.uk"):
    if not raw_html:
        return []
    urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html, flags=re.IGNORECASE)
    limpias = []
    for u in urls:
        u_limpia = html.unescape(u).strip()
        if u_limpia.startswith("/"):
            u_limpia = f"{base_dominio.rstrip('/')}{u_limpia}"
        if "profile_images" not in u_limpia and u_limpia not in limpias:
            limpias.append(u_limpia)
    return limpias


def enviar_a_telegram(mensaje, imagenes):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en variables de entorno.", flush=True)
        return False

    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    try:
        if imagenes:
            foto_url = imagenes[0]
            caption = mensaje[:1024]
            res = requests.post(
                f"{base_url}/sendPhoto",
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "photo": foto_url,
                    "caption": caption,
                },
                timeout=20,
            )
            if res.status_code == 200:
                return True
            print(f"Aviso sendPhoto status {res.status_code}: {res.text}", flush=True)

        res_msg = requests.post(
            f"{base_url}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensaje[:4096],
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if res_msg.status_code == 200:
            return True
        print(f"Error sendMessage status {res_msg.status_code}: {res_msg.text}", flush=True)
        return False
    except Exception as e:
        print(f"Error enviando a Telegram: {e}", flush=True)
        return False


def verificar_actualizacion():
    instancias_rss = [
        f"https://nitter.jaydenha.uk/{X_USERNAME}/rss",
        f"https://nitter.netbub.com/{X_USERNAME}/rss",
    ]

    contenido_xml = None
    dominio_activo = "https://nitter.jaydenha.uk"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for url in instancias_rss:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Consultando {url} -> status {res.status_code}, len {len(res.text)}", flush=True)
            if res.status_code == 200 and ("<rss" in res.text or "<feed" in res.text):
                contenido_xml = res.text
                dominio_activo = url.split(f"/{X_USERNAME}/rss")[0]
                break
        except Exception as e:
            print(f"Error consultando {url}: {e}", flush=True)
            continue

    if not contenido_xml:
        print("Aviso: Ninguna instancia RSS respondió con XML válido en este ciclo.", flush=True)
        return

    try:
        root = ET.fromstring(contenido_xml)
    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}", flush=True)
        return

    items = root.findall(".//item")
    if not items:
        print("Aviso: El XML no contiene elementos <item>.", flush=True)
        return

    memoria = cargar_memoria()

    for item in reversed(items):
        guid = (item.findtext("guid") or "").strip()
        link = (item.findtext("link") or "").strip()
        title = limpiar_html(item.findtext("title") or "")
        desc_raw = item.findtext("description") or ""
        desc_texto = limpiar_html(desc_raw)
        imagenes = extraer_imagenes(desc_raw, dominio_activo)

        cuerpo = desc_texto if len(desc_texto) >= len(title) else title
        base_id = guid or link or cuerpo
        if not base_id:
            continue

        item_hash = generar_hash(base_id)
        if item_hash in memoria:
            continue

        mensaje = f"🦁⚾ *Leones del Caracas* (@{X_USERNAME})\n\n{cuerpo}".replace("*", "")
        enviado = enviar_a_telegram(mensaje, imagenes)
        if enviado:
            guardar_hash(item_hash)
            memoria.add(item_hash)
            print(f"[Bot]: ¡Publicación enviada con éxito! Hash: {item_hash}", flush=True)
            time.sleep(2)


def main():
    print("Iniciando bot continuo autónomo...", flush=True)
    while True:
        try:
            verificar_actualizacion()
        except Exception as err:
            print(f"Error en el bucle principal: {err}", flush=True)
        print(f"Reiniciando ciclo del bot en {INTERVALO_SEGUNDOS} segundos...", flush=True)
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
