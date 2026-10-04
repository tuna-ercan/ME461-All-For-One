@echo off
rem All For One - start the game with the project's environment (run setup.bat once first).
rem Extra options are passed on, e.g.:  run.bat --keyboard
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo The environment is missing - run setup.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py %*
