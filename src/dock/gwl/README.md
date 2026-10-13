# Dock MintOS Glass — tuỳ biến `grouped-window-list` (T11)

**Task:** T11 · **Owner:** Agent H (Shell/Dock), thực hiện cùng Agent D
**Quyết định nền:** **D-1 = `gwl`** — tuỳ biến applet `grouped-window-list@cinnamon.org`
có sẵn của Cinnamon. **Không cài Plank. Không thêm package. Không sửa file applet.**
**Style:** `src/cinnamon/overrides/_40-windowlist-gwl.scss` (thuộc T04, **không sửa ở đây**)
**Cấu hình panel:** `src/dock/gwl/panel-layout.md`

> Tài liệu này thoả tiêu chí Done #2 và #3 của T11: mô tả cách đạt vẻ "dock"
> **không cần cài gì thêm và không sửa file applet**, chỉ dùng cấu hình panel sẵn
> có + CSS của T04; kèm hướng dẫn hoàn tác từng bước. **Không có lệnh
> `apt install` nào trong toàn bộ tài liệu này.**

---

## 1. Hai khái niệm phải phân biệt rõ

Yêu cầu của Agent 5 nói rõ: *"phân biệt rạch ròi dock trong panel và dock nổi độc
lập"*. Đây không phải câu chữ — hai thứ này khác nhau về **cơ chế**, và dự án chỉ
chọn một.

| | **Dock trong panel** ← dự án chọn | **Dock nổi độc lập** |
|---|---|---|
| Là gì | Applet `grouped-window-list` nằm **trong** panel Cinnamon, panel được đặt ở **cạnh dưới** màn hình | Một cửa sổ riêng, nổi, trong suốt, không thuộc panel |
| Ai vẽ | Cinnamon shell vẽ panel; applet vẽ từng nút | Plank/Docky hoặc một chương trình tự viết |
| Style bằng gì | **CSS của St** — `_40-windowlist-gwl.scss` của T04 | File `dock.theme` của Plank (schema khác hẳn) |
| Cần cài thêm | **Không** | Plank (package mới) |
| Cửa sổ có mất khả năng gì không | Không — vẫn là applet chuẩn | Không, nhưng thêm một tiến trình chạy nền |
| Rủi ro | Thấp: dùng đúng cơ chế upstream | Cao: thêm phụ thuộc, thêm điểm hỏng |

**Dự án đi đường "dock trong panel".** Lý do không phải thẩm mỹ mà là ràng buộc:
*"không yêu cầu cài thêm phần mềm trên máy người dùng"* và *"không build dock nổi
độc lập nếu chưa có lý do kỹ thuật và được duyệt"*.

**Chưa có lý do kỹ thuật nào buộc phải làm dock nổi.** Mọi yêu cầu thị giác trong
Scope A (kích thước/khoảng cách icon, nền/viền/độ trong, trạng thái đang chạy,
trạng thái cửa sổ active, hover/focus, app được ghim, app nhiều cửa sổ) đều đạt
được bằng CSS của St trên applet có sẵn — T04 đã hiện thực 59 selector cho đúng
việc đó. Nên **không đề xuất** dock nổi.

---

## 2. NHỮNG GÌ KHÔNG LÀM ĐƯỢC — và bằng chứng

Phần này quan trọng hơn phần "làm được". Ghi rõ để không ai hứa với người dùng
một hiệu ứng mà nền tảng không có.

### 2.1 KHÔNG có phóng to icon khi rê chuột (magnification kiểu macOS)

Hai lớp bằng chứng độc lập, cả hai đều đã đọc từ mã nguồn:

**(a) St không có `transform`.** T04 đã dựng `tests/fixtures/st-allowed-properties.txt`
(161 property) bằng cách đọc các getter thật trong `st-theme-node.c`. `transform`
**không có** trong danh sách đó. St có `border-*`, `background-*`, `box-shadow`,
`-blur`, `transition-*` — nhưng không có gì để scale một actor bằng CSS.
`_40-windowlist-gwl.scss` đã ghi chú điều này ngay ở đầu file.

