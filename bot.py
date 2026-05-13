from flask import Flask, jsonify, request
import os, json, subprocess
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "device": os.environ.get("DEVICE_NAME", "Celular"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "msg": "EYELIVE Bot rodando!"
    })

@app.route('/cmd/<comando>')
def cmd(comando):
    r = {"cmd": comando, "status": "ok", "time": datetime.now().strftime("%H:%M:%S")}
    
    if comando == "status":
        r["bateria"] = "85%"
        r["mensagem"] = "Tudo funcionando!"
    
    elif comando == "foto":
        path = "/data/data/com.termux/files/home/eyelive_foto.jpg"
        os.system(f"termux-camera-photo -c 0 {path} 2>/dev/null")
        r["msg"] = "Foto capturada!"
    
    return jsonify(r)

if __name__ == '__main__':
    print("EYELIVE BOT - Rodando na porta 5050")
    app.run(host='0.0.0.0', port=5050, debug=False)
