# Quy chuẩn wallpaper — MintOS Glass

**Task:** T16 · **Owner:** Agent D (Visual/Assets)
**Phạm vi:** `src/wallpapers/**` · inventory + giấy phép ở `src/wallpapers/MANIFEST.md`
**Token:** `src/cinnamon/tokens/_tokens.scss` (read-only với T16)
**Kiểm chứng:** `tools/lint/wallpapers.py`, `tests/lint/test_wallpapers.py`

> Không tạo ra bảng màu thứ hai: mọi giá trị trong tài liệu này đều là token sẵn
> có của Agent Design Systems, kèm tên token để tra ngược. Cần giá trị chưa có thì
> **mở issue cho Agent B**.

---

## 1. Định dạng: SVG vector tự vẽ

| Quyết định | Lý do |
|---|---|
| **SVG, không raster** | Scale vô hạn nên **một tệp phục vụ mọi độ phân giải** — không cần bản 1080p/1440p/4K riêng. Sinh raster sẽ đòi một công cụ ảnh trên máy người dùng, vi phạm ràng buộc "không yêu cầu cài thêm phần mềm". |
| **Tự vẽ, không tải về** | Không có ảnh stock, ảnh chụp, ảnh AI hay artwork bên thứ ba nào trong `src/wallpapers/`. Nên không có nghĩa vụ ghi công, không rủi ro giấy phép, không có gì phải gỡ. |
| **Không URL ngoài** | Yêu cầu 3.2/3.4 của Agent 5: tài nguyên nằm trong repo, ship cùng dự án, không nhúng URL bên ngoài. Lint khoá bằng `no-external-refs`. |
| **Chỉ `<rect>`, `<path>`, `<linearGradient>`, `<radialGradient>`** | Tập thẻ tối thiểu mà librsvg hỗ trợ ổn định. Không `<filter>`, `<mask>`, `<clipPath>`, `<pattern>`, `<image>`, `<use>` — mỗi thẻ thêm một chỗ kết quả có thể khác nhau giữa phiên bản. |

### Đã xác minh upstream có hỗ trợ SVG

`linuxmint/Cinnamon` @ 6.6.9,
`files/usr/share/cinnamon/cinnamon-settings/modules/cs_backgrounds.py`:

- `:580-581` — `PixCache.get_pix()` lọc theo mimetype, chỉ nhận `image/*`
- `:613-619` — có **nhánh riêng** cho SVG:
  `if mimetype in ("image/svg+xml", "image/avif", "image/jxl"):` rồi
  `GdkPixbuf.Pixbuf.new_from_file(filename)`, kèm comment
  `# rasterize svg with Gdk-Pixbuf and convert to PIL Image`
- `:537` — có `parse_xml_backgrounds_list()`, tức Cinnamon hỗ trợ danh sách nền
  kiểu `gnome-background-properties` XML

**Ranh giới của kết luận này:** đoạn đó nằm trong đường dựng **thumbnail** của
trình chọn nền, và phụ thuộc **gdk-pixbuf có loader SVG**. Đường **vẽ nền thật**
(cinnamon-desktop/muffin) thì **chưa đọc mã**, nên **không tuyên bố**. Ghi thành
mục chưa kiểm chứng trong `MANIFEST.md` mục 6.

---

## 2. Khung hình

| Thuộc tính | Giá trị | Ghi chú |
|---|---|---|
| `viewBox` | `0 0 1920 1080` | 16:9 làm khung thiết kế |
| `width` / `height` | `1920` / `1080` | khớp viewBox |
| `preserveAspectRatio` | **`xMidYMid slice`** | **PHỦ KÍN**, cắt phần thừa |

**`slice` là chỗ wallpaper cố ý KHÁC quy ước icon.** Icon phải dùng mặc định
(`meet`) để không bao giờ bị cắt — cắt icon là mất thông tin. Wallpaper thì ngược
lại: thà cắt bớt mép còn hơn để lại **dải đen** trên màn 16:10 hoặc 21:9. Vì bố
cục wallpaper đối xứng và điểm nhấn nằm lệch (mục 4), cắt mép không phá thiết kế.

Consequence cần nhớ khi thêm wallpaper mới: **không đặt chi tiết quan trọng sát
mép**, vì `slice` sẽ cắt nó trên màn khác tỉ lệ.

---

## 3. Bảng màu

Chỉ dùng các bậc tối nhất của thang gray, cộng accent ở opacity rất nhỏ.

