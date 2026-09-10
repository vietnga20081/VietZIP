# VietZIP — Kế hoạch nâng cấp toàn diện & đặc tả triển khai cho Claude

> **Mục tiêu:** Nâng VietZIP từ một ứng dụng ZIP desktop cơ bản thành một công cụ nén/giải nén hiện đại, an toàn, dễ dùng, ổn định và có trải nghiệm người dùng tốt trên Windows.
>
> **Nguyên tắc quan trọng:** Giữ ứng dụng nhẹ, ưu tiên thư viện chuẩn Python; chỉ thêm dependency khi thật sự cần. Không phá vỡ các chức năng đang chạy tốt.

---

## 1. Bối cảnh code hiện tại

Dự án hiện có:

- `vietzip_app.py`: ứng dụng desktop Python.
- `README.md`: tài liệu hiện tại.
- `requirements.txt`: hiện chỉ có `customtkinter>=5.2.2`.

Công nghệ:

- Python 3.9+
- CustomTkinter
- `zipfile`, `os`, `pathlib`, `shutil`
- `threading` + `queue`

Chức năng hiện tại:

1. Nén nhiều file.
2. Nén thư mục và giữ cấu trúc thư mục.
3. Giải nén ZIP.
4. Xem trước danh sách ZIP.
5. 4 mức nén.
6. Progress bar.
7. Trạng thái/messaging.
8. Mascot thay đổi theo trạng thái.
9. Light/Dark/System.
10. Chạy tác vụ nền để tránh treo UI.

### Các hạn chế cần xử lý

- Chưa có kéo-thả.
- Chưa có hàng đợi tác vụ.
- Chưa có nút Hủy/Dừng.
- Progress hiện chủ yếu dựa trên số entry, chưa phản ánh chính xác dung lượng/thời gian.
- Chưa có tốc độ, ETA.
- Chưa có lịch sử.
- Chưa có cấu hình ứng dụng được lưu lại.
- Chưa có xử lý tốt các file bị thay đổi/xóa trong lúc nén.
- Chưa có kiểm tra trùng tên/ghi đè rõ ràng.
- Giải nén trực tiếp bằng `ZipFile.extract()` cần được bảo vệ khỏi Zip Slip/path traversal.
- Chưa có kiểm tra ZIP bomb hoặc archive bất thường.
- Chưa có kiểm tra CRC trước/sau theo chế độ người dùng.
- Chưa có giao diện chi tiết cho ZIP lớn.
- Chưa có thông tin thống kê trực quan.
- Chưa có mở thư mục chứa file sau khi hoàn thành.
- Chưa có nút mở file ZIP sau khi tạo.
- Chưa có xử lý lỗi theo nhóm dễ hiểu.
- Kiến trúc hiện đang dồn UI + worker + nghiệp vụ vào một file.

---

# 2. Tầm nhìn sản phẩm

VietZIP nên có cảm giác:

> **“Một WinZip/7-Zip mini, thân thiện, tiếng Việt, hiện đại, dễ dùng cho người dùng phổ thông.”**

Ưu tiên:

1. **An toàn**
2. **Dễ sử dụng**
3. **Nhanh**
4. **Không treo giao diện**
5. **Thông tin tiến trình rõ ràng**
6. **Giao diện đẹp**
7. **Có thể mở rộng**
8. **Đóng gói EXE dễ dàng**

Không biến ứng dụng thành một phần mềm quá phức tạp.

---

# 3. Yêu cầu nâng cấp ưu tiên

Chia thành 4 cấp:

## P0 — Bắt buộc

- Refactor kiến trúc.
- Hủy tác vụ.
- Progress chính xác hơn.
- ETA + tốc độ.
- An toàn khi giải nén.
- Xử lý ghi đè.
- Xử lý lỗi tốt.
- Kiểm tra file đầu vào.
- Giao diện Empty State tốt.
- Lưu cấu hình cơ bản.
- Thống kê sau khi hoàn thành.

## P1 — Rất nên có

- Kéo-thả.
- Lịch sử.
- Recent files.
- Mở thư mục sau khi xong.
- Mở ZIP sau khi nén.
- Chế độ nhanh cho thao tác phổ biến.
- Preview ZIP đẹp hơn.
- Search trong ZIP.
- Chọn/bỏ chọn file trong ZIP.
- Tự động tạo thư mục đích.
- Drag/drop reorder danh sách file nén.

