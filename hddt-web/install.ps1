# =============================================================================
# HDDT Checker Web - CAI DAT NHANH TREN WINDOWS (KHONG can Docker).
#
# Chay 1 lenh trong PowerShell tai thu muc nay (hddt-web):
#     powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Script se: tao moi truong ao .venv, cai thu vien Python (Flask, Playwright,
# ddddocr...), cai trinh duyet Chromium cho Playwright. Sau do in ra cac buoc
# tiep theo (chay web, hoac cai chay ngam tu dong).
#
# Yeu cau: da cai Python 3.10+ (https://www.python.org/downloads/ - nho tick
# "Add python.exe to PATH" khi cai).
#
# Du lieu (Excel, anh chup, database, log) mac dinh luu tai D:\HDDT_Check\
# (xem config.py) - khong nam trong thu muc code nay.
# =============================================================================
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

Write-Host "== HDDT Checker Web - cai dat tren Windows ==" -ForegroundColor Cyan

# 1) Tim Python (uu tien Python Launcher 'py -3', roi 'python').
$pyExe = $null
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyExe = 'py'; $pyArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyExe = 'python'
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pyExe = 'python3'
}
if (-not $pyExe) {
    Write-Host "KHONG tim thay Python. Cai Python 3.10+ tai https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "(Nho tick 'Add python.exe to PATH' khi cai) roi chay lai install.ps1." -ForegroundColor Red
    exit 1
}
Write-Host "Dung Python: $pyExe $($pyArgs -join ' ')"

# 2) Tao moi truong ao .venv (neu chua co).
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Tao moi truong ao .venv ..."
    & $pyExe @pyArgs -m venv .venv
}
$vpy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) {
    Write-Host "Tao .venv that bai. Kiem tra lai ban cai Python." -ForegroundColor Red
    exit 1
}

# 3) Cai thu vien Python.
Write-Host "Cai thu vien Python (flask, playwright, ddddocr, openpyxl...) ..."
& $vpy -m pip install --upgrade pip
& $vpy -m pip install -r requirements.txt

# 4) Cai trinh duyet Chromium cho Playwright (co the mat vai phut lan dau).
Write-Host "Cai trinh duyet Chromium cho Playwright (co the mat vai phut) ..."
& $vpy -m playwright install chromium

# 5) Tao truoc thu muc du lieu mac dinh D:\HDDT_Check (neu chua co).
$dataDir = "D:\HDDT_Check"
if (-not (Test-Path $dataDir)) {
    Write-Host "Tao thu muc du lieu mac dinh: $dataDir"
    New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
}

Write-Host ""
Write-Host "== XONG CAI DAT ==" -ForegroundColor Green
Write-Host "Thu muc du lieu (Excel/anh/log/DB): $dataDir" -ForegroundColor Yellow
Write-Host ""
Write-Host "Cac buoc tiep theo:" -ForegroundColor Yellow
Write-Host "  1) Chay web (che do HIEN THI - thay log truc tiep tren terminal):" -ForegroundColor Yellow
Write-Host "       .\.venv\Scripts\python.exe run_web.py"
Write-Host "     Roi mo trinh duyet: http://127.0.0.1:14687 (tu mo san)"
Write-Host ""
Write-Host "  2) (Tuy chon) De web TU CHAY NGAM (an, khong hien cua so) moi khi" -ForegroundColor Yellow
Write-Host "     dang nhap Windows, khong can tu tay chay lenh moi lan:" -ForegroundColor Yellow
Write-Host "       powershell -ExecutionPolicy Bypass -File .\install_web_startup.ps1"
Write-Host ""
Write-Host "  Tai khoan dang nhap mac dinh: admin / Admin@2025!  -> DOI NGAY sau khi dang nhap lan dau." -ForegroundColor DarkYellow
