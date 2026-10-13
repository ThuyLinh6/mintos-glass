# MANIFEST — tài nguyên SVG của Cinnamon theme (T05)

**Owner:** Agent D (Visual/Assets) · **Task:** T05
**Thư mục:** `src/cinnamon/assets/` · **15 tệp, tất cả SVG**
**Xác minh bằng:** `tools/lint/assets.py` và `tests/lint/test_assets.py`

> Tài liệu này là **bản tra ngược token ↔ literal**. St không đọc được SCSS token
> lúc runtime (SVG là tệp riêng, librsvg nạp và raster hoá độc lập, không có CSS
> variable), nên màu **bắt buộc** phải là literal trong tệp. Tiêu chí 3 của T05
> ("không SVG nào hard-code màu trùng token") được hiện thực thành: **mọi literal
> phải bằng đúng một giá trị token và phải được ghi ở đây**. `tools/lint/assets.py`
> bài `colors-are-token-values` kiểm tra bằng máy, tệp này cho người đọc tra ngược.
>
> `DOCUMENTED_EXCEPTIONS` trong lint đang **rỗng** — tức là không literal nào nằm
> ngoài hệ token. Đó là trạng thái cần giữ.

---

## 1. Bảng tra màu: literal → token

| Literal trong SVG | Token nguồn | Giá trị token |
|---|---|---|
| `#3ddc97` | `$mg-status-accent` (= `$mg-color-mint-500`) | `#3ddc97` |
| `#6ee7bd` | `$mg-status-accent-hover` (= `$mg-color-mint-400`) | `#6ee7bd` |
| `#0b0c0e` | `$mg-text-on-accent` (= `$mg-color-gray-950` = `$mg-surface-sunken`) | `#0b0c0e` |
| `#17181c` | `$mg-surface-solid` | `#17181c` |
| `#ffffff` | `$mg-color-gray-0`; đồng thời là bộ ba RGB của `$mg-border-control`, `$mg-border-subtle`, `$mg-surface-hover`, `$mg-surface-active`, `$mg-text-primary`, `$mg-text-secondary` | `#ffffff` |
| `#eceef1` | `$mg-color-gray-100` | `#eceef1` |
| `#ff5f57` | `$mg-status-error` | `#ff5f57` |

## 2. Bảng tra opacity: giá trị → token

Trong SVG dùng `fill-opacity` / `stroke-opacity` / `stop-opacity` thay vì
`rgba()`. Lý do ở mục 5.

| Giá trị | Token nguồn |
|---|---|
| `0.36` | alpha của `$mg-border-control` = `rgba(255,255,255,0.36)` |
| `0.12` | alpha của `$mg-border-subtle` = `rgba(255,255,255,0.12)`; **và** alpha của `$mg-surface-active` = `rgba(255,255,255,0.12)` |
| `0.07` | alpha của `$mg-surface-hover` = `rgba(255,255,255,0.07)` |
| `0.92` | alpha của `$mg-text-primary` = `rgba(255,255,255,0.92)` |
| `0.66` | alpha của `$mg-text-secondary` = `rgba(255,255,255,0.66)` |
| `0.16` | alpha của `$mg-status-accent-subtle` = `rgba(61,220,151,0.16)` |
| `0.55` | `$mg-opacity-glass-low` |
| `0` | đầu/cuối gradient (tắt hẳn) |

---

## 3. Danh sách 15 asset

Kích thước lấy từ **CSS đã biên dịch của T04** (`background-size: contain`), không
phải đoán. Cột "viewBox" là `width`/`height`/`viewBox` của tệp — cả ba phải trùng
nhau để 1 đơn vị SVG = 1px ở 1x, nhờ đó HiDPI scale sắc (tiêu chí 4 của T05).

