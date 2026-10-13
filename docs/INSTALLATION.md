# Hướng dẫn cài đặt MintOS Glass — từng bước

Tài liệu này hướng dẫn theo đúng **cơ chế thực tế đang có** trong repository.
Mỗi bước ghi rõ: lệnh thực thi, thư mục làm việc, kết quả mong đợi và lệnh nào cần `sudo`.

> **Trạng thái (2026-10-13) — đọc trước khi làm theo:**
>
> 1. **Chưa có trình cài đặt tự động.** `tools/cli/` và `tools/build/` chưa tồn tại,
>    không có `install.sh`, không có `dist/`, không có gói `.deb`.
>    Lệnh `python3 -m tools.cli.mintos_glass …` trong tài liệu kế hoạch là **chưa triển khai**.
> 2. **Con đường đã xác minh** là môi trường phát triển offline (Mục 1–5): chạy được trên
>    máy Linux bất kỳ, có output thật kèm theo.
> 3. **Con đường xem trước trên Linux Mint 22.3** (Mục 6–7) là thao tác thủ công dành cho
>    máy thử nghiệm/máy ảo có snapshot. Nguồn theme Cinnamon, icon và wallpaper đã có,
>    nhưng **chưa từng chạy trên Cinnamon thật** — mọi kết quả ở Mục 6–7 đều là
>    *chưa kiểm chứng runtime*. Theme GTK **chưa áp dụng được** vì chưa có `gtk.css`.
> 4. **Không bước nào trong tài liệu này cần `sudo`.** Nếu một thao tác có vẻ cần `sudo`
>    thì dừng lại — đó là dấu hiệu đi sai thiết kế của dự án (ADR-002), hãy báo bug.

**Quy ước:** trừ khi ghi khác, mọi lệnh chạy từ **thư mục gốc repository**
(thư mục `mintos-glass/` sau khi clone). Hai cột trạng thái được dùng trong tài liệu:

- ✅ **Đã xác minh offline** — đã chạy trong môi trường kiểm tra của dự án, có kết quả ghi lại.
- ⚠️ **Chưa kiểm chứng runtime** — suy ra từ mã nguồn upstream/protocol, chưa chạy trên máy Mint thật.

---

## Mục lục

