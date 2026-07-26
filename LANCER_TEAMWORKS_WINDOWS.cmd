@echo off
setlocal
cd /d "%~dp0"

echo === Teamworks-CCNS - Python 3.11 ===

where py >nul 2>nul
if errorlevel 1 (
  echo ERREUR: le lanceur Python "py" est introuvable.
  echo Installez Python 3.11 puis relancez ce fichier.
  pause
  exit /b 1
)

py -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11)" >nul 2>nul
if errorlevel 1 (
  echo ERREUR: Python 3.11 est introuvable.
  echo Installez Python 3.11 puis relancez ce fichier.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement Python 3.11...
  py -3.11 -m venv .venv
  if errorlevel 1 goto :error
)

echo Mise a jour de pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installation des dependances Teamworks...
".venv\Scripts\python.exe" -m pip install -r requirements\python311-core.txt
if errorlevel 1 goto :error

echo Lancement de Teamworks...
".venv\Scripts\python.exe" run_teamworks.py
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Teamworks s'est arrete avec le code %EXITCODE%.
  pause
)
exit /b %EXITCODE%

:error
echo.
echo ERREUR pendant la preparation de Teamworks.
pause
exit /b 1