**(b) Applet GWL cũng không tự làm.** Đã grep toàn bộ applet:
`grouped-window-list@cinnamon.org/appGroup.js` chỉ có **một** hàm animation là
`animate()` ở dòng **1165**, và nó được gọi từ **đúng một chỗ**:

```
appGroup.js:743   launchNewInstance(offload=false) {
appGroup.js:751       this.groupState.app.open_new_window(-1);
appGroup.js:754       this.animate();          <-- chỗ gọi DUY NHẤT
```

Tức là animation chỉ chạy khi **khởi chạy một instance mới từ dock**, không phải
khi rê chuột. Không có đường mã nào nối `hover` với `scale`.

> **Kết luận phải nói với người dùng:** MintOS Glass **không có** hiệu ứng phóng to
> icon khi rê chuột. Hiệu ứng hover là **đổi nền + đổi viền + hiện nhãn**, không
> phải thay đổi kích thước. Đừng mô tả nó là "magnification" hay "zoom".

### 2.2 Cái CÓ thật: animation lúc khởi chạy app

`launcher-animation-effect` là một **gsetting của applet**, không phải CSS. Đã đọc
giá trị thật từ `settings-schema.json` và hành vi thật từ `appGroup.js:1165-1196`:

| Giá trị | Tên trong Settings | Hành vi thật trong mã |
|---|---|---|
| `1` | None | `if (effect === 1) return;` — không làm gì |
| `2` | Fade | `iconBox.ease({opacity: 70, duration: 200})` rồi trả về `255`, LINEAR |
| **`3`** | **Scale** ← **mặc định** | `set_pivot_point(0.5, 0.5)` → `ease({scale_x: 0.8, scale_y: 0.8, duration: 175, EASE_OUT_QUAD})` → `ease({scale_x: 1.1, scale_y: 1.1, duration: 175})` → về `1.0` |

Nên **có** một hiệu ứng co-giãn icon, nhưng nó là **nhịp nảy lúc bấm để mở app**
(0.8 → 1.1 → 1.0, 175ms mỗi nhịp, `EASE_OUT_QUAD`), **không** phải zoom khi rê
chuột. Mô tả đúng như vậy, không gộp hai thứ làm một.

Mặc định đã là `3` (Scale) nên **không cần đổi gì** để có hiệu ứng này.

### 2.3 Chỉ báo "app đang chạy" là THANH GẠCH, không phải chấm tròn

St **không có pseudo-element** (`::before`/`::after`) nên không tạo được một "chấm"
riêng bên dưới icon. T04 hiện thực chỉ báo bằng **`border-bottom` trên chính item
box** — một thanh gạch dưới.

Kỹ thuật chống nhảy layout (đã ghi trong `_40-windowlist-gwl.scss`): St không có
`box-sizing`, border **cộng thẳng** vào kích thước. Nên `border-bottom-width` được
đặt **trước** cho mọi item bằng đúng độ dày tối đa với màu `transparent`, rồi chỉ
đổi **màu** khi `:active`/`:focus`. Đây cũng chính là cách vendor làm (vendor đặt
sẵn `border-bottom-width: 2px` trên `.top`/`.bottom`).

> Đừng mô tả nó là "dot indicator" trong tài liệu người dùng.

### 2.4 Ẩn nhãn cửa sổ KHÔNG làm bằng CSS

Nhãn do **applet** tạo dựa trên gsetting `title-display`. Dùng CSS `width: 0` sẽ để
lại khoảng trắng và phá căn giữa. Cách đúng là đặt gsetting — xem
`panel-layout.md`.

**Tin tốt đã xác minh:** `title-display` **mặc định đã là `1` = "None"**, tức GWL
trên Mint 22.3 vốn **đã ở chế độ chỉ-có-icon**. Nên vẻ "dock" không cần thay đổi
gsetting này — chỉ cần xác nhận là không ai đã đổi nó.

---

