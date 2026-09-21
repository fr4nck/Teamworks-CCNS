@echo off
setlocal
cd /d "%~dp0\.."

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher introuvable.
  exit /b 2
)

py -3.11 tools\recipe_qt_contracts_mysql.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ECHEC - le stop-gate Rail A Windows/MySQL n'est pas valide.
  exit /b %RC%
)

echo.
echo OK - stop-gate technique Rail A Windows/MySQL valide.
exit /b 0