## P2 — Nâng cao

- Mật khẩu/AES encryption.
- Test archive.
- So sánh CRC.
- Batch compression.
- Batch extraction.
- Queue nhiều tác vụ.
- Preset.
- Context menu Windows.
- Portable mode.

## P3 — Có thể phát triển sau

- 7z/RAR.
- Plugin architecture.
- Cloud integration.
- Split archive.
- Benchmark.
- Update checker.
- Telemetry tùy chọn.

---

# 4. Thiết kế giao diện mới

## 4.1. Phong cách

Giữ tinh thần đáng yêu của VietZIP nhưng chuyển sang hướng:

- hiện đại
- sạch
- sáng
- thân thiện
- trẻ trung
- chuyên nghiệp vừa đủ

Không lạm dụng emoji ở mọi thành phần.

Mascot vẫn được giữ nhưng đóng vai trò điểm nhấn.

### Màu sắc đề xuất

Light:

- Background: `#F7F9FC`
- Card: `#FFFFFF`
- Primary: xanh lá/xanh ngọc
- Secondary: xanh dương nhạt
- Success: xanh lá
- Warning: vàng/cam
- Error: đỏ
- Text: xám đậm

Dark:

- Background: gần `#111827`
- Card: gần `#1F2937`
- Text: trắng/xám sáng

Không hard-code màu rải rác trong code. Tạo `ThemeManager` hoặc cấu hình màu tập trung.

---

# 5. Layout mới

## Header

Hiển thị:

- Logo/mascot
- `VietZIP`
- tagline ngắn
- trạng thái hiện tại
- nút theme
- nút Settings

Ví dụ:

```text
📦 VietZIP
Nén & giải nén đơn giản hơn

[ Sáng | Tối | Hệ thống ]   ⚙
```

## Khu vực thao tác nhanh

Tạo 2 card lớn:

```text
┌───────────────────────┐
│ 🗜️ NÉN FILE           │
│ Chọn file hoặc thư mục │
│                       │
│ [ Chọn file ]         │
└───────────────────────┘

┌───────────────────────┐
│ 📂 GIẢI NÉN           │
│ Mở một file ZIP       │
│                       │
│ [ Chọn ZIP ]          │
└───────────────────────┘
```

## Drag & Drop

Khi kéo file vào cửa sổ:

```text
┌─────────────────────────────┐
│                             │
│       📥 Thả file vào đây   │
│                             │
│   Để thêm vào danh sách     │
│                             │
└─────────────────────────────┘
```

---

# 6. Tab Nén file

## Thành phần

### Toolbar

- `+ Thêm file`
- `+ Thêm thư mục`
- `Xóa mục`
- `Xóa tất cả`
- `Thêm từ Clipboard` nếu khả thi

### Danh sách

Mỗi dòng:

```text
📄 photo.jpg
12.4 MB
C:\Users\...\photo.jpg                         ✕
```

Với thư mục:

```text
📁 Documents
124 files • 1.2 GB                              ✕
```

### Thống kê realtime

```text
3 file • 1 thư mục
Tổng dung lượng: 2.34 GB
```

### Tùy chọn

- Mức nén:
  - Không nén
  - Nhanh
  - Cân bằng ⭐
  - Tối đa
- Tạo thư mục gốc
- Giữ cấu trúc thư mục
- Chia archive (P3)
- Mật khẩu (P2)
- Xác minh sau khi nén

### Nút chính

```text
🚀 Nén ngay
```

Disable nếu không có input.

---

# 7. Tab Giải nén

## Khu vực ZIP

Hiển thị:

```text
📦 archive.zip
125 MB
1,284 mục
```

## Preview

Không chỉ dump text.

Có tree/list:

```text
📁 Photos
   📁 2026
      📄 image01.jpg
      📄 image02.jpg

📁 Documents
   📄 report.pdf
```

## Search

Có ô:

```text
🔎 Tìm trong archive...
```

## Filter

- Tất cả
- File
- Thư mục
- Theo extension

## Thông tin

- Tổng file
- Tổng thư mục
- Dung lượng uncompressed
- Dung lượng compressed
- Tỷ lệ nén
- Có mã hóa hay không
- Có lỗi CRC hay không nếu kiểm tra

## Nút

```text
✨ Giải nén
```

Có thêm:

