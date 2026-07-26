import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

# Đọc file .env cạnh app.py nếu có (chạy Docker: đã có sẵn qua environment:
# trong docker-compose.yml nên dòng này chỉ là no-op vô hại; chạy Windows
# native không qua Docker: đây là cách duy nhất nạp .env, vd TELEGRAM_*).
load_dotenv(BASE_DIR / '.env')

# Thư mục dữ liệu (DB, upload, output, ảnh, log):
#   - Docker/Linux (NAS, Pi4): luôn set biến môi trường DATA_DIR=/data (xem
#     docker-compose.yml) -> dùng đúng giá trị đó.
#   - Windows chạy trực tiếp (không Docker), KHÔNG set DATA_DIR: mặc định
#     D:\HDDT_Check — thư mục riêng, không nằm trong OneDrive/git repo, để dữ
#     liệu (Excel, ảnh hóa đơn, DB) không đồng bộ/commit nhầm.
#   - Các hệ điều hành khác không set DATA_DIR: fallback về ./data cạnh app.
if os.environ.get('DATA_DIR'):
    DATA_DIR = Path(os.environ['DATA_DIR'])
elif os.name == 'nt':
    DATA_DIR = Path(r'D:\HDDT_Check')
else:
    DATA_DIR = BASE_DIR / 'data'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hddt-secret-change-in-production-2025')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR}/hddt.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_DIR   = DATA_DIR / 'uploads'
    OUTPUT_DIR   = DATA_DIR / 'outputs'
    SCREENSHOT_BASE = DATA_DIR / 'screenshots'
    LOG_DIR      = DATA_DIR / 'logs'

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

    # Port mặc định 14687 (không dùng 5000 — dễ trùng port app khác).
    PORT = int(os.environ.get('PORT', '14687'))

    # Đường dẫn Chromium — set qua env cho ARM (NAS/Pi4)
    # VD: CHROMIUM_PATH=/usr/bin/chromium
    CHROMIUM_PATH = os.environ.get('CHROMIUM_PATH', None)

    # Số job chạy đồng thời tối đa
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', '1'))

    # Captcha
    MAX_CAPTCHA_AUTO = int(os.environ.get('MAX_CAPTCHA_AUTO', '5'))
    PAGE_WAIT = float(os.environ.get('PAGE_WAIT', '2.5'))

    # Telegram (tùy chọn) — thông báo khi đăng nhập + khi kiểm tra xong. Để
    # trống 1 trong 2 biến = tắt hoàn toàn (không lỗi, chỉ im lặng bỏ qua).
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID', '')

    # Bản quyền hiển thị ở footer web.
    COPYRIGHT_OWNER = os.environ.get('COPYRIGHT_OWNER', 'Nguyễn Xuân Bình')
