def verificar_actualizacion():
    instancias_rss = [
        f"https://nitter.netbub.com/leones_cbbc/rss"
    ]
    
    contenido_xml = None
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for url in instancias_rss:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200 and ("<rss" in res.text or "<feed" in res.text):
                contenido_xml = res.text
                break
        except:
            continue

    if not contenido_xml:
        print("Aviso: Ninguna instancia RSS respondió en este ciclo.", flush=True)
        return
