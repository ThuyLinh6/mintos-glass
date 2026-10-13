# 04 — Phân rã công việc, thứ tự phụ thuộc, phân công agent

**Trạng thái (cập nhật 2026-10-13):** T02 ✅ xong · T01 🟡 một phần (còn `tools/lint/allowlist.py`
+ `tests/fixtures/task-allowlists.json`) · T13 🟡 một phần (còn `st_properties.py`, `css_sanity.py`) ·
T00 ⏸ chờ người dùng · còn lại ⏳ chưa bắt đầu. Xem `docs/decisions.md`.

Quy ước:
- Mỗi task có **ID**, **owner**, **phụ thuộc**, **danh sách file ĐƯỢC PHÉP tạo/sửa (allow-list)** và **điều kiện hoàn thành**.
- Ngoài allow-list là **cấm**. `tools/lint/allowlist.py` (T01) enforce điều này trong CI — xem `06-git-workflow.md` §5.
- Mỗi task = 1 nhánh = 1 PR. Không task nào được sửa file của task khác.

## 0. Ma trận phụ thuộc

```
T00 (verify on target) ──┬────────────────────────────────────────────────┐
                         ▼                                                │
T01 (scaffold+CI) ──► T02 (tokens+generator) ──┬──► T03 (spike: Cinnamon base strategy)
                                               │            │
                                               │            ▼
                                               ├──► T04 (Cinnamon core) ──► T05 (Cinnamon assets)
                                               │            │                    │
                                               │            ▼                    ▼
                                               ├──► T06 (GTK3 core+widgets) ─► T07 (GTK3 assets)
                                               │            │
                                               │            ├──► T08 (GTK3: decorations/WM)
                                               │            ├──► T09 (GTK3: Nemo + Mint apps)
                                               │            └──► T10 (GTK4 + libadwaita)
                                               │
                                               ├──► T11 (Dock adapter)
                                               ├──► T12 (Installer/Rollback CLI)
                                               └──► T13 (Test harness + manual protocol)
                                                            │
        T04,T05,T07,T08,T09,T10,T11,T12,T13 ────────────────┴──► T14 (Docs + release packaging)
```

**Đường găng:** T00 → T01 → T02 → T03 → T04 → T05 → T14.
**Song song tối đa sau T02:** 6 luồng (T04, T06, T10, T11, T12, T13).

## 1. Danh sách task

---

### T00 · Xác minh môi trường trên máy người dùng
- **Owner:** người dùng (agent chỉ cung cấp lệnh, không tự chạy)
- **Phụ thuộc:** —
- **Chặn:** T03, T04, T06, T10, T11, T12 (mọi thứ cần thông tin phiên bản)
- **Được phép tạo/sửa:**
  - `docs/verification/REPORT.md` (điền kết quả)
  - `docs/verification/raw/*.txt` (output thô, dán nguyên văn)
- **Cấm:** mọi thứ khác; **cấm chạy lệnh ghi/sửa hệ thống** — checklist chỉ có lệnh đọc.
- **Done khi:** đủ 8 mục trong `09-verification-checklist.md` §1–§8 có output thật dán kèm, hoặc ghi rõ "không lấy được vì …".

---

### T01 · Scaffold repo + CI + allow-list enforcer
- **Owner:** Agent A (Platform/DevEx)
- **Phụ thuộc:** — (chạy song song với T00)
- **Được phép tạo:**
  ```
  .gitignore  .editorconfig  LICENSE  NOTICE.md  Makefile  README.md
  .github/workflows/ci.yml
  .github/PULL_REQUEST_TEMPLATE.md
  .github/CODEOWNERS
  .github/ISSUE_TEMPLATE/bug.md
  .github/ISSUE_TEMPLATE/visual-defect.md
  tools/lint/allowlist.py
  tools/lint/generated_up_to_date.py
  tools/build/compile_scss.py
  tests/lint/__init__.py  tests/lint/test_allowlist.py
  tests/fixtures/task-allowlists.json
  docs/adr/ADR-000-template.md
  docs/adr/ADR-007-licensing.md
  ```
