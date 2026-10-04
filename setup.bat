@echo off
rem All For One - double-click to set up the game on Windows (runs setup.ps1).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
pause
