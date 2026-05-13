#!/bin/bash
echo "EYELIVE - Instalacao"
pkg install python termux-api -y -qq 2>/dev/null
pip install flask requests -q 2>/dev/null
echo "alias eyelive='bash <(curl -4 -s https://raw.githubusercontent.com/gynbetfc/eyelive/main/eyelive.sh)'" >> ~/.bashrc
source ~/.bashrc 2>/dev/null
echo "Pronto! Digite: eyelive"