- [1. Kiểm tra môi trường](#1-kiểm-tra-môi-trường)
- [2. Chuẩn bị phụ thuộc (chỉ cho máy phát triển)](#2-chuẩn-bị-phụ-thuộc-chỉ-cho-máy-phát-triển)
- [3. Lấy mã nguồn](#3-lấy-mã-nguồn)
- [4. Kiểm tra trạng thái repository](#4-kiểm-tra-trạng-thái-repository)
- [5. “Cài đặt” theo cơ chế hiện có — môi trường phát triển offline](#5-cài-đặt-theo-cơ-chế-hiện-có--môi-trường-phát-triển-offline)
- [6. Xem trước thủ công trên Linux Mint 22.3 (chưa kiểm chứng runtime)](#6-xem-trước-thủ-công-trên-linux-mint-223-chưa-kiểm-chứng-runtime)
- [7. Gỡ cài đặt / rollback bản xem trước](#7-gỡ-cài-đặt--rollback-bản-xem-trước)
- [8. Quy trình cài đặt hoàn chỉnh — kế hoạch chưa triển khai](#8-quy-trình-cài-đặt-hoàn-chỉnh--kế-hoạch-chưa-triển-khai)
- [9. Kiểm tra trạng thái sau cài & khắc phục sự cố](#9-kiểm-tra-trạng-thái-sau-cài--khắc-phục-sự-cố)

---

## 1. Kiểm tra môi trường

### 1.1 Trên máy sẽ dùng để thử theme (Linux Mint đích)

Chạy checklist chỉ-đọc chính thức của dự án trước:
[plan/09-verification-checklist.md](plan/09-verification-checklist.md).
Tối thiểu cần các lệnh sau (tất cả **chỉ đọc**, không `sudo`):

```bash
cat /etc/linuxmint/info
cat /etc/os-release
cinnamon --version
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
loginctl show-session "$XDG_SESSION_ID" -p Type -p Desktop 2>/dev/null
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface gtk-theme
gsettings get org.cinnamon.desktop.interface icon-theme
gsettings get org.cinnamon.desktop.interface cursor-theme
gsettings get org.cinnamon.desktop.wm.preferences theme
```

- **Thư mục làm việc:** bất kỳ (khuyến nghị thư mục home).
- **Kết quả mong đợi:** phiên bản đích của dự án là Linux Mint 22.3, Cinnamon 6.6.x.
  Nếu máy của bạn khác, vẫn chạy được phần offline (Mục 2–5) nhưng **không** nên
  áp dụng bản xem trước ở Mục 6 và phải ghi rõ phiên bản thật khi báo kết quả.
- ⚠️ **Chưa kiểm chứng runtime:** chính đội dự án cũng chưa có kết quả của checklist này
  (`verified_on_target: false` trong `design/tokens/00-meta.json`). Kết quả bạn dán vào
  `docs/verification/REPORT.md` chính là task T00 còn thiếu.

### 1.2 Trên máy phát triển (máy sẽ build/kiểm tra)

```bash
python3 --version
make --version | head -n 1
git --version
```

- **Kết quả mong đợi:** Python ≥ 3.11 (CI dùng 3.11). Dự án chỉ dùng thư viện chuẩn
  Python cho generator/lint/test; không cần cài thêm gói Python nào cho `make tokens-check`.
- Kiểm tra SCSS compiler (cần cho Mục 5.3 và cho test không bị skip):

```bash
python3 -c "import sass; print(sass.__version__)"   # libsass qua Python
command -v pysassc || true                          # hoặc binary pysassc
npx --no-install sass --version || true             # hoặc dart-sass qua npm
```

Nếu cả ba đều trống: làm tiếp Mục 2. Nếu đã có một trong hai compiler: bỏ qua Mục 2.

---

## 2. Chuẩn bị phụ thuộc (chỉ cho máy phát triển)

> Phần này **chỉ dành cho máy phát triển/CI**. Người dùng cuối trên Linux Mint
> **không** phải cài các công cụ này — khi đóng gói xong, CSS sẽ được sinh sẵn
> (nguyên tắc A8 trong [plan/02-architecture.md](plan/02-architecture.md)).
> Không bước nào cần `sudo` nếu dùng môi trường ảo Python hoặc thư mục dự án Node.

Chọn **một** trong hai SCSS compiler (dự án kiểm tra bằng cả hai, nhưng để làm việc
hằng ngày một compiler là đủ; thiếu compiler thì test liên quan sẽ *skip* chứ không fail):

**Cách A — libsass (compiler mà Linux Mint dùng để build theme, bằng chứng E18):**

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install libsass
python3 -c "import sass; print(sass.__version__)"
```

**Cách B — dart-sass (đúng phiên bản đã ghim trong `package.json`):**

```bash
npm install
npx --no-install sass --version
```

- **Thư mục làm việc:** thư mục gốc repository.
- **Kết quả mong đợi:** in ra phiên bản (ví dụ libsass `0.23.0`, dart-sass `1.77.8`).
- **Cảnh báo đã xác minh:** trên hệ thống có PEP 668, `pip install` trực tiếp có thể bị chặn;
  hãy dùng `.venv` như trên thay vì thêm cờ phá vỡ hệ thống hay dùng `sudo pip`.
- `node_modules/` và `.venv/` đã nằm trong `.gitignore`/quy ước loại trừ — không commit chúng.

---

## 3. Lấy mã nguồn

```bash
git clone https://github.com/ThuyLinh6/mintos-glass.git
cd mintos-glass
git status
git log --oneline -5
```

- **Thư mục làm việc sau bước này:** `mintos-glass/` — mọi lệnh về sau đều từ đây.
- **Kết quả mong đợi:** `On branch …` và `nothing to commit, working tree clean`
  nếu bạn chưa sửa gì. Nếu clone từ fork/nhánh khác, ghi lại `git branch --show-current`
  khi báo cáo kết quả.

---

## 4. Kiểm tra trạng thái repository

Mục đích: xác nhận bản checkout đầy đủ và file generated không lệch token,
**trước** khi biên dịch hay sao chép bất cứ thứ gì lên máy Mint.

```bash
make help
make tokens-check
python3 tools/lint/safety_paths.py
ls src/cinnamon/cinnamon.scss src/cinnamon/cinnamon-dark.scss \
   src/icons/MintOS-Glass/index.theme \
   src/wallpapers/mintos-glass-dark.svg
```

- ✅ **Đã xác minh offline.** Kết quả mong đợi (ghi lại tại thời điểm viết tài liệu):
  - `make tokens-check` → `OK — 6 file generated khớp token (lock bff2fa4379d3e277)`
    (mã lock sẽ đổi khi token đổi; điều quan trọng là dòng `OK`, không phải mã lock cụ thể).
  - safety → `OK safety-paths: không có chuỗi cấm trong mã thực thi`.
  - `ls` liệt kê đủ 4 đường dẫn, không có `No such file`.
- Nếu `tokens-check` thất bại: chạy `make tokens` để sinh lại, rồi chạy `make check`.
  Không sửa tay các tệp có tiêu đề `GENERATED — TUYỆT ĐỐI KHÔNG SỬA TAY`.
- Kiểm tra điều **chưa** có (để không hiểu nhầm trạng thái):

```bash
ls src/gtk-3.0/sass/gtk.scss tools/cli tools/build dist 2>&1
```

Kết quả mong đợi hiện tại: cả bốn đều báo `No such file or directory`.
Đây là **trạng thái đúng của dự án** (QA-09/QA-11), không phải lỗi checkout của bạn.

---

## 5. “Cài đặt” theo cơ chế hiện có — môi trường phát triển offline

Chưa có bước cài lên hệ thống ở giai đoạn này. “Cài đặt” hôm nay nghĩa là:
sinh stylesheet từ token, chạy toàn bộ kiểm tra Tầng 1 và biên dịch thử theme Cinnamon
ra một tệp CSS trong `/tmp` để kiểm chứng. Không ghi gì ngoài repository và `/tmp`.

### 5.1 Sinh stylesheet từ design token

```bash
make tokens
make tokens-check
make report
```

- ✅ **Đã xác minh offline.** `make tokens` sinh/cập nhật: `src/cinnamon/tokens/_tokens.scss`,
  `src/gtk-3.0/sass/_tokens.scss`, `src/gtk-4.0/sass/_tokens.scss`,
  `src/libadwaita/tokens.css`, `docs/design-system/tokens.md`, `design/tokens.lock.json`.
- `make report` in toàn bộ token đã phân giải + bảng contrast (các dòng `[PASS]`;
  dòng `[INFO] … role=decorative` là ghi chú có chủ đích, không phải lỗi).
- 4 token bị bỏ qua kèm `WARN BỎ QUA (chưa xác minh)` là hành vi đúng
  (`size.titlebar-height`, `gtk.titlebar.height`, `font.family`, `font.size-base-pt`)
  — chúng chỉ được bật sau khi đo trên máy thật.

### 5.2 Chạy kiểm tra Tầng 1

```bash
make check
python3 tools/lint/st_properties.py
python3 tools/lint/icon_theme.py
python3 tools/lint/wallpapers.py
python3 tools/lint/assets.py
python3 tools/lint/nemo_selectors.py
python3 tools/lint/css_sanity.py; echo "css_sanity exit=$?"
```

- ✅ **Đã xác minh offline** (với SCSS compiler đã cài ở Mục 2):
  `make check` → `Ran 361 tests … OK` và `OK — make check xanh`;
  5 lint đầu đều `OK — 0 lỗi` (`st_properties` còn xác nhận phủ 527/527 selector gốc,
  15 `url()` asset hiệu lực).
- ⚠️ `css_sanity.py` hiện **báo FAIL có chủ đích** (lỗi thật QA-03/QA-05…QA-08/QA-10 đã đăng ký).
  Đừng coi FAIL này là do bạn cài sai; chi tiết ở `tests/fixtures/qa-bug-register.txt`.
  Cũng đừng “sửa cho xanh” bằng cách gỡ lint.
- Nếu output là `OK (skipped=…)` với số skip lớn: bạn đang thiếu SCSS compiler (Mục 2).
  Trong môi trường không compiler của dự án, 73/361 test bị skip. **Skip không phải PASS.**
- `make lint` hiện chỉ chạy `tokens-check` + `safety` (QA-12) — muốn kiểm đầy đủ hãy dùng
  `make check` và các lint liệt kê ở trên.

### 5.3 Biên dịch thử theme Cinnamon

`make scss` **không** dùng được cho việc này (nó chỉ in `TODO(T04): …`, QA-10).
Dùng một trong hai lệnh đã xác minh trực tiếp:

**Bằng libsass (Python, trong `.venv` đã kích hoạt):**

```bash
python3 -c "import sass; open('/tmp/mintos-glass-cinnamon.css','w').write(sass.compile(filename='src/cinnamon/cinnamon.scss'))"
wc -c /tmp/mintos-glass-cinnamon.css
```

**Bằng dart-sass:**

```bash
npx --no-install sass --no-source-map src/cinnamon/cinnamon.scss /tmp/mintos-glass-cinnamon-dart.css
wc -c /tmp/mintos-glass-cinnamon-dart.css
```

- ✅ **Đã xác minh offline.** Kết quả tại thời điểm viết: khoảng **94.349 byte** (libsass)
  và **92.705 byte** (dart-sass). Hai số khác nhau là bình thường (khác `output_style`
  mặc định — đã điều tra ở QA-N01, không phải build không ổn định).
  Dart-sass có thể in cảnh báo *deprecation* cho cú pháp `@import` cũ của vendor — đó là
  cảnh báo, không phải lỗi biên dịch, miễn là tệp CSS được tạo.
- Đây mới là **build kiểm chứng**, chưa phải đóng gói: chưa có thư mục theme hoàn chỉnh,
  chưa có `index.theme`, chưa có `gtk.css`. Xem [BUILD-AND-ISO.md](BUILD-AND-ISO.md).

---

## 6. Xem trước thủ công trên Linux Mint 22.3 (chưa kiểm chứng runtime)

> ⚠️ **Đọc kỹ trước khi làm.** Phần này lắp tay một bản xem trước **chỉ gồm theme
> Cinnamon + icon + wallpaper**. Nó **chưa từng được chạy trên Cinnamon thật** bởi đội dự án.
> Chỉ làm trên máy thử nghiệm/VM có snapshot. Không làm trên máy làm việc chính.
> Theme GTK, khung cửa sổ và app GTK sẽ **không** đổi giao diện Glass vì phần đó chưa có.
> Giao thức kiểm thử chính thức của dự án
> ([../tests/manual/PROTOCOL.md](../tests/manual/PROTOCOL.md) Mục 2) còn yêu cầu dừng lại
> ở bước này cho tới khi `dist/` tồn tại — bản xem trước dưới đây là lựa chọn của người
> thử nghiệm có kinh nghiệm, không phải bản cài đặt được hỗ trợ.

### 6.1 Điều kiện tiên quyết

- [ ] Đã chạy Mục 1.1 và ghi lại phiên bản Mint/Cinnamon/session thật.
- [ ] Đã chụp snapshot VM hoặc có cách khôi phục máy ngoài dự án (rollback của dự án chưa drill).
- [ ] Đã biên dịch `cinnamon.css` thành công ở Mục 5.3 trên máy phát triển
      (có thể chính là máy Mint này nếu bạn đã cài compiler phát triển trên nó —
      nhưng khuyến nghị biên dịch trên máy dev rồi chép sang).
- [ ] Đang đăng nhập bằng tài khoản người dùng thường. **Không dùng `sudo` ở bất kỳ bước nào.**

### 6.2 Chụp snapshot cấu hình hiện tại (bắt buộc, trước khi đổi bất cứ thứ gì)

```bash
mkdir -p ~/.local/state/mintos-glass
{
  echo "org.cinnamon.theme name=$(gsettings get org.cinnamon.theme name)"
  echo "org.cinnamon.desktop.interface gtk-theme=$(gsettings get org.cinnamon.desktop.interface gtk-theme)"
  echo "org.cinnamon.desktop.interface icon-theme=$(gsettings get org.cinnamon.desktop.interface icon-theme)"
  echo "org.cinnamon.desktop.interface cursor-theme=$(gsettings get org.cinnamon.desktop.interface cursor-theme)"
  echo "org.cinnamon.desktop.wm.preferences theme=$(gsettings get org.cinnamon.desktop.wm.preferences theme)"
  date -Is
} | tee ~/.local/state/mintos-glass/manual-snapshot.txt
cat ~/.local/state/mintos-glass/manual-snapshot.txt
```

- **Kết quả mong đợi:** 5 dòng giá trị hiện tại của **chính máy bạn** (thường là họ `Mint-Y…`,
  nhưng đừng giả định — giá trị trong tệp này mới là giá trị rollback của bạn).
- Các khoá trên nằm trong danh sách khoá đóng dự kiến của T12 và đã đối chiếu với
  `cinnamon-settings` upstream (E20), nhưng việc khôi phục bằng snapshot này
  ⚠️ **chưa kiểm chứng runtime**.
- Wallpaper hiện tại: mở `cinnamon-settings backgrounds` và **ghi tay** tên wallpaper đang dùng
  vào cuối tệp snapshot (dự án chưa xác minh khoá `gsettings` cho nền nên không tự ghi bằng lệnh).

### 6.3 Lắp thư mục theme Cinnamon trong thư mục người dùng

Từ thư mục gốc repository (thay đường dẫn tệp CSS nếu bạn biên dịch dart-sass):

```bash
mkdir -p ~/.local/share/themes/MintOS-Glass/cinnamon/assets
cp /tmp/mintos-glass-cinnamon.css ~/.local/share/themes/MintOS-Glass/cinnamon/cinnamon.css
cp src/cinnamon/assets/*.svg    ~/.local/share/themes/MintOS-Glass/cinnamon/assets/
find ~/.local/share/themes/MintOS-Glass -type f | sort
```

- **Kết quả mong đợi:** 1 tệp `cinnamon/cinnamon.css` + 15 tệp SVG trong `cinnamon/assets/`.
  Cấu trúc này suy ra từ cách St phân giải `url("assets/…")` tương đối với thư mục chứa
  `cinnamon.css` (đã kiểm bằng lint `st_properties`: 15 `url()` hiệu lực đều resolve) —
  ⚠️ nhưng chưa được Cinnamon thật nạp thử.
- Chỉ tạo đúng cây thư mục trên. Không chép gì vào `/usr/share/themes`, không chép
  `src/gtk-*` (chưa có `gtk.css` để chép), không tạo `index.theme` giả.

### 6.4 Cài icon theme và wallpaper (sao chép tệp, chưa áp dụng)

```bash
mkdir -p ~/.local/share/icons
cp -r src/icons/MintOS-Glass ~/.local/share/icons/MintOS-Glass
gtk-update-icon-cache ~/.local/share/icons/MintOS-Glass
mkdir -p ~/Pictures/mintos-glass-wallpapers
cp src/wallpapers/mintos-glass-dark.svg \
   src/wallpapers/mintos-glass-dark-calm.svg \
   src/wallpapers/mintos-glass-dark-glass.svg \
   src/wallpapers/mintos-glass-dark-mesh.svg \
   ~/Pictures/mintos-glass-wallpapers/
ls ~/.local/share/icons/MintOS-Glass/index.theme ~/Pictures/mintos-glass-wallpapers/
```

- Lệnh `gtk-update-icon-cache` theo protocol của dự án; nó chỉ ghi cache trong thư mục
  icon của bạn. ⚠️ Chưa kiểm chứng runtime trên Mint 22.3.
- Lưu ý phạm vi: đường dẫn `~/.local/share/icons/` là vị trí chuẩn của icon theme người dùng
  (protocol Mục 2 dùng đường dẫn này), nằm **ngoài** hai đường dẫn trong nguyên tắc an toàn
  gốc — cần được T12 chính thức hoá khi viết trình cài đặt.

### 6.5 Áp dụng giao diện

Ưu tiên dùng giao diện Settings để thấy rõ tên theme máy bạn thực sự nhận diện:

1. Mở `cinnamon-settings themes` (hoặc `cinnamon-settings backgrounds` cho wallpaper).
2. Ghi lại: theme `MintOS-Glass` có xuất hiện ở mục Cinnamon hay không.
   - Nếu **không xuất hiện**: dừng lại, đừng ép bằng `gsettings`. Ghi `BLOCKED` kèm
     output `ls -R ~/.local/share/themes/MintOS-Glass` và chuyển sang Mục 7 (xoá bản xem trước).
   - Phần GTK của bộ chọn **sẽ không** có MintOS-Glass đúng nghĩa — đó là trạng thái
     đã biết (thiếu `gtk-3.0/gtk.css`, QA-09), không phải lỗi thao tác.
3. Chọn `MintOS-Glass` cho theme Cinnamon; chọn `MintOS-Glass` cho icon theme;
   chọn một tệp trong `~/Pictures/mintos-glass-wallpapers/` làm nền.
4. Đăng xuất và đăng nhập lại (cách an toàn nhất để shell nạp lại theme; tránh dùng
   `cinnamon --replace` khi chưa có người kiểm chứng quy trình trên máy của bạn).

Đường lệnh tương đương (chỉ khi Settings đã liệt kê được theme; **không** đặt `gtk-theme`):

```bash
gsettings set org.cinnamon.theme name "MintOS-Glass"
gsettings set org.cinnamon.desktop.interface icon-theme "MintOS-Glass"
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface icon-theme
```

- ⚠️ **Chưa kiểm chứng runtime.** Tên `MintOS-Glass` khớp `theme_dir_name` trong
  `design/tokens/00-meta.json` và tên thư mục ở 6.3; khoá `org.cinnamon.theme name`
  và `icon-theme` đã đối chiếu upstream (E20). Không có bằng chứng chúng hoạt động
  trên máy đích cho tới khi có kết quả T00/PROTOCOL.
- **Không** chạy `gsettings set org.cinnamon.desktop.interface gtk-theme "MintOS-Glass"`:
  theme GTK chưa tồn tại, làm vậy chỉ tạo trạng thái cấu hình trỏ tới theme thiếu tệp.
- Dock trong panel (tuỳ chọn): làm theo [../src/dock/gwl/panel-layout.md](../src/dock/gwl/panel-layout.md)
  sau khi theme Cinnamon đã nạp. Không có hiệu ứng phóng to icon khi rê chuột.

### 6.6 Xác minh kết quả bản xem trước

Chỉ đọc, không `sudo`:

```bash
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface gtk-theme
gsettings get org.cinnamon.desktop.interface icon-theme
ls ~/.local/share/themes/ ~/.local/share/icons/
journalctl --user -b | grep -iE 'cinnamon|st_theme|croco|css' | tail -50
```

- **Đạt (ở mức quan sát):** desktop đăng nhập lại được, panel/menu mở bình thường,
  log không có `There was some problem parsing the theme`, `Did not find color property`
  hay `Unrecognized`. Đây là các chuỗi lỗi thật được protocol dùng (Mục P1/P2) —
  ⚠️ vẫn phải có ảnh chụp 26 bối cảnh theo `tests/manual/screenshot-matrix.csv`
  mới được gọi là kiểm thử Tầng 2.
- **Không đạt / nghi ngờ:** làm ngay Mục 7, giữ nguyên output log để báo bug.
  Không thử “sửa” bằng cách chép tệp vào đường dẫn hệ thống.

---

## 7. Gỡ cài đặt / rollback bản xem trước

> ⚠️ Trình tự này là rollback **thủ công (Cấp 2)**, viết từ protocol và mã nguồn upstream,
> **chưa được drill** (tiêu chí R1/R3–R5/R7 đang BLOCKED). Lệnh rollback tự động
> `python3 -m tools.cli.mintos_glass rollback` **chưa tồn tại** — đừng chạy.
> Thứ tự rất quan trọng: **đặt lại `gsettings` trước, xoá thư mục sau**, để không
> bao giờ cấu hình trỏ tới theme đã bị xoá (protocol R5).

### 7.1 Khôi phục bằng giao diện (khuyến nghị)

1. Mở `cinnamon-settings themes`, chọn lại đúng theme Cinnamon và icon theme đã ghi
   trong `~/.local/state/mintos-glass/manual-snapshot.txt`.
2. Mở `cinnamon-settings backgrounds`, chọn lại wallpaper cũ đã ghi ở Mục 6.2.
3. Đăng xuất/đăng nhập lại, xác nhận desktop bình thường.
4. Chỉ sau đó mới xoá tệp đã chép (Mục 7.3).

### 7.2 Khôi phục bằng lệnh (khi không dùng được giao diện)

Mở `~/.local/state/mintos-glass/manual-snapshot.txt`, thay `<giá-trị-cũ>` bằng
**giá trị của chính máy bạn** (giữ nguyên dấu nháy đơn nếu có trong output `get` thì
bỏ dấu nháy khi `set` theo cú pháp `gsettings` thông thường — hãy đối chiếu từng dòng):

```bash
gsettings set org.cinnamon.theme name "<giá-trị-cũ>"
gsettings set org.cinnamon.desktop.interface icon-theme "<giá-trị-cũ>"
# Chỉ đặt lại gtk-theme / wm theme NẾU bạn đã từng đổi chúng (bản xem trước không đổi):
# gsettings set org.cinnamon.desktop.interface gtk-theme "<giá-trị-cũ>"
# gsettings set org.cinnamon.desktop.wm.preferences theme "<giá-trị-cũ>"
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface icon-theme
```

Sau đó đăng xuất/đăng nhập lại. Nếu desktop gặp sự cố không vào được giao diện,
khôi phục từ snapshot VM (điều kiện tiên quyết ở 6.1) — dự án chưa có cơ chế cứu hộ
đã kiểm chứng cho trường hợp này, và tài liệu không bịa ra một cơ chế như vậy.

### 7.3 Xoá tệp của bản xem trước

Chỉ chạy **sau** 7.1 hoặc 7.2 và sau khi đăng nhập lại thành công:

```bash
rm -rf ~/.local/share/themes/MintOS-Glass
rm -rf ~/.local/share/icons/MintOS-Glass
rm -rf ~/Pictures/mintos-glass-wallpapers
ls ~/.local/share/themes/ ~/.local/share/icons/
```

- Giữ lại `~/.local/state/mintos-glass/manual-snapshot.txt` cho tới khi chắc chắn
  không cần khôi phục nữa; xoá nó là xoá bằng chứng rollback của lần thử.
- Kiểm tra không còn dấu vết: hai lệnh `gsettings get` ở 7.2 phải trả về giá trị cũ,
  và `ls` không còn thư mục `MintOS-Glass`. Đây mới là điều kiện “gỡ sạch” ở mức thủ công;
  tiêu chí tự động R1/R2 vẫn chưa được xác minh.

---

## 8. Quy trình cài đặt hoàn chỉnh — kế hoạch chưa triển khai

Phần này mô tả đích đến để người đóng góp biết việc còn thiếu. **Không lệnh nào
dưới đây chạy được hôm nay**; chúng là thiết kế của task T12/T14 trong
[plan/04-work-breakdown.md](plan/04-work-breakdown.md), chưa phải hướng dẫn sử dụng.

Dự kiến trình cài đặt (`tools/cli/mintos_glass/`, Python stdlib) sẽ có các lệnh
`probe | install | apply | rollback | uninstall | status | selftest` với các ràng buộc cứng:

1. Chỉ ghi vào `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`
   (cần bổ sung chính thức đường dẫn icon), không `sudo`/`apt`/`dpkg`, có `--dry-run`.
2. Snapshot toàn bộ khoá sẽ đổi vào `~/.local/state/mintos-glass/snapshot-<UTC>.json`
   **trước** khi đổi bất kỳ khoá nào; chỉ chạm danh sách khoá đóng
   (`org.cinnamon.theme name`, `org.cinnamon.desktop.interface {gtk-theme, icon-theme,
   cursor-theme, gtk-color-scheme}`, `org.cinnamon.desktop.wm.preferences theme`).
3. `rollback` khôi phục đúng snapshot, xoá thư mục theme, chạy lại nhiều lần an toàn (idempotent).
4. `tools/build/assemble.py` lắp `dist/MintOS-Glass/` hoàn chỉnh (kèm `index.theme`,
   `cinnamon/cinnamon.css`, `gtk-3.0/gtk.css`…) để trình cài đặt chỉ sao chép nguyên cây.

Điều kiện để được coi là triển khai xong: T06/T08 (GTK + khung cửa sổ) hoàn thành,
`dist/` build tự động được, và rollback drill R1–R10 trong
[plan/07-acceptance-criteria.md](plan/07-acceptance-criteria.md) đạt trên máy Mint thật.
Chi tiết build/ISO: [BUILD-AND-ISO.md](BUILD-AND-ISO.md).

---

## 9. Kiểm tra trạng thái sau cài & khắc phục sự cố

### 9.1 Xác định trạng thái hiện tại (chỉ đọc)

```bash
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface gtk-theme
gsettings get org.cinnamon.desktop.interface icon-theme
ls -1 ~/.local/share/themes/ 2>/dev/null
ls -1 ~/.local/share/icons/ 2>/dev/null
test -f ~/.local/share/themes/MintOS-Glass/cinnamon/cinnamon.css && echo "cinnamon.css: có" || echo "cinnamon.css: KHÔNG có"
test -f dist/MintOS-Glass/gtk-3.0/gtk.css && echo "dist gtk.css: có" || echo "dist gtk.css: KHÔNG có (trạng thái đúng hiện tại)"
```

### 9.2 Sự cố thường gặp

| Triệu chứng | Nguyên nhân đã biết | Cách xử lý |
|---|---|---|
| `No module named tools.cli…` | CLI chưa triển khai (T12) | Không có lệnh tự động. Dùng quy trình thủ công Mục 6–7 hoặc chờ T12 |
| `make scss` xong mà không có tệp mới | Target là stub (QA-10) | Biên dịch thủ công theo Mục 5.3 |
| Test bị `skipped` hàng loạt | Thiếu SCSS compiler (QA-01 ở CI cũng vậy) | Cài compiler ở Mục 2 (máy dev), chạy lại `make check` |
| `css_sanity.py` FAIL | Lỗi thật đã đăng ký QA-03/QA-05… | Xem `tests/fixtures/qa-bug-register.txt`; không phải lỗi cài đặt |
| Theme GTK không hiện trong Settings | Thiếu `gtk-3.0/gtk.css` (QA-09/V2, E19) | Trạng thái hiện tại của dự án; đừng tạo `gtk.css` rỗng để “cho hiện” |
| Cinnamon báo lỗi parse theme | Cần log thật để chẩn đoán | Lưu `journalctl` (Mục 6.6), rollback Mục 7, báo bug kèm log + phiên bản Cinnamon |
| Icon chọn rồi mà không đổi | Cache icon / chưa đăng nhập lại | `gtk-update-icon-cache` (Mục 6.4) + đăng nhập lại; chưa khỏi thì giữ nguyên Mint-Y và báo kết quả BLOCKED |
| Wallpaper SVG không hiện | Đường vẽ nền SVG chưa xác minh; phụ thuộc loader SVG của gdk-pixbuf (protocol Mục 1) | Ghi kết quả `gdk-pixbuf-query-loaders \| grep -i svg` vào báo cáo; chọn lại wallpaper cũ |

### 9.3 Báo cáo kết quả thử nghiệm

Điền [plan/09-verification-checklist.md](plan/09-verification-checklist.md) và
[../tests/manual/PROTOCOL.md](../tests/manual/PROTOCOL.md): chép
`tests/manual/RESULTS-template.md` thành tệp kết quả có ngày + người chạy, ghi mức
bằng chứng (Static/Build/Runtime/Integration) cho từng tiêu chí. Không ghi `ĐẠT`
cho mục chỉ mới “trông có vẻ đúng”, và không tuyên bố rollback hoạt động nếu chưa
làm đủ trình tự Mục 7 trên máy thật.
