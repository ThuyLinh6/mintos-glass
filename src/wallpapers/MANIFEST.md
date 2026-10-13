# MANIFEST — Wallpaper MintOS Glass (T16)

**Owner:** Agent D (Visual/Assets) · **Task:** T16
**Thư mục:** `src/wallpapers/` · **4 tệp, tất cả SVG vector tự vẽ**
**Quy chuẩn:** `docs/design-system/wallpaper-spec.md`
**Xác minh bằng:** `tools/lint/wallpapers.py` · `tests/lint/test_wallpapers.py`

---

## 1. Danh sách 4 wallpaper

| Tệp | Điểm nhấn | Vùng sáng nhất (đo) | Nhãn desktop |
|---|---|---|---|
| `mintos-glass-dark.svg` | **mặc định.** Dải chéo ba bậc tối + một vầng mint ở góc dưới-trái | `#132d24` | **12.67:1** ✅ |
| `mintos-glass-dark-calm.svg` | thuần gradient dọc, **không** điểm sáng | `#121316` | **16.01:1** ✅ |
| `mintos-glass-dark-mesh.svg` | ba vầng mint/xanh chồng rất nhạt ở ba góc | `#0e211b` | **14.46:1** ✅ |
| `mintos-glass-dark-glass.svg` | hai dải chéo mô phỏng lớp kính | `#1c1e22` | **14.39:1** ✅ |

Cả bốn cùng một khung `1920 × 1080` với `preserveAspectRatio="xMidYMid slice"` nên
một tệp **phủ kín** màn hình ở mọi tỉ lệ và mọi độ phân giải, không để lại dải đen
và không cần bản render riêng cho 4K.

**Biến thể Light Glass: CHƯA có, có chủ đích.** Quyết định D-2 của dự án là
`dark_first` (token Light được định nghĩa và kiểm parity nhưng `emit:false`). Ship
wallpaper Light trước khi D-2 mở khoá sẽ là ship một thứ mà hệ token chưa bật, và
sẽ phải đo lại toàn bộ ràng buộc tương phản ở mục 3 cho nền sáng. Khi D-2 mở
khoá: thêm `mintos-glass-light*.svg`, và **đổi ngưỡng của bài
`desktop-label-contrast`** vì chữ sáng `#eeeeee` trên nền sáng sẽ không qua nổi —
đó là lúc phải bàn lại màu nhãn desktop với Agent 1 (màu này bị Nemo khoá, xem
mục 3).

---

## 2. Nguồn và giấy phép

| Thành phần | Nguồn | Giấy phép | Quyền phân phối |
|---|---|---|---|
| 4 tệp SVG | **Tự vẽ hoàn toàn** trong dự án này — chỉ có `<rect>`, `<path>` và `<linearGradient>`/`<radialGradient>` dựng từ toạ độ gốc | GPL-3.0-or-later (theo `LICENSE` của repo) | ✅ toàn quyền |
| Giá trị màu | `src/cinnamon/tokens/_tokens.scss` của chính repo | GPL-3.0-or-later | ✅ |
| Ảnh chụp, ảnh stock, ảnh AI, artwork tải về | **KHÔNG CÓ** | — | ✅ không có gì cần xin phép |
| Font nhúng, ảnh raster nhúng (`<image>`) | **KHÔNG CÓ** | — | ✅ |
| URL ngoài | **KHÔNG CÓ** | — | ✅ |

**Không có tài nguyên bên thứ ba nào trong `src/wallpapers/`.** Mọi hình là gradient
của các màu token trên các hình chữ nhật/đường thẳng tự đặt toạ độ. Nên không có
nghĩa vụ ghi công, không có rủi ro giấy phép, và không có gì phải gỡ khi cần.

Lint khoá điều này bằng ba bài: `no-external-refs` (không URL ngoài, không
`<image>`/`<script>`/`<use>`/`<filter>`), `colors-are-token-values` (mọi hex và mọi
`stop-opacity`/`fill-opacity` phải khớp một giá trị token), và `no-blur-claim`.

---

## 3. Vì sao nền tối là RÀNG BUỘC chứ không phải sở thích

