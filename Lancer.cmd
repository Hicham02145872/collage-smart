@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 goto erreur
)
.venv\Scripts\python.exe -m pip install --timeout 120 -r requirements.txt
if errorlevel 1 goto erreur
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.headless false --browser.gatherUsageStats false --theme.base dark
goto fin
:erreur
echo Installation impossible. Verifiez Python 3.12 et la connexion Internet.
pause
:fin
