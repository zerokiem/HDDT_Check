@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [*] Chuong trinh tu dong cai dat va chay check hoa don

echo [*] Kiem tra Python...
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    ) else (
        echo [*] Khong tim thay Python. Thu cai dat tu dong bang winget...
        winget install --id Python.Python.3.12 -e --source winget
        if errorlevel 1 (
            echo [!] Khong the cai dat Python tu dong.
            echo [!] Vui long cai Python 3 tu https://www.python.org/downloads/ va chay lai.
            pause
            exit /b 1
        )
        echo [*] Python da cai xong. Vui long mo lai terminal va chay lai script.
        pause
        exit /b 0
    )
)

%PYTHON_CMD% --version >nul 2>nul
if errorlevel 1 (
    echo [!] Python khong hoat dong dung.
    echo [!] Vui long mo lai terminal va chay lai script.
    pause
    exit /b 1
)

echo [*] Nang cap pip...
%PYTHON_CMD% -m pip install --upgrade pip

echo [*] Cai dat dependencies...
%PYTHON_CMD% -m pip install -r "%SCRIPT_DIR%requirements.txt"

echo [*] Cai dat Playwright browser...
%PYTHON_CMD% -m playwright install chromium

echo [*] Tao shortcut tren Desktop...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$wsh = New-Object -ComObject WScript.Shell; $lnk = $wsh.CreateShortcut('%USERPROFILE%\Desktop\Check_Hoa_Don.lnk'); $lnk.TargetPath = '%SCRIPT_DIR%run_full_auto.bat'; $lnk.WorkingDirectory = '%SCRIPT_DIR%'; $lnk.IconLocation = 'cmd.exe,0'; $lnk.Description = 'Chay Check Hoa Don'; $lnk.Save()"

echo [*] Chay script...
%PYTHON_CMD% "%SCRIPT_DIR%check_hddt_cl_v8.py"

if errorlevel 1 (
    echo [!] Script da ket thuc voi loi.
) else (
    echo [*] Da ket thuc.
)
pause
