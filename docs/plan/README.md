# MintOS Glass — Kế hoạch kỹ thuật (Giai đoạn 0: Khảo sát & Lập kế hoạch)

Trạng thái: **DRAFT — chờ xác nhận phạm vi**
Ngày lập: 2026-10-13
Nhánh: `arena/0b177d6e-mintos-glass` (từ `main` @ `d010363`)
Mục tiêu hệ thống: Linux Mint 22.3 "Zena" · Cinnamon 6.6 · **chỉ cải tiến UI, không thay đổi chức năng hệ thống**

> Trong giai đoạn này **không có** mã theme, không có script cài đặt, không có module giả.
> Toàn bộ nội dung dưới đây là khảo sát + thiết kế + quy trình.

## Mục lục

| # | Tài liệu | Nội dung |
|---|----------|----------|
| 01 | [`01-survey.md`](01-survey.md) | Kết quả khảo sát repo + **bảng bằng chứng upstream** (37 mục, kèm đường dẫn file/dòng) |
| 02 | [`02-architecture.md`](02-architecture.md) | Kiến trúc dự án + cấu trúc thư mục đề xuất + các quyết định kiến trúc (ADR) |
| 03 | [`03-design-system.md`](03-design-system.md) | Design system dùng chung: token 3 tầng, generator, ràng buộc từng nền tảng |
| 04 | [`04-work-breakdown.md`](04-work-breakdown.md) | 15 nhiệm vụ, thứ tự phụ thuộc, phân công agent, **danh sách file được phép sửa** |
| 05 | [`05-testing-strategy.md`](05-testing-strategy.md) | Chiến lược kiểm thử: CI offline chạy được thật + protocol trên máy người dùng |
| 06 | [`06-git-workflow.md`](06-git-workflow.md) | Branch, review, tích hợp, CODEOWNERS, enforcement allow-list |
| 07 | [`07-acceptance-criteria.md`](07-acceptance-criteria.md) | Tiêu chí nghiệm thu: giao diện / chức năng / hiệu năng / rollback |
| 08 | [`08-risks.md`](08-risks.md) | 16 rủi ro, mức độ, mitigation, owner, điều kiện chặn |
| 09 | [`09-verification-checklist.md`](09-verification-checklist.md) | **Những gì phải xác minh trên máy thật** — lệnh copy-paste, chỉ đọc |

## Ba phát hiện làm thay đổi kiến trúc (đã xác minh từ mã nguồn upstream)

1. **Theme Cinnamon của bên thứ ba bắt buộc phải HOÀN CHỈNH.**
   Cinnamon nạp stylesheet mặc định (`/usr/share/cinnamon/theme/cinnamon.css`) chỉ ở vai trò
   `fallback_stylesheet`, mà theo `src/st/st-theme.c` thì fallback này **non-cascading** — chỉ áp dụng
   khi stylesheet của người dùng không trả về property nào **và** widget có cờ `important`.
   → Không thể viết theme "chỉ ghi đè vài chỗ". Phải fork toàn bộ `cinnamon-sass` của Cinnamon 6.6.

2. **Cinnamon 6.6 có backdrop blur THẬT (`-blur`) nhưng chi phí rất cao.**
   `-blur: N` chạy `N` vòng lặp, mỗi vòng `g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()` (đọc ngược GPU→CPU)
   + `cogl_texture_new_from_data()` (tải lại CPU→GPU), **mỗi lần paint**.
   → Mặc định TẮT blur. "Glass" đạt được bằng rgba + gradient + border + shadow. Blur thật chỉ ở biến thể opt-in, giá trị nhỏ, diện tích nhỏ.

3. **Muffin 6.6 KHÔNG đọc `metacity-1/metacity-theme-3.xml`.**
   `MetaTheme` trong muffin 6.6.3 chỉ là struct opaque rỗng, không có parser XML, không build-depend `libmetacity`.
   Khung cửa sổ được vẽ bằng **GTK3 CSS** qua `gtk_css_provider_get_named()` với widget path
   `window.background.ssd > decoration > headerbar.titlebar.horizontal.default-decoration > label.title`.
   → Module WM = một phần của module GTK3, không phải module metacity riêng.

## Quyết định cần người dùng xác nhận trước khi triển khai

Xem cuối tài liệu này và `02-architecture.md` §ADR. Bốn câu hỏi quyết định:

- **D-1 Dock**: dùng applet `grouped-window-list` có sẵn (0 gói mới) hay hỗ trợ Plank (nếu máy đã có sẵn)?
- **D-2 Phạm vi biến thể**: Dark-only / Light-only / cả hai?
- **D-3 Accent**: xanh macOS, xanh Mint, hay trung tính?
- **D-4 Vị trí cài**: `~/.local/share/themes/` (không cần root, rollback tức thì — **khuyến nghị**) hay `/usr/share/themes/`?

## Nguyên tắc bất biến (áp dụng cho mọi nhiệm vụ)

1. Không ghi bất cứ thứ gì ngoài `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`.
2. Không `sudo`, không `apt`/`dpkg`, không sửa file trong `/usr`, `/etc`.
3. Mọi khoá gsettings/dconf bị thay đổi đều phải được snapshot trước và khôi phục được bằng 1 lệnh.
4. Không tuyên bố "đã kiểm thử" nếu không có output thật đính kèm.
5. Không giả định phiên bản/cấu trúc — nếu chưa xác minh thì ghi vào `09-verification-checklist.md`.
