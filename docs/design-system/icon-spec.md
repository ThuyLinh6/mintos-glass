# Quy chuẩn thiết kế icon — MintOS Glass

**Task:** T15 · **Owner:** Agent D (Visual/Assets)
**Phạm vi:** `src/icons/MintOS-Glass/**` · inventory ở `src/icons/MintOS-Glass/MANIFEST.md`
**Token:** `design/tokens/*.json` → `src/cinnamon/tokens/_tokens.scss` (read-only với T15)
**Kiểm chứng:** `tools/lint/icon_theme.py`, `tests/lint/test_icon_theme.py`

> Tài liệu này là **quy chuẩn thiết kế** (yêu cầu 4.4 của Agent 5). Nó không tạo
> ra một bảng màu thứ hai: mọi giá trị màu ở đây đều là token sẵn có của Agent
> Design Systems, kèm tên token để tra ngược. Nếu cần một giá trị chưa có, quy tắc
> là **mở issue cho Agent B**, không tự thêm vào đây.

---

## 1. Lưới và vùng an toàn

| Thuộc tính | Giá trị | Ghi chú |
|---|---|---|
| `viewBox` | `0 0 24 24` | thống nhất cho **mọi** icon, kể cả symbolic |
| `width` / `height` | `24` / `24` | bằng `viewBox` để 1 đơn vị SVG = 1px ở 1x |
| Vùng sống (live area) | `20 × 20`, từ `(2,2)` tới `(22,22)` | lề 2px mỗi phía |
| Vùng an toàn tuyệt đối | `18 × 18`, từ `(3,3)` | nét không được chạm ra ngoài vùng này |
| `Type` trong `index.theme` | `Scalable` | `MinSize=16`, `MaxSize=512` |

**Vì sao 24 mà không phải 16 hay 48:** 24 là bội chung thuận tiện cho cả 16, 24,
32, 48 (GTK xin icon ở các cỡ đó), đủ chi tiết để vẽ hình dễ nhận ra, và đủ nhỏ để
nét 1.5 còn nghĩa. Đây là lựa chọn **chưa kiểm trên máy thật** — xem MANIFEST mục 8.

**Vì sao dùng `Scalable` thay vì sinh nhiều cỡ raster:** theme thuần SVG thì một
tệp phục vụ mọi kích thước không mất nét. Sinh raster 16/22/24/32/48/64/96/128/256
như Mint-Y sẽ nhân số tệp lên ~9 lần và **đòi một công cụ render trên máy người
dùng** — vi phạm ràng buộc "không yêu cầu người dùng cài thêm phần mềm".
`render-png.sh` trong allow-list của T15 chỉ để mô tả pipeline cho **agent đóng gói
ISO**, không chạy trên máy người dùng.

---

## 2. Nét vẽ (stroke)

| Vai trò | Độ rộng | Đầu nét | Ghi chú |
|---|---|---|---|
| Nét chính | `1.5` | `round` | mặc định cho line icon |
| Nét nhấn mạnh | `1.7` – `1.8` | `round` | glyph trên nền app icon, dấu `+`/`−`, dấu ✕ |

`1.4` là **sàn cứng**: `test_stroke_widths_are_within_the_spec_range` duyệt mọi
`stroke-width` trong theme và đòi `1.4 ≤ w ≤ 2.0`. Đã bắt được một nét `1.2` lạc
vào `folder-open.svg` trong lần chạy đầu — ở 16px (scale 0.667) nét 1.2 chỉ còn
0.8px và biến mất.
| Nét mảnh (chi tiết) | `1.4` | `round` | đường kẻ trong tài liệu, chi tiết phụ |
| Nét dày (vòng nhẫn) | `2.0` | — | thân của bánh răng settings |

**Toàn bộ dùng `stroke-linecap="round"` và `stroke-linejoin="round"`.** Không có
ngoại lệ. Nét vuông cho cảm giác kỹ thuật/cứng; bo tròn là một phần của ngôn ngữ
"soft glass" và giúp icon không gãy ở kích thước nhỏ.

Nét **không** nhỏ hơn `1.4`: ở 16px (scale 0.667) nét 1.4 thành ~0.93px, đã là
giới hạn dưới trước khi mất hẳn.

---

## 3. Bán kính bo góc

