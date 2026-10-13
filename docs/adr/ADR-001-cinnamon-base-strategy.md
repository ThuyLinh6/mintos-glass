# ADR-001 · Nền tảng cho Cinnamon theme: fork upstream sass hay overlay `@import`?

- Trạng thái: **PROVISIONAL — chọn A, chờ spike T03 xác minh phương án B**
- Ngày: 2026-10-13
- Liên quan: `docs/plan/02-architecture.md` §ADR-001, `docs/plan/04-work-breakdown.md` T03/T04, rủi ro R1

## Bối cảnh

Đã xác minh từ mã nguồn Cinnamon `6.6.9`:

1. `js/ui/main.js → loadTheme()`:
   ```js
   _defaultCssStylesheet = global.datadir + '/theme/cinnamon.css';
   ...
   let theme = new St.Theme ({ fallback_stylesheet: _defaultCssStylesheet });
   if (_cssStylesheet != null) { stylesheetLoaded = theme.load_stylesheet(_cssStylesheet); }
   if (!stylesheetLoaded) { theme.load_stylesheet(_defaultCssStylesheet); ... }
   ```
2. `src/st/st-theme.c`, doc comment của `PROP_FALLBACK_STYLESHEET`:
   > *"Fallback stylesheet - non-cascading. It is applied only if the user-selected stylesheets
   > fail to return any properties, and the StWidget has its `important` property set."*

**Hệ quả:** stylesheet mặc định của Cinnamon **không** đóng vai trò lớp nền để kế thừa.
Một selector mà theme của ta không định nghĩa sẽ **không có style nào cả** (trừ widget có cờ `important`).
Vì vậy theme Cinnamon bắt buộc phải **hoàn chỉnh** — đây là rủi ro R1, mức "Chết".

3. Theme mặc định của Cinnamon 6.6 được build từ SCSS modular:
   `data/theme/cinnamon-sass/{cinnamon.scss,_colors.scss,_drawing.scss,_common.scss,_widgets.scss,widgets/*.scss}`
   (17 partial trong `widgets/`, tổng 2385 dòng), biên dịch bằng `pysassc`/`sassc` (libsass)
   theo `data/theme/cinnamon-sass/meson.build`.

4. `src/st/st-theme.c:892-936` **có** xử lý `AT_IMPORT_RULE_STMT`, resolve qua `_st_theme_resolve_url()`.
   Nghĩa là về nguyên tắc theme có thể `@import` một file CSS khác lúc runtime.

## Các phương án

### A. Fork `data/theme/cinnamon-sass` @6.6.9 vào `src/cinnamon/vendor/`, reskin bằng tầng `overrides/`

Ưu:
- Bảo đảm đủ selector cho Cinnamon 6.6, kể cả phần **mới** của 6.6 mà theme cũ không có:
  app menu redesign (`.appmenu`, `#appmenu-search-entry`, sidebar/user/favorites),
  applet `favorites@` và `nightlight@`, screensaver, on-screen keyboard mới.
- Không phụ thuộc file trên máy người dùng → hành vi giống nhau trên mọi máy.
- Re-base được: khi Mint cập nhật Cinnamon, diff vendor cũ ↔ vendor mới cho biết chính xác selector nào thêm/bớt.
- Cho phép CI kiểm tra **coverage 100%** selector (`test_cinnamon_coverage.py`, tiêu chí V4).

Nhược:
- Đưa ~2400 dòng mã GPL-2.0-or-later vào repo → nghĩa vụ giấy phép (ADR-007).
- Phải quản lý 2 tầng (vendor + overrides), và kỷ luật "không sửa tay vendor".

### B. Overlay mỏng: `@import url("/usr/share/cinnamon/theme/cinnamon.css")` rồi ghi đè

Ưu:
- Code rất nhỏ (vài trăm dòng).
- Tự bám theo bản Cinnamon đang cài → không lệch khi Mint cập nhật.
- Không vendor mã GPL → nghĩa vụ giấy phép nhẹ hơn (vẫn nên ghi công).

Nhược / chưa xác minh:
- **Chưa xác minh** `_st_theme_resolve_url()` có chấp nhận đường dẫn tuyệt đối
  `/usr/share/cinnamon/theme/cinnamon.css` hay chỉ resolve tương đối so với file đang import.
- **Chưa xác minh** thứ tự cascade: rule sau `@import` có thực sự thắng rule trong file được import không.
- Nếu import fail (đường dẫn đổi, file bị thay), theme **trống hoàn toàn** → desktop gần như không dùng được.
- Không kiểm soát được phiên bản: máy A và máy B có thể render khác nhau.
- Không có fixture ổn định cho CI coverage.

## Quyết định

**Chọn A làm mặc định.** Chạy spike T03 (≤ 2 ngày, cần máy thật) để đo B.
Nếu B được xác minh hoạt động **và** cho kết quả ổn định, có thể chuyển sang mô hình lai:
B làm lớp nền + A làm dự phòng (ship cả `cinnamon.css` tự chứa).

## Điều kiện để lật quyết định sang B

Tất cả phải đúng, có bằng chứng từ máy thật:
1. `@import url("/usr/share/cinnamon/theme/cinnamon.css")` nạp được (không có warning trong journal).
2. Rule ghi đè **sau** `@import` thắng rule trong file được import, với cùng độ đặc hiệu selector.
3. Asset tương đối của theme mặc định vẫn resolve đúng (checkbox/radio/calendar-arrow SVG).
4. Kết quả giống nhau trên 2 lần logout/login liên tiếp.

Nếu thiếu bất kỳ mục nào → giữ A, và ghi kết quả vào ADR này.

## Việc phải làm trước khi thực thi A

- Thêm `LICENSE` (GPL-3.0-or-later) — xem ADR-007. **Chặn**: không có LICENSE thì không vendor.
- Tạo `src/cinnamon/vendor/cinnamon-6.6-sass/VENDOR.md` ghi: repo, ref `6.6.9`, commit SHA đầy đủ,
  license từng phần (Cinnamon GPL-2.0+, `src/st` LGPL-2.1+), ngày lấy, khẳng định không sửa tay.
- Tạo fixture `tests/fixtures/cinnamon-6.6-selectors.txt` từ chính bản vendor (không lấy từ trí nhớ).