- `Giải nén vào thư mục mới`
- `Mở thư mục sau khi xong`

---

# 8. Progress UI

Đây là phần cần nâng cấp mạnh.

Hiện tại không nên chỉ:

```text
██████████ 70%
```

Mà hiển thị:

```text
Đang nén...

████████████████░░░░ 72%

72%
Đã xử lý: 1.24 GB / 1.72 GB
Tốc độ: 86.4 MB/s
Còn khoảng: 00:08
File hiện tại: video.mp4
```

Có:

- Progress %
- bytes processed
- total bytes
- tốc độ
- ETA
- file hiện tại
- số file đã xử lý / tổng file

---

# 9. Nút Hủy

Bắt buộc phải có.

Khi đang chạy:

```text
⏹ Hủy
```

Worker phải có:

```python
cancel_event = threading.Event()
```

Worker kiểm tra:

```python
if cancel_event.is_set():
    return
```

Không được kill thread cưỡng bức.

Sau khi hủy:

- dừng tác vụ an toàn
- xóa file ZIP tạm nếu đang tạo
- thông báo:
  `Đã hủy thao tác.`
- UI trở về trạng thái bình thường

---

# 10. File tạm khi nén

Không ghi thẳng vào output cuối cùng.

Nên:

```text
output.zip.tmp
```

Sau khi thành công:

```text
os.replace(temp_path, output_path)
```

Nếu lỗi/hủy:

```text
xóa temp_path
```

Mục tiêu:

> Không để người dùng nhận một file ZIP giả nhưng tưởng là file hoàn chỉnh.

---

# 11. An toàn khi giải nén — P0

Không dùng trực tiếp:

```python
zf.extract(member, path=dest_dir)
```

mà phải kiểm tra path.

Mục tiêu chống:

- `../../evil.exe`
- absolute path
- Windows drive path
- path traversal

Tạo hàm:

```python
def safe_extract_path(base_dir: Path, member_name: str) -> Path:
    ...
```

Sau khi resolve:

```python
target.relative_to(base_dir)
```

Nếu không nằm trong `base_dir`:

```python
raise SecurityError(...)
```

---

# 12. Bảo vệ ZIP bomb

Trước khi giải nén cần thống kê:

- compressed size
- uncompressed size
- số file
- tỷ lệ nén

Ví dụ cảnh báo:

```text
⚠️ Archive bất thường

File ZIP chỉ 5 MB nhưng có thể giải nén thành hơn 20 GB.

Bạn có chắc muốn tiếp tục?
[Hủy] [Tiếp tục]
```

Không nên đặt một giới hạn cứng quá thấp.

Đưa cấu hình vào Settings:

```text
Cảnh báo archive lớn:
[✓]

Ngưỡng:
10 GB
```

---

# 13. Ghi đè file

Khi giải nén gặp file đã tồn tại:

Hiện dialog:

```text
File đã tồn tại

photo.jpg

○ Ghi đè
○ Bỏ qua
○ Đổi tên tự động

☐ Áp dụng cho tất cả

[Hủy] [Tiếp tục]
```

Không overwrite âm thầm.

Có thể mặc định:

> Đổi tên tự động

để an toàn cho người dùng phổ thông.

---

# 14. Xử lý file lỗi

Phân biệt:

### File không tồn tại

```text
Không tìm thấy file:
C:\...\abc.jpg
```

### Permission denied

```text
Không có quyền truy cập file.
Hãy đóng file hoặc chọn thư mục khác.
```

### Disk full

```text
Không đủ dung lượng ổ đĩa.
```

### ZIP hỏng

```text
File ZIP bị hỏng hoặc không hợp lệ.
```

### File đang được sử dụng

Hiển thị tên file cụ thể.

Không dùng thông báo:

```text
str(exc)
```

làm nội dung duy nhất cho người dùng.

Log kỹ thuật có thể giữ riêng.

---

# 15. Lịch sử

Thêm panel:

```text
🕘 Lịch sử
```

Lưu:

- thời gian
- thao tác
- input
- output
- kích thước
- thời gian chạy
- trạng thái

Ví dụ:

```text
10:42  🗜️ Nén
Photos → photos.zip
1.4 GB → 620 MB
✓ Thành công

09:18  📂 Giải nén
backup.zip
✓ Thành công
```

Cho phép:

