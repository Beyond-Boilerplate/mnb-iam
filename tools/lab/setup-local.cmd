@echo off
REM Double-click / cmd.exe launcher for Windows IdentityIQ lab setup
setlocal
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-local.ps1" %*
endlocal
