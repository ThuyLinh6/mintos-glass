# Benchmark hiệu năng — cách đo, ngưỡng, và số đã đo được

**Task:** T13 · **Owner:** Agent J (QA)
**Phạm vi:** 9 tiêu chí hiệu năng P1–P9 của `docs/plan/07-acceptance-criteria.md`
**Nguyên tắc:** đo bằng lệnh và ghi **số thô**. Không ghi "mượt", "nhanh", "có vẻ ổn".

> **Ranh giới quan trọng:** chỉ **P6, P7, P8** đo được offline. **P1–P5 và P9 bắt
> buộc phải có máy Linux Mint thật** — chúng đo hành vi của compositor và shell đang
> chạy, không có cách nào suy ra từ mã nguồn. Tệp này ghi sẵn cách đo để người có
> máy chạy, **không** suy diễn kết quả thay họ.

---

## 1. Số đã đo được trong đợt QA này (offline, trong sandbox)

Môi trường: sandbox Linux, `libsass 3.6.6` (Python), `dart-sass 1.77.8` (node).
**Không phải** máy Linux Mint 22.3 — nên các con số build dưới đây là chỉ dấu, không
phải cam kết về thời gian trên máy người dùng.

### 1.1 Thời gian biên dịch (liên quan P7)

`src/cinnamon/cinnamon.scss`, `output_style="expanded"`, 3 lần liên tiếp:

| Lần 1 | Lần 2 | Lần 3 | Trung vị |
|---|---|---|---|
| 40 ms | 41 ms | 46 ms | **41 ms** |

Đầu ra: **93 018 B (90.8 KB)**, **889 rule**.

Ngưỡng P7 là **≤ 60 s** cho toàn bộ build `src/` → `dist/`. Riêng phần SCSS Cinnamon
đã đo là 41 ms, tức thấp hơn ngưỡng **ba bậc độ lớn**. Nhưng:

> **P7 vẫn BLOCKED, không phải ĐẠT.** `make scss` hiện **không build gì cả** — thân
> target chỉ `echo` ra một dòng `TODO(T04): …` (bug **QA-10**). Nên chưa tồn tại một
> quy trình `src/` → `dist/` để mà đo. Con số 41 ms ở trên là đo **bằng lời gọi
> libsass trực tiếp**, không phải qua quy trình build của dự án. Ghi rõ sự khác biệt
> này để không ai chép 41 ms vào ô P7 rồi đánh dấu ĐẠT.

### 1.2 Kích thước (liên quan P6)

| Thành phần | Số tệp | Kích thước |
|---|---|---|
| `src/cinnamon/assets/` (asset St của T05) | 16 | 20.0 KB |
| `src/icons/MintOS-Glass/` (icon theme T15) | 124 | 108.0 KB |
| `src/wallpapers/` (wallpaper T16) | 5 | 21.1 KB |
| `cinnamon.css` đã biên dịch | 1 | **90.8 KB** |
| `src/cinnamon/vendor/` (SCSS nguồn, **không ship**) | 23 | 55.1 KB |

**Đối chiếu ngưỡng P6:**

| Ngưỡng | Giá trị | Kết quả |
|---|---|---|
| `cinnamon.css` ≤ 400 KB | 90.8 KB | ✅ **ĐẠT** (dư 4.4 lần) |
| `gtk.css` ≤ 500 KB | — | ⛔ **KHÔNG ĐO ĐƯỢC** — `src/gtk-3.0/sass/gtk.scss` chưa tồn tại (QA-09) |
| tổng `dist/` ≤ 8 MB | ~0.23 MB **ước tính thiếu** | ⚠️ **MỘT PHẦN** — xem ghi chú |

> Con số 0.23 MB là **CSS + asset + icon + wallpaper**, **chưa có** `gtk.css` và
> **chưa có** bất kỳ thứ gì T12/T14 sẽ thêm (tệp meta, cấu hình mặc định, tài liệu
> cài đặt). Nên nó là **cận dưới**, không phải số cuối. Không được chép vào ô P6
> như một kết quả hoàn tất — P6 phải đo trên `dist/` **thật** sau khi QA-09 và
> QA-10 được sửa.
>
> Điều đáng chú ý: bộ tài nguyên SVG-only này rất nhẹ. 124 icon chỉ 108 KB (~870 B
> mỗi icon) trong khi một icon theme raster nhiều kích thước thường nặng hàng chục
> MB. Đây là hệ quả trực tiếp của quyết định dùng `Type=Scalable` thay vì sinh
> raster 8 cỡ — và nó cũng là lý do ngưỡng 8 MB gần như không thể bị vượt.

### 1.3 Rào blur (P8) — ĐÃ ĐẠT, kiểm bằng thực nghiệm

Không chỉ đọc mã: đã **bơm thử** giá trị blur vượt trần vào bản sao in-memory của
primitives và gọi `check_blur_cap`.