- **Được phép sửa:** `README.md` (đã tồn tại)
- **Cấm:** `src/**`, `design/**`, `dist/**`
- **Done khi:**
  1. `make help` chạy được trong sandbox này (không cần sass).
  2. CI chạy `allowlist.py` và fail khi một PR chạm file ngoài allow-list của task khai báo trong commit message.
  3. `tests/fixtures/task-allowlists.json` chứa allow-list của **toàn bộ** T00–T14.
  4. `LICENSE` = GPL-3.0-or-later, `NOTICE.md` có chỗ cho vendor attribution.
  5. Có bằng chứng CI chạy thật (link/URL hoặc log dán vào PR).

---

### T02 · Design tokens + generator
- **Owner:** Agent B (Design Systems)
- **Phụ thuộc:** T01
- **Được phép tạo:**
  ```
  design/tokens/*.json            (7 file)
  design/tokens/token-schema.json
  design/tokens.lock.json         (generated)
  design/reference/NOTES.md
  tools/tokens/generate.py
  tools/tokens/README.md
  tools/lint/contrast.py
  docs/design-system/tokens.md    (generated)
  docs/design-system/tokens-preview.css (generated)
  tests/lint/test_tokens.py  tests/lint/test_contrast.py
  ```
- **Được phép tạo (file sinh, sẽ bị T04/T06/T10/T11 ghi đè nội dung):**
  `src/cinnamon/tokens/_tokens.scss`, `src/gtk-3.0/sass/_tokens.scss`,
  `src/gtk-4.0/sass/_tokens.scss`, `src/libadwaita/tokens.css`,
  `src/dock/plank/MintOS-Glass/dock.theme`
- **Cấm:** mọi file `.scss`/`.css` khác trong `src/` (trừ 5 file sinh ở trên), `dist/**`
- **Done khi:** 6 tiêu chí ở `03-design-system.md` §6 đạt, kèm log `make tokens && make lint-tokens`.

---

### T03 · Spike: chiến lược nền cho Cinnamon theme (ADR-001)
- **Owner:** Agent C (Cinnamon) + người dùng chạy thử
- **Phụ thuộc:** T00, T01
- **Được phép tạo:**
  ```
  docs/adr/ADR-001-cinnamon-base-strategy.md
  spike/README.md
  spike/option-b-import/cinnamon/cinnamon.css      # ≤ 40 dòng, chỉ để thử
  spike/option-b-import/index.theme
  ```
- **Cấm:** `src/**`, `dist/**`, `design/**`
- **Nội dung thí nghiệm:** kiểm chứng `_st_theme_resolve_url()` có resolve đường dẫn tuyệt đối
  `/usr/share/cinnamon/theme/cinnamon.css` không, và thứ tự cascade khi `@import` đứng đầu file.
- **Done khi:** ADR-001 có **kết luận kèm bằng chứng** (ảnh chụp hoặc log từ máy thật), hoặc ghi rõ
  "không xác minh được → chọn phương án A". Không được kết luận "hoạt động" mà không có bằng chứng.

---

### T04 · Cinnamon theme — vendor + core
- **Owner:** Agent C (Cinnamon)
- **Phụ thuộc:** T02, T03
- **Được phép tạo:**
  ```
  src/cinnamon/vendor/cinnamon-6.6-sass/**        # pristine, kèm VENDOR.md
  src/cinnamon/cinnamon.scss
  src/cinnamon/cinnamon-dark.scss
  src/cinnamon/overrides/_00-globals.scss
  src/cinnamon/overrides/_10-surfaces.scss
  src/cinnamon/overrides/_20-panel.scss
  src/cinnamon/overrides/_30-menus-startmenu.scss
  src/cinnamon/overrides/_40-windowlist-gwl.scss
  src/cinnamon/overrides/_50-dialogs-osd-notif.scss
  src/cinnamon/overrides/_60-calendar-desklets.scss
  src/cinnamon/overrides/_70-expo-scale-alttab.scss
  src/cinnamon/overrides/_80-keyboard-screensaver-lookingglass.scss
  src/cinnamon/overrides/_90-blur-variant.scss
  tools/lint/st_properties.py
  tests/fixtures/st-allowed-properties.txt
  tests/fixtures/cinnamon-6.6-selectors.txt
  tests/lint/test_st_properties.py
  tests/lint/test_cinnamon_coverage.py
  docs/testing/cinnamon-selector-coverage.md
  ```
