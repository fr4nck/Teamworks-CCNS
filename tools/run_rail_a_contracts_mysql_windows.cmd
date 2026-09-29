@echo off
setlocal
cd /d "%~dp0\.."

where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher introuvable.
  exit /b 2
)

set "REPORT_DIR=artifacts\rail-a-mysql"
set "REPORT=%REPORT_DIR%\console.txt"
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

echo Teamworks Rail A - recette Windows/MySQL
echo Rapport : %CD%\%REPORT%
echo.

py -3.11 tools\recipe_qt_contracts_mysql.py > "%REPORT%" 2>&1
set "RC=%ERRORLEVEL%"

type "%REPORT%"
echo.

if not "%RC%"=="0" (
  echo ECHEC - le stop-gate Rail A Windows/MySQL n'est pas valide.
  echo Diagnostic conserve dans %REPORT%
  exit /b %RC%
)

echo OK - stop-gate technique Rail A Windows/MySQL valide.
echo Diagnostic conserve dans %REPORT%
exit /b 0
