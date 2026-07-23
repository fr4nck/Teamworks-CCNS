@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\teamworks
py -3.11 teamworks\Teamworks.py
pause
