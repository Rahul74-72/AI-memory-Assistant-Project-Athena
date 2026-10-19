@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Athena is not set up yet. Follow the one-time setup in README.md.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows_shortcut.ps1"
if errorlevel 1 (
  echo Could not create the shortcut.
  pause
  exit /b 1
)
echo Project Athena is now available on your Desktop.
pause
