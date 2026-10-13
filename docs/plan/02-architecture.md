# 02 — Kiến trúc dự án & cấu trúc thư mục

## 1. Nguyên tắc kiến trúc

| # | Nguyên tắc | Lý do (bằng chứng) |
|---|---|---|
| A1 | **Token-first.** Một nguồn sự thật duy nhất cho màu/kích thước/blur/motion; mọi stylesheet đều được sinh từ token | Tránh 4 bản CSS lệch nhau; cho phép nhiều agent làm song song |
| A2 | **Cinnamon theme phải hoàn chỉnh** — fork `cinnamon-sass` của Cinnamon 6.6 rồi reskin, không viết mới từ số 0 | E6: fallback stylesheet non-cascading |
| A3 | **GTK3 là trụ cột** — một stylesheet GTK3 phục vụ 3 nhiệm vụ: app GTK3, Nemo, và khung cửa sổ muffin | E19 (bắt buộc có `gtk-3.*`), E29 (Nemo cần `@theme_*`), E32 (muffin đọc GTK3 CSS) |
| A4 | **GTK4/libadwaita ở chế độ bảo thủ** — chỉ đổi màu + window controls | E23 (khuyến nghị chính thức của upstream) |
| A5 | **Không có module metacity** | E31: muffin 6.6 không parse XML |
| A6 | **Blur mặc định TẮT**; "glass" = rgba + gradient + hairline border + shadow. Blur thật nằm ở biến thể opt-in | E11: chi phí `blur_size ×` GPU readback mỗi lần paint |
| A7 | **Cài ở user-level**, không root, atomic, rollback 1 lệnh | E7/E19b/E22: cả Cinnamon, cs_themes và libadwaita đều quét `~/.local/share/themes` **đầu tiên** |
| A8 | **Build deterministic**: SCSS → CSS commit vào repo, CI kiểm tra "generated up-to-date" | Theo cách mint-themes làm (E17/E18); người dùng không cần cài sass |
| A9 | **Không icon theme riêng ở Phase 1** — kế thừa Mint-Y | Giảm 90% khối lượng; tránh rủi ro thiếu icon |

## 2. Sơ đồ kiến trúc

```
                         ┌──────────────────────────────────────────┐
                         │  design/tokens/*.json  (NGUỒN SỰ THẬT)   │
                         └───────────────────┬──────────────────────┘
                                             │ tools/tokens/generate.py
             ┌───────────────┬───────────────┼───────────────┬────────────────┐
             ▼               ▼               ▼               ▼                ▼
   src/cinnamon/     src/gtk-3.0/    src/gtk-4.0/   src/libadwaita/   src/dock/plank/
   tokens/_tokens    sass/_tokens    sass/_tokens   tokens.css        dock.theme
        .scss             .scss           .scss     (@define-color)   (INI R;;G;;B;;A)
             │               │               │               │                │
             │ sass          │ sass          │ sass          │ (css thuần)    │ (template)
             ▼               ▼               ▼               │                │
   src/cinnamon/vendor/  gtk.css         gtk.css             │                │
   cinnamon-6.6-sass/    gtk-dark.css    gtk-dark.css        │                │
   + overrides/*.scss         │               │              │                │
             │                │               │              │                │
             ▼                ▼               ▼              ▼                ▼
      ┌─────────────────────────────────────────────────────────────────────────────┐
      │  tools/build/assemble.py  →  dist/MintOS-Glass/  (theme dir hoàn chỉnh)      │
      │                                      │                                       │
      │  + index.theme  + thumbnail.png  + cinnamon/cinnamon.css  + gtk-3.0/…        │
      │  + gtk-4.0/…    + libadwaita-1.5/…   + assets/                              │
      └──────────────────────────────────────┬──────────────────────────────────────┘
                                             │ tools/cli (mintos-glass)
                                             ▼
              ┌──────────────────────────────────────────────────────────┐
              │ ~/.local/share/themes/MintOS-Glass/     (không cần root)  │
              │ ~/.local/state/mintos-glass/snapshot-*.json  (rollback)   │
              └──────────────────────────────────────────────────────────┘
```

## 3. Cấu trúc thư mục đề xuất