| Vai trò | Giá trị | Token tương ứng |
|---|---|---|
| Khung app icon (squircle) | `5.5` trên khung `20 × 20` | tỉ lệ ~27.5%, tương đương `$mg-radius-xl` nếu có |
| Chi tiết lớn (màn hình, máy in, khay) | `1.6` – `1.8` | xấp xỉ `$mg-radius-sm` (6px) scale về lưới 24 |
| Chi tiết nhỏ (đầu nét, răng bánhgear) | `0.85` – `1.5` | — |
| Góc gấp của tài liệu | không bo | bo sẽ làm mất dấu hiệu "gấp giấy" |

**Quy tắc:** bo góc phải **tỉ lệ thuận** với kích thước phần tử. Bo `5.5` cho một
chi tiết 4px sẽ biến nó thành viên thuốc; bo `0.5` cho khung 20px sẽ trông sắc và
lạc khỏi ngôn ngữ thiết kế.

---

## 4. Bảng màu

**Chỉ dùng token.** Không có màu nào trong bộ icon này được gõ tay.

### 4.1 Màu nét vẽ cho icon KHÔNG-symbolic

Đây là ràng buộc khó nhất và là chỗ duy nhất **bắt buộc phải đo**.

Một icon theme phục vụ **cả** hộp thoại chọn tệp của app GTK chạy theme sáng
**lẫn** desktop/nền tối của MintOS Glass. Cùng một tệp icon phải đọc được trên cả
hai. Đã đo toàn bộ thang xám bằng `tools/lint/contrast.py`, ngưỡng **3:1** cho đối
tượng đồ hoạ (WCAG 1.4.11):

| Token | Hex | Trên nền trắng | Trên nền tối `#121316` | Kết luận |
|---|---|---|---|---|
| `$mg-color-gray-200` | `#cfd2d7` | 1.52:1 ✗ | 12.25:1 ✓ | chỉ dùng được nền tối |
| `$mg-color-gray-300` | `#a5a9b0` | 2.36:1 ✗ | 7.87:1 ✓ | chỉ dùng được nền tối |
| **`$mg-color-gray-400`** | **`#7c8087`** | **3.97:1 ✓** | **4.68:1 ✓** | **ĐẠT CẢ HAI → dùng làm nét vẽ** |
| `$mg-color-gray-500` | `#55585f` | 7.12:1 ✓ | 2.61:1 ✗ | chỉ dùng được nền sáng |
| `$mg-color-gray-600` | `#3a3d43` | 10.89:1 ✓ | 1.71:1 ✗ | chỉ dùng được nền sáng |
| `$mg-status-accent` | `#3ddc97` | 1.77:1 ✗ | 10.51:1 ✓ | chỉ dùng được nền tối |

**Chỉ `gray-400` vượt ngưỡng trên cả hai nền.** Nó là màu nét vẽ mặc định của mọi
line icon không-symbolic. Lint có bài `ink-contrast-both-backdrops` đo lại mỗi lần
chạy, nên đổi sang màu khác sẽ đỏ ngay.

> **Hệ quả thiết kế quan trọng:** accent mint `#3ddc97` **không dùng được làm nét
> vẽ** cho icon không-symbolic, dù nó là màu thương hiệu — nó chỉ đạt 1.77:1 trên
> nền trắng. Mint chỉ dùng làm **chi tiết nhấn** nằm trong một hình đã có đường bao
> `gray-400` (xem 4.4). Đây là một chỗ mà nhận diện thương hiệu phải nhường khả
> năng đọc, đúng theo yêu cầu "không hy sinh tương phản/khả năng đọc để bắt chước".

### 4.2 Icon `-symbolic`: một màu đen thuần

GTK tô lại icon symbolic theo **màu chữ của widget**, bằng cách dùng **kênh alpha**
của ảnh chứ không dùng màu gốc. Nên:

- mọi hình trong `symbolic/` vẽ bằng đúng `$mg-color-black` (`#000000`)
- **không** gradient, **không** màu thứ hai, **không** `fill-opacity` khác nhau
  giữa các phần (khác alpha nghĩa là khác mức tô, sẽ thành vệt loang)

Vi phạm thì icon bị tô thành một khối đặc mất chi tiết. Lint khoá bằng bài
`symbolic-monochrome`.

### 4.3 Nền và glyph của app icon (squircle)

Mọi cặp glyph/nền dưới đây **đã đo đạt ≥ 3:1**:

