#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
pkg update -y
pkg install -y python git clang libxml2 libxslt
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python scripts/init_db.py
echo "Finessa initialized. Edit .env, then run: . .venv/bin/activate && python app.py"
