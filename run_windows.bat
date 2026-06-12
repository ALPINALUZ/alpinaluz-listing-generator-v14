@echo off
cd /d %~dp0
echo ========================================
echo  Alpinaluz Listing Generator V17.11
echo ========================================
if not exist .venv (
    py -3 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
pause
