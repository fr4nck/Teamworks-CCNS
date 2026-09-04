@echo off
setlocal
if /I "%~1"=="recruitment" (
  call "%~dp0poc\qt-theme\run_recruitment_windows.cmd"
) else (
  call "%~dp0poc\qt-theme\run_windows.cmd"
)
exit /b %ERRORLEVEL%
