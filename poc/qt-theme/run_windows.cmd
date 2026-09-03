@echo off
setlocal
cd /d "%~dp0"

for %%I in ("%~dp0..\..\") do set "REPO_ROOT=%%~fI"
set "PYTHONPATH=%REPO_ROOT%\teamworks;%REPO_ROOT%;%PYTHONPATH%"
set "TEAMWORKS_QT_SOURCE=production"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt POC] Creation de l'environnement isole...
  py -m venv .venv || goto :error
)

echo [Teamworks Qt POC] Mise a jour des dependances du POC...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt POC] Verification de la syntaxe...
".venv\Scripts\python.exe" -m py_compile app.py launcher.py theme_engine.py data_adapter.py domain_read_adapter.py production_read_adapter.py models.py pilot_view.py contract_editor.py frugality.py || goto :error

echo [Teamworks Qt POC] Lancement lecture seule sur les readers Teamworks reels...
".venv\Scripts\python.exe" launcher.py
goto :eof

:error
echo.
echo Echec du lancement du POC Qt.
pause
exit /b 1