| Vai trò | Token | Hex |
|---|---|---|
| Nền tối nhất | `$mg-surface-sunken` (= `$mg-color-gray-950`) | `#0b0c0e` |
| Nền giữa | `$mg-surface-base` (= `$mg-color-gray-900`) | `#121316` |
| Nền sáng nhất được phép | `$mg-surface-solid` (= `$mg-color-gray-850`) | `#17181c` |
| Mép trên của dải (chỉ biến thể glass) | `$mg-color-gray-800` | `#1c1e22` |
| Vầng sáng chính | `$mg-status-accent` (= `$mg-color-mint-500`) | `#3ddc97` |
| Vầng sáng phụ | `$mg-color-mint-400` / `$mg-color-mint-700` | `#6ee7bd` / `#1f8f5f` |
| Vầng lạnh (chỉ biến thể mesh) | `$mg-color-blue-500` | `#3b9dff` |

Opacity **chỉ** được lấy từ alpha có sẵn trong token: `$mg-status-accent-subtle`
(0.16), `$mg-border-hairline` (0.08), `$mg-surface-hover` (0.07), cộng `0` và `1`
cho hai đầu gradient. Lint bài `colors-are-token-values` đối chiếu cả hex lẫn
opacity.

**Không dùng `rgba()` trong SVG** — librsvg hỗ trợ `rgba()` trong presentation
attribute không nhất quán giữa các phiên bản. Dùng hex + `stop-opacity` /
`fill-opacity`. Cùng ràng buộc đã áp dụng cho asset T05.

**Trần độ sáng là ràng buộc, không phải gợi ý.** Màu nền sáng nhất được phép là
`#1c1e22`. Lý do ở mục 5: nhãn icon desktop bị Nemo khoá màu nên nền là đòn bẩy
duy nhất.

---

## 4. Bố cục

1. **Vùng giữa màn hình không có chi tiết nào.** Chỉ có gradient nền.
2. **Điểm nhấn nằm lệch**, và **không nằm trong vùng icon desktop**. Nemo/Cinnamon
   xếp icon từ **góc trên-trái** đi xuống theo cột, nên vùng cần tránh là
   `x < 0.55·W` **và** `y < 0.55·H`. Lint có bài `accent-placement` kiểm toạ độ
   tâm (`cx`,`cy`) của **mọi** `radialGradient` và WARN nếu tâm rơi vào vùng đó.
3. **Mọi điểm nhấn là vầng sáng lớn, biên rất mềm** — gradient tắt dần về
   `stop-opacity="0"`. Không đường nét cứng, không hoạ tiết lặp, không chữ, không
   logo.
4. **Không có gì sát mép** — xem mục 2 về `slice`.

Đã có một lần WARN thật trong quá trình làm: `mintos-glass-dark-mesh.svg` đặt vầng
đầu tiên ở `(260,200)`. Đã dời sang `(400,700)`. Lưu ý đó **không phải** lỗi
tương phản (lúc đó vẫn đo 14.46:1) mà là bố cục — dời đi để vùng icon sạch hơn.

### Bốn biến thể và mục đích của từng cái

| Biến thể | Điểm nhấn | Dùng khi nào |
|---|---|---|
| `mintos-glass-dark.svg` | dải chéo ba bậc + vầng mint dưới-trái | **mặc định.** Cân bằng giữa nhận diện và độ êm |
| `mintos-glass-dark-calm.svg` | thuần gradient dọc, **không** điểm sáng | người dùng để nhiều icon desktop, màn hình nhỏ, hoặc cần nền tối đa trung tính |
| `mintos-glass-dark-mesh.svg` | ba vầng mint/xanh ở ba góc | muốn thấy rõ ngôn ngữ "glass" hơn |
| `mintos-glass-dark-glass.svg` | hai dải chéo mô phỏng lớp kính | muốn nhận diện thương hiệu mạnh nhất |

Thứ tự tăng dần về độ hiện diện của thương hiệu cũng là thứ tự **giảm dần** về
tương phản nhãn desktop (16.01 → 12.67:1). Cả bốn đều qua xa ngưỡng nên đây chỉ là
ghi chú để chọn, không phải cảnh báo.

---

## 5. Ràng buộc tương phản — phần quan trọng nhất

### 5.1 Vì sao wallpaper gánh ràng buộc này

T09 đã xác minh từ mã nguồn (ghi trong `docs/testing/nemo-checklist.md`):

- Nemo nạp `nemo-style-application.css` ở
  `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` (**600**), cao hơn theme (**200**).
- GTK 3.24 **không có `!important`** — chuỗi "important" xuất hiện **0 lần** trong
  `gtkcssparser.c`, `gtkcssprovider.c`, `gtkstylecascade.c` @ 3.24.42.