- **Cấm:** `src/cinnamon/vendor/**` sau khi đã commit bản pristine (mọi thay đổi phải nằm trong `overrides/`),
  `src/gtk-*/**`, `src/libadwaita/**`, `dist/**`, `design/tokens/**`
- **Done khi:**
  1. `VENDOR.md` ghi repo, ref (`6.6.9`), commit SHA đầy đủ, license (GPL-2.0-or-later / st LGPL-2.1+), ngày lấy, và khẳng định **không sửa tay**.
  2. Biên dịch ra `cinnamon.css` **bằng cả libsass và dart-sass**, không lỗi.
  3. `st_properties.py` pass: 0 property lạ (đối chiếu `tests/fixtures/st-allowed-properties.txt`).
  4. **Coverage selector**: mọi selector trong `cinnamon-6.6-selectors.txt` đều có mặt trong output
     (đây là chốt chặn cho E6 — theme phải hoàn chỉnh).
  5. Không có `-blur` trong output của biến thể chuẩn (chỉ có ở biến thể `-Blur`).
  6. `transition-duration` là property animation duy nhất được dùng (không có easing).

---

### T05 · Cinnamon assets (SVG)
- **Owner:** Agent D (Visual/Assets)
- **Phụ thuộc:** T02 (cần token màu), chạy song song T04
- **Được phép tạo:**
  ```
  src/cinnamon/assets/**/*.svg
  src/cinnamon/assets/MANIFEST.md
  tools/lint/assets.py
  tests/lint/test_assets.py
  ```
- **Cấm:** `src/cinnamon/**/*.scss` (kể cả `overrides/`), `src/gtk-*/**`
- **Done khi:** mọi `url("…")` trong `cinnamon.css` resolve tới file tồn tại; SVG well-formed (parse bằng
  `xml.etree`); không SVG nào hard-code màu trùng token (phải dùng màu từ token hoặc ghi lý do);
  có `@2x` hoặc `viewBox` đúng để scale HiDPI.

---

### T06 · GTK3 — core + widgets
- **Owner:** Agent E (GTK)
- **Phụ thuộc:** T02
- **Được phép tạo:**
  ```
  src/gtk-3.0/sass/_palette.scss
  src/gtk-3.0/sass/_colors.scss
  src/gtk-3.0/sass/_colors-public.scss
  src/gtk-3.0/sass/_drawing.scss
  src/gtk-3.0/sass/_common.scss
  src/gtk-3.0/sass/_widgets.scss
  src/gtk-3.0/sass/gtk.scss
  src/gtk-3.0/sass/gtk-dark.scss
  tools/lint/gtk_colors.py
  tests/fixtures/gtk-public-colors.txt
  tests/lint/test_gtk_colors.py
  ```
- **Cấm:** `_decorations.scss`, `_apps-*.scss`, `src/gtk-4.0/**`, `src/libadwaita/**`, `dist/**`
- **Done khi:**
  1. `gtk.css` và `gtk-dark.css` biên dịch được bằng **libsass** (bắt buộc — E18) và dart-sass.
  2. `gtk_colors.py` pass: xuất đủ **toàn bộ** tên trong `tests/fixtures/gtk-public-colors.txt` (= E33)
     **và** đủ `@theme_bg_color`, `@theme_fg_color`, `@theme_selected_bg_color`,
     `@theme_selected_fg_color`, `@theme_unfocused_bg_color` (= E29, Nemo phụ thuộc).
  3. Output chứa selector tối thiểu: `window.background`, `.titlebar`, `headerbar`, `button`,
     `entry`, `treeview.view`, `textview text`, `scrollbar`, `menu`, `.popup`, `notebook`,
     `progressbar`, `scale`, `switch`, `check`, `radio`, `tooltip`, `decoration`.
  4. Không dùng property GTK3 không tồn tại (lint theo danh sách property GTK 3.24).