Đây là phần quan trọng nhất của T16 và là chỗ T16 **đóng một vòng lặp mở từ T09**.

### 3.1 Màu nhãn icon desktop bị Nemo KHOÁ

T09 đã xác minh từ mã nguồn (ghi trong `docs/testing/nemo-checklist.md`):

- Nemo nạp `nemo-style-application.css` ở
  `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` (**600**), cao hơn theme (**200**).
- GTK 3.24 **không có `!important`** — đã kiểm: chuỗi "important" xuất hiện **0
  lần** trong `gtkcssparser.c`, `gtkcssprovider.c`, `gtkstylecascade.c` @ 3.24.42.
- Nên rule `.nemo-desktop.nemo-canvas-item` của Nemo **thắng tuyệt đối** trên
  desktop. Theme không đổi được màu nhãn.
- Token `$mg-nemo-desktop-label-text: #eeeeee` chính là giá trị Nemo đang dùng.

**Hệ quả:** nếu nhãn icon desktop không đọc được thì thứ **duy nhất** sửa được là
**nền phía sau nó**. Wallpaper không phải trang trí tuỳ ý — nó là một phần của
phương trình tương phản mà ta không điều chỉnh được vế kia. Đó là lý do ràng buộc
tương phản nằm trong lint của T16 chứ không phải trong tài liệu thiết kế.

### 3.2 Số đo trên wallpaper THẬT

Nhãn desktop là **chữ**, nên ngưỡng đúng là **4.5:1** (WCAG 1.4.3), không phải 3:1.
T16 trong plan chỉ đòi ≥ 3:1; ta đặt mục tiêu cao hơn vì vế kia của phương trình
bị khoá.

| Wallpaper | Vùng sáng nhất | `#eeeeee` trên đó | 4.5:1 | 7:1 (AAA) |
|---|---|---|---|---|
| `mintos-glass-dark-calm.svg` | `#121316` | **16.01:1** | ✅ | ✅ |
| `mintos-glass-dark-mesh.svg` | `#0e211b` | **14.46:1** | ✅ | ✅ |
| `mintos-glass-dark-glass.svg` | `#1c1e22` | **14.39:1** | ✅ | ✅ |
| `mintos-glass-dark.svg` | `#132d24` | **12.67:1** | ✅ | ✅ |

Cả bốn đều qua **cả** 4.5:1 lẫn 7:1. Bản mặc định thấp nhất (12.67:1) vì nó có
vầng mint đậm nhất — vẫn dư rất xa ngưỡng.

### 3.3 Nhãn ở trạng thái ĐÃ CHỌN — xác nhận lại kết luận của T09

T09 đo trên **ba mức chói mô hình** vì lúc đó chưa có wallpaper thật, và kết luận:
token `$mg-nemo-desktop-label-selected-text: #f5f5f5` **FAIL** (1.47 / 1.90 /
2.53:1), còn `$mg-text-on-accent: #0b0c0e` **PASS** (12.23 / 9.46 / 7.10:1) — nên
T09 đã vá stylesheet dùng `#0b0c0e`.

Đo lại trên **wallpaper thật** (chip = `rgba(61,220,151,0.8)` composite lên vùng
sáng nhất của từng wallpaper):

| Wallpaper | Chip sau composite | `#0b0c0e` (T09 đã vá) | `#f5f5f5` (token gốc) |
|---|---|---|---|
| `mintos-glass-dark-calm.svg` | `#34b47d` | **7.43:1** ✅ | **2.42:1** ❌ |
| `mintos-glass-dark-glass.svg` | `#36b680` | **7.60:1** ✅ | **2.36:1** ❌ |
| `mintos-glass-dark-mesh.svg` | `#34b77e` | **7.66:1** ✅ | **2.34:1** ❌ |
| `mintos-glass-dark.svg` | `#35b980` | **7.83:1** ✅ | **2.29:1** ❌ |