- Nên `.nemo-desktop.nemo-canvas-item` của Nemo **thắng tuyệt đối** trên desktop:
  theme không đổi được màu nhãn icon.
- `$mg-nemo-desktop-label-text: #eeeeee` chính là giá trị Nemo đang dùng.

**Hệ quả:** vế "màu chữ" của phương trình tương phản bị khoá. Vế duy nhất còn sửa
được là **nền phía sau nó**. Nên ràng buộc tương phản của nhãn desktop thuộc về
wallpaper, và phải được đo trong lint của T16.

### 5.2 Ngưỡng

Nhãn desktop là **chữ** → ngưỡng đúng là **4.5:1** (WCAG 1.4.3), không phải 3:1
dành cho đối tượng đồ hoạ. T16 trong plan chỉ đòi ≥ 3:1; ta tự đặt cao hơn vì
không còn cách nào khác để cải thiện tỉ lệ.

### 5.3 Số đo thật

| Wallpaper | Vùng sáng nhất | `#eeeeee` trên đó | 4.5:1 | 7:1 |
|---|---|---|---|---|
| `mintos-glass-dark-calm.svg` | `#121316` | **16.01:1** | ✅ | ✅ |
| `mintos-glass-dark-mesh.svg` | `#0e211b` | **14.46:1** | ✅ | ✅ |
| `mintos-glass-dark-glass.svg` | `#1c1e22` | **14.39:1** | ✅ | ✅ |
| `mintos-glass-dark.svg` | `#132d24` | **12.67:1** | ✅ | ✅ |

### 5.4 Đóng vòng lặp mở từ T09

T09 đo trên **ba mức chói mô hình** vì lúc đó chưa có wallpaper thật, kết luận
token `$mg-nemo-desktop-label-selected-text: #f5f5f5` FAIL và vá stylesheet sang
`$mg-text-on-accent: #0b0c0e`. Đo lại trên wallpaper **thật**
(chip = `rgba(61,220,151,0.8)` composite lên vùng sáng nhất):

| Wallpaper | Chip | `#0b0c0e` (đã vá) | `#f5f5f5` (token gốc) |
|---|---|---|---|
| calm | `#34b47d` | **7.43:1** ✅ | **2.42:1** ❌ |
| glass | `#36b680` | **7.60:1** ✅ | **2.36:1** ❌ |
| mesh | `#34b77e` | **7.66:1** ✅ | **2.34:1** ❌ |
| dark | `#35b980` | **7.83:1** ✅ | **2.29:1** ❌ |

**Kết luận của T09 được xác nhận độc lập trên dữ liệu thật.** Vấn đề token
`#f5f5f5` **vẫn mở với Agent 1**. Lint có bài `selected-label-contrast` sẽ **WARN**
nếu một wallpaper mới khiến `#f5f5f5` đạt ngưỡng, để kết luận này không âm thầm
lỗi thời.

### 5.5 Cách tính "vùng sáng nhất" và giới hạn của nó

Lint **không lấy mẫu pixel** — việc đó cần một bộ raster, mà ràng buộc dự án là
không yêu cầu người dùng cài thêm phần mềm. Thay vào đó: trích mọi cặp
`stop-color`/`stop-opacity` và `fill`/`fill-opacity`, composite từng lớp lên nền tối
nhất, lấy màu sáng nhất.

**Đây là xấp xỉ theo hướng AN TOÀN**: nó bỏ qua hiệu ứng nhiều lớp chồng đúng một
chỗ, mà thực tế thì chồng lớp sẽ tối hơn hoặc bằng kết quả tính từng-lớp. Nên kết
quả **không bao giờ lạc quan hơn thực tế**.

`tests/lint/test_wallpapers.py::TestLuminanceModelIsConservative` khoá các tính chất
làm nên sự an toàn đó: composite khớp giá trị đã biết, contrast đối xứng và khớp
21:1 cho đen/trắng, luminance đúng thứ tự, vùng sáng nhất không bao giờ tối hơn
nền, và **`layers()` không bỏ sót lớp nào** (đếm ngược số `<stop>` + số `fill="#…"`
trong tệp rồi so). Bài cuối là bài quan trọng: nếu `layers()` bỏ sót một lớp sáng
thì mọi kết luận tương phản ở trên trở thành giả.

**Giới hạn phải xét lại nếu mở rộng:** mô hình này không còn đủ nếu wallpaper
dùng `<pattern>`, nhiều gradient chồng phức tạp, hoặc raster nhúng. Hiện đã chặn
các thẻ đó qua `no-external-refs`, nhưng thêm biến thể mới thì phải kiểm lại.