---

### T07 · GTK3 assets
- **Owner:** Agent D (Visual/Assets)
- **Phụ thuộc:** T02
- **Được phép tạo:** `src/gtk-3.0/assets/**`, `src/gtk-3.0/assets.svg`, `src/gtk-3.0/assets.txt`,
  `src/gtk-3.0/render-assets.sh` *(chỉ tạo, không chạy trên máy người dùng)*
- **Cấm:** `src/gtk-3.0/sass/**`
- **Done khi:** ADR-005 được kiểm chứng (SVG nạp được trong GTK3 trên máy thật) **hoặc** có pipeline
  PNG `@1x/@2x` hoàn chỉnh; mọi `url()` trong `gtk.css` resolve.

---

### T08 · GTK3 — decorations / khung cửa sổ (thay cho module metacity)
- **Owner:** Agent E (GTK)
- **Phụ thuộc:** T06
- **Được phép tạo/sửa:** `src/gtk-3.0/sass/_decorations.scss` **và chỉ file đó**
- **Cấm:** mọi file khác trong `src/gtk-3.0/sass/`
- **Done khi:**
  1. Có đủ selector theo widget path đã xác minh (E32):
     `window.background.ssd`, `window.background.ssd decoration`,
     `headerbar.default-decoration`, `.titlebar.default-decoration`,
     `.default-decoration .title`, `.default-decoration button.titlebutton{,.close,.maximize,.minimize}`.
  2. Có `decoration { box-shadow: … }` cho cả trạng thái `:backdrop` và maximized/tiled.
  3. **Đo được** chiều cao titlebar thực tế trên máy thật và ghi vào `docs/testing/wm-metrics.md`
     (vì E32b: muffin lấy `get_min_size`/`get_padding_and_border` từ CSS — padding của ta = chiều cao thật).
  4. `tools/lint/muffin_decorations.py` pass.

---

### T09 · GTK3 — Nemo + ứng dụng Mint
- **Owner:** Agent F (Apps)
- **Phụ thuộc:** T06
- **Được phép tạo:** `src/gtk-3.0/sass/_apps-nemo.scss`, `src/gtk-3.0/sass/_apps-mint.scss`,
  `src/gtk-3.0/sass/_apps-gtk3-misc.scss`, `tools/lint/nemo_selectors.py`,
  `tests/fixtures/nemo-required-selectors.txt`, `tests/lint/test_nemo_selectors.py`,
  `docs/testing/nemo-checklist.md`
- **Cấm:** các file sass core của T06, `src/gtk-4.0/**`
- **Done khi:**
  1. Phủ **toàn bộ** selector trong `tests/fixtures/nemo-required-selectors.txt` (nguồn: E27, E28, E29, E30):
     `.nemo-window`, `.nemo-window-pane`, `.nemo-inactive-pane .view`, `.nemo-window-pane widget.entry`,
     `.floating-bar`, `.places-treeview` + 6 property `-NemoPlacesTreeView-disk-full-*`,
     `.nemo-places-sidebar`, `.sidebar`, `.nemo-desktop-window`, `.nemo-canvas-item`,
     `.nemo-desktop`, `.nemo-desktop.nemo-canvas-item{,:hover,:selected}`, `.nemo-desktop.view .entry`.
  2. **Không** ghi đè `-NemoIconContainer-activate-prelight-icon-label` (giữ hành vi gốc — ràng buộc "không đổi chức năng").
  3. Màu chữ icon desktop đạt contrast ≥ 3:1 trên nền wallpaper mẫu (đo, không đoán).
  4. Có mục cho app Mint: `cinnamon-settings`, `xed`, `xplayer`, `xreader`, `xviewer`, `pix`, `mintupdate`,
     `mintinstall`, `nemo` — tối thiểu là không phá vỡ (không selector gây xung đột).