- mở output
- mở thư mục
- xóa lịch sử
- dùng lại thao tác

Lưu JSON tại thư mục cấu hình người dùng.

Không lưu dữ liệu nhạy cảm không cần thiết.

---

# 16. Recent files

Hiển thị tối đa khoảng 10 file gần đây:

```text
Gần đây

📦 backup.zip
📦 project.zip
📦 photos.zip
```

Click để mở nhanh.

---

# 17. Settings

Tạo cửa sổ Settings.

## General

- Ngôn ngữ
- Theme
- Hiện mascot
- Hiện thông báo

## Compression

- Mức nén mặc định
- Thư mục lưu mặc định
- Xác minh archive

## Extraction

- Hỏi khi ghi đè
- Tự tạo thư mục
- Mở thư mục sau khi giải nén
- Cảnh báo archive lớn

## Performance

- Số worker
- Kích thước buffer

Không cho người dùng phổ thông chỉnh quá nhiều thông số nguy hiểm.

---

# 18. Kiến trúc code mới

Không tiếp tục phát triển mọi thứ trong `vietzip_app.py`.

Đề xuất:

```text
vietzip/
│
├── main.py
├── app.py
│
├── core/
│   ├── __init__.py
│   ├── compressor.py
│   ├── extractor.py
│   ├── archive_info.py
│   ├── security.py
│   ├── progress.py
│   └── models.py
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── compress_view.py
│   ├── extract_view.py
│   ├── settings_view.py
│   ├── history_view.py
│   ├── widgets.py
│   └── theme.py
│
├── services/
│   ├── history_service.py
│   ├── settings_service.py
│   └── recent_service.py
│
└── utils/
    ├── file_utils.py
    ├── format_utils.py
    └── logging_utils.py
```

Nếu refactor quá lớn gây rủi ro, có thể thực hiện từng bước.

---

# 19. Data model

Tạo dataclass:

```python
@dataclass
class ProgressInfo:
    operation: str
    current_file: str
    current_index: int
    total_files: int
    processed_bytes: int
    total_bytes: int
    percent: float
    speed_bps: float
    eta_seconds: float | None
```

Kết quả:

```python
@dataclass
class OperationResult:
    success: bool
    output_path: str | None
    file_count: int
    original_size: int
    compressed_size: int
    elapsed_seconds: float
    error: str | None = None
    cancelled: bool = False
```

---

# 20. Progress chính xác

Không nên tính progress chỉ theo:

```python
i / total_files
```

Vì một file 5 GB và 100 file 1 KB sẽ tạo cảm giác sai.

Nên tính theo bytes:

```python
processed_bytes / total_bytes
```

Nếu không lấy được kích thước chính xác thì fallback về số file.

---

# 21. Tính tốc độ

Dùng:

```python
speed = processed_bytes / elapsed
```

Có smoothing để tốc độ không nhảy liên tục.

Ví dụ:

```text
86.4 MB/s
```

---

# 22. ETA

Nếu speed > 0:

```python
remaining = total_bytes - processed_bytes
eta = remaining / speed
```

Format:

```text
00:08
01:42
12:35
```

---

# 23. Nén folder

Hiện tại logic:

```python
base_parent = p.parent
arcname = full.relative_to(base_parent)
```

Cần kiểm tra rõ hành vi khi chọn:

- một folder
- nhiều folder
- file + folder
- folder lồng nhau
- hai input có cùng tên
- cùng một file được chọn hai lần

Không để archive bị collision ngoài ý muốn.

---

# 24. Duplicate detection

Khi user thêm:

```text
photo.jpg
photo.jpg
```

hoặc một folder chứa file đã được thêm riêng.

Phải tránh đưa cùng một file vào archive nhiều lần nếu có thể.

UI có thể cảnh báo:

```text
⚠️ Một số file đã có trong danh sách.
[Giữ nguyên] [Loại trùng]
```

---

# 25. Preview ZIP

Không load hàng chục nghìn item vào UI cùng lúc.

Dùng:

- lazy loading
- giới hạn hiển thị ban đầu
- search
- filter

Ví dụ:

```text
Hiển thị 500 / 24,582 mục

[ Tải thêm ]
```

Search theo tên.

---

# 26. ZIP metadata

Khi chọn ZIP:

Hiển thị:

```text
Tên: backup.zip
Kích thước: 854 MB
Số mục: 12,452
Kích thước sau giải nén: 2.8 GB
Tỷ lệ nén: 69.5%
```