**Kết luận của T09 được xác nhận độc lập trên dữ liệu thật.** Bản vá `#0b0c0e`
đúng, và token `#f5f5f5` vẫn sai ở cả bốn nền (2.29–2.42:1, tức chưa bằng một nửa
ngưỡng 4.5:1). Vấn đề token này **vẫn mở với Agent 1** — T09 đã báo, T16 xác nhận
lại bằng số đo khác. Lint có bài `selected-label-contrast` sẽ **WARN** nếu một
wallpaper mới khiến `#f5f5f5` đạt ngưỡng, để kết luận này không âm thầm lỗi thời.

### 3.4 Cách tính "vùng sáng nhất" — và giới hạn của nó

Lint **không** lấy mẫu pixel (việc đó cần một bộ raster, mà ràng buộc của dự án là
**không yêu cầu người dùng cài thêm phần mềm**). Thay vào đó nó trích mọi cặp
`stop-color`/`stop-opacity` và `fill`/`fill-opacity` khỏi SVG, composite từng lớp
lên nền tối nhất, rồi lấy màu sáng nhất.

**Đây là xấp xỉ theo hướng AN TOÀN**, không phải đo pixel: nó bỏ qua hiệu ứng
nhiều lớp chồng đúng một chỗ (thực tế sẽ tối hơn hoặc bằng kết quả tính). Nên kết
quả **không bao giờ lạc quan hơn thực tế** — nếu chữ qua ngưỡng theo cách tính này
thì nó qua theo pixel thật.

Điều **chưa** được cách tính này bảo đảm: một wallpaper tương lai dùng `<pattern>`,
nhiều gradient chồng phức tạp, hoặc raster nhúng thì mô hình composite từng-lớp
có thể không còn đủ. Lint đã chặn `<image>`/`<filter>`/`<pattern>`-style complexity
qua bài `no-external-refs`, nhưng nếu bộ wallpaper mở rộng thì phải xét lại mô hình
này — đã ghi thành việc còn lại ở mục 6.

---

## 4. Vì sao không có blur, và không ngụ ý có blur

`mintos-glass-dark-glass.svg` có hai dải chéo mô phỏng **lớp kính**. Đó là
**gradient thuần**, không phải blur. Không có `<filter>`, không
`feGaussianBlur`, và MANIFEST không dùng chữ "blur" để mô tả hiệu ứng của tệp.

Hai lý do, cả hai đã xác minh ở T04:

1. `-blur` của St **có thật** trong `st-theme-node.c` (`:2132`), nhưng mỗi lần
   paint nó trả giá `blur_size` × (`g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()`
   + `cogl_texture_new_from_data()`), và cần `CLUTTER_FEATURE_SHADERS_GLSL`. Nên
   dự án **không ship** thứ phụ thuộc blur.
2. Yêu cầu của dự án nói rõ: không tuyên bố blur khi chỉ dùng độ trong suốt hoặc
   gradient. Wallpaper là chỗ dễ vi phạm nhất vì "glass" gợi đúng hiệu ứng đó.

Lint có bài `no-blur-claim` quét **nội dung** SVG (bỏ qua comment) và FAIL nếu thấy
`blur`/`feGaussianBlur`/`feDropShadow`.

---

## 5. Không xung đột với icon desktop

Yêu cầu 3.3 của T16: *"vùng giữa màn hình không có chi tiết gắt, điểm nhấn nằm
lệch khỏi khu vực icon"*.

Nemo/Cinnamon xếp icon desktop từ **góc trên-trái** đi xuống theo cột. Nên vùng cần
tránh là nửa trên bên trái. Lint có bài `accent-placement` kiểm toạ độ tâm
(`cx`,`cy`) của **mọi** `radialGradient` và WARN nếu tâm nằm trong vùng
`x < 0.55·W` **và** `y < 0.55·H`.

Đã có một lần WARN thật: `mintos-glass-dark-mesh.svg` đặt vầng đầu tiên ở
`(260,200)`. Đã dời sang `(400,700)` — vẫn lệch về trái để giữ bố cục ba góc,
nhưng xuống dưới vùng icon. **Bài `desktop-label-contrast` mới là trọng tài cuối**:
một điểm nhấn nằm trong vùng icon vẫn chấp nhận được nếu nó đủ mờ để chữ còn đọc
được (lúc đó vầng ở `(260,200)` đo 14.46:1, tức là qua). Dời đi là để bố cục tốt
hơn, không phải để chữa một lỗi tương phản.