---

### T10 · GTK4 + libadwaita
- **Owner:** Agent G (GTK4)
- **Phụ thuộc:** T02; **chặn bởi T00** (cần biết phiên bản libadwaita + kết quả `ADW_DEBUG_THEMES`)
- **Được phép tạo:**
  ```
  src/gtk-4.0/sass/{_colors.scss,_colors-public.scss,_common.scss,gtk.scss,gtk-dark.scss}
  src/gtk-4.0/assets/**
  src/libadwaita/{defaults-light.css,defaults-dark.css,base.css,base-hc.css}
  src/libadwaita/assets/**
  src/libadwaita/README.md
  tools/build/libadwaita_dirname.py     # suy ra libadwaita-<maj>.<min> từ version detect được
  tests/lint/test_libadwaita_files.py
  ```
- **Cấm:** `src/gtk-3.0/**`, `src/cinnamon/**`
- **Done khi:**
  1. `src/libadwaita/` có **đủ 4 file** `base.css`, `base-hc.css`, `defaults-light.css`, `defaults-dark.css` (E22).
     Thiếu `base-hc.css` ⇒ fail (libadwaita sẽ bỏ qua theme khi user bật high-contrast).
  2. `base.css` chỉ đổi **màu + window controls** (E23); diff phải cho thấy không có thay đổi layout/geometry.
  3. Tên thư mục đích được **suy ra động** (`libadwaita-1.5` cho Mint 22.3, `libadwaita-1.0` cho bản cũ hơn) —
     không hard-code.
  4. Có ghi lại kết quả `ADW_DEBUG_THEMES=1` từ máy thật; nếu theme name không tới được libadwaita (E25),
     ghi mitigation vào `docs/adr/ADR-003-gtk4-theme-name.md`.

---

### T11 · Dock adapter
- **Owner:** Agent H (Shell/Dock) — **chờ D-1**
- **Phụ thuộc:** T02, T04
- **Được phép tạo:**
  ```
  src/dock/gwl/README.md
  src/dock/gwl/panel-layout.md
  src/dock/plank/MintOS-Glass/dock.theme        (generated từ tokens)
  src/dock/plank/README.md
  tools/lint/plank_theme.py
  tests/lint/test_plank_theme.py
  ```
- **Cấm:** `src/cinnamon/**` (style của grouped-window-list phải đi qua `overrides/_40-windowlist-gwl.scss` của T04)
- **Done khi:**
  1. `dock.theme` đúng schema Plank (E35): đủ 2 section, đủ key, màu `R;;G;;B;;A` là **số nguyên**.
  2. Tài liệu GWL mô tả cách đạt vẻ "dock" **không cần cài gì thêm và không sửa file applet** —
     chỉ dùng cấu hình panel sẵn có + CSS của T04; kèm hướng dẫn hoàn tác từng bước.
  3. **Không** có lệnh `apt install` nào trong tài liệu; chỉ có nhánh "nếu plank đã có sẵn".

---

### T12 · Installer / Rollback CLI
- **Owner:** Agent I (Tooling) — task an toàn nhất, cần review kỹ nhất
- **Phụ thuộc:** T02; nên xong trước khi T04/T06 merge để test sớm
- **Được phép tạo:**
  ```
  tools/cli/mintos_glass/{__init__,__main__,paths,snapshot,detect,apply,rollback}.py
  tools/build/assemble.py
  dist/.gitkeep
  tests/lint/test_paths_hardcoded.py
  tests/cli/test_snapshot_roundtrip.py
  docs/testing/rollback-drill.md
  ```
