#!/bin/bash
echo "👁️ EYELIVE - Instalação"
echo "========================"
pkill -f python 2>/dev/null; sleep 1
echo "📦 Atualizando..."
pkg update -y -qq && pkg upgrade -y -qq
echo "🐍 Python..."
pkg install python -y -qq
echo "📦 Dependências..."
pip install flask requests -q 2>/dev/null

# Perguntar nome do dispositivo
echo ""
echo "📱 Qual o nome deste dispositivo?"
echo "   Ex: Meu Celular, Celular do João, Tablet..."
read -p "   Nome: " DEVICE_NAME
[ -z "$DEVICE_NAME" ] && DEVICE_NAME="Celular"

DEVICE_ID=$(echo $DEVICE_NAME | tr ' ' '_' | tr '[:upper:]' '[:lower:]')

echo "alias eyelive='bash <(curl -4 -s https://raw.githubusercontent.com/gynbetfc/eyelive/main/tesla.sh)'" >> ~/.bashrc
source ~/.bashrc 2>/dev/null

echo ""
echo "✅ Instalado!"
echo "   Nome: $DEVICE_NAME"
echo "   ID: $DEVICE_ID"
echo ""
echo "🚀 Digite: eyelive"
echo ""

# Salvar config
echo "DEVICE_NAME="$DEVICE_NAME"" > ~/.eyelive_config
echo "DEVICE_ID="$DEVICE_ID"" >> ~/.eyelive_config
