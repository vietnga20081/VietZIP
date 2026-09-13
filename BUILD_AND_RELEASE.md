# 🚀 Hướng Dẫn Cập Nhật & Đóng Gói (Build & Release) Trên GitHub

Tài liệu này hướng dẫn chi tiết quy trình cập nhật mã nguồn và kích hoạt hệ thống CI/CD tự động đóng gói ứng dụng **VietZIP** trên GitHub Actions thành file cài đặt Windows (`.exe`) và bản di động (`.zip`).

---

## 📋 Mục Lục
1. [Tổng Quan Hệ Thống Build](#1-tổng-quan-hệ-thống-build)
2. [Cách 1: Cập Nhật & Phát Hành Chính Thức (Tạo Release qua Git Tag) — Khuyên Dùng](#2-cách-1-cập-nhật--phát-hành-chính-thức-tạo-release-qua-git-tag)
3. [Cách 2: Kích Hoạt Build Thử Nghiệm Từ Giao Diện GitHub (Manual Trigger)](#3-cách-2-kích-hoạt-build-thử-nghiệm-từ-giao-diện-github-manual-trigger)
4. [Cách 3: Đóng Gói Trực Tiếp Trên Máy Tính Cá Nhân (Local Build)](#4-cách-3-đóng-gói-trực-tiếp-trên-máy-tính-cá-nhân-local-build)
5. [Mẹo & Xử Lý Khi Cần Đổi Hoặc Xóa Tag](#5-mẹo--xử-lý-khi-cần-đổi-hoặc-xóa-tag)

---

## 1. Tổng Quan Hệ Thống Build

VietZIP được cấu hình quy trình CI/CD tự động trong file [`.github/workflows/build-release.yml`](.github/workflows/build-release.yml). Mỗi khi được kích hoạt trên máy ảo Windows (`windows-latest`):
- ✅ Cài đặt môi trường **Python 3.13**.
- ✅ Cài đặt toàn bộ dependencies trong `requirements.txt`, cùng `pyinstaller` và `pytest`.
- ✅ Chạy bộ kiểm thử tự động (`pytest -v`). Nếu phát hiện lỗi, tiến trình sẽ dừng lại để tránh phát hành phiên bản lỗi.
- ✅ Đóng gói bản Portable (`VietZIP.spec`) thành `VietZIP_Portable.zip`.
- ✅ Tạo gói cài đặt Wizard (`VietZIP_Setup.spec`) thành `VietZIP_Setup.exe` (tự động tạo shortcut Desktop, Start Menu và đăng ký menu chuột phải).
- ✅ Tải file sản phẩm lên mục **Artifacts** và tự động xuất bản tại mục **GitHub Releases** khi có Tag phiên bản.

---

## 2. Cách 1: Cập Nhật & Phát Hành Chính Thức (Tạo Release qua Git Tag)

Đây là quy trình chuẩn khi bạn hoàn thiện tính năng hoặc sửa lỗi và muốn cung cấp bản cập nhật mới cho người dùng tải về.

### Bước 1: Commit và đẩy mã nguồn mới lên nhánh `main`
Mở Terminal / PowerShell tại thư mục dự án:

```bash
# 1. Kiểm tra các file đã chỉnh sửa
git status

# 2. Thêm toàn bộ các file thay đổi vào staging
git add .

# 3. Tạo commit với nội dung rõ ràng
git commit -m "fix: sua loi an cua so chuc nang va cap nhat thong tin donate"

# 4. Đẩy mã nguồn lên GitHub
git push origin main
```

### Bước 2: Đánh Tag phiên bản mới và đẩy lên GitHub
Hệ thống GitHub Actions được lập trình để **tự động chạy** khi phát hiện một Tag bắt đầu bằng chữ `v` (ví dụ `v2.0.1`, `v2.0.2`, `v2.1.0`):

```bash
# 1. Đánh tag phiên bản mới
git tag -a v2.0.1 -m "VietZIP Release v2.0.1"

# 2. Đẩy tag lên GitHub
git push origin v2.0.1
```

> **Lưu ý:** Nếu bạn muốn đẩy cả commit và tag cùng lúc:
> ```bash
> git push origin main --tags
> ```

### Bước 3: Theo dõi tiến trình và nhận file sản phẩm
1. Truy cập repo GitHub: [https://github.com/vietnga20081/VietZIP](https://github.com/vietnga20081/VietZIP)
2. Chọn tab **Actions**: Bạn sẽ thấy workflow **Build & Release VietZIP** đang chạy biểu tượng màu vàng xoay tròn 🟡.
3. Chờ khoảng 3 – 5 phút đến khi chuyển sang màu xanh lá ✅.
4. Chuyển sang mục **Releases** (bên phải trang chính repository) hoặc đường dẫn:
   [https://github.com/vietnga20081/VietZIP/releases](https://github.com/vietnga20081/VietZIP/releases)
5. Bản Release mới `VietZIP v2.0.1` sẽ có sẵn 2 file tải về:
   - 📦 `VietZIP_Setup.exe` (Trình cài đặt tự động)
   - 📦 `VietZIP_Portable.zip` (Bản chạy ngay không cần cài đặt)

---

## 3. Cách 2: Kích Hoạt Build Thử Nghiệm Từ Giao Diện GitHub (Manual Trigger)

Nếu bạn chỉ muốn build thử nghiệm mã nguồn trên nhánh `main` để kiểm tra file `.exe` hoạt động có ổn định không mà **chưa muốn tạo bản phát hành chính thức (Release)**:

1. Truy cập vào kho mã nguồn trên trình duyệt: [https://github.com/vietnga20081/VietZIP/actions](https://github.com/vietnga20081/VietZIP/actions)
2. Ở danh sách bên trái, nhấp chọn workflow **Build & Release VietZIP**.
3. Ở góc trên bên phải, bấm vào nút **Run workflow** (có biểu tượng mũi tên xổ xuống).
4. Giữ nguyên nhánh **Branch: main** và bấm nút màu xanh **Run workflow**.
5. Chờ build hoàn tất (khoảng 3 – 5 phút):
   - Nhấp vào lượt chạy vừa xong.
   - Kéo xuống dưới cùng tại mục **Artifacts**, bạn sẽ thấy mục:
     **`VietZIP-Windows-Build`**
   - Nhấp vào để tải về file `.zip` chứa cả `VietZIP_Setup.exe` và `VietZIP_Portable.zip`.

---

## 4. Cách 3: Đóng Gói Trực Tiếp Trên Máy Tính Cá Nhân (Local Build)

Nếu bạn muốn build thử trực tiếp trên máy tính Windows của mình:

### Tùy chọn A: Sử dụng file script tự động
Nhấp đúp chuột vào file:
```cmd
build_windows.bat
```
Hoặc mở PowerShell / CMD tại thư mục dự án và chạy:
```cmd
.\build_windows.bat
```

### Tùy chọn B: Chạy thủ công bằng lệnh
```bash
# 1. Cài đặt các thư viện cần thiết
pip install -r requirements.txt pyinstaller pytest

# 2. Chạy test
pytest -v

# 3. Đóng gói ứng dụng chính VietZIP
python -m PyInstaller VietZIP.spec --noconfirm --clean

# 4. Đóng gói bộ cài đặt Setup Wizard (VietZIP_Setup.exe)
python -c "import shutil; shutil.make_archive('payload', 'zip', 'dist/VietZIP')"
python -m PyInstaller VietZIP_Setup.spec --noconfirm --clean

# 5. Xóa file zip trung gian
Remove-Item -Path payload.zip -ErrorAction SilentlyContinue
```

Sau khi hoàn tất, kết quả sẽ nằm trong thư mục `dist/`:
- `dist\VietZIP\VietZIP.exe` (Ứng dụng chạy độc lập)
- `dist\VietZIP_Setup.exe` (Bộ cài đặt Setup Wizard)

---

## 5. Mẹo & Xử Lý Khi Cần Đổi Hoặc Xóa Tag

Nếu bạn vừa tạo một Tag (ví dụ `v2.0.1`) nhưng phát hiện cần sửa gấp một file và muốn gắn lại tag này:

```bash
# 1. Xóa tag tại máy tính cá nhân (local)
git tag -d v2.0.1

# 2. Xóa tag trên GitHub (remote)
git push --delete origin v2.0.1

# 3. Sửa code, commit lại
git add .
git commit -m "fix: cap nhat bo sung"
git push origin main

# 4. Tạo lại tag và push lên GitHub để kích hoạt lại build
git tag -a v2.0.1 -m "VietZIP Release v2.0.1"
git push origin v2.0.1
```