- **Cấm:** `src/**`, `design/**`
- **Ràng buộc cứng (phải có test tự động):**
  1. Chỉ 2 đường dẫn được ghi: `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`.
     `test_paths_hardcoded.py` quét toàn bộ `tools/` và fail nếu thấy chuỗi `/usr`, `/etc`, `/opt`, `sudo`, `apt`, `dpkg`.
  2. Trước khi đổi bất kỳ khoá gsettings nào: snapshot **đầy đủ** giá trị cũ vào
     `~/.local/state/mintos-glass/snapshot-<UTC>.json`.
  3. `rollback` khôi phục **đúng** snapshot và xoá thư mục theme; `rollback` chạy được **nhiều lần** (idempotent).
  4. Khoá được phép chạm (danh sách đóng): `org.cinnamon.theme name`;
     `org.cinnamon.desktop.interface {gtk-theme, icon-theme, cursor-theme, gtk-color-scheme}`;
     `org.cinnamon.desktop.wm.preferences theme`;
     `org.gnome.desktop.interface gtk-theme` **chỉ khi** ADR-003 quyết định cần (E25).
     Ngoài danh sách → từ chối.
  5. `--dry-run` cho mọi lệnh ghi. `selftest` chạy được không cần theme tồn tại.
  6. Chỉ dùng Python stdlib + `gi` (PyGObject, có sẵn trên Mint) và fallback sang binary `gsettings`.
- **Done khi:** 6 ràng buộc trên có test pass trong CI + `docs/testing/rollback-drill.md` có log thật từ máy người dùng.

---

### T13 · Test harness + protocol thủ công
- **Owner:** Agent J (QA)
- **Phụ thuộc:** T01, T02
- **Được phép tạo:**
  ```
  tests/lint/test_css_sanity.py     tools/lint/css_sanity.py
  tests/manual/PROTOCOL.md
  tests/manual/screenshot-matrix.csv
  tests/manual/RESULTS-template.md
  tests/fixtures/**  (ngoài các fixture do T04/T06/T09 tạo)
  docs/testing/perf-benchmark.md
  ```
- **Cấm:** `src/**`, `dist/**`
- **Done khi:** `make lint` chạy xanh trong sandbox này (bằng chứng: log CI), và `PROTOCOL.md` có đủ
  số lượt kiểm tra để phủ `07-acceptance-criteria.md`.

---

### T14 · Docs + đóng gói release
- **Owner:** Agent K (Docs/Release)
- **Phụ thuộc:** tất cả
- **Được phép tạo/sửa:** `README.md`, `docs/**` (trừ `docs/verification/REPORT.md` của T00),
  `src/theme-meta/**`, `.github/workflows/release.yml`, `Makefile` (chỉ target `dist`/`release`)
- **Done khi:** người dùng mới làm theo README và cài + rollback thành công mà không cần đọc mã nguồn;
  `dist/` build ra theme dir đúng chuẩn; có tag và artifact.

### T15 · Icon theme hệ thống (MintOS-Glass)
- **Owner:** Agent D (Visual/Assets)
- **Phụ thuộc:** T02 (token màu). Phối hợp: Agent C (icon trên panel/applet),
  Agent E (icon trong app GTK), Agent F (icon thư mục/ổ đĩa/tệp trong Nemo).
- **Lý do task này chưa từng có trong plan:** bản work-breakdown gốc chỉ có T05
  (asset SVG cho Cinnamon theme) và T07 (asset cho GTK3) — cả hai là asset *của
  theme*, không phải **icon theme cấp hệ thống** dùng chung cho menu, dock, Nemo,
  Settings, desktop, hộp thoại chọn tệp. Đây là phạm vi Agent D được giao bổ sung
  nên phải có allow-list riêng, nếu không sẽ xung đột với quy tắc "một file, một
  owner".
- **Được phép tạo:**
  ```
  src/icons/MintOS-Glass/index.theme
  src/icons/MintOS-Glass/**/*.svg
  src/icons/MintOS-Glass/MANIFEST.md
  src/icons/MintOS-Glass/render-png.sh        (chỉ tạo, KHÔNG chạy trên máy người dùng)
  docs/design-system/icon-spec.md
  tools/lint/icon_theme.py
  tests/fixtures/icon-theme-core.txt
  tests/lint/test_icon_theme.py
  ```
