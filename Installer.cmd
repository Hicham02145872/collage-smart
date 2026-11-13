@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Installez Python 3.12, puis relancez Installer.cmd.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
if not exist .venv\Scripts\python.exe exit /b 1
.venv\Scripts\python.exe -m pip install --timeout 120 -r requirements.txt
if errorlevel 1 (
  echo Installation incomplete. Verifiez la connexion Internet et relancez.
  pause
  exit /b 1
)
echo Installation terminee. Lancez Lancer.cmd pour ouvrir l'application.
pause
