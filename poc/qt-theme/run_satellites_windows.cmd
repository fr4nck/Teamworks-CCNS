@echo off
setlocal
cd /d "%~dp0"

for %%I in ("%~dp0..\..\") do set "REPO_ROOT=%%~fI"
set "PYTHONPATH=%REPO_ROOT%\teamworks;%REPO_ROOT%;%PYTHONPATH%"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt POC] Creation de l'environnement isole Python 3.11...
  py -3.11 -m venv .venv || goto :error
)

echo [Teamworks Qt POC] Mise a jour des dependances Qt...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt POC] Verification de la syntaxe des satellites...
".venv\Scripts\python.exe" -m py_compile theme_engine.py generalities_satellites.py satellites_gallery.py || goto :error
".venv\Scripts\python.exe" -m compileall -q ui || goto :error

echo [Teamworks Qt POC] Ouverture de la galerie satellites Generalites...
".venv\Scripts\python.exe" satellites_gallery.py
goto :eof

:error
echo.
echo Echec du lancement de la galerie Qt.
pause
exit /b 1
