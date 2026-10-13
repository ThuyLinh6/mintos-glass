# 07 — Tiêu chí nghiệm thu

Bốn nhóm: **Giao diện · Chức năng · Hiệu năng · Rollback**.
Mỗi tiêu chí có: cách kiểm chứng, bằng chứng bắt buộc, và trạng thái hiện tại.

Ký hiệu trạng thái: `[T1]` = kiểm chứng được offline trong CI · `[T2]` = bắt buộc trên máy thật ·
`[T1+T2]` = cả hai.

> Hiện tại **chưa có tiêu chí nào đạt** — repo chưa có mã. Bảng này là định nghĩa "Done", không phải báo cáo.

## 1. Giao diện (Visual)

| ID | Tiêu chí | Kiểm chứng | Bằng chứng |
|---|---|---|---|
| V1 | Theme xuất hiện trong Cinnamon Settings ở **cả 3** mục: Themes, GTK, Cinnamon | `[T2]` | ảnh `cinnamon-settings themes` |
| V2 | `dist/MintOS-Glass/` có `gtk-3.0/gtk.css` (điều kiện để hiện trong picker, E19) | `[T1]` | CI |
| V3 | **Không có widget nào không được style** (nền đen/trắng thô, chữ mất) trong 26 bối cảnh của screenshot matrix | `[T1+T2]` | coverage test + 26 ảnh |
| V4 | Mọi selector của Cinnamon 6.6 stock theme đều có mặt trong output (E6) | `[T1]` | `test_cinnamon_coverage.py` |
| V5 | 0 property St không hợp lệ trong `cinnamon.css` | `[T1]` | `st_properties.py` |
| V6 | Đúng token: không giá trị màu/bán kính hard-code ngoài `design/tokens/` | `[T1]` | grep + `tokens-drift` |
| V7 | Contrast: text × surface ≥ **4.5:1** (body), ≥ **3:1** (large text & UI component) | `[T1]` tính toán + `[T2]` đo trên ảnh | `contrast.py` + ảnh |
| V8 | Đủ 4 trạng thái cho mọi control tương tác: normal / hover / active / focus, cộng `:insensitive` và `:backdrop` | `[T1+T2]` | selector list + ảnh |
| V9 | Dark và light (nếu D-2 = cả hai) nhất quán: cùng radius, cùng spacing, cùng hierarchy; chỉ khác màu | `[T1+T2]` | diff cấu trúc + ảnh ghép |
| V10 | Icon desktop Nemo đọc được trên wallpaper **sáng** và **tối** | `[T2]` | 2 ảnh + đo contrast |
| V11 | Titlebar SSD (muffin) và CSD (GTK) **cùng ngôn ngữ**: cùng chiều cao, cùng vị trí nút, cùng bán kính | `[T2]` | ảnh cạnh nhau |
| V12 | Nút cửa sổ theo quy ước macOS khi bật `ButtonLayout` tương ứng; **không** tự đổi layout của người dùng | `[T1+T2]` | `index.theme` + ảnh |
| V13 | Asset sắc ở scale 1.0 / 1.25 / 2.0 | `[T2]` | 3 ảnh cùng widget |
| V14 | Không dùng `-blur` trong biến thể chuẩn; biến thể `-Blur` chỉ dùng `-blur ≤ 6` và không dùng cho panel full-width | `[T1]` | grep output |
| V15 | Theme vẫn **đẹp và dùng được** khi GLSL không khả dụng (E12 — blur bị bỏ qua) | `[T2]` | ảnh với biến thể Blur trên máy không có GLSL, hoặc mô phỏng |

## 2. Chức năng (Functional — "giữ nguyên chức năng hệ thống")