## 3. Những gì ĐẠT ĐƯỢC, và đạt bằng cái gì

Mọi dòng dưới đây đều trỏ tới một thứ **đã tồn tại**: selector trong
`_40-windowlist-gwl.scss` của T04, hoặc gsetting thật của applet.

| Yêu cầu Scope A | Đạt bằng | Trạng thái |
|---|---|---|
| Kích thước / khoảng cách icon | CSS trên `.grouped-window-list-item-box` (+ `padding`, `spacing`) + gsetting `panel-zone-icon-sizes` | ✅ T04 + `panel-layout.md` |
| Nền / viền / độ trong của nút | CSS `background-color`, `border-*` trên `.grouped-window-list-item-box` | ✅ T04 |
| Trạng thái hover | `.grouped-window-list-item-box:hover` | ✅ T04 |
| Trạng thái focus | `.grouped-window-list-item-box:focus` | ✅ T04 |
| Cửa sổ active / đang chạy | `.grouped-window-list-item-box:active`, `:outlined` — hiện bằng thanh gạch dưới (mục 2.3) | ✅ T04 |
| App cần chú ý | `.grouped-window-list-item-demands-attention` | ✅ T04 |
| App được ghim (pinned) | gsetting `pinned-apps`; CSS không phân biệt pinned/running — cả hai là cùng một `.grouped-window-list-item-box` | ⚠️ xem mục 5 |
| App nhiều cửa sổ | `.grouped-window-list-number-label`, `.grouped-window-list-badge`, `.grouped-window-list-thumbnail-menu` + `.item-box` | ✅ T04 |
| Menu xem trước (thumbnail) | `.grouped-window-list-thumbnail-menu`, `.item-box:selected`, `.item-box:outlined`, `.grouped-window-list-thumbnail-label`, `.grouped-window-list-thumbnail-alert` | ✅ T04 |
| Vị trí panel khác nhau | `.grouped-window-list-item-box.top/.bottom/.left/.right` (kể cả `StBin` con ở `.left`/`.right`) | ✅ T04 |
| Progress (ví dụ đang tải) | `.grouped-window-list-item-box .progress` | ✅ T04 |
| Badge thông báo | `.grouped-window-list-notifications-badge` + `-badge-label` | ✅ T04 |
| Nhãn nút | `.grouped-window-list-button-label`, `.grouped-window-list-item-label`, `:hover .grouped-window-list-item-label` | ✅ T04 |
| Phóng to icon khi rê chuột | — | ❌ **bất khả thi**, mục 2.1 |

### Không mất chức năng nào của Cinnamon

Đây là ràng buộc cứng của Scope A: *"không được làm mất khả năng chuyển cửa sổ,
ghim ứng dụng, quản lý cửa sổ của Cinnamon"*. Thoả được vì:

- **Không sửa một dòng nào trong file applet.** Chỉ thêm CSS lên trên và đọc/ghi
  gsetting sẵn có.
- **Không thay applet** bằng thứ khác. Vẫn là `grouped-window-list@cinnamon.org`
  gốc, nên mọi tính năng của nó (nhóm cửa sổ, thumbnail, Super+số, cycle menu,
  kéo-thả để ghim, menu ngữ cảnh) còn nguyên.
- CSS chỉ đổi **màu, viền, nền, padding** — không đổi cấu trúc actor, không ẩn
  element nào bằng `width:0`/`height:0`.

Các gsetting chức năng **giữ nguyên mặc định**, không đụng tới:
`scroll-behavior`, `thumbnail-scroll-behavior`, `show-thumbnails`,
`animate-thumbnails`, `vertical-thumbnails`, `sort-thumbnails`,
`highlight-last-focused-thumbnail`, `onclick-thumbnails`, `thumbnail-timeout`,
`thumbnail-size`, `enable-hover-peek`, `hover-peek-time-in`, `hover-peek-time-out`,
`hover-peek-opacity`, `show-recent`, `show-all-workspaces`,
`window-display-settings`, `cycleMenusHotkey`, `show-apps-order-hotkey`,
`show-apps-order-timeout`, `super-num-hotkeys`.
Danh sách này lấy từ `settings-schema.json` của applet (33 khoá), đã đọc thật.

