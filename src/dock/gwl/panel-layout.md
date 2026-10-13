# Cấu hình panel cho dock MintOS Glass (T11)

**Task:** T11 · **Quyết định nền:** D-1 = `gwl`
**Đọc trước:** `src/dock/gwl/README.md` (đặc biệt mục 2 — những gì KHÔNG làm được)
**Style:** `src/cinnamon/overrides/_40-windowlist-gwl.scss` (T04, **không sửa ở đây**)

> Tệp này liệt kê **đúng những gsetting sẵn có** cần đặt để panel Cinnamon trông
> như một dock, kèm **giá trị mặc định thật** đã đọc từ mã nguồn. Không có lệnh cài
> package nào ở đây. Không sửa file applet nào.

---

## 1. Vì sao cấu hình nằm ở gsetting chứ không ở CSS

Hai thứ quyết định vẻ "dock" mà **CSS không với tới được**:

1. **Chiều cao panel.** Panel là một actor của Cinnamon shell, chiều cao do
   gsetting quyết định. CSS của applet chỉ vẽ **bên trong** phần panel được cấp.
2. **Ẩn nhãn cửa sổ.** Nhãn do **applet** sinh ra dựa trên gsetting
   `title-display`. T04 đã ghi chú: dùng CSS `width: 0` sẽ để lại khoảng trắng và
   phá căn giữa — đó là cách sai.

Nên dock = **CSS của T04** (màu, viền, nền, padding, trạng thái) **+ gsetting**
(hình học, nhãn). Hai tầng, không tầng nào thay được tầng kia.

**Tin tốt đã xác minh:** `title-display` **mặc định đã là `1` = "None"**, tức GWL
trên Mint 22.3 vốn **đã ở chế độ chỉ-có-icon**. Không cần đổi gì cho mục này.

---

## 2. gsetting của panel — schema `org.cinnamon`

Đã đọc từ `linuxmint/Cinnamon` @ 6.6.9, `data/org.cinnamon.gschema.xml`.

| Khoá | Type | **Mặc định thật** | Dùng cho dock |
|---|---|---|---|
| `panels-height` | `as` | `['1:40']` | Chiều cao panel. **Chú ý tên là số nhiều** — `panels-height`, không phải `panel-height`. Định dạng `"<panelId>:<px>"`. |
| `panel-zone-icon-sizes` | `s` | `'[{"panelId": 1, "left": 0, "center": 0, "right": 24}]'` | Kích thước icon theo từng vùng của panel. `0` = theo mặc định của zone. |

**Hai điều phải nói rõ, không được làm ngơ:**

- **`panels-height` có thể không phải giá trị thực tế lúc chạy.** Chính description
  trong gschema viết: *"Note, this value may or may not be the true value in use at
  runtime, depending on any scaling that may be occurring (on hidpi screens, for
  instance)."* Nên trên màn HiDPI, con số đặt vào **không** suy ra trực tiếp chiều
  cao pixel thật. Phải kiểm bằng mắt trên máy thật — chưa kiểm.
- **`panel-zone-icon-sizes` mô tả các ZONE của panel** (left/center/right), là nơi
  đặt applet và system tray. **Chưa xác minh** nó có tác động lên kích thước icon
  do chính GWL vẽ hay không — icon của applet có thể đi theo đường khác. Đã ghi
  thành mục chưa kiểm chứng, **không tuyên bố** là dùng được.

Đặt chiều cao thế nào: panel mặc định 40px. Muốn dock "dày" hơn thì tăng lên.
**Không có cơ sở đã kiểm chứng** cho một con số tối ưu, và giới hạn thật là icon
có bị kẹp hay không — việc đó phải thử trên máy thật. `README.md` mục 6 ghi rõ đây
là mục chưa kiểm chứng; **không** đưa ra một con số rồi gọi nó là đã tối ưu.

---

## 3. gsetting của applet — `grouped-window-list@cinnamon.org`

Đã đọc từ `settings-schema.json` của applet (33 khoá). Bảng dưới đây chỉ liệt kê
những khoá **liên quan tới vẻ dock**; các khoá còn lại **giữ nguyên mặc định**
(danh sách đầy đủ ở `README.md` mục 3).

| Khoá | Type | **Mặc định** | Các lựa chọn thật | Đề xuất cho dock |
|---|---|---|---|---|
| `title-display` | combobox | **`1`** | `1`=None · `2`=Application name · `3`=Window title · `4`=Window title (only for the focused window) | **`1` — đã là mặc định, không cần đổi.** Đây là thứ làm panel thành "chỉ có icon". |
| `launcher-animation-effect` | combobox | **`3`** | `1`=None · `2`=Fade · `3`=Scale | **`3` — đã là mặc định.** Xem mục 4 về giới hạn của nó. |
| `pinned-apps` | generic | `['nemo.desktop', 'firefox.desktop', 'org.gnome.Terminal.desktop']` | danh sách tên file `.desktop` | **Giữ mặc định**, hoặc người dùng tự ghim bằng kéo-thả. Không ghi đè danh sách này từ script — đó là thiết lập cá nhân. |
| `thumbnail-size` | combobox | `6` | `3`=Small · `6`=Medium · `9`=Large · `12`=Largest | **Giữ `6`.** Thumbnail không phải một phần của vẻ dock. |
| `enable-hover-peek` | checkbox | `True` | — | **Giữ nguyên.** Đây là chức năng, không phải thẩm mỹ. |

### Không ghi đè thiết lập cá nhân của người dùng

`pinned-apps` là danh sách app **người dùng đã chọn**. Một script cài đặt mà ghi đè
nó sẽ xoá các app họ đã ghim. Nên tài liệu này **chỉ mô tả giá trị**, và để người
dùng tự đặt qua *System Settings → Applets → Grouped Window List → Configure*.
Việc tự động hoá (nếu thật sự cần) thuộc **T12** và phải tôn trọng ràng buộc
"không ghi đè thiết lập cá nhân" đã áp dụng cho Nemo.