| ID | Tiêu chí | Kiểm chứng | Bằng chứng |
|---|---|---|---|
| F1 | **0 thay đổi hành vi.** Theme chỉ là CSS + asset; không patch Cinnamon, không sửa applet, không đổi schema, không đổi keybinding | `[T1]` | diff `dist/` chỉ chứa CSS/SVG/PNG/INI/theme |
| F2 | Không ghi gì ngoài `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/` | `[T1]` | `safety-paths` + `test_paths_hardcoded.py` |
| F3 | Không cần root, không `apt`/`dpkg`, không tải gì | `[T1]` | grep tooling |
| F4 | Toàn bộ 20 thao tác trong PROTOCOL §2.4 hoạt động **y hệt** trước và sau khi cài | `[T2]` | checklist có tick + ảnh khi có khác biệt |
| F5 | 33 applet bundled (E14) hiển thị đúng, kể cả 2 applet mới của 6.6: `favorites@`, `nightlight@` | `[T1+T2]` | coverage + ảnh panel đầy applet |
| F6 | App menu mới của Cinnamon 6.6 (sidebar avatar/places/favorites, search) đủ style | `[T2]` | 3 ảnh (mở, hover, search) |
| F7 | Nemo: icon view, list view, compact view, F3 dual-pane, rename, floating bar, places sidebar + disk-full bar, desktop icons — tất cả đúng | `[T1+T2]` | `nemo_selectors.py` + 6 ảnh |
| F8 | Không ghi đè `-NemoIconContainer-activate-prelight-icon-label` (giữ hành vi gốc) | `[T1]` | grep |
| F9 | Khoá màn hình / screensaver: mở được, nhập được mật khẩu, **unlock thành công** | `[T2]` | ảnh + ghi chú |
| F10 | On-screen keyboard và IBus popup dùng được | `[T2]` | 2 ảnh |
| F11 | App GTK4/libadwaita nhận theme (`libadwaita-1.5/`) **hoặc** ghi nhận rõ là không nhận + lý do (E25) | `[T2]` | log `ADW_DEBUG_THEMES=1` |
| F12 | `base-hc.css` tồn tại và high-contrast mode không làm theme bị bỏ qua | `[T1+T2]` | `test_libadwaita_files.py` + ảnh |
| F13 | Đổi theme sang Mint-Y rồi đổi lại MintOS-Glass hoạt động, không cần logout | `[T2]` | ghi log |
| F14 | Không phá `cinnamon-settings`, `mintupdate`, `mintinstall`, `xed`, `xplayer`, `xreader`, `xviewer`, `pix` | `[T2]` | 8 ảnh |
| F15 | `text-scaling-factor` 1.25 và fractional scaling không làm vỡ layout | `[T2]` | 2 ảnh |
| F16 | Cả X11 và Wayland (nếu máy hỗ trợ) đều dùng được; nếu chỉ test 1 → ghi rõ phạm vi | `[T2]` | `loginctl show-session` output |

## 3. Hiệu năng (Performance)

| ID | Tiêu chí | Kiểm chứng | Bằng chứng |
|---|---|---|---|
| P1 | Không có lỗi/warning parse CSS trong log (`Did not find color property`, `Unrecognized`, `There was some problem parsing the theme`) | `[T2]` | `journalctl` output |
| P2 | CPU% của `cinnamon` khi nghỉ ≤ baseline Mint-Y **+ 2 điểm %** (trung vị 3 lần đo, 10s mỗi lần) | `[T2]` | `pidstat` output, cả baseline |
| P3 | Thời gian mở menu ≤ baseline **+ 33 ms** (trung vị 10 lần) | `[T2]` | video đếm frame hoặc log |
| P4 | Không stutter khi kéo/thả cửa sổ, khi mở Expo/Scale | `[T2]` | ghi nhận + video nếu có |
| P5 | Biến thể `-Blur` (`-blur: 4`, menu/OSD): CPU% tăng ≤ **8 điểm %** so với biến thể không blur, không stutter | `[T2]` | số đo A/B |
| P6 | Kích thước file: `cinnamon.css` ≤ 400 KB; `gtk.css` ≤ 500 KB; tổng `dist/` ≤ 8 MB (không blur assets thừa) | `[T1]` | CI size gate |
| P7 | Thời gian build theme (từ `src/` → `dist/`) ≤ 60s trên máy dev | `[T1]` | log |
| P8 | **Không** dùng `-blur` trên bề mặt > 600×400 px; generator từ chối token vi phạm | `[T1]` | `tools/tokens/generate.py` clamp test |
| P9 | Ghi lại cơ sở lý thuyết chi phí blur (E11) trong báo cáo perf, kèm phép tính cho cấu hình máy thật | `[T2]` | `docs/testing/perf-benchmark.md` |