---

## 4. Cài đặt và hoàn tác

### 4.1 Không có gì để cài

Dock dùng **applet có sẵn** trong Cinnamon 6.6 (`files/usr/share/cinnamon/applets/`
của chính Cinnamon, không phải từ `cinnamon-spices-applets`). Thứ duy nhất cần có
là **theme đã cài**, việc đó thuộc T12.

**Trong toàn bộ tài liệu T11 không có lệnh `apt install` nào** — đó là tiêu chí
Done #3.

### 4.2 Hai thứ thay đổi trên máy người dùng

1. **Theme CSS** — nằm trong `~/.local/share/themes/MintOS-Glass/` (đường ghi được
   phép theo ADR-002, không cần root).
2. **gsetting của applet và của panel** — Cinnamon tự ghi vào
   `~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/`
   (đã xác minh: `js/ui/settings.js:744` dùng
   `GLib.get_user_config_dir()` + `cinnamon/spices/<uuid>`). Đây là **cơ chế lưu cấu
   hình chuẩn của chính Cinnamon**, không phải ta ghi tay vào file hệ thống.

Cả hai đều ở thư mục của người dùng, **không cần root, không sửa file hệ thống**.

### 4.3 Hoàn tác từng bước

Thứ tự quan trọng: làm ngược lại thứ tự đã cài.

**Bước 1 — trả gsetting của applet về mặc định.**
Mở *System Settings → Applets → Grouped Window List → Configure*, đặt lại các giá
trị ở `panel-layout.md` mục 3 về **mặc định** (bảng đó có ghi sẵn cột mặc định).
Cách này không cần terminal và không ghi file bằng tay.

**Bước 2 — trả chiều cao panel về mặc định.**
Kéo mép panel trong *Panel settings*, hoặc đặt lại gsetting `panels-height` về
`['1:40']` (mặc định thật, đã đọc từ `data/org.cinnamon.gschema.xml:147`).

**Bước 3 — đổi theme về theme cũ.**
*System Settings → Themes*, chọn lại theme Cinnamon như trước.

**Bước 4 — xoá theme (tuỳ chọn).**
Xoá thư mục `~/.local/share/themes/MintOS-Glass/`. Không có gì khác để dọn: không
package đã cài, không file hệ thống đã sửa, không schema đã thêm.

**Sau bước 3 hệ thống đã trở lại đúng trạng thái ban đầu**; bước 4 chỉ là dọn đĩa.
CLI tự động hoá các bước này thuộc **T12** — tài liệu T11 chỉ mô tả, không tự
chạy lệnh ghi.

---

## 5. Giới hạn còn lại, và các lựa chọn (chưa làm gì cả)

Yêu cầu Scope A: *"nếu cơ chế applet không đáp ứng được một yêu cầu, phải ghi rõ
giới hạn và đề xuất phương án TRƯỚC khi xây thành phần tuỳ chỉnh"*. Đây là phần đó.