- **Cấm:** `src/cinnamon/**` (việc chọn icon theme là gsetting
  `org.cinnamon.desktop.interface icon-theme`, thuộc T12; style icon trên panel đi
  qua `overrides/` của T04), `src/gtk-*/**`, `design/tokens/**`,
  `src/icons/**/index.theme` của theme khác.
- **Done khi:**
  1. `index.theme` hợp lệ theo Icon Theme Spec của freedesktop: có `[Icon Theme]`
     với `Name`, `Inherits`, `Directories`; **mọi thư mục liệt kê trong
     `Directories` phải tồn tại thật** và **mọi thư mục tồn tại phải được liệt kê**
     (không khai báo khả năng mà tài nguyên không đáp ứng).
  2. Chuỗi `Inherits` đảm bảo **không icon nào biến mất** khi theme thiếu: kế thừa
     một theme chắc chắn có trên Mint rồi tới `hicolor`.
  3. Tên icon lấy từ **`Icon=` trong file `.desktop` thật** của từng app (đã xác
     minh từ mã nguồn), không đặt tên theo trí nhớ.
  4. Icon `*-symbolic` phải **đơn sắc** (một màu, không gradient, không nhiều màu)
     để GTK tô lại được theo màu chữ.
  5. SVG well-formed (`xml.etree`), có `viewBox`, không tham chiếu URL ngoài,
     không `<script>`/`<image>`/`<filter>`.
  6. Màu trong SVG tra ngược được về token, cùng cơ chế đã áp dụng ở T05.
  7. Có `MANIFEST.md` ghi: icon nào đã có, icon nào **chưa** có và fallback về đâu,
     nguồn tên icon, và giấy phép của mọi thành phần bên thứ ba.

---

### T16 · Wallpaper và tài nguyên hình ảnh dùng chung
- **Owner:** Agent D (Visual/Assets)
- **Phụ thuộc:** T02 (token màu)
- **Được phép tạo:**
  ```
  src/wallpapers/**
  src/wallpapers/MANIFEST.md
  docs/design-system/wallpaper-spec.md
  tools/lint/wallpapers.py
  tests/lint/test_wallpapers.py
  ```
- **Cấm:** `src/cinnamon/**`, `src/gtk-*/**`, `src/icons/**`, `design/tokens/**`
- **Done khi:**
  1. Wallpaper là **SVG vector tự vẽ** (không tải từ Internet, không nhúng URL
     ngoài, không dùng tài nguyên không có quyền phân phối). SVG scale vô hạn nên
     một tệp phục vụ mọi độ phân giải; nếu cần raster thì `render-png.sh` mô tả
     pipeline chứ **không chạy trên máy người dùng**.
  2. Có biến thể Dark Glass, và ghi rõ biến thể Light Glass sẽ thêm khi D-2 mở khoá.
  3. Nền wallpaper phải đủ tối để **nhãn icon desktop đạt ≥ 3:1** — đo bằng
     `tools/lint/contrast.py`, không đoán. Đây là điểm giao nhau với Done #3 của T09:
     T09 đã đo nhãn desktop trên wallpaper *mô hình* ba mức chói; T16 cung cấp
     wallpaper *thật* để đo lại.
  4. Không xung đột thị giác với icon desktop: vùng giữa màn hình không có chi tiết
     gắt, điểm nhấn nằm lệch khỏi khu vực icon.
  5. `MANIFEST.md` ghi nguồn + giấy phép của từng tệp.

---

### T17 · Kiến trúc System Settings + đề xuất Control Center
- **Owner:** Agent 6 (Settings & Control Center UI)
- **Phụ thuộc:** khảo sát Cinnamon 6.6.9; phối hợp Agent 3 (T06 GTK3 core),
  Agent 2 (T04 Cinnamon shell/applet), Agent 5 (T15 icon theme)