| Thí nghiệm | Kết quả |
|---|---|
| `blur.MAX_ALLOWED` = 6, bơm `blur.none/sm/md/lg` = 99 | `check_blur_cap` trả về **8 lỗi** `blur vượt trần: … = 99 > MAX_ALLOWED 6` |
| Lần thử ĐẦU (sai): bơm 99 vào **mọi** key `blur.*` kể cả `MAX_ALLOWED` | trả về **0 lỗi** — vì trần cũng thành 99 nên không gì vượt nó |

> Lần thử đầu cho kết quả trông như "guard hỏng". **Nguyên nhân là test sai, không
> phải guard sai.** Đã ghi thành mục `QA-N02` trong
> `tests/fixtures/qa-bug-register.txt` để không ai "sửa" một guard đang hoạt động.
> Đây là ví dụ cụ thể vì sao một phép đo phải đi kèm mô tả **cách** đo.

Đồng thời đã xác minh **không có `-blur` nào trong CSS đã biên dịch**
(`tools/lint/st_properties.py --forbid-blur`, và `css_sanity.py` kiểm lại độc lập).
Lý do không ship blur đã xác minh ở T04: `-blur` có thật trong St
(`st-theme-node.c` khoảng dòng 2132) nhưng mỗi lần paint trả giá `blur_size` ×
(`g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()` + `cogl_texture_new_from_data()`)
và cần `CLUTTER_FEATURE_SHADERS_GLSL`.

---

## 2. Cách đo P1–P5 và P9 (BẮT BUỘC máy thật)

Chưa đo được. Ghi sẵn cách đo để kết quả giữa những lần chạy khác nhau so sánh được.

**Nguyên tắc chung cho mọi phép đo dưới đây:** phải đo **cả theme mặc định** làm
đường cơ sở trên **cùng một máy, cùng một phiên đăng nhập**. Một con số tuyệt đối
không có ý nghĩa; chỉ **chênh lệch so với theme mặc định** mới có ý nghĩa.

### P1 — hành vi redraw của shell

```
cinnamon-looking-glass      # mục Perf / inspector
journalctl -b --user | grep -iE 'cinnamon|muffin' | grep -iE 'warn|error'
```
Ghi: số cảnh báo/lỗi, có vòng lặp redraw bất thường không.
**So với:** cùng lệnh dưới theme mặc định.

### P2 — thời gian vào Scale với nhiều cửa sổ

Mở **10 cửa sổ** (cố định: 3 Nemo, 2 terminal, 2 trình duyệt, 1 Settings, 1 xed,
1 trình xem ảnh). Vào Scale. Đo bằng **quay màn hình 60 fps** rồi đếm frame từ lúc
bấm phím tắt tới lúc các thumbnail ổn định — không dùng cảm giác.
Ghi: số ms, và số fps quan sát được trong lúc animation.

### P3 — độ trễ popup

Với **mỗi** popup: menu ứng dụng, popup âm lượng, popup nguồn, popup mạng, lịch,
notification. Đo từ lúc bấm tới lúc popup hiện đầy đủ, bằng quay màn hình 60 fps.
Ghi thành bảng 6 dòng. Đây là chỗ dễ chủ quan nhất nên **bắt buộc** đo bằng frame.

### P4 — CPU

```
ps -o pid,pcpu,rss,comm -C cinnamon,muffin
```
Ghi hai trạng thái: (a) **khi nghỉ** 60 s không chạm chuột, lấy 5 mẫu cách nhau 10 s;
(b) **khi mở popup** âm lượng và giữ nó mở 30 s.
**So với:** cùng phép đo dưới theme mặc định. Chênh lệch khi nghỉ là con số quan
trọng nhất — một theme làm shell bận rộn khi không làm gì là lỗi thật.

### P5 — bộ nhớ

```
ps -o pid,rss,vsz,comm -C cinnamon,muffin
smem -P cinnamon -t      # nếu có
```
Ghi RSS trước khi áp theme và sau khi áp theme, **sau khi đăng nhập lại** (để loại
bộ nhớ tạm của phiên cũ).

### P9 — thời gian đăng nhập

Đo từ lúc nhập mật khẩu tới lúc panel và desktop icon hiện đủ, bằng quay màn hình.
Chạy **3 lần**, ghi cả ba và lấy trung vị. Một lần duy nhất không đủ vì lần đầu sau
khi đổi theme sẽ phải dựng lại cache icon.

> **Riêng P9 có một bước phải làm đúng thứ tự:** lần đăng nhập ĐẦU TIÊN sau khi cài
> icon theme sẽ chạy `gtk-update-icon-cache` ngầm hoặc dựng cache lần đầu, nên sẽ
> chậm hơn. Đo lần 1 và lần 2–3 **tách riêng** và ghi cả hai. Nếu chỉ ghi lần 1 rồi
> kết luận "chậm" thì sai; nếu chỉ ghi lần 3 rồi kết luận "nhanh" thì bỏ sót chi
> phí thật mà người dùng phải trả một lần.