| # | Tệp | viewBox | CSS khai báo | Selector dùng nó |
|---|---|---|---|---|
| 1 | `checkbox-off.svg` | 20×20 | `20px × 20px` | `.check-box StBin`, `.check-box:focus StBin`, `.check-box-2 StBin`, `.check-box-2:focus StBin` |
| 2 | `checkbox.svg` | 20×20 | `20px × 20px` | `:checked` và `:focus:checked` của cả `.check-box` lẫn `.check-box-2` |
| 3 | `radio-off.svg` | 20×20 | `20px × 20px` | `.radiobutton StBin`, `.radiobutton:focus StBin` |
| 4 | `radio.svg` | 20×20 | `20px × 20px` | `.radiobutton:checked StBin`, `.radiobutton:focus:checked StBin` |
| 5 | `toggle-off.svg` | 46×26 | `46px × 26px` | `.toggle-switch`, `.toggle-switch-us`, `.toggle-switch-intl` |
| 6 | `toggle-on.svg` | 46×26 | `46px × 26px` | `.toggle-switch:checked`, `-us:checked`, `-intl:checked` |
| 7 | `calendar-arrow-left.svg` | 16×16 | `16px × 16px` | `.calendar-change-month-back`, `.calendar-change-month-forward:rtl` |
| 8 | `calendar-arrow-left-hover.svg` | 16×16 | (kế thừa) | `:hover` của hai selector trên |
| 9 | `calendar-arrow-right.svg` | 16×16 | `16px × 16px` | `.calendar-change-month-forward`, `.calendar-change-month-back:rtl` |
| 10 | `calendar-arrow-right-hover.svg` | 16×16 | (kế thừa) | `:hover` của hai selector trên |
| 11 | `close.svg` | 24×24 | **`22px × 22px`** và **`26px × 26px`** | `.window-close` (22px), `.workspace-close-button` (26px) |
| 12 | `add-workspace.svg` | 35×200 | `35px × 200px` | `.workspace-add-button` |
| 13 | `add-workspace-hover.svg` | 35×200 | (kế thừa) | `.workspace-add-button:hover` |
| 14 | `trash-icon.svg` | 48×48 | **`48px × 48px`** | `.window-close-area` |
| 15 | `corner-ripple.svg` | 52×52 | `52px × 52px` | `.ripple-box`, `.ripple-box:rtl` |

**`close.svg` dùng chung cho hai kích thước (22px và 26px).** viewBox 24×24 vuông
nên `background-size: contain` scale về cả hai mà không méo. Không nhân đôi tệp chỉ
để khác 4px.

**`trash-icon.svg`:** rule vendor khai báo `400px × 120px` nhưng T04 đã override
thành `48px × 48px`. Lint chỉ so với rule **còn hiệu lực** (last-wins theo selector
đơn) — bản đầu của lint so với cả rule đã bị đè và báo FAIL giả. Đã sửa.

---

## 4. Quyết định thiết kế, kèm số ĐO

Toàn bộ đo bằng `tools/lint/contrast.py` của repo (WCAG relative luminance), ngưỡng
**3:1** cho đối tượng đồ hoạ (WCAG 1.4.11). Không đoán.

### 4.1 Glyph trên nền accent phải TỐI, không phải trắng

| Cặp màu | Tương phản | 3:1 |
|---|---|---|
| tick/knob `#0b0c0e` trên `#3ddc97` | **11.07:1** | ✅ PASS |
| tick/knob `#ffffff` trên `#3ddc97` | **1.77:1** | ❌ FAIL |

Áp dụng cho: dấu tick của `checkbox.svg`, chấm trong của `radio.svg`, knob của
`toggle-on.svg`.

**Đây là chỗ cố ý LỆCH khỏi macOS.** macOS dùng knob trắng trên nền xanh. Yêu cầu
dự án nói rõ: *"Không hy sinh tương phản/khả năng đọc để bắt chước giao diện
macOS."* Nên knob tối. Cùng tiền lệ đã chốt ở T02/T04 cho chip accent (trắng trên
mint `#2bb67a` = 2.60:1 FAIL → lật sang `text-on-accent` = 7.52:1 PASS).

### 4.2 Nút đóng: glyph tối trên nền `status-error`

| Cặp màu | Tương phản | 3:1 |
|---|---|---|
| ✕ `#0b0c0e` trên `#ff5f57` | **6.55:1** | ✅ PASS |
| ✕ `#ffffff` trên `#ff5f57` | **2.99:1** | ❌ FAIL (sát ngưỡng) |