Nếu archive có encrypted entries:

```text
🔐 Có mã hóa
```

---

# 27. Verify archive

Sau khi nén, nếu bật:

```python
zf.testzip()
```

Nếu lỗi:

```text
⚠️ Archive được tạo nhưng kiểm tra CRC thất bại.
```

Đề xuất mặc định:

- bật với archive quan trọng
- có thể tắt để nhanh hơn

---

# 28. Mật khẩu

P2.

Không tự triển khai một thuật toán mã hóa yếu.

`zipfile` chuẩn của Python không phù hợp để cung cấp trải nghiệm AES ZIP hiện đại.

Nếu triển khai:

- chọn thư viện uy tín
- password không lưu plain text
- không log password
- không đưa password vào history
- xóa biến password sau khi dùng nếu phù hợp

UI:

```text
🔐 Bảo vệ bằng mật khẩu

Mật khẩu: ••••••••
Xác nhận: ••••••••

☐ Hiện mật khẩu
```

---

# 29. Kéo thả

Ưu tiên P1.

Có thể dùng:

```text
tkinterdnd2
```

Nhưng phải kiểm tra compatibility với CustomTkinter và Windows.

Nếu dependency này gây lỗi đóng gói, cung cấp fallback:

- click chọn file vẫn hoạt động 100%.

---

# 30. Context menu

P2/P3.

Windows Explorer:

```text
Chuột phải
→ VietZIP
   → Nén thành ZIP
   → Giải nén vào thư mục
```

Không làm ảnh hưởng ứng dụng chính.

---

# 31. Batch operations

Cho phép:

```text
file1.zip
file2.zip
file3.zip

[Giải nén tất cả]
```

Hiển thị queue:

```text
1/3  file1.zip     ✓
2/3  file2.zip     ⏳
3/3  file3.zip     ⏸
```

---

# 32. Queue

Nếu có nhiều tác vụ:

```text
Hàng đợi

✓ photos.zip
⏳ backup.zip
⏸ documents.zip

[Chạy] [Tạm dừng] [Hủy]
```

P2.

Không cần multiprocessing ở phiên bản đầu nếu threading đủ tốt.

---

# 33. Keyboard shortcuts

Thêm:

- `Ctrl + O`: mở/thêm file
- `Ctrl + Shift + O`: thêm thư mục
- `Ctrl + Enter`: bắt đầu
- `Esc`: hủy
- `Delete`: xóa mục đang chọn
- `Ctrl + L`: xóa danh sách
- `Ctrl + ,`: Settings

Hiển thị trong tooltip/menu.

---

# 34. Accessibility

Cần hỗ trợ:

- font dễ đọc
- tương phản tốt
- nút không chỉ dùng emoji
- keyboard navigation
- focus rõ ràng
- cửa sổ resize tốt
- minimum size hợp lý
- không phụ thuộc hoàn toàn vào màu sắc để biểu diễn trạng thái

---

# 35. Responsive UI

Không dùng quá nhiều kích thước pixel cố định.

Khi resize:

- list mở rộng
- preview mở rộng
- button không bị cắt
- status bar luôn nhìn thấy

Kiểm tra ít nhất:

- 800×600
- 1024×768
- 1366×768
- 1920×1080

---

# 36. Mascot

Giữ mascot nhưng tinh giản.

State:

```text
IDLE      📦
WORKING   ⚙️
SUCCESS   🎉
ERROR     😿
CANCELLED 😐
```

Không đổi emoji quá nhanh gây rối mắt.

Có animation nhẹ nếu dễ triển khai.

---

# 37. Toast thay cho MessageBox quá nhiều

Không dùng `messagebox.showinfo()` cho mọi success.

Thay bằng toast:

```text
✓ Nén thành công
photos.zip • 624 MB
```

Có nút:

```text
[Mở file] [Mở thư mục]
```

MessageBox chỉ dùng cho:

- lỗi nghiêm trọng
- xác nhận
- cảnh báo bảo mật
- ghi đè

---

# 38. Error logging

Tạo log:

```text
logs/vietzip.log
```

Log:

- timestamp
- operation
- exception
- traceback

Không log:

- password
- dữ liệu file
- nội dung nhạy cảm

Trong UI chỉ hiện thông báo thân thiện.

