# 08 — Rủi ro kỹ thuật và mitigation

Thang điểm: **Xác suất** (Thấp / Trung bình / Cao) × **Tác động** (Nhẹ / Nặng / Chết).
"Chặn" = rủi ro phải được giải quyết **trước khi** bắt đầu triển khai module liên quan.

| ID | Rủi ro | Xác suất | Tác động | Mitigation | Owner | Chặn task |
|---|---|---|---|---|---|---|
| **R1** | **Theme Cinnamon không hoàn chỉnh** → widget hiển thị không style (nền đen/trắng). Nguyên nhân đã xác minh: fallback stylesheet là *non-cascading*, chỉ áp dụng khi user stylesheet không trả về property nào **và** widget có cờ `important` (E6) | Cao nếu viết từ đầu | Chết | ADR-001 phương án A: fork `data/theme/cinnamon-sass` @6.6.9 làm nền. Thêm CI gate `test_cinnamon_coverage.py` đối chiếu 100% selector upstream (V4) | T04 | T04 |
| **R2** | **`-blur` làm sập hiệu năng.** Đã xác minh cơ chế: `for (i=0; i<blur_size; i++)` mỗi vòng `g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()` + `cogl_texture_new_from_data()`, **mỗi lần paint** (E11). Panel 1920×40 với `-blur: 20` ≈ 6 MB GPU→CPU→GPU mỗi frame | Cao | Nặng | Mặc định TẮT blur (A6). Generator clamp `blur ≤ 6` và cấm blur trên bề mặt lớn (P8). Blur chỉ ở biến thể opt-in, phải qua benchmark P5. Ghi cơ sở lý thuyết vào báo cáo | T02, T04 | T04 (biến thể Blur) |
| **R3** | **Blur không chạy** vì thiếu `CLUTTER_FEATURE_SHADERS_GLSL` (E12) — St chỉ in `g_message` rồi bỏ qua, theme trông "sai" mà không có lỗi rõ ràng | Trung bình | Nhẹ | Theme phải đẹp khi blur bị bỏ qua (V15). Detect GLSL trong `tools/cli detect` và cảnh báo người dùng trước khi cho bật biến thể Blur | T12 | — |
| **R4** | **App GTK4/libadwaita không nhận theme.** Đã xác minh: Cinnamon ghi `org.cinnamon.desktop.interface gtk-theme` (E20) nhưng libadwaita đọc từ portal hoặc `org.gnome.desktop.interface gtk-theme` (E24), và legacy impl không cung cấp theme name | Trung bình | Nặng | T00 mục 5: chạy `ADW_DEBUG_THEMES=1` để xác định nguồn thật. Nếu lệch → ADR-003: installer đặt thêm `org.gnome.desktop.interface gtk-theme` (nằm trong danh sách khoá đóng, có snapshot, rollback được) | T10, T12 | T10 |
| **R5** | **Sai tên thư mục libadwaita.** Mã Mint hiện tại suy ra `libadwaita-<MAJOR>.<MINOR>` → `libadwaita-1.5` (E21), nhưng bản cũ hơn hard-code `libadwaita-1.0`; `mint-themes` upstream có cả `-1.5/-1.7/-1.9` | Trung bình | Nặng | Không hard-code. `tools/build/libadwaita_dirname.py` đọc phiên bản libadwaita thực tế trên máy và sinh đúng tên; hỗ trợ cả 1.0/1.5/1.7/1.9 | T10 | T10 |
| **R6** | **libsass vs dart-sass lệch nhau.** Mint build bằng `pysassc` (libsass, đã deprecated) (E4, E18). Cú pháp dart-only (`@use`, `math.div`, `sass:color`) sẽ build được ở dev nhưng vỡ ở Mint | Cao | Nặng | ADR-004: giới hạn cú pháp ở giao của hai compiler; CI build bằng **cả hai** và fail khi lệch | T01, T04, T06 | T04, T06 |
| **R7** | **Nghĩa vụ giấy phép.** Vendor SCSS của Cinnamon là tác phẩm dẫn xuất GPL-2.0-or-later (`st` là LGPL-2.1+) (E15); mint-themes là GPL-3+ (E16). Phát hành mà không có LICENSE/NOTICE = vi phạm | Cao nếu bỏ qua | Chết (pháp lý) | Repo = GPL-3.0-or-later (tương thích upward với GPL-2+). `NOTICE.md` ghi nguồn + commit SHA. **Không** trộn mã mint-themes và Cinnamon trong cùng file. ADR-007 + 2 approval khi sửa `vendor/` | T01 | T04 |
| **R8** | **Trôi phiên bản (version drift).** Cinnamon 6.6.x ra bản vá (đã có tới 6.6.9) và Mint có thể cập nhật → selector mới xuất hiện, theme ta thiếu | Cao (theo thời gian) | Nặng | `VENDOR.md` pin SHA. Task định kỳ "re-base vendor" mỗi khi Mint cập nhật Cinnamon. CI coverage so với file fixture — khi fixture được cập nhật từ upstream mới, gap lộ ra ngay | T04 | — |
| **R9** | **Không có môi trường test trong sandbox** (không có `cinnamon`, `nemo`, `gsettings`, `sass`, `xvfb`) → mọi khẳng định thị giác đều là suy đoán | Chắc chắn | Nặng | Tách 2 tầng kiểm thử (05 §1, §2). Cấm tuyên bố đã test (05 §5). Mọi PR đổi output thị giác phải kèm ảnh từ máy thật | T13 | toàn bộ |
| **R10** | **Xung đột giữa nhiều agent** trên file dùng chung (`cinnamon.scss`, `gtk.scss`, `_tokens.scss`) | Cao | Nặng | Một file một owner; allow-list enforce bằng CI job #1; file tổng hợp chỉ owner core được sửa; task khác muốn thêm partial phải mở issue | T01 | T01 |
| **R11** | **Làm hỏng hệ thống người dùng** (ghi nhầm vào `/usr`, đổi khoá dconf không khôi phục được, xoá theme cũ) | Thấp nếu tuân thủ | Chết | Ràng buộc cứng của T12: 2 đường dẫn duy nhất, danh sách khoá đóng, snapshot trước khi đổi, `--dry-run`, `selftest`, `safety-paths` CI, rollback Cấp 2 không phụ thuộc code của ta | T12 | T12 |
| **R12** | **Nemo vỡ màu** vì theme thiếu `@theme_*`. Đã xác minh `nemo-style-fallback-mandatory.css` dùng `@theme_bg_color`, `@theme_selected_bg_color`, `@theme_unfocused_bg_color` (E29) | Cao nếu quên | Nặng | `gtk_colors.py` bắt buộc đủ bộ E33 + 5 khoá `@theme_*` của Nemo; CI gate #6 | T06 | T06 |
| **R13** | **Titlebar sai kích thước.** muffin lấy `get_min_size()`/`get_padding_and_border()` từ CSS (E32b) → padding của ta thành chiều cao thật; đoán sai sẽ lệch với CSD | Trung bình | Nhẹ | T08 bắt buộc **đo** chiều cao thật trên máy và ghi vào `docs/testing/wm-metrics.md`, không dùng giá trị đoán | T08 | T08 |
| **R14** | **HiDPI / fractional scaling làm asset mờ hoặc layout vỡ** | Trung bình | Nhẹ | SVG-first (ADR-05) để scale miễn phí; test matrix scale 1.0/1.25/2.0 (V13, F15) | T05, T07 | — |
| **R15** | **Wayland khác X11.** Cinnamon 6.6 cải thiện Wayland; hiệu ứng St/offscreen có thể hành xử khác | Trung bình | Trung bình | T00 ghi `XDG_SESSION_TYPE`; PROTOCOL yêu cầu test cả hai nếu máy hỗ trợ; nếu chỉ test 1 thì ghi rõ phạm vi chưa test (F16) | T00, T13 | — |
| **R16** | **Phạm vi phình to** (icon theme, cursor theme, font, GTK2, greeter, applet tuỳ chỉnh) → không bao giờ xong | Cao | Nặng | A9: không icon theme ở Phase 1. GTK2 = Phase 2, ưu tiên thấp. Không viết applet/desklet riêng. Ghi rõ "out of scope" trong README | T14, lead | — |

