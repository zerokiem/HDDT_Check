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

> **Lưu ý Raspberry Pi OS:** mặc định kernel Raspberry Pi OS **tắt memory
> cgroup controller** (kiểm tra: `cat /proc/cgroups | grep memory` — cột thứ 3
> = 0 nghĩa là đang tắt), nên `mem_limit` trong `docker-compose.yml` **không
> thực sự được Docker áp dụng** (kiểm tra: `docker inspect hddt_web --format
> '{{.HostConfig.Memory}}'` ra `0`) dù không báo lỗi gì. Muốn bật thật, thêm
> vào cuối dòng `cmdline.txt` (`/boot/cmdline.txt` hoặc `/boot/firmware/cmdline.txt`
> tùy bản Raspberry Pi OS): `cgroup_enable=memory cgroup_memory=1` rồi
> **khởi động lại Pi** — đây là thay đổi ảnh hưởng toàn máy (cần reboot), cân
> nhắc kỹ nếu Pi đang chạy dịch vụ khác 24/7 (Home Assistant, AdGuard...).
> Không bật thì container vẫn chạy bình thường, chỉ là không có giới hạn RAM
> cứng — `MAX_CONCURRENT_JOBS=1` vẫn là hàng rào chính chống dùng quá nhiều RAM.

## 6. Vị trí lưu dữ liệu

Mặc định (chưa chỉnh `DATA_PATH` trong `.env`), toàn bộ dữ liệu nằm tại:

```
~/HDDT_Check/hddt-web/data/
├── hddt.db          ← Database (user, job, lịch sử, cấu hình Telegram lưu qua web)
├── uploads/         ← File Excel đã tải lên
├── outputs/         ← File Excel kết quả MẶC ĐỊNH (không nhập "Thư mục lưu" lúc upload)
├── screenshots/     ← Ảnh chụp từng job (mặc định)
└── logs/            ← Log từng job
```

Ví dụ trên Pi4 hiện tại: `/home/pi/HDDT_Check/hddt-web/data/`. Nếu lúc upload
có nhập **"Thư mục lưu kết quả"** riêng, Excel + ảnh của job đó nằm ở đường dẫn
đã nhập (phải là đường dẫn có thật **bên trong container** — với Docker nghĩa
là đường dẫn đó phải nằm trong 1 thư mục đã mount, thường chỉ dùng tiện ích
này khi chạy Windows native; trên Docker nên để trống, dùng mặc định).

## 7. Backup

Dừng container trước khi backup để tránh ghi dở SQLite (chỉ mất vài giây):

```bash
cd ~/HDDT_Check/hddt-web
docker compose stop
tar -czf ~/hddt_backup_$(date +%Y%m%d).tar.gz data/
docker compose start
```

Đặt cron chạy hàng đêm nếu muốn tự động (`crontab -e`):
```
0 2 * * * cd ~/HDDT_Check/hddt-web && tar -czf ~/backup/hddt_$(date +\%Y\%m\%d).tar.gz data/
```

## 8. Vận hành thường ngày — Dừng/chạy lại, cập nhật

```bash
cd ~/HDDT_Check/hddt-web

docker compose stop           # DỪNG container (nhẹ máy Pi4 hẳn, dữ liệu vẫn còn nguyên) — dùng lệnh này khi cần "tắt bớt cho nhẹ Pi4"
docker compose start          # CHẠY LẠI (không build lại, tận dụng image đã có)
docker compose restart        # khởi động lại nhanh (sau khi sửa code .py — không cần build lại)
docker compose down           # dừng + xóa container (network/container object) — data/ không mất, image không mất, dùng "up -d" để tạo lại container
docker compose up -d          # tạo/chạy lại container
docker compose logs --tail=100
docker compose ps             # xem đang chạy hay đã dừng
docker compose build          # chỉ cần khi đổi requirements.txt hoặc Dockerfile
```

> **`stop`/`start` vs `down`/`up`**: `stop` chỉ tạm dừng tiến trình bên trong
> (giữ nguyên container), `start` chạy lại tức thì — dùng cặp này khi chỉ muốn
> tắt/mở lại cho nhẹ máy. `down` xóa hẳn container (phải tạo lại bằng `up -d`,
> chậm hơn 1 chút nhưng vẫn không cần build lại, không mất dữ liệu vì `data/`
> là bind-mount ở ngoài container).

- **Sửa code** (`app.py`, `checker_web.py`...): code được bind-mount, sửa xong
  chỉ cần `docker compose restart`, không cần build lại image.
- **Cập nhật code mới từ Git**: `git pull && docker compose restart`
  (`docker compose build` thêm nếu `requirements.txt` có đổi).
- **Dữ liệu** (DB, Excel, ảnh, log) nằm trong `./data` (hoặc `DATA_PATH` đã
  chỉnh trong `.env`) — không mất khi `stop`/`start`/`restart`/`down`/`up`/rebuild.

## 9. Xử lý sự cố

| Triệu chứng | Cách xử lý |
|---|---|
| Container cứ "Restarting" liên tục | `docker compose logs` xem traceback Python lúc khởi động |
| `port is already allocated` | Đổi `PORT` trong `.env` sang port khác chưa dùng |
| Chromium crash / timeout khi check hóa đơn | Tăng `shm_size` trong `docker-compose.yml`, hoặc tăng `MEM_LIMIT` |
| `ddddocr`/`onnxruntime` lỗi import trên ARM64 | `docker compose exec web python3 -c "import ddddocr"` để xem traceback cụ thể; thường do thiếu wheel ARM64 — thử `pip install --no-cache-dir --force-reinstall onnxruntime` trong container |
| Không truy cập được từ máy khác trong LAN | Kiểm tra firewall (`ufw status` nếu có bật), kiểm tra `docker compose ps` container đã "Up" |
