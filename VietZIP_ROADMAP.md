# VietZIP — Roadmap nâng cấp

Mỗi version chỉ tập trung **1 nhóm tính năng**, độc lập với nhau, có thể phát hành
riêng lẻ. Thứ tự dưới đây xếp theo mức ưu tiên đề xuất (giá trị cao / công sức thấp
lên trước) — có thể đảo thứ tự tùy nhu cầu thực tế, vì các version không phụ thuộc
lẫn nhau trừ khi ghi chú riêng.

Mỗi mục có: **Mục tiêu**, **Việc cần làm**, **File/module liên quan**, **Tiêu chí hoàn thành**.

---

## v2.1 — Thao tác nhanh trong danh sách & xem trước

**Mục tiêu:** Giảm thao tác thừa khi làm việc với file đã chọn/đã giải nén, không đổi kiến trúc.

**Việc cần làm:**
- [ ] `FileList` (màn hình Nén): hỗ trợ Ctrl+Click / Shift+Click để chọn nhiều dòng, thêm nút "Xóa mục đã chọn"
- [ ] `ArchiveContentsWindow`: thêm checkbox mỗi dòng + nút "Giải nén mục đã chọn" (chỉ giải nén phần được tick thay vì cả archive)
- [ ] Double-click vào 1 file text/ảnh nhỏ (< 5MB) trong `ArchiveContentsWindow` → xem trước ngay trong cửa sổ phụ, không cần giải nén ra đĩa
- [ ] Core: thêm hàm `extract_selected(zip_path, members, dest_dir, ...)` trong `extractor.py` (tái dùng logic hiện có, chỉ lọc theo danh sách tên)

**File/module liên quan:** `ui/components/file_list.py`, `ui/archive_contents_view.py`, `core/extractor.py`

**Tiêu chí hoàn thành:** Chọn 3/10 file trong 1 archive → chỉ 3 file đó xuất hiện ở thư mục đích; test hồi quy cho `extract_selected` pass.

---

## v2.2 — Đa ngôn ngữ (Tiếng Việt / English)

**Mục tiêu:** Mở khóa dropdown "Ngôn ngữ" đang bị khóa cứng trong Settings.

**Việc cần làm:**
- [ ] Tạo lớp i18n mỏng: `utils/i18n.py` với dict `{"vi": {...}, "en": {...}}` và hàm `t(key)`
- [ ] Rà toàn bộ chuỗi hiển thị trong `ui/*.py` và `ui/components/*.py`, thay bằng `t("...")`
- [ ] Lưu lựa chọn ngôn ngữ vào `settings_service` (`language: "vi" | "en"`)
- [ ] Cần khởi động lại app để áp dụng (ghi rõ trong UI) — tránh phải viết cơ chế đổi ngôn ngữ real-time phức tạp

**File/module liên quan:** toàn bộ `ui/`, `services/settings_service.py`, file mới `utils/i18n.py`

**Tiêu chí hoàn thành:** Chọn "English" → khởi động lại → toàn bộ nhãn, thông báo lỗi, tooltip hiển thị tiếng Anh; không còn chuỗi tiếng Việt hard-code sót lại.

---

## v2.3 — Hỗ trợ giải nén RAR / 7Z ⭐ (ưu tiên cao nhất)

**Mục tiêu:** Đây là điểm nghẽn thực tế lớn nhất — người dùng Việt Nam tải file .rar rất phổ biến.

**Việc cần làm:**
- [ ] Thêm dependency `py7zr` (cho .7z) và `rarfile` (cho .rar, cần `unrar`/`bsdtar` trên máy hoặc bundle theo installer)
- [ ] `core/archive_info.py`: thêm hàm nhận diện định dạng theo magic bytes (không chỉ theo đuôi file), trả về `ArchiveMetadata` chung cho cả 3 định dạng
- [ ] `core/extractor.py`: tách logic đọc entry theo định dạng (adapter pattern: `ZipReader`, `SevenZipReader`, `RarReader` cùng interface)
- [ ] `ui/extract_view.py`: cập nhật bộ lọc file dialog (`*.zip;*.rar;*.7z`), cập nhật `is_zip()` → đổi tên thành `is_supported_archive()`
- [ ] Cảnh báo rõ nếu thiếu `unrar` binary trên máy (RAR5 cần binary ngoài, không thuần Python) — hướng dẫn cài đặt trong Settings
- [ ] **Chỉ giải nén**, không hỗ trợ *tạo* file RAR/7z (RAR là định dạng có bản quyền, không nên tự nén sang RAR)

