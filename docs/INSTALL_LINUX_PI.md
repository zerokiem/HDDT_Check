# Cài đặt HDDT Checker Web trên Linux / Raspberry Pi 4 (Docker)

Áp dụng cho Pi4 (hoặc bất kỳ máy Linux ARM64/x86_64 nào có Docker). Cùng 1 bộ
code với bản Windows — xem [README.md](../README.md) để hiểu cấu trúc chung.

## 1. Yêu cầu

- Docker Engine + Docker Compose đã cài (`docker --version`, `docker compose version`
  hoặc `docker-compose version`).
- Cổng **14687** trống trên máy (kiểm tra: `sudo ss -tln | grep 14687`).
- Nếu máy đang chạy dịch vụ khác chiếm nhiều RAM (Home Assistant, AdGuard Home...),
  xem mục [5. Lưu ý RAM](#5-lưu-ý-ram-máy-chia-sẻ) trước khi chạy.

## 2. Cài đặt — Cách A: từ file ZIP

```bash
# Copy file zip lên máy (scp/rsync/USB...), rồi:
unzip HDDT_Check.zip -d ~/HDDT_Check
cd ~/HDDT_Check/hddt-web
cp .env.example .env
nano .env          # đổi SECRET_KEY, PORT nếu cần
docker compose up -d --build
```

## 3. Cài đặt — Cách B: từ Git

```bash
git clone git@github.com:zerokiem/HDDT_Check.git ~/HDDT_Check
# hoặc: git clone https://github.com/zerokiem/HDDT_Check.git ~/HDDT_Check
cd ~/HDDT_Check/hddt-web
cp .env.example .env
nano .env
docker compose up -d --build
```

> Trên NAS Synology dùng `sudo docker-compose` (gạch nối) thay vì `docker compose`
> — xem [INSTALL_NAS_SYNOLOGY.md](INSTALL_NAS_SYNOLOGY.md).

## 4. Kiểm tra & truy cập

```bash
docker compose ps                 # container "hddt_web" phải ở trạng thái "Up"
docker compose logs -f            # xem log real-time (Ctrl+C để thoát xem, container vẫn chạy)
```

Truy cập:
- Trong LAN: `http://<ip-lan-cua-pi4>:14687`
- Qua Tailscale (nếu có cài): `http://<tailscale-ip>:14687`

Tài khoản mặc định: `admin` / `Admin@2025!` — **đổi mật khẩu ngay** sau khi đăng nhập lần đầu (Sidebar → Đổi mật khẩu).

## 4.1. Đưa ra internet qua domain (hddt.binhnx.io.vn)

Bản mặc định chạy **HTTP thường** (chưa có HTTPS) — chỉ mở port này ra internet
khi đã hiểu rủi ro (mật khẩu đăng nhập truyền dạng không mã hóa). Các bước:

1. Đảm bảo DNS `hddt.binhnx.io.vn` đã trỏ đúng IP mạng nhà bạn (kiểm tra:
   `nslookup hddt.binhnx.io.vn`).
2. Đăng nhập trang quản trị router, thêm Port Forwarding:
   - Port ngoài: `14687` → IP nội bộ Pi4 → Port trong: `14687`, giao thức TCP.
3. Truy cập thử: `http://hddt.binhnx.io.vn:14687`.

Muốn nâng cấp lên HTTPS sau này (khuyến nghị): dùng Cloudflare Tunnel (không cần
mở port router) hoặc đặt Caddy/nginx phía trước dùng chứng chỉ qua DNS-01 challenge
(không cần port 80 — hữu ích nếu port 80 trên máy đã bị dịch vụ khác chiếm, như
AdGuard Home).

## 5. Lưu ý RAM (máy chia sẻ)

Nếu Pi4 đang chạy chung Home Assistant/AdGuard/Node-RED... RAM trống có thể
khá ít. `docker-compose.yml` đã đặt sẵn `mem_limit: 768m` (sửa trong `.env`
qua biến `MEM_LIMIT`) để container không "ăn" hết RAM máy làm crash các dịch
vụ khác. Nếu Chromium hay bị lỗi/crash giữa chừng, thử tăng `MEM_LIMIT` lên
`1g` (nếu máy đủ RAM) hoặc giảm `MAX_CONCURRENT_JOBS=1` (mặc định đã là 1).

Theo dõi RAM: `docker stats hddt_web`.

## 6. Vận hành thường ngày

```bash
cd ~/HDDT_Check/hddt-web

docker compose restart        # khởi động lại (sau khi sửa code .py — không cần build lại)
docker compose down           # dừng hẳn
docker compose up -d          # chạy lại
docker compose logs --tail=100
docker compose build          # chỉ cần khi đổi requirements.txt hoặc Dockerfile
```

- **Sửa code** (`app.py`, `checker_web.py`...): code được bind-mount, sửa xong
  chỉ cần `docker compose restart`, không cần build lại image.
- **Cập nhật code mới từ Git**: `git pull && docker compose restart`
  (`docker compose build` thêm nếu `requirements.txt` có đổi).
- **Dữ liệu** (DB, Excel, ảnh, log) nằm trong `./data` (hoặc `DATA_PATH` đã
  chỉnh trong `.env`) — không mất khi restart/rebuild container.

## 7. Xử lý sự cố

| Triệu chứng | Cách xử lý |
|---|---|
| Container cứ "Restarting" liên tục | `docker compose logs` xem traceback Python lúc khởi động |
| `port is already allocated` | Đổi `PORT` trong `.env` sang port khác chưa dùng |
| Chromium crash / timeout khi check hóa đơn | Tăng `shm_size` trong `docker-compose.yml`, hoặc tăng `MEM_LIMIT` |
| `ddddocr`/`onnxruntime` lỗi import trên ARM64 | `docker compose exec web python3 -c "import ddddocr"` để xem traceback cụ thể; thường do thiếu wheel ARM64 — thử `pip install --no-cache-dir --force-reinstall onnxruntime` trong container |
| Không truy cập được từ máy khác trong LAN | Kiểm tra firewall (`ufw status` nếu có bật), kiểm tra `docker compose ps` container đã "Up" |
