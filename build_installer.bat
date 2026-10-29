@echo off
setlocal
title MousePilot - Build Installer
echo ========================================================
echo       MousePilot - Rebuild Application and Installer
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Compiling MousePilot Application...
py -3.11 -m PyInstaller packaging\mousepilot.spec --distpath dist --workpath build -y

echo [2/3] Packing Payload Archive...
py -3.11 -c "import shutil, os; shutil.make_archive('packaging/payload', 'zip', 'dist/MousePilot')"

echo [3/3] Compiling Standalone Installer MousePilot_Setup.exe...
py -3.11 -m PyInstaller packaging\installer_app.py --onefile --name "MousePilot_Setup" --add-data "packaging\payload.zip;." --add-data "app\assets\icon.png;." --add-data "app\assets\icon.ico;." --icon "app\assets\icon.ico" --noconsole --distpath dist --workpath build -y

copy /y dist\MousePilot_Setup.exe .

echo.
echo ========================================================
echo   BUILD COMPLETED!
echo   Installer is ready at: dist\MousePilot_Setup.exe
echo ========================================================
pause
