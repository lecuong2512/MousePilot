@echo off
setlocal
title MousePilot - Mouse Button Controller

echo ========================================================
echo       MousePilot - Windows Mouse Button Controller
echo ========================================================
echo.

set "PY_CMD="

if exist "D:\Python311\python.exe" (
    set "PY_CMD=D:\Python311\python.exe"
    goto :FOUND
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3.11 -c "import sys" >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py -3.11"
        goto :FOUND
    )
    set "PY_CMD=py"
    goto :FOUND
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
    goto :FOUND
)

echo [ERROR] Python was not found on your system!
echo Please make sure Python is installed and added to PATH.
pause
exit /b 1

:FOUND
echo Starting MousePilot via: %PY_CMD%
echo.
%PY_CMD% "%~dp0main.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with code: %ERRORLEVEL%
    pause
)

endlocal
