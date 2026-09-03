@echo off
setlocal
cd /d "%~dp0"

for %%I in ("%~dp0..\..\") do set "REPO_ROOT=%%~fI"
set "PYTHONPATH=%REPO_ROOT%\teamworks;%REPO_ROOT%;%PYTHONPATH%"
set "TEAMWORKS_QT_SOURCE=production"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt POC] Creation de l'environnement isole Python 3.11...
  py -3.11 -m venv .venv || goto :error
)

echo [Teamworks Qt POC] Mise a jour des dependances Qt...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt POC] Chargement des dependances Teamworks necessaires aux readers reels...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r "%REPO_ROOT%\requirements\python311-core.txt" || goto :error

echo [Teamworks Qt POC] Verification de la syntaxe...
".venv\Scripts\python.exe" -m py_compile app.py launcher.py theme_engine.py data_adapter.py domain_read_adapter.py production_read_adapter.py models.py pilot_view.py legacy_individual_tabs.py legacy_sheets.py legacy_contract_wizard.py generalities_satellites.py contract_editor.py frugality.py || goto :error
".venv\Scripts\python.exe" -m compileall -q ui || goto :error

echo [Teamworks Qt POC] Lancement lecture seule sur les readers Teamworks reels...
".venv\Scripts\python.exe" launcher.py
goto :eof

:error
echo.
echo Echec du lancement du POC Qt.
pause
exit /b 1
