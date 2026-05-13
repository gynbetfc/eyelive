#!/bin/bash
echo "EYELIVE"
rm -f bot.py 2>/dev/null
pkill -f python 2>/dev/null
sleep 1
curl -4 -s "https://raw.githubusercontent.com/gynbetfc/eyelive/main/main.py" -o bot.py
export EYELIVE_TOKEN=$(cat ~/.eyelive_token 2>/dev/null)
python bot.py &
sleep 5
termux-open-url http://127.0.0.1:5050 2>/dev/null
echo "http://127.0.0.1:5050"
wait
rm -f bot.py
