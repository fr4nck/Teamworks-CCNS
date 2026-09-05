@echo off
setlocal
cd /d "%~dp0"

for %%I in ("%~dp0..\..\") do set "REPO_ROOT=%%~fI"
set "PYTHONPATH=%REPO_ROOT%\teamworks;%REPO_ROOT%;%PYTHONPATH%"

if not exist ".venv\Scripts\python.exe" (
  echo [Teamworks Qt benchmark] Creation de l'environnement isole...
  py -3.11 -m venv .venv || goto :error
)

echo [Teamworks Qt benchmark] Mise a jour des dependances du POC...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto :error

echo [Teamworks Qt benchmark] Verification de la syntaxe...
".venv\Scripts\python.exe" -m py_compile benchmark_models.py runtime_async_smoke.py models.py data_adapter.py domain_read_adapter.py frugality.py pilot_generalities.py pilot_view.py individual_activity_presenter.py generalities_page.py legacy_individual_tabs.py individual_pages.py || goto :error

echo [Teamworks Qt benchmark] Smoke runtime asynchrone A vers B vers C...
".venv\Scripts\python.exe" runtime_async_smoke.py || goto :error

echo [Teamworks Qt benchmark] Test 1000 individus / 6 contrats par individu...
".venv\Scripts\python.exe" benchmark_models.py || goto :error

echo.
echo [Teamworks Qt benchmark] Termine. Copiez les lignes [Teamworks Qt runtime], [Teamworks Qt benchmark] et [Teamworks Domain benchmark] ci-dessus.
pause
goto :eof

:error
echo.
echo Echec du benchmark Qt.
pause
exit /b 1
