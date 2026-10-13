# 05 — Chiến lược kiểm thử

Nguyên tắc chỉ đạo: **không có môi trường Linux Mint trong sandbox của agent**, nên kiểm thử chia làm
2 tầng rõ ràng. Không được trộn lẫn kết quả của hai tầng này, và không bao giờ trình bày kết quả
tầng 2 như thể agent đã tự chạy.

```
TẦNG 1 — OFFLINE (CI, agent chạy được thật, bằng chứng = log CI)
         Kiểm tra tính ĐÚNG ĐẮN về cấu trúc: biên dịch, cú pháp, độ phủ selector,
         property hợp lệ, token nhất quán, contrast, allow-list, an toàn đường dẫn.

TẦNG 2 — ON-TARGET (người dùng chạy, bằng chứng = output/ảnh dán vào docs/verification)
         Kiểm tra tính ĐÚNG về THẨM MỸ + HÀNH VI + HIỆU NĂNG.
```

## 1. Tầng 1 — kiểm thử offline (chạy được trong CI)

### 1.1 Build
| Test | Lệnh | Fail khi |
|---|---|---|
| SCSS biên dịch (libsass) | `pysassc` / `sassc` | lỗi cú pháp, hàm không tồn tại |
| SCSS biên dịch (dart-sass) | `sass` (npm) | dùng cú pháp dart-only → phá build của Mint (E18) |
| Hai compiler cho output tương đương | so sánh sau khi chuẩn hoá | lệch ngữ nghĩa (ADR-004) |
| `dist/` không lệch `src/` | `generated_up_to_date.py` | quên build trước khi commit (A8) |
| Token không drift | regenerate + diff `tokens.lock.json` | sửa tay file generated |

