@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [*] Installing PyInstaller...
py -3 -m pip install --upgrade pip pyinstaller

echo [*] Building executable...
py -3 -m PyInstaller --onefile --noconsole check_hddt_cl_v8.py

echo [*] Output created in dist\
if exist dist\check_hddt_cl_v8.exe (
    echo [*] Executable: dist\check_hddt_cl_v8.exe
) else (
    echo [!] Build may have failed. Check the output above.
)
pause
