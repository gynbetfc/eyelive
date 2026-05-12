#!/bin/bash
source ~/.eyelive_config 2>/dev/null
[ -z "$DEVICE_NAME" ] && DEVICE_NAME="Celular"
[ -z "$DEVICE_ID" ] && DEVICE_ID="celular"

echo "👁️ EYELIVE - $DEVICE_NAME"
rm -f bot.b64 2>/dev/null
pkill -f python 2>/dev/null
sleep 1

curl -4 -s "https://raw.githubusercontent.com/gynbetfc/eyelive/main/main.py?t=$(date +%s)" -o bot.b64
python -c "import base64; open('bot.py','w').write(base64.b64decode(open('bot.b64').read()).decode())"
rm bot.b64

export DEVICE_NAME="$DEVICE_NAME"
export DEVICE_ID="$DEVICE_ID"

python bot.py &
sleep 5
termux-open-url http://127.0.0.1:5000 2>/dev/null
echo "✅ http://127.0.0.1:5000"
wait
rm -f bot.py