## 4. Khả năng rollback

| ID | Tiêu chí | Kiểm chứng | Bằng chứng |
|---|---|---|---|
| R1 | `rollback` khôi phục **chính xác** toàn bộ khoá đã đổi: `gsettings list-recursively` diff rỗng và `dconf dump /org/cinnamon/` diff rỗng | `[T2]` | 2 file diff rỗng, dán vào report |
| R2 | Sau rollback, không còn dấu vết: `~/.local/share/themes/MintOS-Glass*` đã xoá | `[T2]` | `ls` output |
| R3 | `rollback` **idempotent** — chạy lần 2 không lỗi, không đổi gì thêm | `[T1+T2]` | test + log |
| R4 | `--dry-run` có cho mọi lệnh ghi, và không tạo bất kỳ thay đổi nào | `[T1+T2]` | test + log |
| R5 | Snapshot được tạo **trước** khi đổi khoá, có timestamp, lưu ở `~/.local/state/mintos-glass/`, và **không** bị ghi đè bởi lần cài sau | `[T1+T2]` | test + `ls -l` |
| R6 | Chỉ chạm danh sách khoá **đóng** (5–6 khoá, xem `04-work-breakdown.md` T12 ràng buộc 4) | `[T1]` | test liệt kê key được phép |
| R7 | Cấp 2 (rollback thủ công không cần CLI của ta) được tài liệu hoá và **đã thử** | `[T2]` | log thử |
| R8 | Cài theme **không** làm mất theme cũ: không ghi đè, không đổi tên, không xoá bất kỳ theme nào có sẵn | `[T1+T2]` | `ls /usr/share/themes` trước/sau |
| R9 | Nếu CLI crash giữa chừng, hệ thống vẫn trở về được bằng Cấp 2 | `[T2]` | drill có chủ đích |
| R10 | Toàn bộ thao tác rollback ≤ **60 giây** kể từ lúc người dùng quyết định | `[T2]` | đo thời gian |

## 5. Tiêu chí chặn release (gate)

| Gate | Điều kiện |
|---|---|
| **G0 → v0.1.0** | V1–V8, V14; F1–F5; P1, P6, P7; R2, R8 |
| **G1 → v0.2.0** | thêm V9–V13; F7, F9, F13, F14; P2–P4; R1, R3–R6, R10 |
| **G2 → v0.3.0** | thêm F11, F12 |
| **G3 → v0.5.0** | thêm P5, P8, P9, V15 |
| **G4 → v1.0.0** | tất cả V/F/P/R, F15, F16, R7, R9 |

**Blocker tự động:** bất kỳ mục nào của F1, F2, F3, F4, F9, R1 vi phạm → dừng toàn bộ release, rollback, mở incident.

## 6. Bằng chứng tối thiểu cho một bản release

1. `docs/verification/REPORT-<ngày>.md` — điền đủ 8 mục của `09-verification-checklist.md`.
2. `docs/testing/results/<ngày>/` — ảnh của 26 bối cảnh × số variant đã phát hành.
3. `docs/testing/perf-benchmark.md` — số đo P2, P3, P5 kèm baseline.
4. Log rollback drill R1–R3, R7.
5. Link CI run xanh của commit được tag.
6. `NOTICE.md` cập nhật vendor SHA nếu có vendor mới.
