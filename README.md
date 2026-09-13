# VietZIP 📦 — Công cụ Nén & Giải nén Hiện đại, An toàn cho Windows

> **“Một WinZip/7-Zip mini, thân thiện, tiếng Việt, hiện đại, dễ dùng cho người dùng phổ thông.”**

VietZIP là ứng dụng desktop nén và giải nén file ZIP được xây dựng bằng Python và CustomTkinter, chú trọng vào **bảo mật**, **trải nghiệm người dùng mượt mà**, **không đơ giao diện**, và **thống kê chi tiết theo thời gian thực**.

---

## ✨ Tính năng nổi bật

### 🗜️ Nén dữ liệu mạnh mẽ & linh hoạt
- **Nén file & thư mục:** Hỗ trợ chọn nhiều file, thư mục lồng nhau, bảo toàn thư mục rỗng và cấu trúc gốc.
- **Phát hiện trùng lặp thông minh:** Tự động loại bỏ file trùng lặp nếu người dùng chọn nhiều lần hoặc chọn folder chứa file riêng lẻ.
- **4 Mức độ nén:**
  - *Siêu nhanh* (Store - không nén)
  - *Nhanh* (Level 3)
  - *Cân bằng ⭐* (Level 6 - khuyến nghị)
  - *Nén tối đa 🐢* (Level 9)
- **Bảo vệ bằng mật khẩu (AES-256):** Tích hợp chuẩn mã hóa AES hiện đại thông qua `pyzipper`.
- **Xác minh toàn vẹn (Verify CRC):** Tự động kiểm tra file ZIP sau khi tạo (`testzip()`) để đảm bảo không bị lỗi dữ liệu.
- **Tập tin tạm thời (`.tmp`):** Quá trình nén ghi vào file `.tmp` và chỉ đổi tên nguyên tử (`os.replace`) khi hoàn tất 100%, bảo vệ người dùng khỏi việc mở phải file dở dang.

### 📂 Giải nén an toàn & trực quan
- **Chống Zip Slip & Path Traversal:** Cơ chế `safe_extract_path` ngăn chặn triệt để mọi mã độc cố tình nhảy ra khỏi thư mục đích (`../../evil.exe`).
- **Phát hiện & Cảnh báo Zip Bomb:** Kiểm tra tỷ lệ nén bất thường (> 50:1 hoặc kích thước giải nén vượt ngưỡng cấu hình) để bảo vệ bộ nhớ và ổ cứng.
- **Chính sách xử lý ghi đè linh hoạt:**
  - *Tự động đổi tên* (`file (1).ext`) — an toàn cho người dùng phổ thông
  - *Ghi đè file cũ*
  - *Bỏ qua file đã tồn tại*
- **Xem trước danh sách nội dung:** Hiển thị cây danh mục chi tiết, kích thước nén/giải nén, tỷ lệ tiết kiệm dung lượng.
- **Tìm kiếm & Bộ lọc nhanh:** Tìm kiếm file tức thì (`🔎 Tìm trong archive...`) và lọc theo *Tất cả / Chỉ file / Chỉ thư mục*.
- **Tự động gợi ý thư mục con:** Tùy chọn tự giải nén vào thư mục cùng tên với file ZIP.

### ⚡ Hiệu năng & Trải nghiệm (UX/UI)
- **Xử lý nền (`threading` + `queue`):** Giao diện luôn phản hồi mượt mà, không bao giờ bị đơ hay Not Responding.
- **Nút Hủy (Cancel) an toàn:** Cho phép dừng tác vụ bất kỳ lúc nào, giải phóng tài nguyên và tự dọn dẹp file tạm.
- **Tiến độ chính xác theo Bytes:** Không tính theo số lượng file mà tính theo dung lượng byte thực tế.
- **Tốc độ & Thời gian còn lại (ETA):** Tính tốc độ truyền dữ liệu (MB/s có thuật toán làm mượt EMA) và dự đoán thời gian hoàn thành chính xác (`00:08`, `01:42`).
- **Kéo & Thả (Drag & Drop):** Kéo thả file/folder trực tiếp từ Windows Explorer vào cửa sổ ứng dụng (hỗ trợ bởi `tkinterdnd2`).
- **Lịch sử tác vụ (History):** Lưu lại 300 lần nén/giải nén gần nhất, cho phép mở nhanh file kết quả hoặc mở thư mục chứa.
- **Danh sách gần đây (Recent files):** Truy cập nhanh các file ZIP đã mở gần đây.
- **Toast Notifications:** Thông báo hoàn tất gọn gàng với nút **[📦 Mở file]** và **[📂 Mở thư mục]**.
- **Mascot cảm xúc:** Biểu tượng thay đổi theo trạng thái: Chờ (`📦`), Đang chạy (`⚙️/🚀`), Hoàn thành (`🎉`), Lỗi (`😿`), Đã hủy (`😐`).
- **Giao diện đa sắc:** Hỗ trợ chế độ Sáng (`Light`), Tối (`Dark`), và Theo hệ thống (`System`).

---

## 📁 Cấu trúc dự án