Có nút:

```text
Sao chép chi tiết lỗi
```

---

# 39. Settings persistence

Lưu:

```json
{
  "theme": "System",
  "compression_level": 6,
  "open_folder_after_operation": true,
  "verify_archive": true,
  "warn_large_archive": true,
  "history_enabled": true
}
```

Đặt ở thư mục user config, không ghi cạnh source code nếu không cần.

---

# 40. History persistence

Dùng JSON hoặc SQLite.

Với phiên bản nhỏ:

> JSON là đủ.

Nếu history lớn:

> chuyển SQLite.

Giới hạn khoảng 100–500 records.

---

# 41. Đóng gói Windows

Thêm:

```text
build_windows.bat
```

và spec cho PyInstaller.

Ví dụ mục tiêu:

```text
dist/
└── VietZIP/
    └── VietZIP.exe
```

Ưu tiên `--onedir` trước vì ổn định và startup tốt hơn.

Sau khi ổn định mới cân nhắc `--onefile`.

---

# 42. Icon

Tạo icon VietZIP riêng:

- hộp ZIP
- màu xanh/ngọc
- đơn giản
- nhận diện tốt ở kích thước nhỏ

Đưa vào:

```text
assets/
└── vietzip.ico
```

Không hard-code đường dẫn tuyệt đối.

---

# 43. README mới

README phải có:

1. Giới thiệu
2. Screenshot
3. Tính năng
4. Cài đặt
5. Chạy từ source
6. Build EXE
7. Cấu trúc project
8. Bảo mật
9. Troubleshooting
10. Roadmap
11. License

---

# 44. Requirements

Chỉ thêm dependency khi cần.

P0:

```text
customtkinter>=5.2.2
```

P1 nếu drag-drop:

```text
tkinterdnd2
```

P2 encryption/7z phải đánh giá riêng.

Không thêm thư viện chỉ để làm đẹp nếu CustomTkinter đã đáp ứng.

---

# 45. Testing

Tạo thư mục:

```text
tests/
```

Test:

### Compression

- file đơn
- nhiều file
- folder
- folder rỗng
- unicode filename
- filename tiếng Việt
- file lớn
- file 0 byte
- duplicate input

### Extraction

- ZIP bình thường
- ZIP chứa Unicode
- folder
- nested folder
- existing file
- invalid ZIP
- Zip Slip
- archive lớn
- encrypted ZIP nếu có hỗ trợ

### UI

- không freeze
- cancel
- resize
- dark/light
- empty state

---

# 46. Unicode

Bắt buộc test:

```text
Tiếng Việt
中文
日本語
한국어
é
emoji
```

Không được làm mất tên file.

---

# 47. File đang thay đổi

Trong lúc nén, file có thể bị:

- xóa
- đổi tên
- đang được ghi
- bị lock

Worker cần bắt exception cho từng file.

Tùy mode:

### Strict

Gặp lỗi → dừng toàn bộ.

### Continue

Bỏ qua file lỗi và ghi danh sách lỗi.

UI:

```text
⚠️ 2 file không thể nén

[ Xem danh sách lỗi ]
```

Đề xuất mặc định:

> Continue với warning, trừ lỗi nghiêm trọng.

---

# 48. Disk space

Trước khi giải nén archive lớn:

- kiểm tra dung lượng khả dụng nếu có thể.
- so sánh với estimated uncompressed size.

Nếu thiếu:

```text
⚠️ Có thể không đủ dung lượng

Cần khoảng: 12.4 GB
Còn trống: 8.1 GB

[Hủy] [Tiếp tục]
```

Không đảm bảo tuyệt đối vì filesystem có thể thay đổi trong lúc chạy.

---

# 49. Open file/folder

Sau thành công:

```text
✓ Hoàn tất!

photos.zip
624 MB

[ Mở file ] [ Mở thư mục ] [ Đóng ]
```

Trên Windows dùng:

```python
os.startfile(...)
```

Có fallback cho macOS/Linux.

---

# 50. Smart default

Khi nén:

Nếu chọn:

```text
C:\Photos
```

gợi ý:

```text
Photos.zip
```

Nếu chọn nhiều file:

```text
Archive_2026-09-10.zip
```

Nếu chọn một ZIP để giải nén:

```text
C:\...\archive\
```

hoặc:

```text
archive_extracted\
```

---

