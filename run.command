#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "========================================"
echo " Alpinaluz Listing Generator V18.2.8"
echo "========================================"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