---

## 3. Hai phép đo đặc thù cần chú ý

### 3.1 Nhãn icon desktop trên wallpaper (V10 + liên quan V7)

Đã đo **trước** bằng `tools/lint/contrast.py` trên 4 wallpaper thật của T16
(không phải trên mức chói mô hình):

| Wallpaper | Vùng sáng nhất | Nhãn `#eeeeee` trên đó |
|---|---|---|
| `mintos-glass-dark-calm.svg` | `#121316` | **16.01:1** |
| `mintos-glass-dark-mesh.svg` | `#0e211b` | **14.46:1** |
| `mintos-glass-dark-glass.svg` | `#1c1e22` | **14.39:1** |
| `mintos-glass-dark.svg` (mặc định) | `#132d24` | **12.67:1** |

Cả bốn qua ngưỡng 4.5:1 và cả 7:1 (AAA). **Nhưng đây là tính toán, không phải đo
trên ảnh thật** — mô hình "vùng sáng nhất" là xấp xỉ theo hướng an toàn (bỏ qua hiệu
ứng nhiều lớp chồng đúng một chỗ). V10 vẫn đòi **đo trên ảnh chụp thật** bằng công
cụ lấy mẫu màu, vì:

- compositor có thể áp thêm độ sáng/tương phản;
- wallpaper có thể bị scale/crop khác dự kiến (`preserveAspectRatio="xMidYMid slice"`);
- **chưa xác minh** desktop có render SVG làm nền không (mới chỉ đọc mã đường
  thumbnail trong `cs_backgrounds.py:613-619`).

Cách đo trên ảnh: chụp màn hình, dùng công cụ lấy mẫu màu đọc giá trị RGB tại (a)
vùng nền ngay cạnh chữ nhãn và (b) chính chữ nhãn, rồi tính tỉ lệ tương phản từ hai
giá trị đó. **Không** ước lượng bằng mắt.

### 3.2 Icon ở kích thước nhỏ (V13 + F14)

Rủi ro đã biết và **chưa kiểm được**: bộ icon dùng lưới 24×24 với nét 1.4–1.8. Khi
GTK yêu cầu 16 px, hệ số scale là 0.667 nên nét 1.4 còn ~0.93 px — sát ngưỡng mất
nét. Đây là lý do tập icon giữ hình đơn giản.

Cách đo: chụp cùng một nhóm icon ở **16 / 22 / 24 / 32 / 48 px** (đổi icon size
trong Nemo và trong Settings), soi ở 100% **không phóng to ảnh**, và ghi nhận icon
nào mất chi tiết. So sánh trực tiếp với Mint-Y ở cùng kích thước — nếu Mint-Y rõ hơn
ở 16 px thì đó là một phát hiện cần ghi, kèm ảnh đối chiếu.

---

## 4. Bảng tóm tắt trạng thái

| ID | Ngưỡng | Đã đo? | Kết quả | Còn thiếu gì |
|---|---|---|---|---|
| **P1** | không có vòng lặp redraw bất thường | ❌ | — | máy thật |
| **P2** | không chậm hơn theme mặc định một cách thấy được | ❌ | — | máy thật + quay 60 fps |
| **P3** | như P2, cho 6 loại popup | ❌ | — | máy thật + quay 60 fps |
| **P4** | CPU khi nghỉ không tăng | ❌ | — | máy thật, cần cả đường cơ sở |
| **P5** | ghi số, chưa cam kết ngưỡng | ❌ | — | máy thật |
| **P6** | cinnamon.css ≤400KB · gtk.css ≤500KB · dist ≤8MB | ✅ một phần | 90.8 KB **ĐẠT**; hai mục kia **không đo được** | `gtk.scss` (QA-09) và `dist/` thật (QA-10) |
| **P7** | build ≤ 60 s | ⛔ **BLOCKED** | 41 ms là đo libsass trực tiếp, **không phải** qua quy trình build | `make scss` phải build thật (QA-10) |
| **P8** | không `-blur` trên bề mặt >600×400; generator từ chối token vi phạm | ✅ | **ĐẠT** — `check_blur_cap` trả 8 lỗi khi bơm blur=99; 0 `-blur` trong CSS | — |
| **P9** | ghi số, chưa cam kết ngưỡng | ❌ | — | máy thật, 3 lần đăng nhập |

**Kết luận phần hiệu năng:** 1 ĐẠT (P8) · 1 MỘT PHẦN (P6) · 1 BLOCKED (P7) ·
6 CHƯA ĐO (P1–P5, P9). Không có mục nào được đánh ĐẠT dựa trên suy luận.