## Rủi ro đã bị LOẠI TRỪ nhờ khảo sát (không cần mitigation)

| Từng lo ngại | Kết luận xác minh |
|---|---|
| "Phải viết `metacity-1/metacity-theme-3.xml` cho khung cửa sổ" | **Không cần.** muffin 6.6.3 chỉ còn `MetaTheme` stub, không parser XML, không build-depend libmetacity (E31). Khung cửa sổ đi qua GTK3 CSS (E32) |
| "Cinnamon không có backdrop blur, phải giả lập" | **Sai.** Có `-blur` và `-bumpmap` thật (E8, E9) — nhưng chi phí cao (E11) nên mặc định vẫn không dùng |
| "GTK4/libadwaita không thể theme trên Mint" | **Sai.** Mint patch libadwaita và đọc `<theme>/libadwaita-1.5/` (E21, E22). Chỉ cần thận trọng theo E23 |
| "Cinnamon theme có thể kế thừa theme mặc định" | **Chỉ một phần.** Default là `fallback_stylesheet` non-cascading (E6) → không kế thừa được theo nghĩa thông thường |
| "Theme GTK4-only cũng được" | **Sai.** Picker của Cinnamon yêu cầu `gtk-3.*/gtk.css` (E19) |

## Ba việc phải làm TRƯỚC khi viết bất kỳ dòng CSS nào

1. **T00** — lấy 8 mục thông tin từ máy thật (`09-verification-checklist.md`). Không có nó, R4/R5/R13/R15 đều là ẩn số.
2. **T02** — chốt design tokens. Mọi module đều phụ thuộc; làm sau sẽ phải sửa lại 5 lần.
3. **ADR-001 + ADR-007** — chốt chiến lược nền Cinnamon (R1) và giấy phép (R7). Sai ở đây thì toàn bộ T04 phải làm lại.