---

## 6. Không blur, và không ngụ ý có blur

`mintos-glass-dark-glass.svg` có hai dải chéo mô phỏng **lớp kính**. Đó là
**gradient thuần**. Không `<filter>`, không `feGaussianBlur`, và tài liệu không
dùng chữ "blur" để mô tả hiệu ứng của tệp.

Hai lý do, cả hai đã xác minh ở T04:

1. `-blur` của St **có thật** (`st-theme-node.c:2132`) nhưng mỗi lần paint trả giá
   `blur_size` × (`g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()` +
   `cogl_texture_new_from_data()`), và cần `CLUTTER_FEATURE_SHADERS_GLSL`. Dự án
   **không ship** thứ phụ thuộc blur.
2. Yêu cầu dự án: **không tuyên bố blur khi chỉ dùng độ trong suốt hoặc gradient**.
   Wallpaper là chỗ dễ vi phạm nhất vì chữ "glass" gợi đúng hiệu ứng đó.

Lint bài `no-blur-claim` quét **nội dung** SVG (bỏ qua comment giải thích) và FAIL
khi thấy `blur`/`feGaussianBlur`/`feDropShadow`.

Chiều sâu "glass" của MintOS Glass thuộc về **Cinnamon theme và GTK theme**
(gradient nền, `box-shadow`), không thuộc về wallpaper.

---

## 7. Biến thể Light Glass: chưa có, có chủ đích

Quyết định **D-2 = `dark_first`**: token Light được định nghĩa và kiểm parity
nhưng `emit:false`. Ship nền Light trước khi D-2 mở khoá là ship một thứ mà hệ
token chưa bật.

Khi D-2 mở khoá, việc cần làm **không chỉ là đổi màu**:

1. Thêm `mintos-glass-light*.svg`.
2. **Xét lại toàn bộ mục 5.** Chữ nhãn desktop `#eeeeee` trên nền sáng sẽ **không
   qua nổi** 4.5:1. Mà màu đó bị Nemo khoá, theme không đổi được. Nên nền Light sẽ
   cần một cơ chế khác (ví dụ Nemo có tuỳ chọn riêng, hoặc chấp nhận fallback),
   và việc đó phải bàn với Agent 1 + Agent F **trước khi** vẽ.
3. Lint hiện tại sẽ FAIL đúng như mong đợi — đừng hạ ngưỡng để cho qua.

---

## 8. Thêm wallpaper mới — quy trình

1. Chọn khung `1920 × 1080` + `preserveAspectRatio="xMidYMid slice"`.
2. Nền lấy từ ba bậc gray tối nhất (mục 3); **không** vượt quá `#1c1e22`.
3. Opacity chỉ lấy từ alpha có trong token.
4. Điểm nhấn đặt **ngoài** vùng `x < 0.55·W` và `y < 0.55·H`; không chi tiết sát mép.
5. Không `<filter>`/`<image>`/`<pattern>`, không `rgba()`, không blur.
6. Chạy `python3 tools/lint/wallpapers.py -v` và **ghi lại số đo vào MANIFEST.md**.
7. Thêm vào `EXPECTED` và các bảng `MEASURED_*` trong `tests/lint/test_wallpapers.py`
   — nếu không, test sẽ đỏ vì bộ wallpaper đã đổi.
8. Chạy `python3 -m unittest tests.lint.test_wallpapers`.

---

## 9. Việc còn lại

| Ưu tiên | Việc | Chặn bởi |
|---|---|---|
| **P4** | Xác minh trên máy thật: desktop có render SVG làm nền không (khác với thumbnail trong Settings) | cần máy Mint (T00) |
| **P4** | Kiểm **banding** của gradient trên màn thật — nền tối rất dễ lộ sọc bậc thang | cần máy Mint |
| **P4** | Quyết định đường đăng ký wallpaper cho ISO: thả vào thư mục nền hay dùng `gnome-background-properties` XML (`parse_xml_backgrounds_list()` đã xác minh là có tồn tại) | T12/T14 |
| — | Biến thể Light Glass | **D-2 chưa mở khoá** |
| — | Token `#f5f5f5` cho nhãn đã-chọn | **vẫn mở với Agent 1** — T16 đã xác nhận lại bằng số đo thật |

**Không nằm trong phạm vi T16:** chọn wallpaper lúc chạy (gsetting của
cinnamon-desktop, thuộc T12), và asset của Cinnamon theme (thuộc T05).