Ngoài ra cả bốn wallpaper đều **không có chi tiết nào ở vùng giữa màn hình**: mọi
điểm nhấn là vầng sáng lớn, biên rất mềm (gradient tắt dần về `stop-opacity="0"`),
không có đường nét cứng, không có hoạ tiết lặp, không có chữ.

---

## 6. Trạng thái kiểm chứng

### ĐÃ kiểm chứng offline
Chạy `python3 tools/lint/wallpapers.py -v` và
`python3 -m unittest tests.lint.test_wallpapers`:

- 4 tệp parse được bằng `xml.etree`, thẻ gốc `<svg>` đúng namespace
- `viewBox="0 0 1920 1080"`, `width`/`height` khớp, `preserveAspectRatio="xMidYMid slice"`
- tên tệp khớp `mintos-glass-dark*` lowercase kebab-case
- không URL ngoài (khai báo `xmlns` được miễn), không
  `<script>`/`<image>`/`<filter>`/`<mask>`/`<clipPath>`/`<use>`/`<foreignObject>`
- không `blur`/`feGaussianBlur`/`feDropShadow` trong nội dung
- không `rgba()` — dùng hex + `stop-opacity`/`fill-opacity`
- mọi hex và mọi giá trị opacity tra ngược được về token
- nhãn desktop `#eeeeee` đạt ≥ 4.5:1 trên vùng sáng nhất của **cả bốn** nền
- nhãn đã-chọn `#0b0c0e` đạt ≥ 4.5:1 trên chip composite của **cả bốn** nền
- không điểm nhấn nào nằm trong vùng icon desktop
- MANIFEST khớp hai chiều với tệp trên đĩa, có đủ mục giấy phép / Light Glass / tự vẽ / desktop

### CHƯA kiểm chứng — cần Linux Mint 22.3 thật
Không có máy Mint nên **không xác nhận** và **không tuyên bố** đã xác nhận:

**MỘT PHẦN ĐÃ XÁC MINH TỪ MÃ NGUỒN** (không còn là ẩn số như bản nháp):

`linuxmint/Cinnamon` @ 6.6.9, `files/usr/share/cinnamon/cinnamon-settings/modules/cs_backgrounds.py`:

- Dòng **580-581**: `PixCache.get_pix()` lọc theo mimetype, chỉ nhận
  `mimetype.startswith("image/")`.
- Dòng **613-619**: có **nhánh riêng** cho SVG —
  `if mimetype in ("image/svg+xml", "image/avif", "image/jxl"):` rồi
  `GdkPixbuf.Pixbuf.new_from_file(filename)` để raster, kèm comment
  `# rasterize svg with Gdk-Pixbuf and convert to PIL Image`.
- Dòng **537**: có `parse_xml_backgrounds_list()`, tức Cinnamon **có** hỗ trợ danh
  sách nền kiểu `gnome-background-properties` XML — đây là đường đăng ký wallpaper
  cho agent đóng gói (T12/T14), không phải thứ T16 tự làm.

=> **ĐÃ xác minh:** Cinnamon Settings 6.6 có code xử lý SVG tường minh, nên
wallpaper SVG của T16 là lựa chọn **được upstream hỗ trợ**, không phải ta tự bịa ra
một định dạng mà hệ không hiểu. Ranh giới của kết luận này: đoạn code đó nằm trong
đường dựng **thumbnail** của trình chọn nền, và nó **phụ thuộc gdk-pixbuf có loader
SVG** (librsvg) — điều đó thì chưa kiểm trên máy thật.

Còn **chưa** kiểm chứng:

