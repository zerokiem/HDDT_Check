# Cài đặt HDDT Checker Web trên Windows (không cần Docker)

Dùng cho máy Windows dùng làm "máy check web" (chạy trực tiếp bằng Python,
không qua Docker). Dữ liệu (Excel, ảnh chụp, database, log) mặc định lưu tại
**`D:\HDDT_Check\`** — thư mục riêng, không nằm trong OneDrive/git repo.

## 1. Yêu cầu

- Windows 10/11
- Python 3.10+ đã cài, nhớ tick **"Add python.exe to PATH"** lúc cài
  ([tải tại đây](https://www.python.org/downloads/))

## 2. Cài đặt — Cách A: từ file ZIP

1. Giải nén file `HDDT_Check.zip` vào đâu cũng được, ví dụ `D:\HDDT_Check_App\`.
2. Mở PowerShell tại thư mục `hddt-web` bên trong (chuột phải → "Open in Terminal"
   hoặc `cd` vào đó).
3. Chạy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

## 2. Cài đặt — Cách B: từ Git

```powershell
git clone git@github.com:zerokiem/HDDT_Check.git
cd HDDT_Check\hddt-web
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

`install.ps1` tự động: tạo môi trường ảo `.venv`, cài Flask/Playwright/ddddocr...,
cài trình duyệt Chromium cho Playwright, và tạo sẵn thư mục `D:\HDDT_Check\`.

## 3. Chạy web — 2 chế độ

### Chế độ HIỂN THỊ (chạy tay, thấy log trực tiếp)

```powershell
.\.venv\Scripts\python.exe run_web.py
```

Cửa sổ terminal hiện log real-time từng bước kiểm tra hóa đơn. Trình duyệt tự
mở `http://127.0.0.1:14687`. Đóng cửa sổ terminal (hoặc Ctrl+C) để tắt web.

### Chế độ ẨN (tự chạy ngầm mỗi khi đăng nhập Windows)

```powershell
powershell -ExecutionPolicy Bypass -File .\install_web_startup.ps1
```

Tạo 1 Windows Scheduled Task chạy bằng `pythonw.exe` (không hiện cửa sổ console)
mỗi khi đăng nhập Windows. Muốn chạy ngay không cần đăng xuất/đăng nhập lại:

```powershell
Start-ScheduledTask -TaskName "HDDT Checker Web"
```

Dừng web đang chạy ẩn:
```powershell
Get-Process pythonw | Stop-Process
```

Gỡ bỏ tự động chạy (quay lại chạy tay):
```powershell
Unregister-ScheduledTask -TaskName "HDDT Checker Web" -Confirm:$false
```

## 4. Đăng nhập lần đầu

Mở `http://127.0.0.1:14687` → đăng nhập `admin` / `Admin@2025!` → **đổi mật
khẩu ngay** (Sidebar → Đổi mật khẩu).

## 5. Truy cập từ máy khác trong mạng/Tailscale

Không cần cấu hình gì thêm — `run_web.py` đã bind `0.0.0.0` sẵn. Từ điện thoại/
laptop khác cùng mạng LAN hoặc cùng Tailscale, mở `http://<ip-may-nay>:14687`.

## 6. Đổi thư mục dữ liệu (nếu không muốn dùng D:\HDDT_Check)

Đặt biến môi trường `DATA_DIR` trước khi chạy, ví dụ:
```powershell
$env:DATA_DIR = "E:\Du_lieu_HDDT"
.\.venv\Scripts\python.exe run_web.py
```

## 7. Cập nhật code mới

```powershell
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # nếu requirements.txt có đổi
```
Chạy lại `run_web.py` (hoặc restart Scheduled Task nếu đang chạy ẩn) để áp dụng.
