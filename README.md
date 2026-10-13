# MintOS Glass

Bộ giao diện desktop phong cách “glass” hiện đại (bề mặt bán trong suốt, viền mảnh,
điểm nhấn xanh Mint) cho **Linux Mint 22.3 “Zena” — Cinnamon 6.6**.

Mục tiêu: **cải tiến giao diện, giữ nguyên chức năng hệ thống.** Dự án không viết lại
Cinnamon, không thay thế desktop environment, không patch mã nguồn hệ thống và
không cài thêm gói phần mềm lên máy người dùng.

> **Đọc trước khi cài:** hiện **chưa có bản cài đặt hoàn chỉnh cho người dùng cuối**.
> Phần theme Cinnamon (Dark Glass), icon theme và wallpaper đã có mã nguồn và đã
> qua kiểm tra tĩnh offline; phần theme GTK, trình cài đặt/rollback tự động, đóng gói
> `dist/` và ISO **chưa triển khai**. Xem mục [12. Giới hạn hiện tại](#12-giới-hạn-hiện-tại)
> và [docs/INSTALLATION.md](docs/INSTALLATION.md) để biết chính xác việc gì làm được hôm nay.

---

## Mục lục

- [1. Giới thiệu](#1-giới-thiệu)
- [2. Tính năng](#2-tính-năng)
- [3. Yêu cầu hệ thống](#3-yêu-cầu-hệ-thống)
- [4. Lấy mã nguồn](#4-lấy-mã-nguồn)
- [5. Cài đặt](#5-cài-đặt)
- [6. Áp dụng giao diện](#6-áp-dụng-giao-diện)
- [7. Build package](#7-build-package)
- [8. Tạo ISO](#8-tạo-iso)
- [9. Gỡ cài đặt và rollback](#9-gỡ-cài-đặt-và-rollback)
- [10. Khắc phục sự cố](#10-khắc-phục-sự-cố)
- [11. Đóng góp](#11-đóng-góp)
- [12. Giới hạn hiện tại](#12-giới-hạn-hiện-tại)
- [Tài liệu liên quan](#tài-liệu-liên-quan)
- [Giấy phép](#giấy-phép)

---

## 1. Giới thiệu

MintOS Glass là một **theme** (không phải một bản phân phối Linux mới, cũng không
phải desktop environment mới). Theme được xây dựng trên nền:

| Thành phần | Giá trị đã chốt |
|---|---|
| Hệ điều hành đích | Linux Mint 22.3 “Zena” (nền Ubuntu 24.04) |
| Desktop | Cinnamon 6.6 (mã theme vendor được ghim theo Cinnamon `6.6.9`) |
| Biến thể đang làm | **Dark Glass** (Phase 1). Light Glass đã định nghĩa token nhưng chưa bật |
| Màu nhấn (accent) | Xanh Mint `#3ddc97` (quyết định D-3) |
| Dock | Style applet có sẵn `grouped-window-list@cinnamon.org` trong panel (D-1), không dùng Plank, không cài thêm gói |
| Vị trí cài dự kiến | `~/.local/share/themes/MintOS-Glass` — cấp người dùng, **không cần root** (D-4 / ADR-002) |
| Giấy phép | GPL-3.0-or-later — xem [LICENSE](LICENSE) và [NOTICE.md](NOTICE.md) |

### Trạng thái tổng quan

| Nhóm việc | Trạng thái | Bằng chứng trong repo |
|---|---|---|
| Khảo sát & kế hoạch | ✅ Xong | `docs/plan/` (9 tài liệu, 37 mục bằng chứng upstream) |
| Design token + generator | ✅ Xong (offline) | `design/tokens/`, `tools/tokens/generate.py`, `make tokens-check` |
| Theme Cinnamon Dark Glass (nguồn SCSS) | ✅ Có mã, biên dịch được offline | `src/cinnamon/` — xem mục 2 |
| Asset Cinnamon (SVG) | ✅ Xong (offline) | `src/cinnamon/assets/` (15 tệp) |
| Icon theme hệ thống | ✅ Có mã (122 icon SVG) | `src/icons/MintOS-Glass/` |
| Wallpaper | ✅ Có mã (4 bản Dark, SVG) | `src/wallpapers/` |
| Style Nemo + app Mint (partial SCSS) | 🟡 Đã viết nhưng **chưa được nối** vào theme GTK | `src/gtk-3.0/sass/_apps-nemo.scss`, `_apps-mint.scss` |
| Theme GTK 3 (lõi) / GTK 4 / libadwaita | ❌ Chưa triển khai | Thiếu entry point — xem mục 12 |
| Trình cài đặt / rollback tự động (CLI) | ❌ Chưa triển khai | `tools/cli/` chưa tồn tại |
| Đóng gói `dist/` | ❌ Chưa triển khai | `dist/` chưa tồn tại; `make scss` hiện chỉ in dòng TODO |
| ISO Linux Mint tùy biến | ❌ Chưa triển khai | Chưa có công cụ/cấu hình ISO nào — xem mục 8 |
| Kiểm thử trên máy Linux Mint thật | ❌ Chưa thực hiện | `verified_on_target: false` trong `design/tokens/00-meta.json` |

Mọi khẳng định kỹ thuật trong kế hoạch đều được đối chiếu với mã nguồn upstream thật
(`linuxmint/Cinnamon` @ `6.6.9`, `linuxmint/muffin` @ `6.6.3`, `linuxmint/nemo`,
`linuxmint/mint-themes`, `linuxmint/libadwaita`) và có trích dẫn đường dẫn tệp/dòng
trong `docs/plan/01-survey.md`.

### Ba phát hiện định hình kiến trúc

1. **Theme Cinnamon của bên thứ ba phải HOÀN CHỈNH.** Cinnamon nạp stylesheet mặc định chỉ ở vai trò
   `fallback_stylesheet` mà theo `src/st/st-theme.c` là *non-cascading* — chỉ áp dụng khi stylesheet
   người dùng không trả về property nào **và** widget có cờ `important`. Không thể viết theme “ghi đè vài chỗ”.
   → Dự án vendor nguyên trạng `data/theme/cinnamon-sass` của Cinnamon 6.6.9 vào
   `src/cinnamon/vendor/cinnamon-6.6-sass/` rồi ghi đè ở `src/cinnamon/overrides/`.
2. **Cinnamon 6.6 có backdrop blur thật (`-blur`) nhưng rất đắt.** Mã nguồn upstream (`src/st/st-background-effect.c` trong repo Cinnamon) chạy
   `blur_size` vòng lặp, mỗi vòng đọc ngược framebuffer GPU→CPU rồi tải lại texture, mỗi lần vẽ.
   → Mặc định **tắt** blur; “glass” đạt được bằng `rgba` + gradient + viền mảnh (hairline) + đổ bóng.
   Biến thể có blur thật chưa được bật.
3. **Muffin 6.6 không đọc `metacity-1/metacity-theme-3.xml`.** `MetaTheme` chỉ còn là struct rỗng;
   khung cửa sổ được vẽ bằng **GTK 3 CSS** (`window.background.ssd > decoration > headerbar.titlebar.default-decoration`).
   → Không cần module metacity; phần khung cửa sổ thuộc về theme GTK 3 (chưa triển khai — xem mục 12).

### Nguyên tắc an toàn bất biến

1. Chỉ ghi vào `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`
   (cài icon thủ công ở bản xem trước dùng thêm `~/.local/share/icons/MintOS-Glass` — xem INSTALLATION).
2. Không `sudo`, không `apt`/`dpkg`, không sửa tệp trong `/usr`, `/etc`.
3. Mọi khoá `gsettings` bị đổi đều phải được chụp lại (snapshot) trước và khôi phục được.
4. Không tuyên bố “đã kiểm thử” khi chưa có output thật.
5. Chưa xác minh thì ghi vào checklist, không đoán.

---

## 2. Tính năng

### Đã có (đã kiểm chứng offline bằng test/lint trong repo)

| Tính năng | Mô tả | Kiểm chứng |
|---|---|---|
| Design token 3 tầng | Một nguồn sự thật duy nhất cho màu/kích thước/bán kính/motion trong `design/tokens/*.json`, sinh ra SCSS/CSS/Markdown | `make tokens-check`, `make report` |
| Cổng tương phản WCAG | Mọi cặp chữ/nền bắt buộc trong `design/tokens/50-a11y.json` phải đạt ngưỡng; đo trên backdrop xấu nhất | `python3 tools/tokens/generate.py --scheme all --report` |
| Theme Cinnamon Dark Glass | Vendor Cinnamon 6.6.9 nguyên trạng + 9 tệp ghi đè (`overrides/_00…_80`) cho panel, menu, grouped-window-list (dock trong panel), hộp thoại, OSD, thông báo, calendar, expo/scale/alt-tab, bàn phím ảo, screensaver | Biên dịch SCSS được; `python3 tools/lint/st_properties.py` (0 lỗi, phủ 527/527 selector gốc) |
| Asset Cinnamon | 15 tệp SVG (checkbox, radio, toggle, mũi tên calendar, close…) | `python3 tools/lint/assets.py` |
| Icon theme `MintOS-Glass` | 122 icon SVG (apps, places, devices, mimetypes, actions, status + bản symbolic đơn sắc), kế thừa `Mint-Y,Adwaita,gnome,hicolor` để không icon nào biến mất | `src/icons/MintOS-Glass/index.theme`, `python3 tools/lint/icon_theme.py` |
| Wallpaper Dark Glass | 4 wallpaper SVG tự vẽ (`mintos-glass-dark*.svg`), nhãn icon desktop đạt tương phản 12,67:1 – 16,01:1 (đo bằng lint) | `python3 tools/lint/wallpapers.py`, `src/wallpapers/MANIFEST.md` |
| Tài liệu dock trong panel | Cách biến panel + `grouped-window-list` thành “dock” chỉ bằng cấu hình sẵn có + CSS, kèm hoàn tác | `src/dock/gwl/README.md`, `src/dock/gwl/panel-layout.md` |
| Bộ lint + test Tầng 1 | 361 test offline (token, contrast, property St, độ phủ selector, icon, wallpaper, an toàn đường dẫn…) | `make check` (cần SCSS compiler — xem mục 3) |
| Protocol kiểm thử thủ công | Checklist phủ 50 tiêu chí nghiệm thu (Visual/Functional/Performance/Rollback) cho máy Mint thật | `tests/manual/PROTOCOL.md` |

### Đang phát triển / mới có một phần

| Hạng mục | Phần đã có | Phần còn thiếu |
|---|---|---|
| Style cho Nemo + app Mint | `_apps-nemo.scss` (624 dòng), `_apps-mint.scss` (415 dòng) + lint selector | Chưa có `src/gtk-3.0/sass/gtk.scss` nên hai tệp này **chưa nằm trong bất kỳ CSS nào được phát hành** (bug QA-09) |
| GTK 4 / libadwaita | Đã sinh `src/gtk-4.0/sass/_tokens.scss` và `src/libadwaita/tokens.css` | Chưa có file theme GTK 4/libadwaita thật (`gtk.scss`, `defaults-*.css`, `base.css`, `base-hc.css`); hai tệp token trên chưa được tệp nào nạp (QA-13) |
| Hạ tầng CI | Workflow `.github/workflows/ci.yml` có job token/safety/test/SCSS | Job `tests` chưa cài SCSS compiler nên trên runner sạch nhiều test bị bỏ qua mà job vẫn xanh (QA-01, P1) |
| Makefile | `tokens`, `tokens-check`, `report`, `lint`, `test`, `check`, `safety` chạy thật | Target `scss` chưa build — chỉ in `TODO(T04)` (QA-10); `make lint` mới chạy 2 trong số các lint hiện có (QA-12) |

### Mới ở giai đoạn đề xuất (chưa có mã)

- **Trình cài đặt/rollback CLI** (`tools/cli/mintos_glass`) — mới có thiết kế trong
  `docs/plan/02-architecture.md` và ràng buộc trong `docs/plan/04-work-breakdown.md` (task T12).
- **Đóng gói `dist/` + bản phát hành** (task T14) và **ISO tùy biến** — chưa triển khai, xem mục 7–8.
- **Control Center / Quick Settings** — Cinnamon 6.6 không có thành phần tương đương; mới có
  đề xuất tại `docs/proposals/control-center.md`, chưa viết applet nào.
- **Biến thể Light Glass** và **biến thể có blur thật** (`-Blur`) — token Light đã định nghĩa
  (`emit: false`), biến thể blur chưa bật vì chưa đo được chi phí trên máy thật.
- **Plank dock nổi** — đã loại khỏi Phase 1 (D-1); không cài thêm gói nào.

Chi tiết từng lỗi đã biết kèm bằng chứng và lệnh tái hiện: `tests/fixtures/qa-bug-register.txt`.

---

## 3. Yêu cầu hệ thống

### 3.1 Để dùng thử theme (người dùng / người kiểm thử)

| Yêu cầu | Chi tiết |
|---|---|
| Hệ điều hành đích | Linux Mint 22.3 “Zena”, Cinnamon 6.6 — **chưa được xác minh trên máy thật** (xem mục 12) |
| Quyền cần thiết | Tài khoản người dùng thường. **Không cần và không được dùng `sudo`** cho mọi bước trong tài liệu này |
| Phần mềm cần cài thêm | **Không có** (đúng ràng buộc của dự án). Bản xem trước thủ công ở INSTALLATION chỉ dùng lệnh có sẵn trên Mint (`cp`, `gsettings`, Settings) |
| Snapshot nên có | Nên chụp snapshot máy ảo hoặc sao lưu cấu hình trước khi thử, vì rollback tự động chưa tồn tại |

### 3.2 Để phát triển / kiểm tra offline (máy phát triển, bất kỳ Linux nào)

Đây là môi trường đã được dùng để kiểm chứng các lệnh trong tài liệu này:

| Công cụ | Bắt buộc? | Dùng để làm gì | Ghi chú đã xác minh |
|---|---|---|---|
| `git` | Có | Lấy mã nguồn | — |
| `python3` (≥ 3.11, chỉ thư viện chuẩn) | Có | Generator token, toàn bộ lint/test Tầng 1 | CI dùng Python 3.11 trên `ubuntu-24.04` (`.github/workflows/ci.yml`) |
| `make` | Có | Các target `tokens`/`lint`/`test`/`check` trong `Makefile` | — |
| SCSS compiler: **libsass** (`pysassc` / module Python `sass`) **hoặc** **dart-sass** (`sass` 1.77.8) | Cần cho test đầy đủ + biên dịch theme | Biên dịch `src/cinnamon/*.scss`; test tự bỏ qua (skip) nếu thiếu compiler | Thiếu compiler: vẫn chạy được token/safety, nhưng **73/361 test bị skip** (sandbox) và CI có lỗi QA-01 tương tự. Cài đặt hai compiler này chỉ dành cho máy phát triển/CI, **không** phải máy người dùng cuối |
| `node` + `npm`/`npx` | Chỉ khi dùng dart-sass | Chạy `sass@1.77.8` (khai báo trong `package.json`) | Chỉ cần trên máy phát triển |

Không cần `meson`, `ninja`, `sassc` hệ thống, máy ảo hay kết nối mạng cho test Tầng 1
(trừ lần đầu cài SCSS compiler trên máy phát triển).

---

## 4. Lấy mã nguồn

```bash
git clone https://github.com/ThuyLinh6/mintos-glass.git
cd mintos-glass
git status
```

Kết quả mong đợi: `git status` báo working tree sạch. Mọi lệnh trong README này và
trong `docs/INSTALLATION.md` đều chạy **từ thư mục gốc của repository** (`mintos-glass/`)
trừ khi ghi rõ thư mục khác.

Kiểm tra nhanh sau khi clone (không cần SCSS compiler, không ghi gì lên hệ thống):

```bash
make help
make tokens-check
python3 tools/lint/safety_paths.py
```

Kết quả mong đợi: `tokens-check` in `OK — 6 file generated khớp token`;
safety in `OK safety-paths: không có chuỗi cấm trong mã thực thi`.

---

## 5. Cài đặt

> ⚠️ **Chưa có trình cài đặt.** Thư mục `tools/cli/` và `tools/build/` trong kiến trúc
> dự kiến **chưa tồn tại**; chưa có script `install.sh`, chưa có gói `.deb`, chưa có
> `dist/` để sao chép. Lệnh `python3 -m tools.cli.mintos_glass …` được nhắc trong
> `docs/plan/06-git-workflow.md` là **kế hoạch (task T12), hiện chạy sẽ báo lỗi
> “No module named …”** — đừng dùng.

Có hai việc làm được hôm nay, hướng dẫn chi tiết từng bước ở
**[docs/INSTALLATION.md](docs/INSTALLATION.md)**:

1. **Thiết lập môi trường phát triển offline** (mọi máy Linux): clone, cài SCSS compiler
   trên máy phát triển, chạy `make check`, biên dịch thử `cinnamon.css`. Đã xác minh.
2. **Xem trước thủ công (chỉ Cinnamon + icon + wallpaper) trên Linux Mint 22.3**:
   tự biên dịch `cinnamon.css`, tự lắp thư mục theme vào `~/.local/share/themes/MintOS-Glass/`,
   sao chép icon theme và wallpaper, rồi áp dụng bằng Settings/`gsettings`.
   **Chưa kiểm chứng runtime** — chỉ nên làm trên máy thử nghiệm/máy ảo có snapshot,
   và theme GTK sẽ chưa đổi vì phần GTK chưa có (mục 6).

Quy trình cài đặt hoàn chỉnh dự kiến (snapshot → cài → áp dụng → rollback bằng một lệnh)
được mô tả như **kế hoạch chưa triển khai** trong INSTALLATION mục 8 và
`docs/plan/04-work-breakdown.md` (T12/T14). Không bước nào trong quy trình dự kiến đó
được coi là đã hoạt động.

---

## 6. Áp dụng giao diện

Bảng này chỉ áp dụng cho bản xem trước thủ công ở INSTALLATION. Mọi khoá `gsettings`
dưới đây đều nằm trong danh sách khoá đóng dự kiến của T12 và đã được đối chiếu với
`cinnamon-settings` upstream (bằng chứng E20 trong `docs/plan/01-survey.md`),
nhưng **chưa chạy trên máy Mint thật**.

| Thành phần | Cách áp dụng (bản xem trước) | Trạng thái |
|---|---|---|
| Dark Glass (theme Cinnamon) | Sao chép theme đã lắp vào `~/.local/share/themes/MintOS-Glass/`, rồi chọn trong `cinnamon-settings themes` **hoặc** `gsettings set org.cinnamon.theme name "MintOS-Glass"` (phải snapshot trước — xem INSTALLATION mục 6) | Nguồn SCSS xong; **chưa kiểm chứng runtime** |
| GTK theme | **Chưa áp dụng được.** Cinnamon Settings chỉ liệt kê theme GTK khi có `gtk-3.0/gtk.css` (E19); tệp này chưa tồn tại nên theme sẽ không hiện đúng trong bộ chọn GTK và khung cửa sổ chưa đổi | ❌ Chưa triển khai (T06/T08) |
| Icon theme | Sao chép `src/icons/MintOS-Glass/` vào `~/.local/share/icons/MintOS-Glass/`, làm mới cache icon, rồi chọn trong Settings hoặc `gsettings set org.cinnamon.desktop.interface icon-theme "MintOS-Glass"` | Icon đã có; **chưa kiểm chứng runtime** |
| Wallpaper | Sao chép 4 tệp `src/wallpapers/mintos-glass-dark*.svg` vào thư mục ảnh của bạn rồi chọn trong `cinnamon-settings backgrounds` (không dùng khoá `gsettings` vì dự án chưa xác minh khoá nền trên máy đích) | Wallpaper đã có; đường vẽ nền SVG **chưa kiểm chứng runtime** |
| Dock trong panel | Đặt panel ở cạnh dưới + applet `grouped-window-list` theo `src/dock/gwl/panel-layout.md`; style do theme Cinnamon đảm nhiệm. Không có phóng to icon khi rê chuột (nền tảng không hỗ trợ — bằng chứng trong `src/dock/gwl/README.md`) | Tài liệu xong; **chưa kiểm chứng runtime** |
| Cấu hình Cinnamon khác | Không đổi gì thêm. Dự án không tự ý đổi font, button-layout, applet hay phím tắt của bạn | — |

---

## 7. Build package

Chưa có quy trình đóng gói hoàn chỉnh. Tóm tắt trung thực (chi tiết ở
**[docs/BUILD-AND-ISO.md](docs/BUILD-AND-ISO.md)**):

| Việc | Lệnh / vị trí | Trạng thái đã xác minh |
|---|---|---|
| Sinh stylesheet từ token | `make tokens` / `make tokens-check` | ✅ Chạy thật; 6 tệp generated khớp lock |
| Kiểm tra toàn bộ Tầng 1 | `make check` | ✅ 361 test OK **khi có** SCSS compiler; thiếu compiler thì nhiều test skip |
| Biên dịch theme Cinnamon | Tự chạy libsass/dart-sass trên `src/cinnamon/cinnamon.scss` (lệnh cụ thể trong BUILD-AND-ISO) | ✅ Đã biên dịch trong sandbox: ~94 KB (libsass) / ~93 KB (dart-sass) |
| Build bằng Makefile | `make scss` | ❌ **Không build.** Target hiện chỉ in `TODO(T04): …` và không tạo `dist/` (QA-10) |
| Lắp thư mục theme `dist/MintOS-Glass/` | `tools/build/assemble.py` (dự kiến) | ❌ Chưa tồn tại. Thiếu cả `index.theme` của theme GTK (`src/theme-meta/` chưa có) nên chưa đóng gói được |
| Gói `.deb` / tarball phát hành / workflow release | — | ❌ Chưa có (không có `.github/workflows/release.yml`, không có script đóng gói) |

Không tuyên bố “build package thành công” cho tới khi `dist/` được tạo tự động,
được kiểm tra và được thử trên máy Mint thật.

---

## 8. Tạo ISO

**Chưa triển khai.** Repository hiện không chứa bất kỳ thành phần nào của một quy
trình tạo ISO: không cấu hình Cubic/live-build, không script tạo ISO, không preseed,
không cấu hình mặc định cho người dùng mới, không workflow phát hành.

Điều kiện còn thiếu trước khi nói tới ISO (chi tiết và lộ trình dự kiến — **chưa xác minh** —
ở [docs/BUILD-AND-ISO.md](docs/BUILD-AND-ISO.md) mục 4):

1. Theme GTK 3 hoàn chỉnh (T06/T08) và phần Nemo/Mint apps được nối vào (T09) —
   hiện theme chưa đủ điều kiện xuất hiện trong bộ chọn của Cinnamon Settings (V2 chưa đạt).
2. Trình cài đặt/rollback đã drill thành công trên máy thật (T12, tiêu chí R1–R10).
3. Đóng gói `dist/` + kiểm thử runtime đủ 50 tiêu chí trong `tests/manual/PROTOCOL.md`
   trên Linux Mint 22.3 thật (hiện 36/50 tiêu chí đang BLOCKED vì chưa có máy đích).
4. Quyết định cơ chế đưa theme vào ISO (gói hệ thống hay cấu hình mặc định) — chưa chốt,
   và mọi phương án đều phải giữ nguyên tắc không phá vỡ khả năng rollback.

Không có lệnh tạo ISO nào để chạy ở thời điểm này; mọi lệnh ISO trong tài liệu
BUILD-AND-ISO đều được đánh dấu là kế hoạch.

---

## 9. Gỡ cài đặt và rollback

Chưa có lệnh rollback tự động (CLI của T12 chưa tồn tại) và rollback tự động **chưa
được kiểm chứng**. Hai cách khôi phục hiện có:

1. **Khôi phục bằng giao diện (khuyến nghị cho bản xem trước):** mở
   `cinnamon-settings themes`, chọn lại theme Cinnamon/GTK/icon cũ của bạn
   (giá trị đã ghi trong snapshot ở INSTALLATION mục 6), chọn lại wallpaper cũ,
   rồi đăng xuất/đăng nhập lại. Sau đó mới xoá thư mục đã sao chép.
2. **Khôi phục thủ công bằng `gsettings` (Cấp 2):** đặt lại **từng khoá đã đổi** về
   đúng giá trị trong snapshot của chính máy bạn — không dùng giá trị mẫu của máy khác —
   rồi xoá `~/.local/share/themes/MintOS-Glass`, `~/.local/share/icons/MintOS-Glass`
   và đăng nhập lại. Trình tự đầy đủ (đặt lại icon-theme **trước** khi xoá thư mục)
   ở INSTALLATION mục 7.

Cảnh báo trung thực: trình tự trên được viết dựa trên mã nguồn upstream và protocol
của dự án, **chưa được drill trên máy Mint thật** (tiêu chí R1/R3–R5/R7 đang BLOCKED).
Vì vậy bản xem trước chỉ nên thử trên máy có snapshot/VM rollback.

---

## 10. Khắc phục sự cố

| Triệu chứng | Cách kiểm tra | Giải thích / hướng xử lý |
|---|---|---|
| `make check` báo nhiều test bị *skipped* | Kiểm tra `python3 -c "import sass"` và `npx sass --version` | Thiếu SCSS compiler trên máy phát triển. Cài libsass hoặc dart-sass (mục 3.2) rồi chạy lại. Skip không phải PASS |
| `make scss` “thành công” nhưng không có `dist/` | `ls dist` | Đúng trạng thái hiện tại (QA-10): target chỉ in TODO. Dùng lệnh biên dịch thủ công trong BUILD-AND-ISO |
| `python3 tools/lint/css_sanity.py` báo FAIL | Đọc danh sách FAIL trong output | Đang có lỗi thật đã đăng ký (QA-03, QA-05…QA-08, QA-10). Lint chéo này cố ý đỏ; xem `tests/fixtures/qa-bug-register.txt` |
| `make tokens-check` báo file generated lệch | Chạy `make tokens` rồi commit cả token và file generated | Ai đó đã sửa tay file generated hoặc sửa token mà chưa sinh lại |
| Theme không hiện trong bộ chọn GTK của Cinnamon Settings | `ls dist/MintOS-Glass/gtk-3.0/gtk.css` | **Mong đợi ở trạng thái hiện tại**: chưa có `gtk.css` (QA-09/V2). Không phải lỗi cài đặt của bạn |
| Theme Cinnamon không đổi / báo lỗi parse (trên máy Mint) | `journalctl --user -b \| grep -iE 'cinnamon\|st_theme\|css'` | Tìm `There was some problem parsing the theme`, `Did not find color property`. Rollback theo mục 9 rồi báo bug kèm output này |
| Icon không đổi sau khi chọn icon theme | `gtk-update-icon-cache ~/.local/share/icons/MintOS-Glass` rồi đăng nhập lại | Cache icon chưa làm mới (lệnh theo `tests/manual/PROTOCOL.md`; chưa kiểm chứng runtime) |
| Không biết hệ thống đang ở trạng thái nào | `gsettings get org.cinnamon.theme name`; `gsettings get org.cinnamon.desktop.interface gtk-theme`; `gsettings get org.cinnamon.desktop.interface icon-theme`; `ls ~/.local/share/themes/ ~/.local/share/icons/` | Các lệnh `get`/`ls` này chỉ đọc, an toàn. So với snapshot đã lưu trước khi áp dụng |

Mọi lệnh kiểm tra log/gsettings ở trên đều là lệnh **chỉ đọc**, trừ
`gtk-update-icon-cache` (chỉ ghi cache trong thư mục icon của bạn).

---

## 11. Đóng góp

Quy trình đầy đủ: `docs/plan/06-git-workflow.md`. Tóm tắt bắt buộc:

1. **Một nhánh = một task = một PR.** Tiền tố nhánh: `feat/Txx-…`, `fix/Txx-…`,
   `spike/Txx-…`, `chore/Txx-…`. Không commit trực tiếp vào `main`.
2. **Chỉ sửa tệp trong allow-list của task** (liệt kê trong `docs/plan/04-work-breakdown.md`).
   Một tệp chỉ có một owner; cần sửa tệp của task khác thì mở issue trước.
3. **Commit message** theo mẫu `<type>(<task>): <mô tả>` và **bắt buộc** có dòng
   `Task: Txx` ở cuối (job CI `allowlist` kiểm tra dòng này). Giả định kỹ thuật phải có
   `Refs: E##` trỏ tới `docs/plan/01-survey.md`.
4. **Trước khi mở PR:** chạy `make check` và dán log vào PR; nếu đổi token thì kèm
   `make report`. Dùng mẫu `.github/PULL_REQUEST_TEMPLATE.md`, liệt kê rõ phần
   **chưa kiểm chứng** — để trống mục đó đồng nghĩa “mọi thứ đã kiểm chứng”.
5. **An toàn:** không `sudo`/`apt`/`dpkg` trong tooling, không ghi ngoài hai đường dẫn
   ở nguyên tắc an toàn, không thêm `-blur` vào output nếu chưa có ADR + số đo.
   `src/cinnamon/vendor/**`, `tools/cli/**`, `LICENSE`, `NOTICE.md` cần 2 approval.
6. **Không tuyên bố đã test trên máy thật** nếu không có output/ảnh tại
   `docs/verification/`. Bug mới phát hiện trên máy thật phải được đóng băng thành
   test Tầng 1 trước khi sửa (xem `docs/plan/05-testing-strategy.md`).

Người dùng mới muốn chạy kiểm thử trên máy Mint: bắt đầu từ
`docs/plan/09-verification-checklist.md` (chỉ gồm lệnh đọc) và
`tests/manual/PROTOCOL.md`.

---

## 12. Giới hạn hiện tại

Danh sách này là một phần của cam kết của dự án: phần chưa làm được phải nói rõ.

**Chưa có kiểm thử runtime nào.** Toàn bộ kiểm chứng hiện tại là offline (Tầng 1:
biên dịch, lint, test cấu trúc). Chưa từng cài/chạy theme trên Linux Mint 22.3 /
Cinnamon 6.6 thật; `design/tokens/00-meta.json` ghi `verified_on_target: false`.
36/50 tiêu chí nghiệm thu đang BLOCKED vì lý do này (`tests/manual/PROTOCOL.md`).

**Chưa triển khai:**

- Theme GTK 3 lõi (T06: `gtk.scss`, `_colors.scss`, `_common.scss`…), tài nguyên GTK 3 (T07),
  khung cửa sổ muffin (T08: `_decorations.scss`), GTK 4/libadwaita (T10).
  Hệ quả: chưa có `gtk-3.0/gtk.css`, theme chưa đạt V2, chưa áp dụng được GTK theme.
- Trình cài đặt/rollback CLI (T12), đóng gói `dist/` và phát hành (T14), ISO.
- Biến thể Light Glass (token có, `emit: false`), biến thể blur thật, dock Plank,
  Control Center dạng applet (mới là đề xuất).

**Lỗi/hạn chế đã biết (có bằng chứng, chưa sửa — không thuộc phạm vi sửa của tài liệu này):**

- QA-01 (P1): job `tests` trong CI chưa cài SCSS compiler → trên runner sạch test bị skip mà vẫn xanh.
- QA-03/QA-04 (P2): `_apps-nemo.scss` rò rỉ selector `.dim-label` trần ra mọi app GTK 3; danh sách class chung của lint chưa đầy đủ.
- QA-05…QA-08 (P2/P3): token `font-weight` bị sinh kèm đơn vị `px`, tên token `-pt` mang giá trị px,
  hằng kiểm tra blur bị sinh thành token, token motion trong `40-motion.json` chưa được sinh ra stylesheet.
- QA-09/QA-10/QA-13 (BLOCKED/P2/P3): thiếu entry GTK, `make scss` là stub, token GTK 4/libadwaita chưa được nạp.
- QA-02 (P2): `NOTICE.md` chưa cập nhật theo trạng thái vendor hiện tại (vẫn ghi “chưa vendor” dù
  `LICENSE` và `src/cinnamon/vendor/` đã tồn tại) — cần owner T01 sửa trong commit riêng.
- 4 token đang bị generator bỏ qua có chủ đích vì chưa đo trên máy thật:
  `size.titlebar-height`, `gtk.titlebar.height`, `font.family`, `font.size-base-pt`.

---

## Tài liệu liên quan

| Tài liệu | Nội dung |
|---|---|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Hướng dẫn cài đặt từng bước: môi trường dev offline, xem trước thủ công trên Mint, gỡ cài đặt/rollback |
| [docs/BUILD-AND-ISO.md](docs/BUILD-AND-ISO.md) | Build package và ISO: phần đã xác minh, phần chưa triển khai, lộ trình dự kiến |
| [docs/plan/README.md](docs/plan/README.md) | Bộ kế hoạch kỹ thuật (khảo sát, kiến trúc, design system, phân rã việc, kiểm thử, git workflow, nghiệm thu, rủi ro) |
| [docs/decisions.md](docs/decisions.md) | 4 quyết định phạm vi đã chốt (dock, biến thể, accent, vị trí cài) |
| [docs/plan/09-verification-checklist.md](docs/plan/09-verification-checklist.md) | Checklist chỉ-đọc để xác minh trên máy Linux Mint thật (task T00) |
| [tests/manual/PROTOCOL.md](tests/manual/PROTOCOL.md) | Protocol kiểm thử thủ công phủ 50 tiêu chí nghiệm thu |
| [tests/fixtures/qa-bug-register.txt](tests/fixtures/qa-bug-register.txt) | Sổ bug QA: mức độ, bằng chứng, lệnh tái hiện, owner |
| [tools/tokens/README.md](tools/tokens/README.md) | Generator design token: cách sinh, quy ước tên, cách thêm token |
| [src/dock/gwl/README.md](src/dock/gwl/README.md) | Dock trong panel bằng grouped-window-list: làm được gì, không làm được gì |
| [docs/proposals/control-center.md](docs/proposals/control-center.md) | Đề xuất Control Center (chưa triển khai) |

Cấu trúc thư mục chính: `design/tokens/` (nguồn sự thật) → `tools/tokens/generate.py` →
`src/cinnamon/`, `src/gtk-3.0/`, `src/gtk-4.0/`, `src/libadwaita/`; tài nguyên ở
`src/cinnamon/assets/`, `src/icons/`, `src/wallpapers/`; kiểm tra ở `tools/lint/` và `tests/`.

## Giấy phép

GPL-3.0-or-later — xem [LICENSE](LICENSE). Mã vendor từ Cinnamon
(`src/cinnamon/vendor/cinnamon-6.6-sass/`, GPL-2.0-or-later / LGPL-2.1-or-later)
được ghi nguồn, commit SHA và checksum trong
`src/cinnamon/vendor/cinnamon-6.6-sass/VENDOR.md`; xem thêm
`docs/adr/ADR-007-licensing.md`. Lưu ý QA-02 ở mục 12: `NOTICE.md` cần được cập nhật
cho khớp trạng thái vendor hiện tại.
n tại.