### 1.2 Lint CSS — cổng quan trọng nhất
| Test | Nguồn chân lý | Bắt được lỗi gì |
|---|---|---|
| `st_properties.py` | `tests/fixtures/st-allowed-properties.txt` trích từ `src/st/st-theme-node.c` @6.6.9 | gõ nhầm `transition-timing-function`, `filter`, `var()`, `opacity` — những thứ St **âm thầm bỏ qua**, khiến UI vỡ mà không có log lỗi |
| `test_cinnamon_coverage.py` | `tests/fixtures/cinnamon-6.6-selectors.txt` trích từ `data/theme/cinnamon-sass/**` @6.6.9 | **thiếu selector** → widget không được style (E6: fallback non-cascading) |
| `css_sanity.py` | — | ngoặc lệch, `url()` trỏ file không tồn tại, `!important` tràn lan, rule rỗng, encoding |
| `gtk_colors.py` | E33 + E29 | thiếu `@define-color` public → app Mint/Nemo vỡ màu |
| `nemo_selectors.py` | E27–E30 | thiếu selector Nemo |
| `muffin_decorations.py` | E32 | thiếu `window.background.ssd` / `decoration` / `.default-decoration` |
| `plank_theme.py` | E35 | sai section, màu không phải `R;;G;;B;;A` số nguyên |
| `libadwaita_files.py` | E22 | thiếu `base-hc.css` → theme bị bỏ qua ở chế độ high-contrast |
| `assets.py` | — | SVG malformed, thiếu `viewBox`, thiếu bản scale |
| `contrast.py` | `50-a11y.json` | text × surface dưới 4.5:1 |
| `allowlist.py` | `task-allowlists.json` | agent sửa file ngoài phạm vi (yêu cầu #6 của đề bài) |
| `test_paths_hardcoded.py` | — | tooling chứa `/usr`, `sudo`, `apt`, `dpkg` (ràng buộc an toàn) |

### 1.3 Bank test "regression có chủ đích"
Mỗi bug thật tìm thấy ở Tầng 2 phải được **đóng băng thành 1 test ở Tầng 1** trước khi sửa.
Ví dụ: phát hiện thiếu `.grouped-window-list-item-demands-attention` → thêm selector đó vào
`tests/fixtures/cinnamon-6.6-selectors.txt` và viết test phủ.

### 1.4 Những gì CI **không** kiểm chứng được (phải nói rõ trong mọi PR)
- Theme có đẹp không, có đúng "chất macOS" không.
- `-blur` có chạy không, tốn bao nhiêu.
- Muffin có thực sự dùng selector `.ssd` trên bản đã cài không.
- libadwaita có thực sự tìm thấy `libadwaita-1.5/` không.
- Ảnh hưởng của Wayland, HiDPI, fractional scaling, multi-monitor.
- Bất kỳ hành vi runtime nào của Nemo/Cinnamon.

## 2. Tầng 2 — protocol kiểm thử trên máy thật

`tests/manual/PROTOCOL.md` (T13 tạo) gồm 6 phần, mỗi phần có: lệnh, kết quả kỳ vọng, ô dán output.

### 2.1 P1 · Cài đặt & nhận diện
```
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface gtk-theme
ls ~/.local/share/themes/
cinnamon-settings themes        # theme PHẢI hiện ở cả 3 mục: Themes / GTK / Cinnamon
```
**Fail nếu:** theme không hiện trong danh sách GTK → thiếu `gtk-3.0/gtk.css` (E19).

### 2.2 P2 · Log lỗi CSS (bắt buộc chạy trước mọi đánh giá thẩm mỹ)
```
journalctl --user -b | grep -iE 'cinnamon|st_theme|croco|css' | tail -50
cinnamon --version
XDG_SESSION_TYPE=... ; loginctl show-session $XDG_SESSION_ID -p Type
```
**Kỳ vọng:** không có `Did not find color property`, không có `Unrecognized …`,
không có `There was some problem parsing the theme` (chuỗi này có thật trong `js/ui/main.js`).

### 2.3 P3 · Screenshot matrix
`tests/manual/screenshot-matrix.csv` — tối thiểu **26 bối cảnh × số variant**:

| # | Bối cảnh | # | Bối cảnh |
|---|---|---|---|
| 1 | Desktop trống + panel | 14 | Alt-Tab |
| 2 | Menu (Cinnamon 6.6 appmenu, có sidebar) | 15 | Expo / workspace |
| 3 | Menu đang hover item | 16 | Scale (overview cửa sổ) |
| 4 | Applet menu con (submenu) | 17 | OSD (volume/brightness) |
| 5 | Window list + grouped-window-list | 18 | Notification (1 dòng & multi-line) |
| 6 | Panel systray + xapp-status | 19 | Calendar applet + events |
| 7 | Cửa sổ SSD (titlebar muffin) focused | 20 | Desklet |
| 8 | Cửa sổ SSD unfocused / maximized / tiled | 21 | Screensaver + màn khoá |
| 9 | Cửa sổ CSD (headerbar) | 22 | On-screen keyboard |
| 10 | Nemo icon view | 23 | Virtual keyboard / IBus popup |
| 11 | Nemo list view + places sidebar (có disk-full bar) | 24 | Looking Glass dialog |
| 12 | Nemo desktop icons trên wallpaper sáng & tối | 25 | App GTK4/libadwaita (vd: GNOME Fonts/Console) |
| 13 | Rename entry + floating-bar + inactive pane (F3) | 26 | cinnamon-settings (nhiều trang) |

Mỗi ảnh kèm: phiên bản Cinnamon, session type, scale factor, theme variant.

### 2.4 P4 · Kiểm tra chức năng (không hồi quy)
Danh sách tối thiểu 20 mục: đổi theme qua Settings rồi đổi lại; bật/tắt Night Light; mở applet menu
bằng phím; drag applet trên panel; edit mode của panel; thêm/xoá workspace; snap/tile cửa sổ;
double-click titlebar (action đã cấu hình); F3 trong Nemo (2 pane); đổi chế độ xem Nemo;
bookmark; rename file; mở Trash; removable-drives; sound applet; power applet; a11y;
đổi `text-scaling-factor` sang 1.25; đổi sang fractional scaling; logout/login; **unlock màn hình khoá**.

> Tiêu chí chặn: **mọi thao tác phải hoạt động y hệt trước khi cài theme.** Nếu một thao tác đổi hành vi
> → đó là defect mức Blocker, không phải "cosmetic".

### 2.5 P5 · Benchmark hiệu năng (bắt buộc trước khi bật bất kỳ `-blur` nào)

Protocol A/B có kiểm soát, chạy 3 lần, lấy trung vị:

| Chỉ số | Cách đo | Ngưỡng pass |
|---|---|---|
| CPU% của `cinnamon` khi nghỉ (desktop tĩnh, 10s) | `pidstat -p $(pgrep -x cinnamon) 1 10` | ≤ baseline Mint-Y + 2 điểm % |
| Thời gian mở menu (10 lần) | quay `ffmpeg`/`simple-screenrecorder` 60fps, đếm frame từ keypress tới render xong | ≤ baseline + 33 ms |
| Frame drop khi kéo cửa sổ | cảm nhận + `cinnamon-looking-glass` perf tab nếu có | không thấy stutter |
| `-blur` trên menu (biến thể Blur, `-blur: 4`) | như trên, so với biến thể không blur | CPU% tăng ≤ 8 điểm %, không stutter |
| `-blur` trên panel full-width 1920×40 | **dự đoán FAIL** theo E11 → đo để xác nhận | không bật trong bản release nếu fail |

Cơ sở lý thuyết phải ghi trong báo cáo (E11): chi phí ≈ `blur_size × w × h × 4` byte GPU→CPU→GPU
**mỗi lần paint**. Với panel 1920×40 và `-blur: 20` → ~6 MB readback mỗi frame.

Bổ sung: kiểm tra `CLUTTER_FEATURE_SHADERS_GLSL` có sẵn không (E12) — nếu không, `-blur` in ra
`g_message` và bị bỏ qua → theme vẫn phải đẹp khi blur không hoạt động.

### 2.6 P6 · Drill rollback (bắt buộc, không có ngoại lệ)
```
# 1. snapshot trạng thái gốc
gsettings list-recursively > /tmp/before.txt
dconf dump /org/cinnamon/  > /tmp/before-cinnamon.dconf

# 2. install + apply
python3 -m tools.cli.mintos_glass install --dry-run
python3 -m tools.cli.mintos_glass install
python3 -m tools.cli.mintos_glass apply

# 3. rollback
python3 -m tools.cli.mintos_glass rollback

# 4. đối chiếu
gsettings list-recursively > /tmp/after.txt
dconf dump /org/cinnamon/  > /tmp/after-cinnamon.dconf
diff /tmp/before.txt /tmp/after.txt && diff /tmp/before-cinnamon.dconf /tmp/after-cinnamon.dconf
ls ~/.local/share/themes/ ~/.local/state/mintos-glass/
```
**Pass khi:** cả hai `diff` rỗng, không còn `MintOS-Glass*` trong `~/.local/share/themes/`,
và `rollback` chạy lần 2 không báo lỗi (idempotent).

## 3. Môi trường kiểm thử (matrix tối thiểu)

| Trục | Giá trị | Ghi chú |
|---|---|---|
| Session | X11, Wayland | Cinnamon 6.6 có Wayland; hiệu ứng St có thể khác — **bắt buộc test cả hai nếu máy hỗ trợ** |
| Scale | 1.0, 1.25 (fractional), 2.0 | ảnh hưởng icon/asset và `text-scaling-factor` |
| Color scheme | dark, light | theo D-2 |
| Wallpaper | sáng, tối, nhiều chi tiết | quyết định độ đọc của glass + icon desktop |
| Monitor | 1, 2 (khác DPI) | panel/OSD positioning |
| GPU | Intel/AMD/NVIDIA | `CLUTTER_FEATURE_SHADERS_GLSL` (E12) |
| Theme baseline | Mint-Y (mặc định) | để đo A/B |

Nếu người dùng chỉ có 1 cấu hình: ghi rõ **phạm vi đã test** và **phạm vi chưa test** trong
`docs/verification/REPORT.md`. Không suy rộng.

## 4. Định nghĩa mức defect

| Mức | Định nghĩa | Xử lý |
|---|---|---|
| **Blocker** | Mất chức năng; không unlock được; Cinnamon crash/restart loop; theme không nạp được | Chặn release, rollback ngay |
| **Critical** | Widget không được style (nền đen/trắng thô); chữ không đọc được (contrast < 3:1); titlebar vỡ layout | Chặn release |
| **Major** | Sai màu/kích thước so với token; thiếu trạng thái hover/focus; lệch giữa dark và light | Sửa trước bản beta |
| **Minor** | Lệch 1–2px, shadow chưa đúng ý, asset chưa sắc | Backlog |
| **Perf** | Vượt ngưỡng §2.5 | Tắt tính năng gây ra (thường là blur) |

Mọi defect phải kèm: ảnh chụp, phiên bản, session type, bước tái hiện, và **1 test Tầng 1 mới** nếu có thể tự động hoá.

## 5. Những tuyên bố KHÔNG được phép xuất hiện trong báo cáo

- "Đã test trên Linux Mint" — nếu agent không có output từ máy thật.
- "Blur chạy mượt" — nếu chưa có số đo §2.5.
- "Tương thích GTK 3.24.x / Nemo 6.6.x" — nếu chưa có kết quả T00.
- "Không ảnh hưởng hiệu năng" — mặc định là **chưa biết**, cho tới khi đo.
