#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Khởi động HDDT Checker Web (chạy trực tiếp trên máy, không cần Docker).

CÁCH DÙNG
---------
    python run_web.py

Mặc định mở tại http://127.0.0.1:14687 và tự động mở trình duyệt mặc định sau
~1 giây. Đóng cửa sổ terminal (hoặc Ctrl+C) để tắt server — đây là chế độ
"HIỂN THỊ" (thấy log trực tiếp trên terminal).

Muốn chạy NGẦM (ẩn, tự khởi động cùng Windows, không cần mở terminal) — xem
install_web_startup.ps1 (tạo Windows Scheduled Task chạy bằng pythonw.exe).

TRUY CẬP TỪ XA (điện thoại/máy khác qua LAN hoặc Tailscale)
------------------------------------------------------------
Mặc định đã bind 0.0.0.0 nên máy khác trong mạng LAN hoặc Tailscale truy cập
được luôn qua địa chỉ IP của máy này, ví dụ: http://192.168.1.x:14687 hoặc
http://100.x.y.z:14687 — không cần đổi gì thêm.
"""
from __future__ import annotations

import sys
import threading
import time
import webbrowser

from app import app

HOST = '0.0.0.0'
PORT = app.config['PORT']


def _open_browser_later():
    time.sleep(1.2)
    try:
        webbrowser.open(f'http://127.0.0.1:{PORT}')
    except Exception:
        pass


if __name__ == '__main__':
    if sys.platform == 'win32':
        threading.Thread(target=_open_browser_later, daemon=True).start()

    print(f'HDDT Checker Web: http://{HOST}:{PORT}   (Ctrl+C để dừng)')
    print(f'Thư mục dữ liệu : {app.config["UPLOAD_DIR"].parent}')
    app.run(host=HOST, port=PORT, threaded=True, debug=False)
