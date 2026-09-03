@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt POC] Creation de l'environnement isole...
  py -m venv .venv || goto :error
)

echo [Teamworks Qt POC] Mise a jour des dependances du POC...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt POC] Verification de la syntaxe...
".venv\Scripts\python.exe" -m py_compile app.py theme_engine.py data_adapter.py || goto :error

echo [Teamworks Qt POC] Lancement du stress-test UI...
".venv\Scripts\python.exe" app.py
goto :eof

:error
echo.
echo Echec du lancement du POC Qt.
pause
exit /b 1
