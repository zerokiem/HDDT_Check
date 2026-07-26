@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [*] Checking Python...
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_CMD=python"
    ) else (
        echo [!] Python not found. Trying to install it automatically...
        winget install --id Python.Python.3.12 -e --source winget
        if errorlevel 1 (
            echo [!] Failed to install Python automatically.
            echo [!] Please install Python 3 from https://www.python.org/downloads/ and rerun this script.
            exit /b 1
        )
        echo [*] Python installed. Please reopen this terminal and run the script again.
        exit /b 0
    )
)

echo [*] Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip

echo [*] Installing Python packages...
%PYTHON_CMD% -m pip install -r requirements.txt

echo [*] Installing Playwright browser...
%PYTHON_CMD% -m playwright install chromium

echo [*] Running script...
%PYTHON_CMD% check_hddt_cl_v8.py
pause