# 51. UX — trạng thái rõ ràng

Mỗi màn hình phải có:

- Empty
- Ready
- Working
- Success
- Error
- Cancelled

Không để người dùng đoán ứng dụng đang làm gì.

---

# 52. Không làm

Không:

- thêm quảng cáo
- gửi file lên cloud
- telemetry mặc định
- thu thập dữ liệu người dùng
- yêu cầu tài khoản
- phụ thuộc Internet để nén/giải nén
- lưu password
- xóa file nguồn sau khi nén nếu chưa được user yêu cầu

---

# 53. Roadmap triển khai

## Phase 1 — Core safety + stability

Làm trước:

1. Refactor worker.
2. Cancel event.
3. Temp output.
4. Progress bytes.
5. Speed/ETA.
6. Safe extraction.
7. Overwrite policy.
8. Better error handling.
9. Disk-space warning.
10. Verify archive.

## Phase 2 — UI/UX

1. Redesign layout.
2. Empty state.
3. Drag-drop.
4. Better file list.
5. ZIP preview tree.
6. Search/filter.
7. Toast.
8. Open file/folder.
9. Settings.
10. Recent.

## Phase 3 — Productivity

1. History.
2. Queue.
3. Batch extraction.
4. Keyboard shortcuts.
5. Presets.
6. Context menu.

## Phase 4 — Advanced

1. Password/AES.
2. 7z.
3. RAR.
4. Split archive.
5. Portable mode.
6. Benchmark.

---

# 54. Tiêu chí nghiệm thu

Claude chỉ hoàn thành khi:

### Core

- [ ] Nén file hoạt động.
- [ ] Nén folder hoạt động.
- [ ] Giải nén ZIP hoạt động.
- [ ] Unicode hoạt động.
- [ ] UI không freeze.
- [ ] Cancel hoạt động.
- [ ] Temp file được cleanup.
- [ ] Không có Zip Slip.
- [ ] Không overwrite âm thầm.

### Progress

- [ ] %
- [ ] bytes
- [ ] speed
- [ ] ETA
- [ ] current file

### UI

- [ ] Light
- [ ] Dark
- [ ] System
- [ ] Resize
- [ ] Empty state
- [ ] Error state
- [ ] Success state
- [ ] Mascot

### Productivity

- [ ] Drag-drop
- [ ] Recent
- [ ] History
- [ ] Settings
- [ ] Open folder
- [ ] Open output

### Quality

- [ ] Không exception chưa xử lý trong luồng UI.
- [ ] Không hard-code path.
- [ ] Không log password.
- [ ] Có logging.
- [ ] Có test.
- [ ] README cập nhật.
- [ ] requirements cập nhật.
- [ ] Build Windows thành công.

---

# 55. Quy tắc triển khai cho Claude

## Quan trọng

Không chỉ viết code minh họa.

Hãy **thực sự chỉnh sửa project hiện tại**.

Quy trình:

### Bước 1

Đọc toàn bộ:

```text
README.md
requirements.txt
vietzip_app.py
```

### Bước 2

Phân tích code hiện tại trước khi sửa.

### Bước 3

Refactor thành module nếu cần.

### Bước 4

Triển khai P0 trước.

### Bước 5

Chạy ứng dụng.

### Bước 6

Test các case:

- file
- folder
- Unicode
- ZIP lỗi
- Zip Slip
- cancel
- output tồn tại
- file lớn

### Bước 7

Triển khai P1.

### Bước 8

Chạy lại toàn bộ test.

### Bước 9

Cập nhật:

```text
README.md
requirements.txt
```

### Bước 10

Nếu môi trường cho phép, build:

```text
VietZIP.exe
```

### Bước 11

Kiểm tra không có regression.

---

# 56. Nguyên tắc code

- Type hints.
- Docstrings cho logic quan trọng.
- Không viết function quá dài.
- Tách UI khỏi business logic.
- Tách worker khỏi UI.
- Không cập nhật Tkinter từ background thread.
- Worker chỉ gửi event qua queue.
- UI thread xử lý queue.
- Không dùng global state nếu không cần.
- Dùng `pathlib`.
- Dùng context manager cho ZIP/file.
- Catch exception cụ thể.
- Không `except Exception` rồi im lặng bỏ qua.
- Không nuốt lỗi.
- Không hard-code Windows-only behavior trong core.

---

# 57. Event architecture

