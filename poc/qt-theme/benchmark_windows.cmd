@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt benchmark] Creation de l'environnement isole...
  py -m venv .venv || goto :error
)

echo [Teamworks Qt benchmark] Mise a jour des dependances du POC...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt benchmark] Verification de la syntaxe...
".venv\Scripts\python.exe" -m py_compile benchmark_models.py models.py data_adapter.py frugality.py || goto :error

echo [Teamworks Qt benchmark] Test 1000 individus / 6 contrats par individu...
".venv\Scripts\python.exe" benchmark_models.py || goto :error

echo.
echo [Teamworks Qt benchmark] Termine. Copiez la ligne [Teamworks Qt benchmark] ci-dessus pour comparer RSS et temps.
pause
goto :eof

:error
echo.
echo Echec du benchmark Qt.
pause
exit /b 1