```
mintos-glass/
├── README.md                          # viết lại: giới thiệu + quick start
├── LICENSE                            # GPL-3.0-or-later (tương thích Cinnamon GPL-2+, E15)
├── NOTICE.md                          # ghi công + license từng phần vendor
├── Makefile                           # make build | lint | test | install | rollback
├── .gitignore
├── .editorconfig
│
├── .github/
│   ├── workflows/ci.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── ISSUE_TEMPLATE/{bug,visual-defect}.md
│
├── docs/
│   ├── plan/                          # ← bộ tài liệu này (Phase 0)
│   ├── design-system/                 # GENERATED từ tokens (trang token, preview)
│   ├── verification/                  # REPORT.md do NGƯỜI DÙNG điền từ 09-checklist
│   ├── testing/                       # protocol, screenshot matrix, kết quả đo
│   └── adr/                           # quyết định kiến trúc, mỗi file 1 ADR
│
├── design/
│   ├── tokens/                        # NGUỒN SỰ THẬT — chỉ T02 được sửa
│   │   ├── 00-meta.json
│   │   ├── 10-primitives.json
│   │   ├── 20-semantic-dark.json
│   │   ├── 20-semantic-light.json
│   │   ├── 30-component.json
│   │   ├── 40-motion.json
│   │   └── 50-a11y.json
│   ├── tokens.lock.json               # hash — CI phát hiện drift
│   └── reference/                     # ghi chú tham chiếu (KHÔNG commit ảnh có bản quyền)
│
├── tools/                             # Python 3 stdlib-only (không pip install trên máy user)
│   ├── tokens/generate.py             # tokens → SCSS/CSS/INI/MD
│   ├── build/
│   │   ├── compile_scss.py            # gọi sassc/pysassc/dart-sass, có fallback
│   │   ├── assemble.py                # dist/ ← src/
│   │   └── render_assets.py           # (chỉ nếu buộc phải raster; mặc định SVG-only)
│   ├── lint/
│   │   ├── st_properties.py           # allowlist property St (từ E8/E36) — cổng CI chính
│   │   ├── css_sanity.py              # cân bằng ngoặc, @import, url() tồn tại
│   │   ├── gtk_colors.py              # đủ @define-color public (E33) + @theme_* (E29)
│   │   ├── nemo_selectors.py          # đủ selector Nemo (E27–E30)
│   │   ├── muffin_decorations.py      # đủ window.background.ssd/decoration/.default-decoration (E32)
│   │   ├── contrast.py                # WCAG AA từ tokens
│   │   ├── assets.py                  # SVG well-formed, kích thước, @1x/@2x
│   │   ├── allowlist.py               # PR chỉ chạm file được phép của task (xem 06)
│   │   └── generated_up_to_date.py    # dist/ không lệch src/
│   └── cli/mintos_glass/              # installer/rollback (T12)
│       ├── __main__.py                # probe|install|apply|rollback|uninstall|status|selftest
│       ├── paths.py                   # HARD-CODE chỉ 2 đường dẫn được ghi
│       ├── snapshot.py                # gsettings/dconf snapshot + restore
│       └── detect.py                  # libadwaita version, session type, plank, fonts
│
├── src/
│   ├── cinnamon/
│   │   ├── vendor/
│   │   │   └── cinnamon-6.6-sass/     # pristine upstream, KHÔNG sửa tay
│   │   │       ├── VENDOR.md          # repo, ref, commit SHA, license, ngày lấy
│   │   │       ├── _colors.scss … widgets/*.scss
│   │   ├── tokens/_tokens.scss        # GENERATED
│   │   ├── overrides/                 # tầng "glass" — phần ta viết
│   │   │   ├── _00-globals.scss       # map token vào biến upstream
│   │   │   ├── _10-surfaces.scss      # mixin glass(), elevated(), hairline()
│   │   │   ├── _20-panel.scss
│   │   │   ├── _30-menus-startmenu.scss
│   │   │   ├── _40-windowlist-gwl.scss
│   │   │   ├── _50-dialogs-osd-notif.scss
│   │   │   ├── _60-calendar-desklets.scss
│   │   │   ├── _70-expo-scale-alttab.scss
│   │   │   ├── _80-keyboard-screensaver-lookingglass.scss
│   │   │   └── _90-blur-variant.scss  # chỉ bật khi build biến thể -Blur
│   │   ├── cinnamon.scss              # entry: tokens → vendor → overrides
│   │   ├── cinnamon-dark.scss         # (nếu D-2 = cả hai)
│   │   └── assets/                    # SVG (St đọc SVG được: upstream ship checkbox.svg, radio.svg…)
│   │
│   ├── gtk-3.0/
│   │   ├── sass/
│   │   │   ├── _tokens.scss           # GENERATED
│   │   │   ├── _palette.scss          # hàm SCSS: shade/mix/alpha compile-time
│   │   │   ├── _colors.scss           # biến nội bộ (dark + light)
│   │   │   ├── _colors-public.scss    # @define-color — PHẢI phủ hết E33
│   │   │   ├── _drawing.scss          # mixin nút/entry/scrollbar
│   │   │   ├── _common.scss           # nền tảng + widget core
│   │   │   ├── _widgets.scss
│   │   │   ├── _decorations.scss      # window.background.ssd, decoration, .default-decoration (E32)
│   │   │   ├── _apps-nemo.scss        # E27–E30
│   │   │   ├── _apps-mint.scss        # cinnamon-settings, xed, xplayer, xreader, xviewer…
│   │   │   ├── _apps-gtk3-misc.scss   # libhandy, lightdm-gtk-greeter (phase 2)
│   │   │   ├── gtk.scss               # entry light
│   │   │   └── gtk-dark.scss          # entry dark
│   │   └── assets/                    # SVG-first; nếu cần PNG thì assets.svg + assets.txt
│   │
│   ├── gtk-4.0/
│   │   ├── sass/{_tokens,_colors,_colors-public,_common,gtk.scss,gtk-dark.scss}
│   │   └── assets/
│   │
│   ├── libadwaita/                    # → dist/<theme>/libadwaita-<MAJ>.<MIN>/
│   │   ├── defaults-light.css         # @define-color cho light (E22)
│   │   ├── defaults-dark.css          # @define-color cho dark
│   │   ├── base.css                   # widget style — bảo thủ: chỉ màu + window controls (E23)
│   │   ├── base-hc.css                # high-contrast (bắt buộc, nếu thiếu libadwaita bỏ qua theme)
│   │   └── assets/
│   │
│   ├── gtk-2.0/gtkrc                  # Phase 2, ưu tiên thấp
│   │
│   ├── dock/
│   │   ├── gwl/README.md              # cách biến grouped-window-list thành dock (không sửa applet)
│   │   └── plank/MintOS-Glass/dock.theme   # GENERATED từ tokens (E35)
│   │
│   └── theme-meta/
│       ├── index.theme                # E34
│       └── thumbnails/                # thumbnail.png + cinnamon/thumbnail.png (bắt buộc để hiện trong picker)
│
├── dist/                              # GENERATED nhưng COMMIT (người dùng không cần toolchain)
│   ├── MintOS-Glass/                  # biến thể chuẩn (không blur)
│   └── MintOS-Glass-Blur/             # biến thể opt-in có -blur (chỉ nếu T03-SPK pass)
│
└── tests/
    ├── lint/                          # pytest chạy OFFLINE trong CI (chạy được thật)
    ├── fixtures/
    │   ├── st-allowed-properties.txt  # từ st-theme-node.c @6.6.9
    │   ├── cinnamon-6.6-selectors.txt # từ cinnamon-sass @6.6.9 — coverage diff
    │   ├── nemo-required-selectors.txt
    │   └── gtk-public-colors.txt
    └── manual/
        ├── PROTOCOL.md                # quy trình chạy trên máy thật
        └── screenshot-matrix.csv      # danh sách ảnh bắt buộc
```