Worker nên gửi event kiểu:

```python
{
    "type": "progress",
    "progress": progress_info
}
```

hoặc dataclass event.

Các event:

```text
started
progress
warning
completed
cancelled
error
```

UI subscribe/poll queue.

Mục tiêu:

> Có thể thay UI sau này mà core compression không phải viết lại.

---

# 58. Logging

Dùng `logging`.

Ví dụ:

```text
INFO  Compression started
INFO  Added 24 files
INFO  Compression completed
WARNING File skipped
ERROR Extraction failed
```

Không ghi full contents.

---

# 59. Performance

Không:

- đọc toàn bộ file vào RAM.
- load toàn bộ archive tree vào UI nếu archive cực lớn.
- tính toán metadata lặp lại quá nhiều lần.

Dùng streaming:

```python
shutil.copyfileobj(...)
```

hoặc API ZIP phù hợp.

Buffer có thể khoảng:

```text
1–4 MB
```

nhưng benchmark thực tế trước khi tối ưu quá mức.

---

# 60. Kết quả cuối mong muốn

VietZIP sau nâng cấp cần mang cảm giác:

```text
┌──────────────────────────────────────────┐
│ 📦 VietZIP                    ☀️  ⚙     │
│ Nén & giải nén đơn giản hơn              │
├──────────────────────────────────────────┤
│                                          │
│  🗜️ NÉN FILE       📂 GIẢI NÉN           │
│  ───────────       ───────────            │
│                                          │
│  Kéo file vào đây                        │
│                                          │
│  📄 photo.jpg       12 MB        ✕       │
│  📁 Documents       240 MB       ✕       │
│                                          │
│  252 MB • 2 mục                          │
│                                          │
│  Mức nén: [ Cân bằng ⭐ ]                 │
│                                          │
│             🚀 NÉN NGAY                  │
│                                          │
├──────────────────────────────────────────┤
│ ████████████████░░░  78%                 │
│ 1.2 GB / 1.5 GB • 84 MB/s • còn 00:04    │
│ Đang xử lý: video.mp4             ⏹ Hủy │
└──────────────────────────────────────────┘
```

---

# 61. Ưu tiên cuối cùng

Nếu thời gian có hạn, hãy ưu tiên chính xác theo thứ tự:

1. **Security**
2. **Không freeze**
3. **Cancel**
4. **Progress**
5. **Error handling**
6. **UI**
7. **Settings**
8. **History**
9. **Drag-drop**
10. **Advanced formats**

Không hy sinh độ ổn định để thêm nhiều tính năng.

---

# 62. Deliverables

Sau khi hoàn thành, project phải có tối thiểu:

```text
README.md
requirements.txt
main.py

vietzip/
    core/
    ui/
    services/
    utils/

tests/

assets/
    vietzip.ico

build_windows.bat
VietZIP.spec
```

Nếu quyết định giữ cấu trúc một file vì lý do tương thích, vẫn phải tách các lớp/logic rõ ràng và giải thích lý do trong README.

---

# 63. Báo cáo cuối cho người dùng

Sau khi code xong, Claude cần báo cáo ngắn:

```text
ĐÃ HOÀN THÀNH VIETZIP

✓ Đã nâng cấp UI
✓ Đã thêm Cancel
✓ Đã thêm progress/ETA
✓ Đã chống Zip Slip
✓ Đã thêm History
✓ Đã thêm Settings
✓ Đã thêm Drag & Drop

Files thay đổi:
- ...
- ...

Dependencies:
- ...

Test:
- 24 passed
- 0 failed

Build:
- VietZIP.exe
```

Nếu có tính năng chưa hoàn thành, phải ghi rõ:

```text
⚠ Chưa hoàn thành:
- AES encryption
- RAR
```

Không được tuyên bố hoàn thành nếu chưa test thực tế.

---

# 64. Yêu cầu đặc biệt về chất lượng

**Không được chỉ sửa giao diện.**

Mục tiêu là nâng cấp cả:

- UX
- architecture
- security
- performance
- reliability
- maintainability

Hãy giữ VietZIP đơn giản với người dùng nhưng mạnh ở bên trong.

**Nguyên tắc sản phẩm:**

> “Một người dùng phổ thông có thể mở VietZIP, kéo file vào, bấm một nút và hiểu ngay chuyện gì đang xảy ra.”