| Chưa kiểm chứng | Điều kiện để kiểm |
|---|---|
| Chính **desktop** có render SVG làm nền không (khác với thumbnail trong Settings) | Đoạn đã đọc chỉ chứng minh đường thumbnail. Đường vẽ nền thật đi qua cinnamon-desktop/muffin — **chưa đọc**, nên **không tuyên bố**. Kiểm bằng cách đặt làm nền rồi xem. |
| gdk-pixbuf trên Mint 22.3 có loader SVG không (cần librsvg) | `gdk-pixbuf-query-loaders` trên máy thật |
| Wallpaper có được **liệt kê** trong Settings → Backgrounds không, và phải đăng ký qua XML hay chỉ cần thả vào thư mục nền | Đã biết có `parse_xml_backgrounds_list()`; chưa biết đường nào áp dụng cho thư mục theme của ta |
| `preserveAspectRatio="xMidYMid slice"` có được tôn trọng khi compositor scale nền không | Thử trên màn 16:9, 16:10, 21:9 |
| Gradient tắt dần có bị **banding** (sọc bậc thang) trên màn thật không | Xem ở chế độ toàn màn, nền tối rất dễ lộ banding |
| Vầng mint có quá sáng dưới ánh sáng ban ngày không | Xem thực tế |
| Mô hình "vùng sáng nhất" ở mục 3.4 có đúng như pixel thật không | Chụp màn hình rồi lấy mẫu pixel so với số lint tính |

**Rủi ro còn lại lớn nhất** (đã thu hẹp sau khi đọc mã nguồn): đoạn SVG được
upstream xử lý là ở **đường thumbnail của trình chọn nền**, còn đường **vẽ nền thật**
thì chưa đọc mã. Nếu trên máy thật hoá ra desktop không render SVG, thì T16 cần
pipeline render ra PNG/JPEG — `render-png.sh` trong allow-list là chỗ mô tả pipeline
đó cho **agent đóng gói ISO**, chạy lúc build chứ **không** chạy trên máy người
dùng. Khi đó phải khai báo độ phân giải thật đã sinh ra, **không khai khống**.

---

## 7. Đóng gói — vị trí trên đĩa và ràng buộc cho agent đóng gói (T12/T14)

### 7.1 Thư mục đích

| Trong repo | Ghi chú |
|---|---|
| `src/wallpapers/*.svg` | 4 tệp SVG |
| `src/wallpapers/MANIFEST.md` | **không cần ship** — tài liệu nội bộ |

**Chưa xác minh thư mục đích đúng**, và **không tuyên bố** đã biết. Có hai khả
năng, và việc chọn thuộc T12:

1. Một thư mục nền hệ thống (cần root — **trái** với ADR-002 và với ràng buộc
   "không sửa file hệ thống").
2. Thư mục nền của người dùng, rồi đăng ký qua `gnome-background-properties` XML.
   Đã xác minh Cinnamon **có** `parse_xml_backgrounds_list()`
   (`cs_backgrounds.py:537`) nên đường XML là có thật.

Nếu chọn đường 2 thì mới đúng các ràng buộc của dự án. **T16 không tự quyết** vì
chưa đọc đủ mã để biết thư mục nào được quét ở mức người dùng.

### 7.2 Không có gì để render

Cả 4 tệp là SVG vector nên **không cần** pipeline raster, **không cần** công cụ ảnh
trên máy người dùng và trên máy build. Nếu kiểm chứng trên máy thật cho thấy
desktop không render SVG (xem mục 6 — đường vẽ nền thật **chưa** đọc mã), thì lúc
đó mới cần `render-png.sh`, và phải khai báo **độ phân giải thật đã sinh ra**,
không khai khống.

### 7.3 Hoàn tác

Xoá các tệp wallpaper đã chép, và gỡ mục đăng ký trong XML nếu có. Không package,
không schema, không file hệ thống.

### 7.4 Cập nhật

Thêm wallpaper mới: theo `docs/design-system/wallpaper-spec.md` mục 8. Ràng buộc
cứng: nền không vượt quá `#1c1e22`, và **phải chạy
`tools/lint/wallpapers.py -v` rồi ghi số đo vào MANIFEST.md** — vì nhãn icon desktop
bị Nemo khoá màu nên wallpaper là đòn bẩy tương phản duy nhất (mục 3.1).
Lint này **không cần compiler SCSS** nên chạy được trong pipeline build ISO.
