#!/bin/bash
echo "EYELIVE - Instalacao"
pkill -f python 2>/dev/null; sleep 1
pkg update -y -qq && pkg upgrade -y -qq
pkg install python -y -qq
pip install flask requests -q 2>/dev/null

echo ""
echo "📱 Nome do dispositivo:"
read -p "   Nome: " DEVICE_NAME
[ -z "$DEVICE_NAME" ] && DEVICE_NAME="Celular"
DEVICE_ID=$(echo $DEVICE_NAME | tr ' ' '_' | tr '[:upper:]' '[:lower:]')

echo "DEVICE_NAME=\"$DEVICE_NAME\"" > ~/.eyelive_config
echo "DEVICE_ID=\"$DEVICE_ID\"" >> ~/.eyelive_config

sed -i '/alias eyelive/d' ~/.bashrc
echo "alias eyelive='bash <(curl -4 -s https://raw.githubusercontent.com/gynbetfc/eyelive/main/eyelive.sh)'" >> ~/.bashrc
source ~/.bashrc 2>/dev/null

echo ""
echo "✅ Instalado! Digite: eyelive"
