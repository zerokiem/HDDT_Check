# Cai Windows Scheduled Task de TU DONG chay HDDT Checker Web (run_web.py) moi
# khi dang nhap Windows, chay AN (khong hien cua so console) - che do "chay
# ngam". Muon xem log truc tiep (che do "hien thi"), dung tay chay:
#     .\.venv\Scripts\python.exe run_web.py
#
# Dung "At log on" (khong phai "At startup") vi can 1 phien dang nhap Windows
# that de mo duoc (Playwright/Chromium headless van chay ngam binh thuong du
# la "At log on" hay "At startup", nhung "At log on" on dinh hon tren may ca
# nhan dang dung hang ngay).
#
# Chay PowerShell voi quyen phu hop (Run as Administrator neu gap loi quyen).
# Chay ngay tai thu muc nay (hddt-web) - tu nhan dien qua $PSScriptRoot.

$TaskName = "HDDT Checker Web"
$ProjectDir = $PSScriptRoot
$PythonwExe = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$Script = Join-Path $ProjectDir "run_web.py"

if (!(Test-Path $PythonwExe)) {
    Write-Host "Khong thay pythonw.exe: $PythonwExe"
    Write-Host "Kiem tra lai da chay install.ps1 chua (tao virtual environment .venv)."
    exit 1
}
if (!(Test-Path $Script)) {
    Write-Host "Khong thay file: $Script"
    exit 1
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$Action = New-ScheduledTaskAction -Execute $PythonwExe -Argument "`"$Script`"" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Chay ngam HDDT Checker Web moi khi dang nhap Windows" -Force

Write-Host "Da cai: '$TaskName' se tu chay AN moi khi dang nhap Windows."
Write-Host ""
Write-Host "Chay ngay bay gio (khong doi den lan dang nhap sau):"
Write-Host "  Start-ScheduledTask -TaskName `"$TaskName`""
Write-Host ""
Write-Host "Mo web: http://127.0.0.1:14687"
Write-Host ""
Write-Host "Dung web dashboard dang chay ngam (khong co nut Stop rieng vi khong co console):"
Write-Host "  Get-Process pythonw | Stop-Process"
Write-Host ""
Write-Host "Go bo tu dong chay khi dang nhap (quay lai chay tay/hien thi neu muon):"
Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskName`" -Confirm:`$false"
