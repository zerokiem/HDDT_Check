# Cài đặt HDDT Checker Web trên NAS Synology (Docker / Container Manager)

Cùng 1 bộ code với bản Linux/Pi4 — xem [INSTALL_LINUX_PI.md](INSTALL_LINUX_PI.md)
cho phần chung (docker-compose, .env, vận hành). Tài liệu này chỉ ghi lại các
điểm **khác biệt riêng của NAS Synology**, đúc kết từ kinh nghiệm triển khai
thực tế dự án DO_Auto trên DS423.

## 1. Yêu cầu

| Thành phần | Yêu cầu |
|---|---|
| DSM | 7.2 trở lên |
| Container Manager | Cài từ Package Center |
| RAM | DS423 chỉ có 2 GB — xem lưu ý RAM bên dưới |
| Ổ đĩa | ≥ 5 GB trống cho image + data |

## 2. Chuẩn bị

### Bật SSH
DSM → **Control Panel** → **Terminal & SNMP** → tick **Enable SSH service**.

### Cấp quyền Docker không cần mật khẩu cho user SSH (khuyến nghị)
Docker socket trên Synology mặc định chỉ `root` dùng được. SSH vào NAS rồi:

```bash
ssh <user>@<ip-nas>
echo '<user> ALL=(ALL) NOPASSWD: /usr/local/bin/docker, /usr/local/bin/docker-compose' \
  | sudo tee /etc/sudoers.d/<user>-docker
sudo chmod 440 /etc/sudoers.d/<user>-docker
sudo -n docker ps   # phải chạy KHÔNG hỏi mật khẩu
```

### Tạo thư mục
```bash
mkdir -p /volume1/docker/hddt-web
```

## 3. Copy code lên NAS

**Từ ZIP** (WinSCP hoặc `scp`):
```bash
scp -r ./HDDT_Check <user>@<ip-nas>:/volume1/docker/hddt-web/
```

**Từ Git** (nhanh hơn, dễ cập nhật sau này):
```bash
ssh <user>@<ip-nas>
cd /volume1/docker/hddt-web
git clone git@github.com:zerokiem/HDDT_Check.git .
```

## 4. Build & chạy

**Quan trọng:** trên NAS Synology, binary tên là `docker-compose` (gạch nối),
KHÔNG phải `docker compose` (2 từ liền) như trên Linux thường:

```bash
cd /volume1/docker/hddt-web/hddt-web
cp .env.example .env
nano .env                              # đổi SECRET_KEY, DATA_PATH=/volume1/docker/hddt-web/data
sudo -n /usr/local/bin/docker-compose build
sudo -n /usr/local/bin/docker-compose up -d
```

Kiểm tra:
```bash
sudo -n /usr/local/bin/docker ps --filter name=hddt_web
sudo -n /usr/local/bin/docker logs hddt_web --tail 50
```

Truy cập: `http://<ip-nas>:14687`

## 5. Lưu ý RAM (DS423 — 2 GB)

Chromium headless + Flask + ddddocr cần khoảng 600–900 MB. `.env` đã đặt sẵn
`MEM_LIMIT=768m` — **không tăng quá 1200m** trên DS423 nếu NAS còn chạy các
dịch vụ khác (Container Manager, File Station...). Nếu gặp lỗi
`OOMKilled` (`docker logs` báo container tự tắt đột ngột), giảm
`MAX_CONCURRENT_JOBS=1` (mặc định đã là 1) và tránh chạy nhiều tác vụ NAS nặng
cùng lúc.

## 6. Vì sao không dùng `apt-get` nếu phải sửa Dockerfile

Nếu sau này cần thêm gói hệ thống trong Dockerfile: một số dòng NAS Synology
gặp lỗi `apt-get`/`docker build` timeout khi build qua BuildKit (network
namespace riêng của BuildKit bị lỗi định tuyến/DNS trên NAS — không phải lỗi
mạng NAS nói chung, "docker run" tay vẫn apt-get bình thường được). Dockerfile
hiện tại của dự án **đã tránh hoàn toàn `apt-get`** (dùng thẳng image
Playwright chính thức đã có sẵn Chromium) nên không gặp vấn đề này. Nếu bắt
buộc phải thêm gói mới, cân nhắc tải binary tĩnh qua HTTPS thay vì `apt-get`.

## 7. Vị trí lưu dữ liệu, backup, vận hành & xử lý sự cố

Xem [INSTALL_LINUX_PI.md § 6-9](INSTALL_LINUX_PI.md#6-vị-trí-lưu-dữ-liệu) —
(vị trí lưu, backup, `stop`/`start`/`restart`/`down`/`up`, xử lý sự cố) — chỉ
nhớ thay `docker compose` bằng `sudo -n /usr/local/bin/docker-compose` khi gõ
lệnh trên NAS, và đường dẫn `~/HDDT_Check/hddt-web/data/` trên Pi4 tương ứng
với `/volume1/docker/hddt-web/hddt-web/data/` (hoặc `DATA_PATH` đã chỉnh) trên NAS.

### Đăng nhập DSM Reverse Proxy (tuỳ chọn, thay vì mở port 14687 trực tiếp)

DSM → **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy** → **Create**:
```
Source:      HTTPS, hddt.<ten-mien-cua-ban>, port 443
Destination: HTTP, localhost, port 14687
```
DSM tự cấp/gia hạn chứng chỉ Let's Encrypt cho bạn — không cần tự cấu hình
certbot/nginx riêng.
