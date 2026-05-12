from flask import Flask, jsonify, request
import os, json, requests, base64, threading, time, subprocess
from datetime import datetime

def _tk():
    t = "now_6SknCt0iPywDyM8breBO2KOlMwWpIr0m3nAP"
    r = ""
    for c in t:
        if c.isalpha():
            b = ord('a') if c.islower() else ord('A')
            r += chr((ord(c) - b - 7) % 26 + b)
        else:
            r += c
    return r

app = Flask(__name__)

DEVICE_ID = os.environ.get("DEVICE_ID", "celular_1")
DEVICE_NAME = os.environ.get("DEVICE_NAME", "Meu Celular")
TOKEN = _tk()
REPO = "gynbetfc/eyelive"

device_data = {"id": DEVICE_ID, "nome": DEVICE_NAME, "ultimo_update": "", "bateria": "?%", "carregando": False, "gps": {"lat": 0, "lng": 0}, "ip": "", "posicao": "?", "status": "online"}

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
    except: return "?"

def coletar():
    while True:
        try:
            b = shell("termux-battery-status 2>/dev/null")
            if b and "percentage" in b:
                bat = json.loads(b)
                device_data["bateria"] = str(bat.get('percentage','?')) + '%'
                device_data["carregando"] = bat.get('plugged','') != ''
            device_data["ip"] = shell("curl -4 -s ifconfig.me 2>/dev/null") or "?"
            device_data["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
            salvar()
        except: pass
        time.sleep(30)

def salvar():
    try:
        fn = f"dados/{DEVICE_ID}.json"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        c = json.dumps(device_data)
        r = requests.get(url, headers=h)
        p = {"message": "Update", "content": base64.b64encode(c.encode()).decode(), "branch": "main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        requests.put(url, json=p, headers=h)
    except: pass

threading.Thread(target=coletar, daemon=True).start()

@app.route('/')
def painel():
    return app.send_static_file('index.html') if os.path.exists('index.html') else '<h1 style="color:#ffd700;text-align:center;font-family:monospace;background:#0a0a1a;padding:50px">EYELIVE<br><a href="/painel_data" style="color:#00ff88">Ver Dados</a></h1>'

@app.route('/painel_data')
def painel_data():
    try:
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/dados", headers=h)
        dispositivos = []
        if r.status_code == 200:
            for arq in r.json():
                if arq['name'].endswith('.json'):
                    rd = requests.get(arq['url'], headers=h)
                    if rd.status_code == 200:
                        d = json.loads(base64.b64decode(rd.json()['content']).decode())
                        d['status'] = 'online'
                        dispositivos.append(d)
        return jsonify(dispositivos)
    except:
        return jsonify([])

if __name__ == '__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0', port=5050, debug=False)