**File/module liên quan:** `core/extractor.py`, `core/archive_info.py`, `ui/extract_view.py`, `requirements.txt`

**Tiêu chí hoàn thành:** Giải nén thành công 1 file .rar và 1 file .7z (có/không mật khẩu) ra đúng nội dung, có test với file mẫu trong `tests/fixtures/`.

---

## v2.4 — Nén riêng từng nguồn (Batch nén)

**Mục tiêu:** Khi chọn nhiều file/thư mục, cho phép nén mỗi nguồn thành 1 ZIP riêng thay vì luôn gộp chung.

**Việc cần làm:**
- [ ] `ui/compress_view.py`: thêm toggle "Nén chung 1 file" / "Nén riêng từng mục" cạnh ô chọn nơi lưu
- [ ] Khi chọn "Nén riêng": ẩn `OutputPicker` đơn, thay bằng chọn 1 thư mục đích chung — tên file ZIP tự sinh theo từng nguồn
- [ ] `core/compressor.py`: thêm hàm `compress_batch(sources, dest_dir, ...)` — chạy tuần tự từng nguồn, gộp `ProgressInfo` theo tổng thể (dùng lại `compress_archive` cho từng mục)
- [ ] `ProgressPanel`: hiển thị thêm "Đang nén mục 2/5: tên_file.zip"
- [ ] Kết quả cuối: `ResultPanel` liệt kê danh sách ZIP đã tạo, mục nào lỗi thì báo riêng (không dừng cả batch vì 1 lỗi)

**File/module liên quan:** `core/compressor.py`, `ui/compress_view.py`, `ui/components/progress_panel.py`, `ui/components/result_panel.py`

**Tiêu chí hoàn thành:** Chọn 5 file → "Nén riêng" → ra đúng 5 file ZIP; 1 file bị lỗi quyền đọc không làm hỏng 4 file còn lại.

---

## v2.5 — Chia nhỏ archive (Split volume)

**Mục tiêu:** Xuất archive thành nhiều phần `.zip.001, .zip.002...` để gửi qua kênh giới hạn dung lượng.

**Việc cần làm:**
- [ ] `AdvancedOptions` (màn hình Nén): thêm ô "Chia file thành các phần" (dropdown: Không chia / 10MB / 100MB / 700MB / Tùy chỉnh)
- [ ] `core/compressor.py`: sau khi nén xong file ZIP hoàn chỉnh, cắt thành các phần theo dung lượng chọn (đơn giản hơn nhiều so với việc nén trực tiếp theo từng phần)
- [ ] Giải nén: `core/extractor.py` cần phát hiện và tự ghép các phần `.001, .002...` lại trước khi đọc — hoặc yêu cầu người dùng chọn phần `.001` và tự tìm các phần còn lại cùng thư mục
- [ ] `ExtractView`: khi chọn file có phần mở rộng `.001`, tự động dò các phần tiếp theo, báo rõ nếu thiếu phần nào

**File/module liên quan:** `core/compressor.py`, `core/extractor.py`, `ui/compress_view.py`, `ui/components/advanced_options.py`

**Tiêu chí hoàn thành:** Nén 1 file 50MB chia thành phần 10MB → ra 5 file `.zip.001`–`.zip.005`; giải nén lại cho ra đúng file gốc (so khớp checksum).

---

## v2.6 — Tự khôi phục ZIP hỏng một phần

**Mục tiêu:** Tận dụng thông tin đã có sẵn trong `archive_info.py` để cứu dữ liệu khi ZIP bị lỗi CRC/header hỏng cục bộ.