## 4. Quyết định kiến trúc (ADR) — cần chốt

### ADR-001 · Nền tảng theme Cinnamon: fork upstream sass hay overlay `@import`?

| Phương án | Ưu | Nhược |
|---|---|---|
| **A. Fork `data/theme/cinnamon-sass` @6.6.9 → `src/cinnamon/vendor/`** (khuyến nghị) | Chắc chắn đủ selector cho 6.6 (kể cả `.appmenu`, `favorites`, `nightlight`, screensaver, OSK); re-base được khi Mint cập nhật; không phụ thuộc file hệ thống | ~2400 dòng phải quản lý; nghĩa vụ GPL (E15) — chấp nhận được |
| B. Overlay mỏng: `@import url("/usr/share/cinnamon/theme/cinnamon.css")` rồi ghi đè | Code rất nhỏ; tự bám theo bản Cinnamon đang cài | E13 xác nhận St **có** hỗ trợ `@import` nhưng `_st_theme_resolve_url()` xử lý đường dẫn tuyệt đối thế nào **chưa xác minh**; thứ tự cascade khi import trước/ghi đè sau **chưa xác minh**; nếu import fail thì theme trống hoàn toàn |

**Quyết định đề xuất: A**, nhưng chạy **spike T03** (30 phút trên máy thật) để đo phương án B.
Nếu B hoạt động → dùng B làm lớp nền và giữ A làm fallback. Ghi kết quả vào `docs/adr/ADR-001*.md`.