| # | Giới hạn | Nguyên nhân (đã xác minh) | Phương án khả dĩ | Đề xuất |
|---|---|---|---|---|
| 1 | Không phóng to icon khi rê chuột | St không có `transform`; applet chỉ animate lúc launch (`appGroup.js:754`) | (a) chấp nhận; (b) sửa `appGroup.js` để thêm `ease({scale})` khi hover; (c) chuyển sang dock nổi | **(a) chấp nhận.** (b) là sửa file applet — bị cấm bởi "không sửa applet", và sẽ vỡ khi Mint cập nhật applet. (c) cần cài thêm phần mềm — bị cấm. Đã ghi rõ ở mục 2.1 để không ai hứa hiệu ứng này. |
| 2 | Chỉ báo "đang chạy" là thanh gạch chứ không phải chấm tròn | St không có pseudo-element | (a) thanh gạch (đang dùng); (b) dùng một ký tự trong `number-label` làm chấm | **(a).** (b) lạm dụng một label có nghĩa khác, sẽ xung đột khi app có nhiều cửa sổ. |
| 3 | CSS không phân biệt được nút **pinned** với nút **đang chạy** | Cả hai là cùng một class `.grouped-window-list-item-box`; applet không thêm class riêng để phân biệt | (a) chấp nhận; (b) sửa applet để thêm class | **(a) chấp nhận**, và **ghi rõ**. Đã grep 59 selector của T04: không có selector nào cho trạng thái "chỉ ghim mà không chạy". Nếu sau này muốn phân biệt thì phải quay lại phương án (b) — tức là sửa applet, cần duyệt trước. |
| 4 | Chiều cao "dock" bị giới hạn bởi chiều cao panel | Panel là một actor của shell; applet nằm trong đó | gsetting `panels-height` | Xem `panel-layout.md`. Đây là lý do dock **không thể** cao tuỳ ý như dock nổi. |
| 5 | Không có khoảng hở giữa dock và mép màn hình | Panel Cinnamon luôn áp sát mép | Chỉ dock nổi mới làm được | **Không làm.** Ghi rõ đây là điểm khác biệt thị giác thật so với macOS, và nó đến từ việc chọn "dock trong panel". |

---

## 6. Trạng thái kiểm chứng

### ĐÃ xác minh từ mã nguồn (Cinnamon 6.6.9)
- Danh sách 33 gsetting của applet, kèm giá trị mặc định và các lựa chọn —
  `settings-schema.json`
- `title-display` mặc định = `1` (None) → vốn đã chỉ-có-icon
- `launcher-animation-effect` mặc định = `3` (Scale), và hành vi thật
  0.8 → 1.1 → 1.0 / 175ms / `EASE_OUT_QUAD` — `appGroup.js:1165-1196`
- `animate()` chỉ được gọi từ `launchNewInstance()` — `appGroup.js:754`
- `pinned-apps` mặc định = `['nemo.desktop', 'firefox.desktop',
  'org.gnome.Terminal.desktop']` — `settings-schema.json`
- gsetting panel tên là **`panels-height`** (số nhiều), type `as`, mặc định
  `['1:40']` — `data/org.cinnamon.gschema.xml:147`
- có `panel-zone-icon-sizes`, mặc định
  `[{"panelId": 1, "left": 0, "center": 0, "right": 24}]` — cùng file `:156`
- cấu hình applet lưu ở `~/.config/cinnamon/spices/<uuid>/` — `js/ui/settings.js:744`
- 59 selector GWL đã có trong `_40-windowlist-gwl.scss` của T04
- St không có `transform` / pseudo-element / `box-sizing` — từ T04
  (`tests/fixtures/st-allowed-properties.txt`, 161 property đọc từ `st-theme-node.c`)

### CHƯA kiểm chứng — cần Cinnamon 6.6 thật
| Chưa kiểm chứng | Điều kiện để kiểm |
|---|---|
| 59 selector của T04 có cho ra đúng vẻ dock như thiết kế không | Cài theme, đặt panel xuống dưới, chụp màn hình |
| `panels-height` lớn hơn 40 có làm icon to ra tương ứng không, hay bị kẹp | Thử các giá trị 40/48/56/64 rồi đo |
| `panel-zone-icon-sizes` có tác động lên icon của GWL không (khoá đó mô tả zone, còn icon applet có thể theo đường khác) | Đặt giá trị khác 0 rồi xem |
| Thanh gạch dưới có bị nhảy layout khi chuyển trạng thái không | Bấm qua lại giữa các app, quan sát |
| Animation Scale có mượt ở 175ms trên máy thật không | Mở app từ dock |
| Có đúng là CSS không phân biệt được pinned/running không | Cần thử trên máy thật; kết luận hiện tại dựa trên việc grep selector và đọc `appGroup.js`, chưa thử bằng mắt |

**Không tuyên bố** bất kỳ mục nào trong bảng trên là đã đạt.