**Việc cần làm:**
- [ ] `core/archive_info.py`: thêm hàm `diagnose_corruption(zip_path)` — quét từng entry, phân loại "đọc được" / "lỗi CRC" / "header hỏng"
- [ ] `core/extractor.py`: thêm chế độ `best_effort=True` — bỏ qua entry lỗi, vẫn giải nén các entry còn đọc được, ghi log chi tiết phần bị bỏ qua
- [ ] `ExtractView`: khi phát hiện ZIP lỗi ở bước xem trước, hiện nút "Thử khôi phục những gì có thể" thay vì chỉ báo lỗi và dừng
- [ ] `ResultPanel`: hiển thị rõ "Khôi phục được 8/10 file, 2 file bị hỏng không thể cứu: ..."

**File/module liên quan:** `core/archive_info.py`, `core/extractor.py`, `ui/extract_view.py`, `ui/components/result_panel.py`

**Tiêu chí hoàn thành:** Với 1 ZIP test bị cố ý ghi đè vài byte giữa file, "Thử khôi phục" lấy ra được các entry không bị ảnh hưởng, báo rõ entry nào mất.

---

## v2.7 — Theo dõi thư mục (Watch folder / tự động nén nền)

**Mục tiêu:** Chạy nền, tự động nén file mới xuất hiện trong 1 thư mục chỉ định — dùng cho backup tự động.

**Việc cần làm:**
- [ ] Service mới `services/watch_service.py`: dùng `watchdog` (thư viện) theo dõi 1 thư mục, debounce sự kiện, gọi `compress_archive` khi có file mới ổn định (không còn ghi dở)
- [ ] `SettingsWindow` → thêm trang "Tự động hóa": chọn thư mục theo dõi, thư mục đích, quy tắc đặt tên, bật/tắt
- [ ] Chạy nền qua system tray icon (cần thêm `pystray` hoặc tương đương) — app có thể thu nhỏ xuống tray thay vì thoát hẳn
- [ ] Thông báo desktop (Windows toast) khi nén nền thành công/lỗi, không làm phiền bằng popup chặn thao tác

**File/module liên quan:** file mới `services/watch_service.py`, `ui/settings_view.py`, `ui/main_window.py` (tray icon), `requirements.txt`

**Tiêu chí hoàn thành:** Thả 1 file vào thư mục theo dõi → sau vài giây tự sinh ra file ZIP tương ứng ở thư mục đích, có thông báo tray, app không cần mở cửa sổ chính.

---

## v2.8 — Tự cập nhật (Auto-update)

**Mục tiêu:** Người dùng luôn có bản mới nhất mà không cần tải thủ công từ GitHub.

**Việc cần làm:**
- [ ] Service mới `services/update_service.py`: gọi GitHub Releases API, so sánh `__version__` hiện tại với tag mới nhất
- [ ] Kiểm tra khi khởi động (bất đồng bộ, không chặn UI), tần suất tối đa 1 lần/ngày (cache kết quả)
- [ ] Có bản mới → hiện Toast "Đã có VietZIP vX.Y — Cập nhật ngay" với nút mở trang tải hoặc tự tải + chạy installer
- [ ] `SettingsWindow`: thêm toggle "Tự động kiểm tra cập nhật" + nút "Kiểm tra ngay"

**File/module liên quan:** file mới `services/update_service.py`, `ui/main_window.py`, `ui/settings_view.py`

**Tiêu chí hoàn thành:** Giả lập phiên bản cũ hơn → app phát hiện đúng bản mới trên GitHub, hiển thị toast, không tự ý tải/cài khi chưa xác nhận.

---

## v2.9 — Command Palette (Ctrl+K)

**Mục tiêu:** Thao tác nhanh bằng bàn phím cho người dùng thành thạo, giảm phụ thuộc vào chuột.

**Việc cần làm:**
- [ ] Component mới `ui/components/command_palette.py`: overlay dạng ô tìm kiếm + danh sách lệnh khớp (fuzzy match đơn giản)
- [ ] Đăng ký danh sách lệnh: chuyển chế độ Nén/Giải nén, mở Lịch sử/Cài đặt, đổi theme, mở gần đây, v.v. (tái dùng các callback đã có trong `MainWindow`)
- [ ] Phím tắt toàn cục `Ctrl+K` mở palette, `Esc` đóng, mũi tên lên/xuống để chọn, `Enter` thực thi

