# HDDT Checker — Kiểm tra Hóa đơn Điện tử

Ứng dụng web tự động kiểm tra tính hợp lệ của hóa đơn điện tử trên cổng
[hoadondientu.gdt.gov.vn](https://hoadondientu.gdt.gov.vn/) của Tổng cục Thuế:
tải lên file Excel danh sách hóa đơn → tự động điền form, giải captcha, tra
cứu từng hóa đơn → xuất Excel kết quả (2 sheet, tô màu theo kết quả) + ảnh
chụp màn hình đối chiếu.

## Tính năng chính (web)

- Đăng nhập nhiều người dùng (user/admin), log lịch sử đăng nhập.
- Tải lên Excel → chạy kiểm tra nền, xem tiến độ % + log real-time trên web
  (giống terminal) khi đang chạy.
- Tải file Excel mẫu chuẩn (nút "Tải file Excel mẫu") — chỉ 7 cột cần thiết,
  có sẵn dropdown, chú thích, ví dụ. Cột **Số & Ký hiệu hóa đơn** cho phép
  nhập gộp kiểu `1-C26TAP-00001765` — hệ thống **tự tách** ra Ký hiệu
  (`C26TAP`) và Số HĐ (`00001765`), không cần tự tách sẵn 2 cột.
- Lịch sử tất cả lần chạy, tải lại Excel/ZIP ảnh/log của từng lần.
- Trang Admin: quản lý user, xem log đăng nhập, xem job của mọi người.
- Chạy **HIỂN THỊ** (terminal thấy log trực tiếp) hoặc **ẨN** (chạy ngầm nền,
  tự khởi động cùng máy) — xem hướng dẫn theo từng nền tảng bên dưới.

## Cấu trúc thư mục

```
HDDT_Check/
├── hddt-web/          ← Ứng dụng web (Flask + Playwright + ddddocr) — dùng chính
├── legacy_cli/         ← Script dòng lệnh cũ (không giao diện web), giữ lại tham khảo
├── docs/               ← Hướng dẫn cài đặt theo từng nền tảng
│   ├── INSTALL_WINDOWS.md
│   ├── INSTALL_LINUX_PI.md
│   └── INSTALL_NAS_SYNOLOGY.md
└── archive/            ← File/code cũ không còn dùng, giữ lại phòng khi cần (không commit git)
```

Dữ liệu chạy (Excel, ảnh chụp, database, log) **không nằm trong repo này**:
- Windows chạy trực tiếp: mặc định `D:\HDDT_Check\`
- Docker (Linux/Pi4/NAS): thư mục `data/` cạnh `docker-compose.yml` (hoặc
  `DATA_PATH` tự chỉnh trong `.env`)

## Cài đặt

Chọn đúng nền tảng của bạn — mỗi tài liệu có cả cách cài từ **file ZIP** lẫn
từ **Git**:

| Nền tảng | Tài liệu |
|---|---|
| Windows (không cần Docker) | [docs/INSTALL_WINDOWS.md](docs/INSTALL_WINDOWS.md) |
| Linux / Raspberry Pi 4 (Docker) | [docs/INSTALL_LINUX_PI.md](docs/INSTALL_LINUX_PI.md) |
| NAS Synology (Docker/Container Manager) | [docs/INSTALL_NAS_SYNOLOGY.md](docs/INSTALL_NAS_SYNOLOGY.md) |

Cổng mặc định: **14687** (Docker và Windows đều dùng chung port này).

## Cấu trúc file Excel đầu vào (tóm tắt)

| Cột | Bắt buộc | Ví dụ |
|---|:---:|---|
| `MST` | ✅ | `0313756193` |
| `Ten_Cty` | — | `CÔNG TY TNHH ABC` |
| `So_KyHieu_HD` | ✅ | `1-C26TAP-00001765` (tự tách Ký hiệu + Số HĐ) |
| `Loai_HD` | ✅ | `GTGT` hoặc `Ban_hang` |
| `Thanh_toan` | ✅ | `746618472` |
| `Tien_thue` | — | `67874407` |
| `Ngay` | — | `14/05/2026` |

File cũ đã có sẵn 2 cột riêng `Ky_hieu` + `So_HD` vẫn dùng được bình thường.
Bấm nút **"Tải file Excel mẫu"** trên web để có file đúng chuẩn kèm hướng dẫn.

## Script dòng lệnh cũ (không web)

Xem [legacy_cli/](legacy_cli/) — `check_hddt_cli.py` chạy trực tiếp bằng dòng
lệnh (Chromium hiện cửa sổ, không cần đăng nhập web), phù hợp khi chỉ cần chạy
nhanh 1 lần trên máy cá nhân. Ứng dụng web (`hddt-web/`) là bản chính, đầy đủ
tính năng hơn (lịch sử, nhiều người dùng, chạy ẩn/nền).

## Các mã kết quả

| Mã | Ý nghĩa |
|---|---|
| **YES** | Hóa đơn tồn tại và đã được cấp mã — hợp lệ |
| **NO** | Không tìm thấy hóa đơn khớp thông tin đã nhập |
| **CAPTCHA_ERR** | Vượt quá số lần thử captcha tự động |
| **UNKNOWN** | Trang trả về nội dung không nhận dạng được |
| **ERROR** | Lỗi kỹ thuật (điền form, timeout, mạng) |
