from flask import Flask, render_template_string, jsonify, request
import os, json, requests, base64, threading, time
from datetime import datetime

app = Flask(__name__)

# Config
DEVICE_ID = os.environ.get("DEVICE_ID", "celular_1")
DEVICE_NAME = os.environ.get("DEVICE_NAME", "Meu Celular")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = "gynbetfc/eyelive"

# Dados do dispositivo (atualizados a cada 30s)
device_data = {
    "id": DEVICE_ID,
    "nome": DEVICE_NAME,
    "ultimo_update": "",
    "bateria": "100%",
    "gps": {"lat": 0, "lng": 0},
    "apps_recentes": [],
    "status": "online"
}

def salvar_no_github():
    """Salva dados do dispositivo no GitHub"""
    try:
        fn = f"dados/{DEVICE_ID}.json"
        url = f"https://api.github.com/repos/{REPO}/contents/{fn}"
        h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
        
        device_data["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
        c = json.dumps(device_data)
        
        r = requests.get(url, headers=h)
        payload = {"message": f"Update {DEVICE_ID}", "content": base64.b64encode(c.encode()).decode(), "branch": "main"}
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]
        requests.put(url, json=payload, headers=h)
    except:
        pass

def atualizar_dados():
    """Thread que atualiza dados periodicamente"""
    while True:
        # Aqui vai coletar dados reais do celular
        device_data["bateria"] = "85%"
        device_data["gps"] = {"lat": -23.5505, "lng": -46.6333}
        salvar_no_github()
        time.sleep(30)

# Iniciar thread de atualização
threading.Thread(target=atualizar_dados, daemon=True).start()

@app.route('/')
def painel():
    """Painel mostrando TODOS os dispositivos"""
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
                        dispositivos.append(dados)
        
        html = "<h1>👁️ EYELIVE - Painel</h1>"
        for d in dispositivos:
            online = "🟢" if d.get('status') == 'online' else "🔴"
            html += f"<div style='border:1px solid #333;padding:10px;margin:10px;border-radius:10px'>"
            html += f"<h3>{online} {d.get('nome','?')}</h3>"
            html += f"<p>🔋 {d.get('bateria','?')} | 📍 GPS: {d.get('gps',{})}</p>"
            html += f"<p>🕐 {d.get('ultimo_update','?')}</p>"
            html += f"</div>"
        
        return html
    except:
        return "<h1>Erro ao carregar</h1>"

@app.route('/api/status')
def status():
    return jsonify(device_data)

if __name__ == '__main__':
    print(f"👁️ EYELIVE - {DEVICE_NAME}")
    print("="*30)
    app.run(host='0.0.0.0', port=5000, debug=False)