| App | Nền (token) | Hex nền | Glyph (token) | Hex glyph | Tương phản |
|---|---|---|---|---|---|
| Nemo | `$mg-status-accent` | `#3ddc97` | `$mg-color-gray-950` | `#0b0c0e` | **11.07:1** |
| Cinnamon Settings | `$mg-color-gray-600` | `#3a3d43` | `$mg-color-gray-100` | `#eceef1` | 9.37:1 |
| Terminal | `$mg-color-gray-950` | `#0b0c0e` | `$mg-color-mint-400` | `#6ee7bd` | 12.89:1 |
| xed | `$mg-color-blue-500` | `#3b9dff` | `$mg-color-gray-950` | `#0b0c0e` | 6.94:1 |
| Web browser | `$mg-color-blue-400` | `#6cb6ff` | `$mg-color-gray-950` | `#0b0c0e` | 9.11:1 |
| Xplayer / media | `$mg-color-red-500` | `#ff5f57` | `$mg-color-gray-950` | `#0b0c0e` | 6.55:1 |
| Xviewer / photo viewer | `$mg-color-amber-500` | `#ffbd2e` | `$mg-color-gray-950` | `#0b0c0e` | 11.71:1 |
| Pix | `$mg-color-amber-600` | `#d99a1f` | `$mg-color-gray-950` | `#0b0c0e` | 8.01:1 |
| Xreader / doc viewer | `$mg-color-gray-400` | `#7c8087` | `$mg-color-gray-950` | `#0b0c0e` | 4.93:1 |
| mintupdate | `$mg-color-green-500` | `#28c840` | `$mg-color-gray-950` | `#0b0c0e` | 8.78:1 |
| mintinstall | `$mg-color-mint-700` | `#1f8f5f` | `$mg-color-gray-100` | `#eceef1` | **3.51:1** |
| Screenshot | `$mg-color-gray-700` | `#2a2c31` | `$mg-color-gray-100` | `#eceef1` | 12.02:1 |

`mintinstall` ở **3.51:1** là cặp sát ngưỡng nhất. Đã cân nhắc đổi sang
`$mg-color-mint-600` nhưng cặp đó thấp hơn. Giữ nguyên và **ghi lại** để lần kiểm
tra trên máy thật chú ý tới icon này.

**Quy tắc suy ra:** glyph **tối** trên nền sáng/trung, glyph **sáng** trên nền tối.
Không bao giờ dùng glyph trắng trên nền accent — cùng kết luận đã đo ở T05
(trắng trên `#3ddc97` = 1.77:1 FAIL).

### 4.4 Vai trò của màu nhấn

Màu (`mint`, `blue`, `red`, `amber`, `green`) chỉ dùng ở **hai** chỗ:

1. **làm nền** app icon (đã đo ở 4.3) — ở đây màu là khối lớn nên nó *là* hình,
   không phải nét
2. **làm chi tiết nhấn nhỏ** bên trong một hình **đã có đường bao `gray-400`**:
   chấm màu trên tab thư mục, nét nội dung của mimetype, dấu `+` của `document-new`
   (nằm trong tấm giấy đã có bao `gray-400`)

**Danh sách này đã bị thu hẹp so với bản nháp đầu, và đó là kết quả của kiểm tra
chứ không phải sở thích.** Bản nháp định dùng accent cho cả dấu `+` của `list-add`
và mũi tên của `view-refresh`. Nhưng ở hai icon đó dấu `+`/mũi tên **chính là toàn
bộ hình dạng** — không có đường bao `gray-400` nào mang nghĩa thay nó. Mà accent
chỉ đạt **1.77:1 trên nền trắng** (đo ở 4.1), nên cả hai icon sẽ gần như vô hình
trong hộp thoại chọn tệp của một app GTK chạy theme sáng. Đã đổi cả hai sang
`gray-400` nét `1.8`/`1.7`. `tests/lint/test_icon_theme.py` có bài
`test_line_icons_use_the_ink_colour` duyệt mọi icon trong `actions/` và `devices/`
và đòi đúng màu nét vẽ chuẩn, nên không quay lại được.

**Không** dùng màu làm đường bao chính của line icon. Lý do ở 4.1: không màu nào
trong bảng đạt 3:1 trên cả hai nền, trừ `gray-400` vốn là màu trung tính.