---

## 4. Nói đúng về animation

`launcher-animation-effect = 3 (Scale)` **có thật** và **là mặc định**. Hành vi đọc
từ `appGroup.js:1165-1196`:

```
effect === 3:
  iconBox.set_pivot_point(0.5, 0.5)
  iconBox.ease({scale_x: 0.8, scale_y: 0.8, duration: 175, EASE_OUT_QUAD})
    → iconBox.ease({scale_x: 1.1, scale_y: 1.1, duration: 175, EASE_OUT_QUAD})
      → về 1.0
```

**Nhưng nó chỉ chạy khi khởi chạy app.** `animate()` được gọi từ **đúng một chỗ**:
`appGroup.js:754`, bên trong `launchNewInstance()`. Không có đường mã nào nối
`hover` với `scale`.

| Nói | Đúng? |
|---|---|
| "Icon nảy nhẹ khi bấm mở app" | ✅ đúng |
| "Icon phóng to khi rê chuột (magnification kiểu macOS)" | ❌ **SAI — không tồn tại** |
| "Hover đổi nền, đổi viền, hiện nhãn" | ✅ đúng, đó là CSS của T04 |

Kết hợp với việc **St không có `transform`** (T04 đã dựng danh sách 161 property
cho phép bằng cách đọc các getter trong `st-theme-node.c`), hiệu ứng phóng-to-khi-rê
là **bất khả thi** trong khuôn khổ "không sửa applet". Đã ghi đầy đủ ở
`README.md` mục 2.1 cùng hai lớp bằng chứng.

---

## 5. Bố cục panel đề xuất

| Mục | Giá trị | Lý do |
|---|---|---|
| Vị trí panel | **dưới cùng** | Dock nằm ở cạnh dưới là bố cục người dùng mong đợi. CSS của T04 có cả bốn biến thể `.top`/`.bottom`/`.left`/`.right` nên đổi vị trí không phá style. |
| Căn applet | vùng **trái** hoặc **giữa** | Tuỳ chọn thẩm mỹ; không ảnh hưởng CSS. |
| Panel tự ẩn | **tắt** | Nếu bật, dock biến mất và mất luôn chức năng của một dock. Gsetting liên quan (`panel-autohide`, delay) thuộc cấu hình panel chung, **không** nằm trong phạm vi T11. |
| `title-display` | `1` (None) | đã là mặc định |
| `launcher-animation-effect` | `3` (Scale) | đã là mặc định |

**CSS của T04 đã phủ cả bốn vị trí panel** (`.grouped-window-list-item-box.top`,
`.bottom`, `.left`, `.right`, kể cả `StBin` con ở `.left`/`.right`), nên người dùng
đổi vị trí panel mà không cần sửa style.

---

## 6. Nhánh "nếu Plank đã có sẵn"

Tiêu chí Done #3 của T11: **không có lệnh `apt install` nào trong tài liệu**; chỉ
có nhánh "nếu plank đã có sẵn".

**D-1 đã chốt là `gwl`, nên nhánh này KHÔNG được dùng.** Nó chỉ tồn tại để ghi rõ
ranh giới:

- **Nếu** một máy nào đó **đã có sẵn** Plank (do người dùng tự cài từ trước, không
  phải do dự án cài), **thì** Plank đọc theme từ một file `dock.theme` theo schema
  riêng, hoàn toàn **không liên quan** tới CSS của St. Allow-list của T11 có dành
  chỗ `src/dock/plank/MintOS-Glass/dock.theme` cho trường hợp đó, với ràng buộc:
  đủ 2 section, đủ key, và màu dạng `R;;G;;B;;A` phải là **số nguyên**.
- **Dự án KHÔNG cài Plank, KHÔNG yêu cầu Plank, và KHÔNG kiểm thử với Plank.**
- **Tệp `dock.theme` đó hiện CHƯA được tạo**, vì D-1 = `gwl`. Nếu sau này cần thì
  phải sinh từ token (không gõ tay màu) và phải kiểm schema. **Không khai là đã có.**

Không có bất kỳ lệnh cài đặt nào trong toàn bộ `src/dock/`.

---

## 7. Trạng thái kiểm chứng

**ĐÃ xác minh từ mã nguồn** (Cinnamon 6.6.9): tên và type của `panels-height`
(`as`, mặc định `['1:40']`) và `panel-zone-icon-sizes` (mặc định
`[{"panelId":1,"left":0,"center":0,"right":24}]`) tại
`data/org.cinnamon.gschema.xml:147,156`; 33 khoá gsetting của applet kèm giá trị
mặc định và danh sách lựa chọn tại `settings-schema.json`; hành vi thật của ba
effect animation tại `appGroup.js:1165-1196`; chỗ gọi `animate()` duy nhất tại
`appGroup.js:754`; nơi lưu cấu hình applet tại `js/ui/settings.js:744`.

**CHƯA kiểm chứng** (cần Cinnamon 6.6 thật — không có máy nên **không tuyên bố**):
`panels-height` lớn hơn 40 có làm icon to ra tương ứng hay bị kẹp;
`panel-zone-icon-sizes` có tác động lên icon do GWL vẽ không; chiều cao pixel thật
trên màn HiDPI; thanh gạch dưới có gây nhảy layout khi đổi trạng thái không;
animation 175ms có mượt không.

**Việc tự động hoá các gsetting này thuộc T12** (installer/rollback CLI). T11 chỉ
mô tả giá trị và cách đặt qua giao diện Settings, **không** tự chạy lệnh ghi.