```text
VietZIP/
├── main.py                     # Entrypoint khởi động chính thức
├── vietzip_app.py              # Wrapper tương thích ngược
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── VietZIP.spec                # Cấu hình PyInstaller cho Windows
├── build_windows.bat           # File batch tự động test và đóng gói EXE
├── assets/
│   ├── vietzip.ico             # Icon ứng dụng định dạng ICO
│   └── vietzip.png             # Icon ứng dụng định dạng PNG
├── vietzip/
│   ├── __init__.py
│   ├── app.py                  # Khởi chạy & quản lý ngoại lệ toàn cục
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py           # Dataclass (ProgressInfo, OperationResult, ArchiveEntry, ...)
│   │   ├── security.py         # Chống Zip Slip & phát hiện Zip Bomb
│   │   ├── progress.py         # Bộ tính toán tiến độ byte, tốc độ EMA, ETA
│   │   ├── compressor.py       # Engine nén: hỗ trợ temp file, cancel, password AES
│   │   ├── extractor.py        # Engine giải nén an toàn, overwrite policy
│   │   └── archive_info.py     # Đọc metadata, danh sách nội dung ZIP
│   ├── services/
│   │   ├── __init__.py
│   │   ├── settings_service.py # Quản lý cấu hình JSON (AppData)
│   │   ├── history_service.py  # Quản lý lịch sử nén/giải nén
│   │   └── recent_service.py   # Quản lý danh sách file mở gần đây
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py       # Thao tác Explorer, đĩa trống, tên file duy nhất
│   │   ├── format_utils.py     # Định dạng dung lượng, thời gian, tốc độ
│   │   └── logging_utils.py    # Ghi log file logs/vietzip.log
│   └── ui/
│       ├── __init__.py
│       ├── theme.py            # Bảng màu, font, mascot
│       ├── widgets.py          # Toast popup, OverwriteDialog
│       ├── compress_view.py    # Giao diện tab Nén file
│       ├── extract_view.py     # Giao diện tab Giải nén
│       ├── history_view.py     # Cửa sổ Lịch sử tác vụ
│       ├── settings_view.py    # Cửa sổ Cài đặt người dùng
│       └── main_window.py      # Cửa sổ chính & quản lý thread worker
└── tests/
    ├── __init__.py
    ├── test_compressor.py      # Test nén file, thư mục, unicode, 0-byte, cancel, pass
    ├── test_extractor.py       # Test giải nén, ghi đè, giải nén pass, cancel, corrupt
    ├── test_security.py        # Test chống Zip Slip, test Zip Bomb
    └── test_services.py        # Test lưu trữ cấu hình & lịch sử
```

---

## 🚀 Cài đặt & Khởi chạy

### Yêu cầu hệ thống
- **Hệ điều hành:** Windows 10/11 (khuyến nghị), tương thích cả macOS & Linux.
- **Python:** Phiên bản 3.9 trở lên.

### Khởi chạy từ mã nguồn
```bash
# 1. Cài đặt các dependencies
pip install -r requirements.txt

# 2. Khởi chạy ứng dụng
python main.py
# (hoặc python vietzip_app.py)
```

### Chạy bộ kiểm thử tự động
```bash
pytest -v
```

---

## 📦 Đóng gói thành file thực thi (.EXE)

Dự án đã có sẵn script đóng gói tự động cho Windows:

1. Chạy file `build_windows.bat` (Local build):
   ```cmd
   build_windows.bat
   ```
2. File thực thi độc lập sẽ được tạo tại:
   ```text
   dist/VietZIP/VietZIP.exe
   dist/VietZIP_Setup.exe
   ```
3. Xem hướng dẫn tự động đóng gói & phát hành trên GitHub Actions tại: **[BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md)**.

---

## ⌨️ Phím tắt tiện lợi

| Phím tắt | Thao tác |
|---|---|
| `Ctrl + O` | Chọn thêm file để nén |
| `Ctrl + Shift + O` | Chọn thêm thư mục để nén |
| `Escape` | Hủy tác vụ đang chạy |
| `Ctrl + ,` | Mở cửa sổ Cài đặt |

---

## 🔒 Bảo mật & Quyền riêng tư

- **Hoạt động 100% Offline:** Không gửi dữ liệu file lên bất kỳ máy chủ đám mây nào.
- **Không ghi log mật khẩu:** Mật khẩu nén/giải nén không bao giờ được lưu vào log file hay lịch sử.
- **Chống khai thác Path Traversal:** Mọi đường dẫn được chuẩn hóa và kiểm tra nghiêm ngặt trước khi ghi đĩa.

---

## 🌐 Website & Kênh phát hành chính thức

- **Website chính thức:** [https://vietzip.vcp.io.vn](https://vietzip.vcp.io.vn)
- **Mã nguồn GitHub:** [https://github.com/vietnga20081/VietZIP](https://github.com/vietnga20081/VietZIP)
- **Bản phát hành mới nhất (Releases):** [Tải VietZIP Setup (.exe)](https://github.com/vietnga20081/VietZIP/releases)

---

## 👥 Về Team VietZIP

VietZIP được phát triển và duy trì bởi **Team VietZIP** với mục tiêu mang đến cho người dùng Việt Nam một phần mềm nén & giải nén file hiện đại, bảo mật và **hoàn toàn miễn phí 100%**.

- ❌ **Không quảng cáo**
- ❌ **Không thu phí bản quyền**
- ❌ **Không thu thập dữ liệu cá nhân**
- ✅ **100% Mã nguồn mở & Thuần Việt**

---

## ☕ Ủng hộ tác giả (Donate)

Nếu VietZIP giúp ích cho công việc và học tập hàng ngày của bạn, hãy tiếp thêm động lực cho Team VietZIP bằng một tách cà phê nhé! 💖

- **Ngân hàng:** ACB
- **Số tài khoản:** `19675051`
- **Chủ tài khoản:** DAO QUOC VIET
- **Nội dung:** `VietZIP Donate`
- **Momo:** `0816086555`

---

## 📜 Giấy phép
Dự án được phát hành theo giấy phép mã nguồn mở MIT License. Bản quyền © 2026 bởi **Team VietZIP**.