Phần nhấn màu là **trang trí**: hình dạng tổng thể vẫn được mang bởi nét
`gray-400` đạt chuẩn. Nên nếu phần màu có hụt tương phản trên nền nào đó thì
*ý nghĩa* của icon vẫn đọc được. Đây là lập luận cần ghi rõ, vì WCAG 1.4.11 áp
dụng cho phần đồ hoạ **mang nghĩa**, không cho trang trí.

### 4.5 Thư mục (places): ba lớp

Hình thư mục dùng ba lớp để đọc được trên cả hai nền mà vẫn phân biệt được loại:

| Lớp | Màu | Vai trò |
|---|---|---|
| Thân sau (có tab) | `gray-400` `#7c8087` | **mang hình dạng** → đạt 3:1 trên cả hai nền |
| Mặt trước | `gray-300` `#a5a9b0` | tạo chiều sâu, phân biệt nắp/thân |
| Chấm nhấn theo loại | hue riêng | phân biệt Documents/Downloads/Pictures/… |

Mã màu của chấm nhấn: `folder-documents` = `$mg-color-blue-400`,
`folder-download` = `$mg-color-green-500`, `folder-pictures` = `$mg-color-amber-500`,
`folder-music` = `$mg-color-red-400`, `folder-videos` và `user-home` =
`$mg-status-accent`, `folder-templates` và `folder-publicshare` = `$mg-color-gray-200`
(hai thư mục này ít dùng nên cố ý **không** cho màu riêng — ít màu nổi hơn nghĩa là
mắt tìm nhanh hơn những thư mục quan trọng).

Mặt trước `gray-300` chỉ đạt 2.36:1 trên nền trắng, nhưng nó **không mang hình
dạng** — thân sau `gray-400` mang. Đúng lập luận ở 4.4.

---

## 5. Hình khối và tỉ lệ

- **App icon:** squircle `20 × 20` đặt tại `(2,2)`, bo `5.5`. Glyph bên trong nằm
  trong vùng `12 × 12` ở giữa, tức cách mép squircle ít nhất 4 đơn vị. Không vẽ
  glyph chạm mép squircle: ở 16px phần chạm mép sẽ dính vào nhau thành một khối.
- **Line icon** (places/devices/mimetypes/actions/status): **không** có khung nền.
  Hình chiếm vùng sống `20 × 20`. Lý do: line icon xuất hiện trên toolbar, sidebar,
  menu — những chỗ đã có nền riêng của widget. Thêm khung sẽ tạo ra "ô vuông trong
  ô vuông".
- **Mimetype:** tất cả dùng chung đường bao tấm giấy
  (`DOC_SHEET`) + góc gấp. Chỉ đổi màu nét nội dung.
- **Tỉ lệ hình học:** ưu tiên hình tròn, chữ nhật bo, tam giác đều. Tránh đường cong
  tự do: chúng không scale xuống 16px một cách dự đoán được.

---

## 6. Bóng đổ

**Không dùng bóng đổ trong icon.** Cụ thể:

- không `<filter>`, không `feGaussianBlur`, không `feDropShadow`
- không `<mask>`, không `<clipPath>`

Ba lý do, theo thứ tự quan trọng:

1. **librsvg cho kết quả khác nhau giữa phiên bản** với filter, và chi phí raster
   cao. Cùng một tệp có thể hiện khác nhau trên Mint 22.3 và trên bản khác.
2. **Icon phải đọc được trên nền bất kỳ.** Bóng đổ giả định hướng sáng và nền; đặt
   lên nền tối thì bóng vô hình, đặt lên nền sáng thì bóng làm bẩn hình.
3. **Chiều sâu được tạo bằng lớp màu, không bằng bóng** — xem 4.5: thân sau
   `gray-400` + mặt trước `gray-300` đủ để đọc ra "thư mục có nắp" mà không cần bóng.

Chiều sâu kiểu "glass" của MintOS Glass (gradient nền, `box-shadow`, `-blur`) thuộc
về **Cinnamon theme và GTK theme**, không thuộc về icon. T04 đã xác minh `-blur`
của St có thật nhưng phải trả giá `cogl_framebuffer_read_pixels()` mỗi lần paint
nên không dùng; icon lại càng không được phụ thuộc vào nó.

Gradient **được phép** ở đúng một chỗ trong repo này: `corner-ripple.svg` của T05
(asset của Cinnamon theme, không phải icon theme). Trong `src/icons/` **không có
gradient nào** — bắt buộc, vì 4.2.