- **Lý do task này chưa từng có trong plan:** work-breakdown gốc coi giao diện
  `cinnamon-settings` là hệ quả của T06 (GTK3 core) nên không có task riêng. Khảo sát
  của Agent 6 cho thấy **không đúng như vậy**: Settings có ba tầng trang với ba chủ
  sở hữu khác nhau, có 3 hook CSS thật (một cái bị khoá), và Cinnamon 6.6 **không có**
  thành phần quick-settings nào để làm Control Center. Những sự kiện đó cần một nơi
  ghi lại có kiểm tra, không thể chỉ nằm trong commit message.
- **Được phép tạo:**
  ```
  docs/design-system/settings-architecture.md
  docs/proposals/control-center.md
  tests/fixtures/cinnamon-settings-hooks.txt
  tools/lint/settings_arch.py
  tests/lint/test_settings_arch.py
  ```
- **Cấm:** `src/gtk-3.0/sass/**` (thuộc T06/T09), `src/cinnamon/**` (thuộc T04),
  `src/icons/**` (thuộc T15), `design/tokens/**`, và **mọi file applet của Cinnamon**.
- **Done khi:**
  1. Ghi được **ba tầng trang** của Settings kèm bằng chứng file:line, và nói rõ tầng
     nào theme với tới được, tầng nào không.
  2. Liệt kê **đúng** hook CSS có thật, mỗi cái kèm bằng chứng; phân biệt hook mở,
     hook bị khoá ở priority cao hơn, và class GTK chung (không phải hook riêng).
  3. Ghi lại bẫy **GtkBuilder id không phải widget name trong GTK3**, kèm bằng chứng
     từ `gtkwidget.c`.
  4. Control Center: **không build applet mới** ở task này (quyết định của người dùng
     2026-10-13). Phải giao **đề xuất** kèm danh sách thành phần bundled đã xác minh,
     API thật của chúng, và rủi ro. Không có nút giả. Không có lệnh cài package.
  5. Có lint kiểm tra **tài liệu khớp fixture hai chiều** — để số liệu trong tài liệu
     không trôi ra khỏi bằng chứng.

---

## 2. Phân công theo agent (tóm tắt)

| Agent | Vai trò | Task | Số file sở hữu |
|---|---|---|---|
| A | Platform / DevEx | T01, T13(hỗ trợ) | 20 |
| B | Design Systems | T02 | 16 |
| C | Cinnamon shell | T03, T04 | 22 |
| D | Visual / Assets | T05, T07, T15, T16 | 4 nhóm asset (Cinnamon SVG, GTK3 asset, icon theme, wallpaper) |
| — | Settings / Control Center | T17 | 2 tài liệu + 1 fixture + lint |
| E | GTK core + WM | T06, T08 | 10 |
| F | Apps (Nemo/Mint) | T09 | 7 |
| G | GTK4 / libadwaita | T10 | 11 |
| H | Dock | T11 | 6 |
| I | Tooling / An toàn | T12 | 10 |
| J | QA | T13 | 8 |
| K | Docs / Release | T14 | 6 |
| — | **Người dùng** | T00 + chạy protocol | 2 |

## 3. Quy tắc chống xung đột giữa các agent

1. **Một file, một owner.** `tests/fixtures/task-allowlists.json` là nguồn sự thật; file nào xuất hiện
   trong 2 allow-list → CI fail ngay ở bước setup.
2. **File tổng hợp** (`src/cinnamon/cinnamon.scss`, `src/gtk-3.0/sass/gtk.scss`) do owner của task core sở hữu.
   Task khác muốn thêm partial phải **mở issue**, không tự sửa.
3. **Token là read-only** với mọi task trừ T02. Task cần token mới → mở issue cho Agent B, không tự thêm.
4. **Vendor là bất biến** sau lần commit đầu (`src/cinnamon/vendor/**`).
5. Commit message bắt buộc có `Task: T04` ở dòng cuối → `allowlist.py` đối chiếu.