Trắng hụt đúng 0.01 — không đủ để "làm tròn" bỏ qua. Dùng glyph tối.

### 4.3 `toggle-off.svg`: track dùng `surface-active`, knob dùng `gray-100`

Trạng thái TẮT phải trông **ì** hơn trạng thái BẬT nhưng vẫn phải thấy được cái
knob ở đâu. Track `rgba(255,255,255,0.12)` flatten trên `$mg-surface-solid`
`#17181c` cho `#333437`; knob `#eceef1` trên đó đo được tương phản cao, đủ để nhận
biết vị trí công tắc. Trạng thái BẬT đổi hẳn track sang accent nên hai trạng thái
phân biệt được **bằng màu chứ không chỉ bằng vị trí knob** — quan trọng với người
mù màu.

### 4.4 `trash-icon.svg` phải TỰ CHỨA nền

T04 **không** đặt `background-color` cho `.window-close-area` (chỉ đặt
`background-image` + `background-size: contain` + 48×48). Vùng này hiện trong chế độ
Scale, **nổi lên trên hình thu nhỏ của cửa sổ** — nền sáng hay tối đều có thể xảy
ra. Nên asset phải tự vẽ nền: rounded rect `$mg-surface-sunken` `#0b0c0e` ở
`$mg-opacity-glass-low` `0.55` + viền `$mg-border-subtle`. Nếu chỉ vẽ glyph trần thì
nó sẽ biến mất trên thumbnail sáng.

### 4.5 `corner-ripple.svg`: một tệp cho cả RTL — đúng hành vi upstream

Vendor dùng **cùng một** `corner-ripple.png` cho cả `.ripple-box` và
`.ripple-box:rtl` (`vendor/cinnamon-6.6-sass/widgets/_base.scss:63-69`, đã đọc). Nên
một đĩa 1/4 neo góc trên-trái, không mirror, là **khớp hành vi upstream** chứ không
phải ta bỏ qua RTL. Ghi lại để không ai "sửa" thành hai tệp.

Dùng `radialGradient` với `stop-opacity` giảm dần về `0` — đây là **gradient thật**,
không phải blur, và **không** tuyên bố là blur. T04 đã xác minh `-blur` của St có
thật nhưng phải trả giá `cogl_framebuffer_read_pixels()` mỗi lần paint nên không
dùng; asset này không phụ thuộc `-blur`.

### 4.6 `add-workspace.svg`: dải 35×200, dấu `+` ở giữa

Kích thước do CSS quyết định (dải dọc trong Expo), không phải ta chọn. Dấu `+` đặt
ở tâm dọc `y=100` để luôn nằm giữa dải bất kể chiều cao panel. Trạng thái thường
dùng `$mg-text-secondary` (`#ffffff` α0.66), hover dùng `$mg-status-accent` — cùng
cặp màu với `calendar-arrow-*` để hai loại nút "xem thêm/đổi trang" nhất quán.

---

## 5. Ràng buộc kỹ thuật khi viết SVG cho St