---

## 7. Icon trên nền sáng và nền tối

| Loại icon | Nền tối | Nền sáng | Cơ chế |
|---|---|---|---|
| `-symbolic` | GTK tô màu chữ sáng | GTK tô màu chữ tối | **kênh alpha** — tự động đúng |
| App icon (squircle) | nền màu tự nổi | nền màu tự nổi | khối màu lớn + glyph đã đo ≥3:1 |
| Line icon | nét `gray-400` = 4.68:1 | nét `gray-400` = 3.97:1 | **một màu duy nhất đạt cả hai** |
| Thư mục | thân `gray-400` | thân `gray-400` | như trên, lớp sáng chỉ là chi tiết |

Đây là lý do **phải** có cả hai dòng: bản `-symbolic` cho chỗ GTK chủ động xin
(panel, menu, toolbar) và bản đầy đủ màu cho chỗ app xin icon theo tên
(desktop, Nemo grid view, hộp thoại). Thiếu một trong hai sẽ lộ fallback về Mint-Y
và phá tính nhất quán.

---

## 8. Quy tắc đặt tên

1. **Có tên chuẩn freedesktop → dùng tên chuẩn.** Không bịa tên mới cho khái niệm
   đã có trong Icon Naming Spec.
2. **App dùng `Icon=` trong `.desktop` của chính nó.** Đã trích từ mã nguồn, bảng ở
   MANIFEST mục 3. Không đặt theo trí nhớ — `cinnamon-settings` là
   `preferences-desktop`, không phải `preferences-system`.
3. **App có tên riêng thì cung cấp CẢ tên chuẩn.** `xplayer` + `multimedia-video-player`.
4. **Symbolic thêm hậu tố `-symbolic`**, và đặt trong `symbolic/<context>/`.
5. **Chữ thường, chỉ `[a-z0-9._-]`.** Lint có bài `naming`.
6. **Không đặt tên ngụ ý Apple chứng thực**, không dùng tên sản phẩm Apple.

---

## 8bis. Họ icon `cs-*` của System Settings (Agent 6)

47 icon cho `cinnamon-settings` nằm trong `scalable/apps/` nhưng là **một họ thiết
kế riêng**, khác 16 icon app ở mục 4.3.

### Vì sao KHÔNG dùng squircle

| | 16 icon app | 47 icon `cs-*` |
|---|---|---|
| Bản chất | app **khởi chạy được** | **mục trong cùng một app** (Settings) |
| Hiện ở đâu | menu, dock, desktop — cỡ lớn | lưới trang chính **lẫn** list/sidebar — cả cỡ nhỏ |
| Ngôn ngữ | squircle đặc màu + glyph | **line icon** + một chi tiết màu |

Squircle + glyph bên trong sẽ **nhoè ở 16-24px**: hai lớp hình (khối nền và nét
glyph) cùng bị scale xuống thì mất tương phản giữa chúng. Line icon chỉ có một lớp
nên sống sót ở cỡ nhỏ. Đây là cùng lý do `mimetypes/` và `places/` đã dùng line icon.

### Cấu trúc màu

- **Nét `$mg-color-gray-400` MANG HÌNH DẠNG** — đã đo 3.97:1 trên nền trắng và
  4.68:1 trên nền tối (mục 4.1), nên hình dạng đọc được trên cả hai nền.
- **Một chi tiết màu theo category** — chỉ là **mã phân loại**, không phải thứ người
  dùng dựa vào để nhận ra icon.

| Category | Hue | Token |
|---|---|---|
| Appearance | `#3ddc97` | `$mg-status-accent` |
| Preferences | `#3b9dff` | `$mg-color-blue-500` |
| Hardware | `#ffbd2e` | `$mg-color-amber-500` |
| Administration | `#ff5f57` | `$mg-status-error` |

**Mỗi icon mang ĐÚNG MỘT hue.** Hai hue trong một icon sẽ phá mã phân loại — khoá
bằng `test_settings_category_hues_are_the_four_documented_ones`.

Chi tiết màu **không cần** đạt 3:1 vì nó không mang nghĩa (đúng lập luận mục 4.4:
WCAG 1.4.11 áp dụng cho phần đồ hoạ **mang nghĩa**). Phần mang nghĩa là nét
`gray-400`, và nó đạt chuẩn trên cả hai nền.