**File/module liên quan:** file mới `ui/components/command_palette.py`, `ui/main_window.py`

**Tiêu chí hoàn thành:** `Ctrl+K` → gõ "cài đặt" → `Enter` → mở đúng `SettingsWindow`; gõ "tối" → thực thi đổi theme sang Dark.

---

## v2.10 — Bộ test UI tự động hóa (headless)

**Mục tiêu:** Đóng gói lại quy trình kiểm thử thủ công qua Xvfb (đã dùng khi rebuild UI) thành bộ test chạy được trong CI, tự phát hiện hồi quy như 2 lỗi đã tìm thấy ở bản rebuild trước.

**Việc cần làm:**
- [ ] Thêm `pytest-xvfb` hoặc script wrapper `xvfb-run` vào pipeline CI (`.github/workflows/`)
- [ ] Viết `tests/ui/` — dựng `MainWindow` thật, giả lập luồng: thêm file → nén → kiểm tra kết quả; load ZIP → giải nén sai/đúng mật khẩu; hủy giữa chừng
- [ ] Chụp ảnh màn hình tự động ở vài bước mốc, lưu làm artifact CI để review bằng mắt khi cần (không assert trên ảnh, chỉ tham khảo)
- [ ] Assert trên **trạng thái thật** (file tồn tại, nội dung đúng, `_stage` đúng) — không assert trên pixel

**File/module liên quan:** thư mục mới `tests/ui/`, `.github/workflows/`

**Tiêu chí hoàn thành:** CI tự chạy được toàn bộ luồng chính mỗi lần push, fail rõ ràng nếu ai đó vô tình phá vỡ luồng nén/giải nén.

---

## v2.11 — Trợ năng (Accessibility)

**Mục tiêu:** Hỗ trợ nhóm người dùng cần đọc màn hình / cỡ chữ lớn / tương phản cao — thường bị bỏ quên nhưng làm tăng số người dùng tiếp cận được.

**Việc cần làm:**
- [ ] Rà tất cả `IconButton` (hiện đã có tooltip) — đảm bảo tooltip cũng đọc được qua Windows Narrator (kiểm tra `automation name` của widget Tk, có thể cần set qua `wm_attributes` hoặc thư viện hỗ trợ)
- [ ] `SettingsWindow` → thêm trang "Trợ năng": cỡ chữ (Nhỏ/Vừa/Lớn — nhân hệ số vào toàn bộ `FONT_*` trong `theme.py`), chế độ tương phản cao (bảng màu thay thế trong `theme.py`)
- [ ] Đảm bảo mọi thao tác chính đều làm được bằng bàn phím thuần túy (đã có nền tảng từ `AppButton` focus ring + Tab trong bản rebuild, cần rà lại toàn bộ luồng)
- [ ] Test bằng Windows Narrator thật trên ít nhất luồng Nén/Giải nén cơ bản

**File/module liên quan:** `ui/theme.py` (thêm bộ màu tương phản cao + hệ số cỡ chữ), `ui/settings_view.py`

**Tiêu chí hoàn thành:** Bật "Cỡ chữ lớn" → toàn bộ UI scale theo, không vỡ layout; điều hướng được toàn bộ luồng nén cơ bản chỉ bằng Tab/Enter/phím mũi tên.

---

## Ghi chú thứ tự

Nếu chỉ chọn 3 version đầu tiên để làm trước, đề xuất: **v2.1 → v2.3 (RAR/7z) → v2.2**,
vì v2.3 mang lại giá trị thực tế lớn nhất cho người dùng cuối, còn v2.2 (đa ngôn ngữ) không
gấp bằng nếu đối tượng dùng chủ yếu vẫn là người Việt.

Các version từ v2.7 trở đi (Watch folder, Auto-update, Command Palette, Test CI, Accessibility)
đòi hỏi thêm dependency hoặc hạ tầng mới (tray icon, GitHub API, CI pipeline) — nên làm sau khi
nhóm tính năng lõi (v2.1–v2.6) đã ổn định.