| Ràng buộc | Lý do | Lint khoá bằng bài |
|---|---|---|
| **Không dùng `rgba()` trong attribute** | librsvg hỗ trợ `rgba()` trong presentation attribute **không nhất quán** giữa các phiên bản; `fill="#rrggbb"` + `fill-opacity` thì luôn hoạt động. St render SVG qua librsvg. | `no-rgba-in-svg` |
| **Không `<script>`, `<image>`, `<foreignObject>`, `<iframe>`, `<use>`** | 15 asset này không cần thẻ nào trong số đó; mỗi thẻ thêm rủi ro và bề mặt tấn công. Yêu cầu mục 2 của Agent 5: không tải tài nguyên từ Internet khi chạy. | `no-external-refs` |
| **Không URL ngoài** (khai báo `xmlns` thì được) | như trên. `xmlns="http://www.w3.org/2000/svg"` là **bắt buộc** và không phải tham chiếu mạng — lint bỏ khai báo namespace ra trước khi quét. | `no-external-refs` |
| **`width` = `height` = `viewBox`** | 1 đơn vị SVG = 1px ở 1x ⇒ HiDPI scale sắc, không cần tệp `@2x` riêng. Tiêu chí 4 của T05 cho chọn "có `@2x` **hoặc** viewBox đúng"; dự án chọn viewBox. | `hidpi-viewbox` |
| **`viewBox` cùng tỷ lệ với `width`/`height` CSS** | `background-size: contain` sẽ để khoảng trống hoặc cắt hình nếu lệch tỷ lệ. | `hidpi-viewbox` |
| **Tên tệp lowercase kebab-case** | nhất quán với quy ước repo và với cách St/vendor đặt tên (`corner-ripple.png`, `add-workspace.svg`). | `naming` |
| **url trong CSS phải có tiền tố `assets/`** | `_st_theme_resolve_url` (`src/st/st-theme.c:1082-1140`, đã đọc ở T04) resolve theo **thư mục của tệp CSS khai báo**. `cinnamon.css` nằm ở gốc theme nên url trần sẽ được tìm ở gốc theme, không phải trong `assets/`. | `no-bare-url` |

**Không dùng `<filter>`** (kể cả `feGaussianBlur`): librsvg hỗ trợ nhưng chi phí
raster cao và kết quả khác nhau giữa phiên bản. Bóng đổ trong bộ asset này được
thể hiện bằng gradient và opacity, không bằng filter.

---

## 6. Cách sinh lại (không có script generator trong repo)

Allow-list của T05 chỉ cho phép `src/cinnamon/assets/**/*.svg`,
`src/cinnamon/assets/MANIFEST.md`, `tools/lint/assets.py`,
`tests/lint/test_assets.py` — **không** cho phép thêm script generator. Nên 15 tệp
này được sinh **một lần** bằng script tạm ngoài repo, script đó **đọc thẳng
`_tokens.scss`** để lấy mọi giá trị màu (không có giá trị nào gõ tay), rồi kết quả
được commit dưới dạng tệp tĩnh.

Tính đúng đắn về sau **không** phụ thuộc script đã mất: `tools/lint/assets.py`
kiểm tra lại toàn bộ ràng buộc ở mục 5 và đối chiếu mọi literal với token trên mỗi
lần chạy. Nếu ai sửa tay một tệp và đưa vào màu ngoài hệ token, lint sẽ đỏ.

Khi cần thêm asset mới: viết tệp SVG, thêm một dòng vào bảng ở mục 3, ghi nguồn
token cho mọi màu, rồi chạy `python3 tools/lint/assets.py`. Nếu literal không khớp
token nào, **đừng** thêm vào `DOCUMENTED_EXCEPTIONS` cho qua chuyện — hãy xin Agent
Design Systems bổ sung token.

---

## 7. Trạng thái kiểm chứng

**ĐÃ kiểm chứng offline** — bằng `python3 tools/lint/assets.py` và
`python3 -m unittest tests.lint.test_assets` (42 bài, cả hai đều nằm trong
allow-list của T05; allow-list **không** cho phép tạo tệp tài liệu nào khác ngoài
chính MANIFEST.md này):
tồn tại tệp, XML well-formed (`xml.etree`), viewBox/kích thước khớp CSS đã biên
dịch, màu ↔ token, không tham chiếu ngoài, không `rgba()` trong attribute, không
`<filter>`/`<mask>`/`<script>`/`<image>`/`<use>`, url resolve, không url trần,
MANIFEST khớp hai chiều, và `tools/lint/st_properties.py` của T04 hết mục PENDING.

**CHƯA kiểm chứng — cần Cinnamon 6.6 thật:**
librsvg trên máy thật có raster đúng như mong đợi không; `background-size: contain`
của St có căn giữa đúng không; asset trông thế nào ở HiDPI 1x/2x/fractional;
`toggle-*.svg` có khớp kích thước thật của `.toggle-switch` trong applet không.
St có cơ chế `PROP_FALLBACK_STYLESHEET` không cascade (đã xác minh ở T04) nên nếu
một asset lỗi thì **không** có tầng nào cứu — phải kiểm bằng mắt trên máy thật.
