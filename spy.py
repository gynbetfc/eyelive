from flask import Flask, jsonify, request
import os

app = Flask(__name__)
MEU_NUMERO = "62996942287"

@app.route('/')
def home():
    return jsonify({"status": "online", "numero": MEU_NUMERO})

@app.route('/ping/<numero>')
def ping(numero):
    if numero == MEU_NUMERO:
        return jsonify({"resposta": "RECEBI!", "numero": MEU_NUMERO, "msg": "Bot esta online e recebeu sua requisicao!"})
    else:
        return jsonify({"resposta": "NUMERO ERRADO", "msg": "Este bot nao responde a esse numero"})

@app.route('/cmd/<comando>')
def cmd(comando):
    return jsonify({"comando": comando, "status": "executado"})

if __name__ == '__main__':
    print(f"SPY rodando - Numero: {MEU_NUMERO}")
    app.run(host='0.0.0.0', port=5050, debug=False)
