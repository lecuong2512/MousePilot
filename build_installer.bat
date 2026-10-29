@echo off
setlocal
title MousePilot - Build Installer
echo ========================================================
echo       MousePilot - Rebuild Application and Installer
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/4] Compiling MousePilot Application (OneFile + VersionInfo)...
py -3.11 -m PyInstaller packaging\mousepilot.spec --distpath dist --workpath build -y

echo [2/4] Compiling Uninstaller Application...
py -3.11 -m PyInstaller packaging\uninstaller.py --onefile --name "uninstall" --icon "app\assets\icon.ico" --noconsole --distpath dist --workpath build -y

echo [3/4] Packing Payload Archive (MousePilot.exe + uninstall.exe)...
py -3.11 -c "import zipfile; z = zipfile.ZipFile('packaging/payload.zip', 'w', zipfile.ZIP_DEFLATED); z.write('dist/MousePilot.exe', 'MousePilot.exe'); z.write('dist/uninstall.exe', 'uninstall.exe'); z.close()"

echo [4/4] Compiling Standalone Installer MousePilot_Setup.exe...
py -3.11 -m PyInstaller packaging\installer_app.py --onefile --name "MousePilot_Setup" --version-file "packaging\version_installer.txt" --add-data "packaging\payload.zip;." --add-data "app\assets\icon.png;." --add-data "app\assets\icon.ico;." --icon "app\assets\icon.ico" --noconsole --distpath dist --workpath build -y

copy /y dist\MousePilot_Setup.exe .
copy /y dist\MousePilot.exe .

if exist MousePilot_Setup.spec del MousePilot_Setup.spec
if exist uninstall.spec del uninstall.spec

echo.
echo ========================================================
echo   BUILD COMPLETED!
echo   - Installer: MousePilot_Setup.exe
echo   - Portable : MousePilot.exe
echo ========================================================
pause
