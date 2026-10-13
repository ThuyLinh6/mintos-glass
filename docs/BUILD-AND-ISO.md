# Build package và tạo ISO — trạng thái và hướng dẫn

Tài liệu này trả lời hai câu hỏi thường bị hiểu nhầm nhất của dự án:
“build gói như thế nào?” và “tạo ISO như thế nào?”. Nguyên tắc viết:
**chỉ ghi lệnh đã chạy được thật là lệnh build; mọi quy trình chưa tồn tại đều
được đánh dấu kế hoạch, không trình bày như đã kiểm chứng.**

> **Kết luận ngắn (2026-10-13):**
> - ✅ Sinh stylesheet từ token và biên dịch **thử** theme Cinnamon: làm được, đã xác minh offline.
> - ❌ Build package (`dist/MintOS-Glass/`, tarball, `.deb`): **chưa triển khai**.
>   `make scss` không build; chưa có `tools/build/assemble.py`, chưa có `src/theme-meta/index.theme`.
> - ❌ Tạo ISO: **chưa triển khai ở bất kỳ mức nào** — không công cụ, không cấu hình,
>   không lệnh. Mục 4 là lộ trình dự kiến, không phải hướng dẫn chạy được.

---

## Mục lục

- [1. Bản đồ quy trình build dự kiến và phần đã có](#1-bản-đồ-quy-trình-build-dự-kiến-và-phần-đã-có)
- [2. Build đã xác minh (chạy được hôm nay)](#2-build-đã-xác-minh-chạy-được-hôm-nay)
- [3. Đóng gói package — chưa triển khai](#3-đóng-gói-package--chưa-triển-khai)
- [4. Tạo ISO — chưa triển khai](#4-tạo-iso--chưa-triển-khai)
- [5. Xác minh kết quả build](#5-xác-minh-kết-quả-build)
- [6. Việc phải làm tiếp theo (cho người đóng góp)](#6-việc-phải-làm-tiếp-theo-cho-người-đóng-góp)

---

## 1. Bản đồ quy trình build dự kiến và phần đã có

Kiến trúc đích (từ [plan/02-architecture.md](plan/02-architecture.md), nguyên tắc A8:
build xác định — SCSS → CSS được sinh sẵn để người dùng cuối không cần toolchain):

```text
design/tokens/*.json ──tools/tokens/generate.py──► src/**/tokens (SCSS/CSS generated)
src/cinnamon/*.scss ──┐
src/gtk-3.0/sass/*.scss ──┼──[compile SCSS]──► CSS ──[assemble]──► dist/MintOS-Glass/ ──► cài / đóng gói / ISO
src/gtk-4.0/sass/*.scss ──┘        ▲                    ▲                     ▲
src/icons, src/wallpapers ─────────┴────────────────────┘              tools/cli (T12)
                          tools/build/compile_scss.py          tools/build/assemble.py
```

| Giai đoạn | Công cụ / tệp | Trạng thái |
|---|---|---|
| Token → stylesheet | `tools/tokens/generate.py` (`make tokens`) | ✅ Đã có, đã xác minh |
| Biên dịch Cinnamon SCSS → CSS | Chạy libsass/dart-sass trực tiếp (Mục 2.3) | ✅ Đã xác minh thủ công trong sandbox |
| Biên dịch GTK 3/4 SCSS → CSS | Entry `src/gtk-3.0/sass/gtk.scss`, `src/gtk-4.0/sass/gtk.scss` | ❌ Chưa có entry point (T06/T10 chưa làm) |
| Lắp thư mục theme | `tools/build/assemble.py` → `dist/MintOS-Glass/` | ❌ Chưa tồn tại (QA-11) |
| Metadata theme | `src/theme-meta/index.theme` + thumbnail | ❌ Chưa tồn tại; mẫu đã khảo sát (E34) |
| Phát hành (tarball/tag/workflow) | `.github/workflows/release.yml` | ❌ Chưa tồn tại |
| Đưa vào ISO | (chưa chọn cơ chế) | ❌ Chưa triển khai — Mục 4 |

Điều kiện tiên quyết về phụ thuộc (máy phát triển): `python3` ≥ 3.11 (stdlib),
`make`, và **một** SCSS compiler (libsass hoặc dart-sass 1.77.8). Cách chuẩn bị:
[INSTALLATION.md](INSTALLATION.md) Mục 2. Không cần `sudo`, `meson` hay `ninja`.
Người dùng cuối sẽ **không** cần các công cụ này khi `dist/` được commit theo A8 —
nhưng hiện `dist/` chưa tồn tại nên cam kết đó chưa thành hiện thực.

---

## 2. Build đã xác minh (chạy được hôm nay)

Mọi lệnh dưới đây chạy từ thư mục gốc repository, không cần `sudo`,
chỉ ghi vào repository và `/tmp`.

### 2.1 Sinh lại file từ design token

```bash
make tokens
make tokens-check
make report
```

- **Đầu ra thực tế:** `src/cinnamon/tokens/_tokens.scss`,
  `src/gtk-3.0/sass/_tokens.scss`, `src/gtk-4.0/sass/_tokens.scss`,
  `src/libadwaita/tokens.css`, `docs/design-system/tokens.md`,
  `design/tokens.lock.json`.
- **Kết quả mong đợi:** `OK — 6 file generated khớp token`. `make report` in bảng
  contrast toàn `[PASS]` (trừ dòng `[INFO]` cho cặp trang trí `border.subtle`).
- Lưu ý: scheme Light không sinh tệp (`emit: false`, quyết định D-2) — dòng
  `[skip] scheme 'light' …` là đúng thiết kế, không phải lỗi build.

### 2.2 Kiểm tra trước khi biên dịch

```bash
make check
python3 tools/lint/st_properties.py
python3 tools/lint/css_sanity.py; echo "exit=$?"
```

- `make check` (lint + 361 test Tầng 1): `OK` khi đã cài SCSS compiler;
  thiếu compiler thì nhiều test `skipped` — **skip không được tính là build đạt**.
- `st_properties.py`: `OK — 0 lỗi`, phủ 527/527 selector gốc Cinnamon 6.6, 0 `-blur`.
- `css_sanity.py`: hiện **FAIL** vì các lỗi thật đã đăng ký
  (QA-03, QA-05…QA-08, QA-10). Một “build xanh toàn diện” chưa tồn tại;
  không được bỏ qua FAIL này khi tuyên bố chất lượng bản build.

### 2.3 Biên dịch theme Cinnamon ra CSS (kiểm chứng, chưa phải đóng gói)

```bash
# libsass (trong .venv đã kích hoạt — xem INSTALLATION Mục 2)
python3 -c "import sass; open('/tmp/mintos-glass-cinnamon.css','w').write(sass.compile(filename='src/cinnamon/cinnamon.scss'))"

# hoặc dart-sass
npx --no-install sass --no-source-map src/cinnamon/cinnamon.scss /tmp/mintos-glass-cinnamon-dart.css

wc -c /tmp/mintos-glass-cinnamon*.css
```

- **Vị trí đầu ra thực tế của bước này:** chỉ là tệp tạm trong `/tmp` — **không** phải
  `dist/`. Đừng chép nhầm vị trí này thành “package”.
- **Kết quả đã đo:** ~94.349 byte (libsass) / ~92.705 byte (dart-sass).
  Chênh lệch do `output_style` mặc định khác nhau (QA-N01 — không phải lỗi).
  Tiêu chí kích thước P6 (`cinnamon.css` ≤ 400 KB) đạt ở mức tệp đơn lẻ này;
  tổng `dist/` ≤ 8 MB chưa đo được vì chưa có `dist/`.
- `src/cinnamon/cinnamon.scss` chỉ là con trỏ tới `cinnamon-dark.scss` (Phase 1 chỉ có
  Dark Glass). Chưa có biến thể Light/Blur để build.

### 2.4 Những lệnh tưởng là build nhưng không phải

| Lệnh | Hành vi thật | Bằng chứng |
|---|---|---|
| `make scss` | Chỉ in `TODO(T04): <compiler> src/cinnamon/cinnamon.scss dist/MintOS-Glass/cinnamon/cinnamon.css`, không tạo tệp/`dist/` | QA-10; chạy xong `ls dist` báo không tồn tại |
| `python3 tools/lint/vendor_integrity.py` (nhắc trong `VENDOR.md`) | Tệp **chưa tồn tại** | Không có trong `tools/lint/` — đừng chạy, đừng trích dẫn như cổng kiểm tra đang hoạt động |
| `python3 -m tools.cli.mintos_glass …` | Module chưa tồn tại | `tools/cli/` chưa có (T12) |

---

## 3. Đóng gói package — chưa triển khai

### 3.1 Một package theme hoàn chỉnh còn thiếu những gì

Theo kiến trúc (Mục 1) và tiêu chí nghiệm thu V1/V2, thư mục phát hành
`dist/MintOS-Glass/` tối thiểu phải có `index.theme`, `cinnamon/cinnamon.css`
+ `cinnamon/assets/`, `gtk-3.0/gtk.css` (+ biến thể dark nếu có), và tuỳ giai đoạn:
`gtk-4.0/`, `libadwaita-1.5/`. Hiện trạng:

| Thành phần package | Trạng thái | Việc chặn |
|---|---|---|
| `cinnamon/cinnamon.css` + 15 asset SVG | Nguồn sẵn sàng để lắp tay (INSTALLATION Mục 6.3) | Chưa có assembler tự động |
| `gtk-3.0/gtk.css` | ❌ Chưa biên dịch được — thiếu `gtk.scss` và toàn bộ lõi T06; partial Nemo/Mint đang mồ côi | QA-09 (BLOCKED, chờ T06) |
| Khung cửa sổ (decorations) | ❌ Thiếu `_decorations.scss` | T08 (cần đo titlebar trên máy thật) |
| `gtk-4.0/` + `libadwaita-1.5/` (4 tệp bắt buộc E22) | ❌ Chỉ có tệp token chưa được nạp | QA-13 (BLOCKED, chờ T10/T00) |
| `index.theme` + thumbnail cho bộ chọn theme | ❌ `src/theme-meta/` chưa tồn tại | T14 |
| Icon theme / wallpaper trong package | Nguồn có (`src/icons/`, `src/wallpapers/`); vị trí cài đích chưa được T12 chính thức hoá | QA-11 |
| Kiểm tra “`dist/` khớp `src/`” | ❌ Chưa có `tools/lint/generated_up_to_date.py` / job tương ứng | T01/T14 |

### 3.2 Quy trình đóng gói dự kiến (KẾ HOẠCH — chưa xác minh, chưa có lệnh chạy được)

Các bước sau là **thiết kế** từ `plan/02-architecture.md` + task T14
(`plan/04-work-breakdown.md`), ghi lại để người làm T14 không phải thiết kế lại.
Không bước nào được coi là đã hoạt động:

1. Viết `tools/build/compile_scss.py`: gọi libsass (ưu tiên, khớp toolchain Mint)
   và kiểm tra chéo dart-sass; fail nếu lệch ngữ nghĩa (ADR-004).
   Khắc phục QA-10 bằng cách cho `make scss` gọi script này thay vì `echo TODO`.
2. Viết `tools/build/assemble.py`: lắp `dist/MintOS-Glass{,-Blur?}/` từ `src/`,
   chép icon/wallpaper theo vị trí cài đã chốt, sinh `index.theme` từ mẫu E34.
3. Thêm cổng kiểm tra: `dist/` tồn tại, đủ tệp bắt buộc (gồm `gtk-3.0/gtk.css`),
   kích thước đạt P6, và job CI “generated up-to-date” fail khi `dist/` lệch `src/`.
4. Chỉ sau khi T12 drill rollback đạt trên máy thật: tạo workflow release,
   tag `v0.x` theo cổng G0…G4 trong `plan/07-acceptance-criteria.md`, đóng tarball.
   Chưa có cổng nào đạt (G0 còn thiếu V2/P7/R8) nên **chưa được gắn tag phát hành**.

### 3.3 Các định dạng gói chưa được chọn

Chưa có quyết định nào về `.deb`, tarball hay chỉ thư mục theme. Không tạo gói
bằng công cụ đóng gói hệ thống (`dpkg-deb`, `fpm`…) khi chưa có ADR và chưa có
trình cài đặt user-level — gói hệ thống sẽ mâu thuẫn với ADR-002 (cài không root,
rollback bằng xoá thư mục). Mọi đề xuất phải qua review theo quy tắc 2-approval
cho đường dẫn nhạy cảm trong `plan/06-git-workflow.md`.

---

## 4. Tạo ISO — chưa triển khai

### 4.1 Trạng thái hiện tại: không có gì để chạy

Đã kiểm tra toàn repository: **0** tệp script shell, **0** cấu hình Cubic/live-build/
`mint-iso`, **0** preseed/kickstart, **0** cấu hình mặc định cho người dùng mới,
**0** workflow release. Dự án hiện là một **theme đang phát triển**, không phải
một bản dựng hệ điều hành. Không tồn tại lệnh tạo ISO đúng sự thật để ghi vào đây.

### 4.2 Vì sao chưa thể làm ISO (điều kiện còn thiếu)

| Điều kiện | Vì sao bắt buộc | Trạng thái |
|---|---|---|
| T00: xác minh trên Mint 22.3 thật | ISO khoá cứng phiên bản Cinnamon/Nemo/libadwaita; đoán sai là hỏng cả ảnh | ❌ Chưa chạy (`verified_on_target: false`) |
| T06/T08/T09: theme GTK hoàn chỉnh | Thiếu `gtk.css` thì theme không qua được bộ chọn của Settings (V2/E19) — ISO sẽ ship giao diện nửa vời | ❌ BLOCKED (QA-09) |
| T12: installer + rollback đã drill | ISO phải có đường lui khi theme lỗi (blocker R1); hiện rollback tự động chưa tồn tại | ❌ Chưa triển khai |
| T14: `dist/` đóng gói + cổng release G0 | Không có package thì không có gì để đưa vào ISO | ❌ Chưa đạt cổng nào |
| Quyết định cơ chế tích hợp ISO | Rải tệp vào ảnh hệ thống (`/usr/share/themes`) mâu thuẫn ADR-002; cài qua first-login script lại cần cơ chế cấu hình mặc định chưa thiết kế — phải chốt bằng ADR trước | ❌ Chưa chốt |
| Kiểm thử ISO (cài mới, live session, người dùng mới — R10) | Cần hạ tầng VM và protocol riêng ngoài `tests/manual/PROTOCOL.md` hiện tại | ❌ Chưa có |

### 4.3 Lộ trình dự kiến tới ISO (KẾ HOẠCH — chưa xác minh)

Thứ tự phụ thuộc lấy từ `plan/04-work-breakdown.md` (T14 phụ thuộc mọi task) —
đây là **kế hoạch**, không phải cam kết thời gian:

1. Hoàn thành T00 → T06/T08 → nối T09 → T10 (nếu đưa GTK 4 vào ảnh).
2. Hoàn thành T12 (installer/rollback, drill R1–R10 trên máy thật) và T14
   (`dist/` + release tarball đạt cổng G0/G1).
3. Chốt ADR cho cơ chế tích hợp ISO (gói user-level khi đăng nhập đầu tiên
   hay thành phần hệ thống) kèm phân tích rollback của chính ISO.
4. Khi đó mới chọn công cụ ISO, viết cấu hình và protocol kiểm thử ISO
   (live boot, cài mới, nâng cấp, gỡ theme trong ISO). Tài liệu này sẽ được viết lại
   bằng lệnh thật sau lần tạo ISO thành công đầu tiên có log kèm theo.

Không dùng các lệnh tạo ISO “mẫu” từ bên ngoài như thể là của dự án, và không
tuyên bố “đã build ISO thành công” khi chưa có tệp ISO + log + kết quả boot thử.

---

## 5. Xác minh kết quả build

Dùng checklist này để phân biệt “đã build thật” với “mới ghi trong tài liệu”:

```bash
# 1) Token không drift
python3 tools/tokens/generate.py --scheme all --check

# 2) Toàn bộ test Tầng 1 (phải thấy OK, không phải OK-skipped hàng loạt)
python3 -m unittest discover -s tests -t .

# 3) CSS Cinnamon biên dịch được và đạt cổng St
python3 -c "import sass; open('/tmp/mintos-glass-cinnamon.css','w').write(sass.compile(filename='src/cinnamon/cinnamon.scss'))"
python3 tools/lint/st_properties.py
wc -c /tmp/mintos-glass-cinnamon.css

# 4) Package: hiện PHẢI báo chưa có — nếu báo “có” hãy kiểm tra bạn đang ở đúng repo/nhánh
ls dist/MintOS-Glass/gtk-3.0/gtk.css 2>&1
ls src/theme-meta/index.theme tools/build/assemble.py 2>&1
```

- Bước 1–3 ✅ đã xác minh offline (361 test OK khi có compiler; CSS ~94 KB; `st_properties` 0 lỗi).
- Bước 4: kết quả đúng hiện tại là `No such file or directory` cho cả hai lệnh.
  Bất kỳ tài liệu/PR nào khẳng định package đã sẵn sàng mà bước 4 vẫn như vậy đều sai.
- Kiểm chứng runtime (theme nạp đẹp, không lỗi parse, hiệu năng, rollback) **không**
  nằm trong các lệnh trên — thuộc `tests/manual/PROTOCOL.md` trên máy Mint thật,
  hiện đang BLOCKED.

---

## 6. Việc phải làm tiếp theo (cho người đóng góp)

Theo thứ tự chặn lẫn nhau (chi tiết allow-list từng task trong
[plan/04-work-breakdown.md](plan/04-work-breakdown.md)):

1. **T00** — chạy checklist trên máy Mint 22.3 thật, điền `docs/verification/REPORT.md`.
2. **T01** — sửa QA-01 (cài compiler cho job `tests`), QA-10 (cho `make scss` build thật
   hoặc đổi mô tả), QA-12 (bổ sung lint cho `make lint`), QA-02 (cập nhật `NOTICE.md`).
3. **T06 → T08 → T09/T10** — tạo entry GTK, decorations, nối partial Nemo/Mint (kèm sửa
   QA-03/QA-04), hoàn thiện 4 tệp libadwaita; sửa QA-05…QA-08 trong generator token.
4. **T12 → T14** — viết `tools/build/*` + CLI, drill rollback, rồi mới đóng gói và bàn ISO.

Mỗi việc trên là một task/PR riêng theo quy ước ở README mục 11; tài liệu này chỉ
mô tả trạng thái, không thay thế allow-list của từng task.
