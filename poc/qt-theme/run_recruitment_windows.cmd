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

echo [Teamworks Qt POC] Verification de la syntaxe Recrutement...
".venv\Scripts\python.exe" -m py_compile recruitment_workspace.py recruitment_selection.py theme_engine.py || goto :error
".venv\Scripts\python.exe" -m compileall -q ui || goto :error

echo [Teamworks Qt POC] Lancement Recrutement en lecture seule...
".venv\Scripts\python.exe" recruitment_workspace.py
goto :eof

:error
echo.
echo Echec du lancement du POC Qt Recrutement.
pause
exit /b 1