### Ràng buộc hình học

Không rect đặc nào trong họ `cs-*` được có cạnh ngắn ≥ 12 đơn vị — đó là ngưỡng
phân biệt "chi tiết accent" với "squircle phủ lưới". Khoá bằng
`test_settings_icons_are_line_style_not_squircle`. Bản đầu của test này phân biệt
bằng **thứ tự thẻ** và đã bắt nhầm bốn icon hợp lệ (`cs-applets`, `cs-themes`,
`cs-panel`, `cs-cat-hardware`); thứ tự thẻ không nói lên được điều gì về squircle,
**kích thước** mới nói được.

### Nguồn tên và ranh giới trung thực

Tên trích bằng máy theo **cấu trúc bảng** trong `cinnamon-settings.py`
(`CATEGORIES`, `CONTROL_CENTER_MODULES`, `STANDALONE_MODULES`) và từ `SidePage(...)`
trong 31 `modules/cs_*.py` — **không grep thô**, vì grep thô khớp cả
`cs-category-view` vốn là **tên CSS class** (`cinnamon-settings.py:288`), không phải
tên icon. Bảng đầy đủ, kể cả 15 tên của app khác **cố ý không vẽ**, ở
`src/icons/MintOS-Glass/MANIFEST.md` mục 4bis.

Category của 3 panel C và 9 trang standalone lấy từ **cột 4 thật** của các bảng đó.
Category của 31 module Python thì **không truy ra được từ nguồn** (upstream gán qua
`sidepage.cat` nhưng cơ chế gán không nằm trong `modules/*.py`) → nhóm theo ngữ
nghĩa, và đó là **quyết định thiết kế của dự án**, không phải tuyên bố về upstream.

---

## 9. Thêm icon mới — quy trình

1. Kiểm tra icon đó **đã có** trong `Inherits` chưa và có thật sự cần nhận diện
   MintOS Glass không. Nếu Mint-Y đã có hình chấp nhận được thì **không vẽ** —
   theme nhỏ là chủ ý, không phải thiếu sót.
2. Vẽ trên lưới `24 × 24`, vùng sống `20 × 20`, nét `1.5`, đầu tròn, bo góc theo §3.
3. Màu **chỉ** lấy từ `_tokens.scss`. Nếu cần màu chưa có → **mở issue cho Agent B**,
   không gõ hex tay.
4. Nếu icon sẽ xuất hiện ở panel/menu/toolbar → làm thêm bản `-symbolic` **đơn sắc**.
5. Thêm một dòng vào `tests/fixtures/icon-theme-core.txt`.
6. Thêm vào MANIFEST.md (danh sách §4) và vào bảng màu nếu dùng cặp glyph/nền mới
   — **kèm số đo tương phản**.
7. Chạy `python3 tools/lint/icon_theme.py -v` và
   `python3 -m unittest tests.lint.test_icon_theme`.

---

## 10. Việc còn lại (theo thứ tự ưu tiên của Agent 5)

| Ưu tiên | Việc | Chặn bởi |
|---|---|---|
| **P1** | Kiểm bằng mắt trên Mint 22.3 thật: icon có hiện không, nét 1.5 ở 16px có mờ không, symbolic có được tô lại đúng không | cần máy thật (T00) |
| **P2** | Bộ icon panel/status **đầy đủ biến thể trạng thái** (network 5 mức × offline/acquiring, battery 5 mức × charging/charged, volume 5 mức) | cần phối hợp Agent 2 để trích đúng tập tên icon từ mã nguồn applet Cinnamon 6.6 — xem MANIFEST mục 6 |
| **P2** | 31 icon `cs-*` cho các module của Cinnamon Settings | đã đếm được danh sách, chưa vẽ |
| **P2** | Mở rộng mimetype phổ biến còn thiếu | — |
| **P4** | Wallpaper (T16) — phải đo lại nhãn icon desktop ≥3:1 trên wallpaper **thật** thay vì ba mức chói mô hình mà T09 đã dùng | T16 |

**Không nằm trong phạm vi T15:** chọn icon theme lúc chạy (gsetting
`org.cinnamon.desktop.interface icon-theme` — thuộc T12), style của icon trên panel
(thuộc T04 qua `overrides/`), và dock (thuộc T11/T04).
