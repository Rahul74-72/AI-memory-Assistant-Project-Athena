@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run the setup steps in README.md first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\start.py
pause