### ADR-002 · Vị trí cài đặt

`~/.local/share/themes/MintOS-Glass` (khuyến nghị) thay vì `/usr/share/themes`.
Bằng chứng: cả 3 consumer đều quét đường dẫn user-level **trước** —
`themeManager.js` (E7), `cs_themes.py` (E19b), `adw-style-manager.c` (E22).
Lợi ích: không cần root, không đụng file hệ thống, rollback = xoá 1 thư mục, cài song song nhiều biến thể.

### ADR-003 · Blur

Mặc định **không** dùng `-blur`. Biến thể `MintOS-Glass-Blur` chỉ được build nếu spike T03-SPK
đo được chi phí chấp nhận được trên máy thật (ngưỡng ở `07-acceptance-criteria.md` §4).
Ràng buộc khi bật: `-blur ≤ 6`, chỉ cho bề mặt ≤ ~600×400 px, không bao giờ cho panel full-width.

### ADR-004 · SCSS compiler

Mint dùng **libsass** (`pysassc`, E18/E4). libsass đã deprecated và không hỗ trợ `@use`/`math.div`.
**Quyết định đề xuất:** giới hạn cú pháp ở **giao** của libsass và dart-sass; CI biên dịch bằng **cả hai**
và fail nếu kết quả khác nhau về ngữ nghĩa. Điều này giữ khả năng đóng góp ngược lên Mint.

### ADR-005 · Asset: SVG-first

Theme Cinnamon 6.6 upstream ship SVG (`checkbox.svg`, `radio.svg`, `calendar-arrow-*.svg`, `toggle-*.svg`)
→ St đọc SVG. GTK3 cũng nạp SVG nếu có librsvg (có sẵn trên Mint).
**Quyết định:** SVG-first, không raster hoá → bỏ được phụ thuộc inkscape/optipng, repo nhẹ, scale HiDPI miễn phí.
Chỉ raster khi có bằng chứng một widget không nạp SVG (ghi vào spike T07-SPK).

### ADR-006 · Dock

Xem câu hỏi D-1. Khuyến nghị: **không** thêm gói mới.
Ưu tiên style applet `grouped-window-list@cinnamon.org` có sẵn (E14) qua tầng Cinnamon theme,
kèm file `dock.theme` cho Plank **chỉ** được kích hoạt nếu CLI detect Plank đã cài sẵn.

### ADR-007 · Giấy phép

Cinnamon = GPL-2.0-or-later, `st` = LGPL-2.1-or-later (E15); mint-themes = GPL-3+ (E16).
Vendor SCSS của Cinnamon → tác phẩm dẫn xuất → phải GPL tương thích.
**Quyết định đề xuất:** repo = **GPL-3.0-or-later**, `NOTICE.md` ghi rõ nguồn + commit SHA của phần vendor.
**Không** sao chép mã từ `mint-themes` (GPL-3+) lẫn Cinnamon vào cùng một file để tránh mơ hồ về nguồn.
