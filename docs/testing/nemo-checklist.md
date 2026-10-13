# Nemo File Manager — bằng chứng, giới hạn và checklist kiểm thử

**Task:** T09 · Agent 4 (Nemo File Manager)
**Trạng thái:** đã triển khai phần offline; **chưa chạy trên máy Mint thật** (cổng T00)
**Phạm vi:** `src/gtk-3.0/sass/_apps-nemo.scss`, `_apps-mint.scss`,
`tools/lint/nemo_selectors.py`, `tests/fixtures/nemo-required-selectors.txt`,
`tests/lint/test_nemo_selectors.py`, tài liệu này.

> Tài liệu này tách rạch ròi **cái đã kiểm chứng** khỏi **cái chưa kiểm chứng**.
> Mục 8 là checklist phải chạy trên Linux Mint 22.3 / Cinnamon 6.6 thật. Không
> mục nào ở đây được phép đọc như "giao diện đã hoạt động".

---

## 1. Nguồn đã xác minh

Mọi kết luận bên dưới đều từ mã nguồn đã **tải về và đọc**, không suy đoán.

| Nguồn | Ref | Dùng để xác minh |
|---|---|---|
| `linuxmint/nemo` | `6.6-maintenance` @ tag **6.6.4** (`meson.build`: `version : '6.6.4'`) | 3 file CSS trong `gresources/`, toàn bộ style class, 7 style property |
| `linuxmint/nemo` | `master.mint22` @ **6.7.8**, head `ed2d34b390917fa11c1031176db489fd5cfbc915` | diff với 6.6.4 để biết stylesheet có an toàn trên cả hai bản |
| `GNOME/gtk` | ref **3.24.42** | `gtkstylecascade.c`, `gtkcssparser.c`, `gtkcssprovider.c`, `gtkapplicationwindow.c` |
| `linuxmint/{xed,pix,xplayer,xreader,xviewer,mintupdate,mintinstall}` | `master` | hook tạo kiểu của từng app Mint |
| `linuxmint/Cinnamon` | **6.6.9**, commit `806c1a4e` | `cinnamon-settings/**/*.py` |

### 1.1 Hai phiên bản Nemo — đã diff, không chọn bừa

Mint 22.3 cài nhánh nào **chưa xác minh được** (E2b2, thuộc cổng T00). Nên đã
tải cả hai và diff ba file CSS:

| File | 6.6.4 | 6.7.8 | Kết luận |
|---|---|---|---|
| `gresources/nemo-style-fallback.css` | 21 dòng | 21 dòng | **GIỐNG HỆT** |
| `gresources/nemo-style-fallback-mandatory.css` | 36 dòng | 36 dòng | **GIỐNG HỆT** |
| `gresources/nemo-style-application.css` | 83 dòng | 71 dòng | 6.6.4 **thêm 3 rule `#drop-bar`** (dòng 73-84) |

=> Fixture lấy **hợp (union)** của cả hai. Khác biệt duy nhất là `#drop-bar`,
được xử lý ở mục 5.4. **Stylesheet này an toàn trên cả 6.6.4 và 6.7.8.**

### 1.2 `#drop-bar` nhiều khả năng là CSS chết trong chính Nemo

Ba rule `#drop-bar` (chỉ có ở 6.6.4) nhắm vào một widget name không tồn tại:
`grep` toàn bộ `src/`, `libnemo-private/`, `eel/` của 6.6.4 cho
`gtk_widget_set_name` ra **đúng một** kết quả là `"nemo-tab-close-button"`;
chuỗi `drop-bar` chỉ trúng `g_signal_new("show-drop-bar", ...)` tại
`src/nemo-view.c:11200` — tên **signal**, không phải tên widget. Nemo 6.6.4 chỉ
có một file `.ui` duy nhất: `gresources/nemo-shortcuts.ui`.

**Chưa xác minh được** widget đó có tồn tại ở nhánh khác hay do extension tạo ra.
Vì nó nằm ở `PRIORITY_APPLICATION` nên theme không thắng được dù sao — ta **không
viết rule cho nó** và **không yêu cầu** nó trong fixture.

---

## 2. Phát hiện kiến trúc quan trọng nhất: ba mức ưu tiên provider

`src/nemo-application.c:306-330` (`init_icons_and_styles`):

| CSS của Nemo | Hằng ưu tiên | Giá trị | So với theme (`PRIORITY_THEME` = 200) |
|---|---|---|---|
| `nemo-style-fallback.css` | `PRIORITY_FALLBACK` | **0** | **Theme THẮNG** |
| `nemo-style-application.css` | `PRIORITY_APPLICATION` | **600** | **Nemo THẮNG** |
| `nemo-style-fallback-mandatory.css` | `PRIORITY_APPLICATION` | **600** | chỉ nạp **có điều kiện** — xem mục 3 |

### 2.1 GTK 3.24 KHÔNG hỗ trợ `!important` — nên priority là tuyệt đối

Đã tải `GNOME/gtk` ref 3.24.42 và đếm chuỗi `important`:

| File | Số dòng | Số lần xuất hiện `important` |
|---|---|---|
| `gtk/gtkcssparser.c` | 1067 | **0** |
| `gtk/gtkcssprovider.c` | 2405 | **0** |
| `gtk/gtkstylecascade.c` | 426 | **0** |

Parser là nơi **duy nhất** có thể nhận diện cú pháp `!`; nếu parser không đọc nó
thì không tầng nào phía sau dùng được. Thêm nữa, `gtk_style_cascade_iter_next()`
(`gtkstylecascade.c:42-71`) chọn provider có `priority` **cao nhất trước** và
`gtk_style_cascade_lookup()` (`:231-258`) duyệt theo đúng thứ tự giảm dần đó để
điền vào `GtkCssLookup`.

**=> Specificity cao hơn hay `!important` đều KHÔNG lật ngược được priority.**
Mọi selector nhóm `[LOCK]` trong stylesheet là bất khả xâm phạm từ phía theme.
Lint `no-important` chặn cứng để không ai thêm vào với niềm tin sai.

> Ghi chú trung thực: `gtk/gtkcssdeclaration.c` **không tải được** trong phiên
> làm việc này (lỗi mạng). Kết luận vẫn vững vì parser là tầng bắt buộc phải đọc
> cú pháp `!` trước tiên, và nó có 0 kết quả.

---

## 3. Tên theme là MỘT PHẦN CỦA CƠ CHẾ — phát hiện ngoài dự kiến

`src/nemo-application.c:283-303` (`process_system_theme`):

```
if (!is_known_supported_theme (theme_name))
    add_fallback_mandatory_css_provider (theme_name);
```

`:245` `supported_theme_hints[] = {"mint", "arc", "numix", "matcha"}`
`:259` `name = g_utf8_casefold (theme_name, -1)`
`:267` `if (g_strstr_len (name, -1, hint)) ret = TRUE;` ← **SO KHỚP CHUỖI CON**

**"MintOS-Glass" → casefold "mintos-glass" → chứa "mint" → TRUE.**
Nemo coi theme của ta là "đã biết có hỗ trợ Nemo" và **KHÔNG nạp**
`nemo-style-fallback-mandatory.css`.

### 3.1 Hai hệ quả, cả hai đều đã xử lý

**(a) Không ai style hộ ba bề mặt này — ta PHẢI tự viết.**
`nemo-style-fallback-mandatory.css` chứa đúng ba thứ: pane không hoạt động (dòng
6), ô nhập trong khung nhìn (dòng 12, 20), thanh nổi (dòng 30). Vì nó không được
nạp, nếu T09 bỏ sót thì chúng rơi về **GTK mặc định** (nền sáng, viền mặc định) —
vỡ giao diện tối ngay giữa cửa sổ. Cả ba đã có mặt và được khoá bằng
`test_inactive_pane_and_entry_and_floating_bar_all_styled`.

**(b) Ràng buộc đặt tên có căn cứ kỹ thuật.**
Nếu đổi tên theme sang thứ **không** chứa `mint`/`arc`/`numix`/`matcha` (ví dụ
"GlassOS"), Nemo sẽ nạp fallback-mandatory ở priority **600** và **đè lên** theme
của ta cho đúng ba selector trên. Đây là ràng buộc kỹ thuật **độc lập** với câu
hỏi chính sách đặt tên Linux Mint đang mở.

Lớp kiểm tra thứ hai (`:173-243`), chỉ chạy khi tên không lọt hint: Nemo
serialize CSS của theme bằng `gtk_css_provider_to_string()` rồi tìm chuỗi con
`"nemo"`; không thấy thì in *"The theme appears to have no nemo support. Adding
some..."*. **Output CSS bắt buộc phải chứa chuỗi `nemo`** — lint `nemo-substring`
và `test_output_contains_nemo_substring` khoá điều đó.

Cùng hàm (`:203-217`) quyết định cách phân giải màu:

| Theme có chứa | Nemo làm gì |
|---|---|
| `theme_selected_bg_color` | giữ nguyên `@theme_*` |
| `@define-color selected_bg_color` | thay `@theme_` → `@` |
| không có cả hai | **bỏ luôn**, không nạp gì |

**=> T06 phải export đủ 5 symbol `@theme_*`** (đã là Done criterion #2 của T06,
nguồn E29). Nếu không, `alpha(@theme_selected_bg_color, 0.8)` trong
`nemo-style-application.css:38` không phân giải được và nền icon desktop khi được
chọn sẽ hỏng — **mà T09 không sửa được từ phía mình**.

Toàn bộ ký hiệu `@` mà ba file CSS của Nemo dùng (đã trích):
`@theme_selected_bg_color` ×7, `@theme_bg_color` ×4, `@theme_selected_fg_color` ×3,
`@theme_fg_color` ×2, `@theme_unfocused_bg_color` ×1, **`@borders` ×1**.
`@borders` **không** phải symbol `theme_*` — nó là tên của Adwaita, chỉ dùng trong
rule `#drop-bar > revealer > box` của 6.6.4. Cần T06 kiểm tra xem
`tests/fixtures/gtk-public-colors.txt` (E33) có `@borders` không.

---

## 4. Kết quả triển khai — số liệu thật

Chạy bằng `libsass 3.6.6` (thứ Mint thật dùng, E18) và `dart-sass 1.77.8`:

| Chỉ số | `_apps-nemo.scss` | `_apps-mint.scss` |
|---|---|---|
| Compile được | ✅ | ✅ |
| Kích thước output | 8 143 B | 2 481 B |
| Số selector trong output | **89** | **31** |
| Số selector fixture bắt buộc | **60/60 phủ đủ** | — |
| Selector nhóm `[LOCK]` viết ra có chủ đích | 16 | 0 |
| libsass vs dart-sass | **299/299 dòng GIỐNG HỆT** | **114/114 dòng GIỐNG HỆT** |
| Lint `nemo_selectors.py` | **OK — 0 lỗi, 0 cảnh báo** | ✅ |
| Test `test_nemo_selectors.py` | **46/46 OK** | ✅ |
| `make check` toàn repo | **OK — 111 tests, OK (skipped=1)** | ✅ |

Bài skip duy nhất là `TestAssets` của T04 (chờ T05 giao 15 file SVG) — không liên
quan T09.

### 4.1 12 bài kiểm tra của `tools/lint/nemo_selectors.py`

| # | id | Kiểm tra |
|---|---|---|
| 1 | `nemo-substring` | output chứa chuỗi `nemo` (điều kiện `nemo-application.c:186`) |
| 2 | `coverage` | đủ 60/60 selector fixture |
| 3 | `disk-full-props` | đủ cả 6 `-NemoPlacesTreeView-disk-full-*` |
| 4 | `no-prelight-label` | **cấm** ghi đè `-NemoIconContainer-activate-prelight-icon-label` |
| 5 | `no-important` | không `!important` (GTK 3.24 không hỗ trợ) |
| 6 | `no-broken-tokens` | không dùng token generator sinh sai |
| 7 | `no-hardcoded-color` | màu phải qua token |
| 8 | `gtk3-property-blocklist` | không dùng property GTK 3.24 không có |
| 8b | `no-bare-generic` | không phát class GTK chung ở dạng **trần** |
| 9 | `no-locked-illusion` | selector `[LOCK]` phải được fixture khai báo |
| 10 | `fixture-integrity` | fixture không bị ô nhiễm |
| 11 | `mint-apps-entries` | đủ 9 app Mint có một mục |
| 12 | `mint-apps-namespaced` | `_apps-mint.scss` không rò rỉ toàn cục |

Lint **không crash** khi SCSS hỏng cú pháp: nó trả về `FAIL compile` có id riêng
(`test_lint_does_not_crash_on_uncompilable_scss`).

---

## 5. Tương phản — ĐO BẰNG `tools/lint/contrast.py`, KHÔNG ĐOÁN

Done criterion #3 yêu cầu "≥ 3:1 **đo trên một wallpaper mẫu**, không đoán".

**Giới hạn trung thực:** không có máy Mint thật (cổng T00) nên **không chụp được
ảnh desktop thật**. Thay vào đó đã đo trên **ba mức chói wallpaper chặn hai đầu**
(trắng `#ffffff` / trung tính `#808080` / đen `#000000`) — wallpaper thật là ảnh
có dải chói nằm trong khoảng đó. Đo bằng chính `tools/lint/contrast.py` của repo
(composite source-over + WCAG relative luminance), không tự viết lại công thức.
Script tái tạo nằm trong `tests/lint/test_nemo_selectors.py::TestDesktopLabelContrast`
nên con số được **kiểm tra tự động mỗi lần chạy test**, không phải số ghi tay.

### 5.1 Trạng thái SELECTED — **token hiện tại FAIL ở cả ba mức**

Chữ `#f5f5f5` (`$mg-nemo-desktop-label-selected-text`) trên nền
`rgba(61,220,151,0.8)` (`$mg-nemo-desktop-label-selected-background`) đã composite:

| Wallpaper | Nền hiệu dụng | Tương phản | 3:1 |
|---|---|---|---|
| `#ffffff` (sáng nhất) | `#64e3ac` | **1.47:1** | ❌ FAIL |
| `#808080` | `#4aca92` | **1.90:1** | ❌ FAIL |
| `#000000` (tối nhất) | `#31b079` | **2.53:1** | ❌ FAIL |

FAIL ở **cả ba** mức ⇒ **không có wallpaper nào cứu được**. Đây đúng là tiền lệ
đã chốt ở T02/T04: trắng trên mint `#2bb67a` = 2.60:1 FAIL, `gray-950` trên mint
= 7.52:1 PASS ⇒ chip accent lật sang `text-on-accent`.

**Phương án đã áp dụng** — `$mg-text-on-accent` (`#0b0c0e`) trên cùng ba nền:

| Wallpaper | Nền hiệu dụng | Tương phản | 3:1 |
|---|---|---|---|
| `#ffffff` | `#64e3ac` | **12.23:1** | ✅ PASS |
| `#808080` | `#4aca92` | **9.46:1** | ✅ PASS |
| `#000000` | `#31b079` | **7.10:1** | ✅ PASS |

**Việc cần Agent Design Systems làm:** đổi
`nemo.desktop.label.selected.text` từ `#f5f5f5` → `#0b0c0e` trong
`design/tokens/*.json`. T09 **không được sửa** file đó (sở hữu của Agent 1). Trong
lúc chờ, stylesheet dùng thẳng `$mg-text-on-accent` và
`test_stylesheet_uses_on_accent_not_the_failing_token` khoá quyết định này;
`test_selected_label_fails_with_the_token_value` sẽ **đỏ** ngay khi token được sửa
— đó là chủ đích, để người sửa biết phải cập nhật stylesheet về lại token.

### 5.2 Trạng thái HOVER — PASS ở cả ba mức

Nền `rgba(0,0,0,0.5)`, chữ `#eeeeee`, Nemo tắt `text-shadow`:

| Wallpaper | Nền hiệu dụng | Tương phản | 3:1 |
|---|---|---|---|
| `#ffffff` | `#808080` | **3.40:1** | ✅ PASS (sát ngưỡng) |
| `#808080` | `#404040` | **8.94:1** | ✅ PASS |
| `#000000` | `#000000` | **18.10:1** | ✅ PASS |

`3.40:1` trên wallpaper trắng là **sát ngưỡng 3:1**. Nếu muốn dư địa, tăng alpha
nền hover từ `0.5` lên `0.6`–`0.65`. Đề xuất, không tự đổi token.

### 5.3 Nhãn CHƯA CHỌN — shadow LỆCH để hở mép glyph

`$mg-nemo-desktop-label-shadow` = `1px 1px 0px rgba(0,0,0,0.8)`, và Nemo cũng dùng
`1px 1px alpha(black,0.8)` (`nemo-style-application.css:28`). Vì shadow **lệch 1px
xuống-phải**, mép **trên-trái** của glyph **không được shadow đỡ** và nằm thẳng
lên wallpaper:

| Wallpaper | Mép KHÔNG có shadow | Thân chữ trên shadow | Nền shadow |
|---|---|---|---|
| `#ffffff` | **1.16:1** ❌ FAIL | **10.89:1** ✅ | `#333333` |
| `#808080` | **3.40:1** ✅ | **15.00:1** ✅ | `#1a1a1a` |
| `#000000` | **18.10:1** ✅ | **18.10:1** ✅ | `#000000` |

**Trên wallpaper sáng, nét chữ phía trên-trái bị mất.** Shadow **không lệch**
(`0 0 2px rgba(0,0,0,0.8)`) che được cả mép: **10.89:1** ngay cả trên nền trắng
(đã đo). ⇒ Đề xuất Agent Design Systems đổi token sang shadow không lệch, hoặc
shadow 4 hướng. T09 không tự sửa token.

### 5.4 Xung đột token đã đo: bán kính canvas item

| | Giá trị | Ai thắng trên desktop |
|---|---|---|
| `$mg-nemo-desktop-canvas-radius` | `4px` | — |
| `nemo-style-application.css:19` | `border-radius: 3px` | **Nemo** (priority 600) |

Token `4px` **không có tác dụng** trên desktop. Ba lựa chọn: chấp nhận 3px, đổi
token thành 3px, hoặc dùng đường `PRIORITY_USER` (mục 6). **Cần quyết định, không
được im lặng bỏ qua** — đã ghi trong SCSS, fixture và `test_canvas_radius_conflict_is_recorded`.

Hai token còn lại **khớp** với giá trị Nemo đang dùng nên an toàn:
`$mg-nemo-desktop-label-text = #eeeeee` (Nemo: `#eeeeee`),
`$mg-nemo-desktop-label-shadow = 1px 1px 0px rgba(0,0,0,0.8)` (Nemo: `1px 1px alpha(black,0.8)`).

---

## 6. Cái gì theme kiểm soát được, cái gì không

### 6.1 `[WIN]` — theme(200) thắng, rule có tác dụng thật

| Vùng | Selector tiêu biểu | Vì sao thắng |
|---|---|---|
| Cửa sổ, toolbar, pathbar, tab | `.nemo-window`, `.nemo-window .primary-toolbar`, `.nemo-window .path-bar button`, `.slider-button`, `#nemo-tab-close-button` | Nemo không style |
| Sidebar (phân cấp Finder) | `.nemo-window .sidebar row{,:hover,:selected}`, `.nemo-places-sidebar row …` | Nemo không style |
| **Chỉ báo dung lượng ổ đĩa** | `.places-treeview` + **6** `-NemoPlacesTreeView-disk-full-*` | Nemo để ở `FALLBACK`(0) |
| Pane không hoạt động (F3) | `.nemo-inactive-pane`, `.view:not(:selected)`, `iconview` | fallback-mandatory **không được nạp** |
| Ô đổi tên / nhập đường dẫn | `.nemo-window .nemo-window-pane widget.entry{,:selected,:focus}` | như trên |
| Thanh nổi (tắt status bar) | `.floating-bar`, `.floating-bar button` | như trên |
| Chỉ báo kéo-thả | `.treeview-drop-indicator` | Nemo **không có rule nào** cho nó |
| Nhãn mờ | `.dim-label` | Nemo không style |
| Khung nhìn icon desktop | `nemo-desktop-icon-view` (node name) | Nemo không style |

### 6.2 `[LOCK]` — Nemo giữ ở `APPLICATION`(600), theme **không** thắng

16 selector: `.nemo-canvas-item`, `.nemo-desktop`, `.nemo-desktop-window{,:backdrop}`,
`.nemo-window.nemo-desktop-window notebook|paned`,
`.nemo-desktop.nemo-canvas-item{,:hover,:selected}`,
`.nemo-desktop.view .entry{,:active,:focus,:backdrop,:selected,:focus:selected,:backdrop:selected}`.

Cụ thể Nemo khoá property nào (`LOCKED_PROPS` trong lint):
`.nemo-canvas-item` → chỉ `border-radius`;
`.nemo-desktop.nemo-canvas-item` → `color`, `text-shadow`;
`:hover` → `background-color`, `background-image`, `text-shadow`;
`:selected` → cả bốn; `.nemo-desktop.view .entry` → 9 property (viền, màu chữ,
caret, gradient nền trắng).

**Nghĩa là: hình dạng nhãn icon trên DESKTOP không đổi được từ theme.** Nhưng
`.nemo-canvas-item` **không** kèm `.nemo-desktop` là canvas item **trong cửa sổ
thường** (icon view), nơi Nemo chỉ khoá `border-radius` — nên `color` của nó trong
cửa sổ **vẫn do ta quyết**. Đó là lý do khối `[LOCK]` không phải CSS chết hoàn toàn.

### 6.3 Đường thoát cho phần bị khoá — KHÔNG cần fork Nemo

GTK3 nạp `~/.config/gtk-3.0/gtk.css` ở **`PRIORITY_USER` (800)**, cao hơn
`APPLICATION` (600). Đó là cơ chế **chuẩn** của GTK3, ở cấp người dùng, không sửa
file hệ thống, không fork, gỡ được bằng cách xoá file.

Nếu cần thật sự đổi nhãn icon desktop, T12 (installer) có thể cài **tuỳ chọn** một
snippet `PRIORITY_USER` chứa đúng khối `[LOCK]` này. **T09 chưa làm** vì:
(1) nó ghi vào thư mục cấu hình người dùng, thuộc thẩm quyền T12;
(2) nó xung đột với yêu cầu "script không được ghi đè thiết lập cá nhân của người
dùng hiện có" — phải phân biệt tài khoản mới và tài khoản đã có;
(3) chưa có quyết định về xung đột bán kính 4px/3px (mục 5.4).

Đây là **đề xuất đã cân nhắc**, không phải việc đã làm.

### 6.4 Không fork, không patch Nemo

Task yêu cầu: chỉ fork/patch khi yêu cầu UI quan trọng **không** thể đạt bằng cách
ít xâm lấn hơn, và phải kèm 5 mục (lý do, file cần sửa, ảnh hưởng cập nhật, chi
phí bảo trì, kế hoạch rollback). **T09 KHÔNG đề xuất fork.** Mọi thứ đạt được bằng
theme + cơ chế chuẩn của GTK3. Phần không đạt được (mục 6.2) đã có đường thoát ít
xâm lấn hơn fork là `PRIORITY_USER` (mục 6.3) — nên điều kiện "không thể đạt bằng
cách ít xâm lấn hơn" **chưa** thoả mãn.

---

## 7. Ứng dụng Mint khác — kết quả khảo sát từng app

**Phát hiện quyết định:** GTK 3.24 **KHÔNG đưa application ID vào CSS**. Đã tải
`GNOME/gtk` ref 3.24.42: `gtk/gtkapplicationwindow.c` (1048 dòng) có **0 lần** xuất
hiện chuỗi `application_id` — `GtkApplicationWindow` không thêm app ID làm style
class, không dùng nó làm CSS node name.

**Hệ quả:** không có cách nào scope một class **chung** về đúng một app. Viết
`.content-view { … }` trong partial của app sẽ áp lên **mọi** app GTK3 dùng class
đó. Nên `_apps-mint.scss` chỉ dùng: (a) class có tên app **trong chính tên class**;
(b) CSS **node name** độc nhất; (c) **widget name** (`#`) độc nhất. Lint
`mint-apps-namespaced` thực thi quy tắc này và chặn cả `#frame` (xplayer có widget
name `frame` nhưng tên quá chung, sẽ trúng widget cùng tên của app khác).

| App | Hook riêng? | Bằng chứng (file:dòng) | Xử lý |
|---|---|---|---|
| **nemo** | ✅ 18 class + 1 widget name + 1 node | `src/nemo-window.c:1999`, `nemo-window-pane.c:1067,1095`, `nemo-places-sidebar.c:4168`, `nemo-pathbar.c:172,379`, `nemo-config-base-widget.c:33,41,71`, `nemo-floating-bar.c:257`, `nemo-blank-desktop-window.c:408`, `nemo-properties-window.c:4971`, `nemo-query-editor.c:182`, `nemo-desktop-icon-grid-view.c:379`, `libnemo-private/nemo-places-tree-view.c:32,43-83`, `nemo-icon-container.c:7141,4861`, `nemo-icon-canvas-item.c:478,1147`, `nemo-tree-view-drag-dest.c:206` | `_apps-nemo.scss` |
| **xreader** | ✅ 5 class + 3 node + 1 name | `shell/ev-window.c:7490` `.xreader-window`; `libview/ev-view.c:5655` node `evview`, `:5827` `.content-view`; `libview/ev-view-presentation.c:1420` node `evpresentationview`, `:153` `.white-mode`; `shell/ev-sidebar-thumbnails.c:439` node `evsidebarthumbnails`; `libdocument/ev-document-misc.c:114,116` `.page-thumbnail`, `.inverted`; name `page-label-entry` | mục 2 |
| **pix** | ✅ 14 class + 1 node + 1 name | `pix/gth-empty-list.c:299` `.empty-view`; `gth-grid-view.c:3748` node `iconview`, `:1327` `.icon`; `gth-curve-editor.c:467` `.histogram`; `gth-progress-dialog.c:155` `.pix-circular-button`; `gth-filter-grid.c:323` `.filter-preview`; `extensions/importer/gth-import-destination-button.c:72` `.highlighted-text`; `dlg-preferences-extensions.c:469,476`; + `void-view`, `toolbox`, `video-player`, `window-overlay`, `title`, `revert-shortcut-button`; name `GthInfoBar` | mục 3 |
| **xed** | ⚠️ chỉ 1 class riêng | `xed/xed-statusbar.c:155` `.xed-statusbar` ← RIÊNG. `xed/xed-searchbar.c:712` `.close-button`, `xed/xed-print-preview.c:567` `.inline-toolbar`, `plugins/filebrowser/xed-file-browser-widget.c:927` `.small-button` ← **CHUNG** | mục 4 |
| **xplayer** | ⚠️ chỉ widget name | `#stage`, `#logo-frame` dùng được; `#frame` **loại** vì quá chung. `src/plugins/grilo/xplayer-grilo.c:1208` `.content-view` và `libgd/gd-tagged-entry.c:228` `.documents-entry-tag` ← **CHUNG** | mục 5 |
| **xviewer** | ❌ **KHÔNG có** | 48 file nguồn, **0** kết quả cho cả `add_class` riêng, `set_name`, `set_css_name` | mục 6 — không viết selector |
| **mintupdate** | ❌ **KHÔNG có** | 0 hook. App ID `com.linuxmint.mintupdate` tìm được nhưng GTK3 không đưa ID vào CSS | mục 7 — không viết selector |
| **mintinstall** | ❌ **KHÔNG có** | 10 file nguồn, 0 hook, không tìm thấy app ID | mục 8 — không viết selector |
| **cinnamon-settings** | ❌ **KHÔNG có** | Cinnamon 6.6.9 `806c1a4e`, quét toàn bộ `files/usr/share/cinnamon/cinnamon-settings/**/*.py`: **1** kết quả duy nhất `modules/cs_backgrounds.py:220` `.inline-toolbar` ← CHUNG | mục 9 — không viết selector |

**Tóm tắt trung thực:** 5/9 app có hook để theme nhắm riêng (nemo, xreader, pix ở
mức đầy đủ; xed, xplayer ở mức giới hạn). **4/9 app KHÔNG có hook nào** — với
chúng, câu trả lời đúng là *"theme GTK3 không thể nhắm riêng vào app này"*, chứ
không phải viết selector đoán mò. Giao diện của 4 app đó do widget GTK chung quyết
định, tức là **T06**.

**Đính chính E30:** plan ghi `nemo-desktop-icon-view` là "style class". Thực tế
`src/nemo-desktop-icon-grid-view.c:379` dùng
`gtk_widget_class_set_css_name(wclass, "nemo-desktop-icon-view")` — là **CSS node
name**, selector đúng là **tên trần không dấu chấm**. Cũng E30 ghi
`nemo-places-sidebar` ở dòng 4161 và `GTK_STYLE_CLASS_SIDEBAR` ở dòng 428; trong
6.6.4 là **4168** và **430**.

**Thiếu token ngữ nghĩa (đã ghi nhận, không tự thêm):** hệ token là dark-first nên
**không có** surface nào nghĩa là "mặt giấy trắng". `_apps-mint.scss` cần nó cho
trang tài liệu xreader (`evview.page-thumbnail`) và `evpresentationview.white-mode`.
Tạm dùng primitive `$mg-color-white` (`#ffffff`) kèm ghi chú. **Không** dùng
`$mg-text-primary` vì nó là `rgba(255,255,255,0.92)` — bán trong suốt, làm nền sẽ
ra **xám** chứ không phải trắng, và dùng token chữ làm token nền là sai ngữ nghĩa
(đã viết nhầm ở bản nháp đầu, đã sửa). Cần Agent 1 bổ sung dạng `surface.paper` /
`surface.page`.

**GtkSourceView (xed):** tự nạp scheme màu **riêng** của nó, không qua `gtk.css`
của theme ⇒ **tô màu cú pháp trong xed không điều khiển được từ theme**. Ghi rõ để
không ai tưởng file này làm được việc đó.

---

## 8. Phân loại kiểm tra: offline / CI / cần máy Mint thật

### (a) Đã chạy OFFLINE và XANH — kết quả thật

| Lệnh | Kết quả thật |
|---|---|
| `python3 tools/lint/nemo_selectors.py -v` | `OK — 0 lỗi` · coverage **60/60** · output **89** selector · **16** selector `[LOCK]` |
| `python3 -m unittest tests.lint.test_nemo_selectors` | **Ran 46 tests — OK** |
| `python3 -m unittest discover -s tests -t .` | **Ran 111 tests — OK (skipped=1)** |
| `make check` | **OK — make check xanh** |
| dart-sass vs libsass trên cả hai partial | **299/299** và **114/114** dòng GIỐNG HỆT |

Môi trường chạy: `PATH=/home/user/.mintos-toolchain/venv/bin:$PATH`. Toolchain nằm
**ngoài** repo (`~/.mintos-toolchain/{venv,node_modules}`) vì
`tools/lint/safety_paths.py:43` `SKIP_DIRS` không có `.venv`/`venv`, venv trong repo
sẽ tạo 31 vi phạm giả từ mã nguồn của chính pip. Đã báo Agent Platform/DevEx.

### (b) Chạy được trong CI (không cần máy Mint)

Toàn bộ mục (a), cộng: `dart-sass` đối chiếu. **Cần bổ sung vào CI** — hiện
`.github/workflows/ci.yml` job `scss` chỉ tự kích hoạt cho
`src/{cinnamon/cinnamon,gtk-3.0/sass/gtk,gtk-4.0/sass/gtk}.scss`, mà **`gtk.scss` là
file của T06 và chưa tồn tại**, nên `_apps-nemo.scss` **chưa được CI biên dịch**.
Hai việc cần Agent Platform/DevEx làm: thêm `tools/lint/nemo_selectors.py` vào job
lint, và đảm bảo `gtk.scss` của T06 `@import "apps-nemo"` + `@import "apps-mint"`.

### (c) **BẮT BUỘC chạy trên Linux Mint 22.3 / Cinnamon 6.6 thật**

Mọi thứ liên quan đến **hành vi runtime**, **bố cục thật**, và **tương phản trên
wallpaper thật**. Không mục nào dưới đây đã được kiểm chứng.

---

## 9. CHECKLIST KIỂM THỬ TRÊN MÁY MINT THẬT

Điều kiện: Linux Mint 22.3, Cinnamon 6.6, theme đã cài ở
`~/.local/share/themes/MintOS-Glass` (ADR-002), **T06 đã giao `gtk.scss`** và đã
`@import` hai partial này. Ghi lại `nemo --version` trước khi bắt đầu.

### 9.0 Trước tiên — xác minh cơ chế (quan trọng nhất)

| # | Việc | Kỳ vọng | Nếu sai thì |
|---|---|---|---|
| 0.1 | `nemo --version` | ghi lại 6.6.x hay 6.7.x | đối chiếu mục 1.1 |
| 0.2 | Mở Nemo, xem terminal chạy nó hoặc `journalctl --user -b \| grep -i nemo` | **KHÔNG** có *"Current gtk theme is not known to have nemo support"* và **KHÔNG** có *"The theme appears to have no nemo support"* | tên theme không lọt hint → xem mục 3.1(b) |
| 0.3 | `grep -c nemo ~/.local/share/themes/MintOS-Glass/gtk-3.0/gtk.css` | **> 0** | T06 chưa `@import "apps-nemo"` |
| 0.4 | `grep -oE '@define-color theme_[a-z_]+' …/gtk.css \| sort -u` | đủ **5** symbol `theme_bg_color`, `theme_fg_color`, `theme_selected_bg_color`, `theme_selected_fg_color`, `theme_unfocused_bg_color` | T06 thiếu → icon desktop khi chọn sẽ hỏng (mục 3.1) |
| 0.5 | Dùng `gtk-inspector` (nếu bật được) xem provider list của một widget Nemo | theme ở priority 200, `nemo-style-fallback.css` ở 0, `nemo-style-application.css` ở 600 | nếu thấy `fallback-mandatory` ở 600 → mục 3.1(b) đã xảy ra |

### 9.1 Cửa sổ chính (yêu cầu 3.1)

- [ ] Nền cửa sổ, toolbar, vùng chứa file có **ba bậc phân cấp** rõ, không phẳng lì
- [ ] Toolbar gọn, không trang trí ăn mất diện tích hữu ích
- [ ] Tiêu đề + cụm nút điều hướng trình bày thống nhất
- [ ] Cửa sổ **active / không active (backdrop) / có focus** khác nhau rõ
- [ ] Mở **2 tab**, đóng tab bằng `#nemo-tab-close-button` — nút hiện rõ khi rê
- [ ] Phóng to / thu nhỏ / kéo giãn cửa sổ: không vỡ bố cục, không lộ nền sáng
- [ ] Cửa sổ ở chế độ **fullscreen (F11)**
- [ ] **HiDPI / fractional scaling (125%, 150%, 200%)**: viền 1px không biến mất, bo góc không méo

### 9.2 Thanh đường dẫn (3.2)

- [ ] Đủ **4** cách điều hướng: Back, Forward, Up, nhập đường dẫn trực tiếp — **không mất cái nào**
- [ ] Đi sâu tới `/usr/share/applications` để đường dẫn **tràn**: mũi tên trượt `.slider-button` **phải hiện ra và bấm được**
- [ ] Chuyển sang **chế độ nhập text** của pathbar (thường là bấm vào vùng đường dẫn) → ô nhập phải theo theme tối, không trắng loá
- [ ] **Điều hướng hoàn toàn bằng bàn phím:** `Alt+←` back, `Alt+→` forward, `Alt+↑` up, `Ctrl+L` mở pathbar, `Tab`/`Shift+Tab` di chuyển focus, `Enter` mở
- [ ] Focus ring nhìn thấy được ở **mọi** widget (không chỉ pathbar)

### 9.3 Sidebar (3.3) — kiểm tra kỹ nhất vì dễ hard-code sai

- [ ] Có đủ Home, Desktop, Documents, Downloads, Pictures, Music, Videos
- [ ] **Trên hệ thống tiếng Việt:** tên các thư mục XDG hiển thị đúng bản dịch
      (`Tài liệu`, `Tải xuống`, …). **Theme không được quyết định tên này** — nếu
      thấy tên tiếng Anh trên hệ tiếng Việt thì đó là cấu hình `user-dirs.dirs`,
      không phải lỗi theme
- [ ] Cắm **USB / thẻ nhớ / ổ di động**: xuất hiện trong mục Devices, gỡ ra thì biến mất
- [ ] Ổ có **chỉ báo dung lượng**: thanh disk-full hiện đúng, **không tràn** ra ngoài hàng
- [ ] **Chỉ báo disk-full trên hàng ĐANG ĐƯỢC CHỌN** phải đọc được (đã đổi sang
      `$mg-border-control` + `$mg-text-primary` trong stylesheet)
- [ ] Mục **Network**: hiện khi có; bấm vào vị trí mạng **không truy cập được** → xem 9.6
- [ ] Thêm một bookmark bằng `Ctrl+D` → xuất hiện ngay, style đúng, **không cần khởi động lại**
- [ ] Kéo giãn sidebar: hàng không vỡ, chữ không bị cắt không có dấu hiệu
- [ ] Sidebar ở chế độ **RTL** (nếu bật được locale RTL): viền phải đổi sang trái
      (đã viết `:dir(rtl)`)

### 9.4 Vùng hiển thị file (3.4)

**Mọi chế độ xem — bắt buộc thử cả bốn:**
- [ ] **Icon view** (`Ctrl+1`): khoảng cách, cỡ icon, nhãn rõ; folder vs file vs
      được-chọn vs có-focus **phân biệt được bằng mắt thường**
- [ ] **List view** (`Ctrl+2`): sắp xếp theo từng cột (tên, kích thước, loại, ngày,
      quyền); hàng xen kẽ nếu có; cột đổi kích thước được
- [ ] **Compact view** (`Ctrl+3`)
- [ ] **List view với rất nhiều cột** + thanh cuộn ngang

**Thao tác file — KHÔNG được mất bất kỳ chức năng nào:**
- [ ] Chọn 1 file, `Ctrl+A` chọn tất cả, `Ctrl`+click chọn rời, `Shift`+click chọn khoảng
- [ ] **Đổi tên** (`F2`) trong icon view → ô nhập `widget.entry` phải theo theme, chữ đọc được
- [ ] **Đổi tên hàng loạt** nếu bản Nemo này có (không giả định là có — ghi lại kết quả)
- [ ] **Kéo-thả** trong cùng thư mục (di chuyển), sang thư mục khác, ra desktop, vào sidebar (bookmark)
- [ ] Chỉ báo kéo-thả `.treeview-drop-indicator` trong **list view** phải **rất rõ**
  khi kéo file qua các hàng
- [ ] **Sao chép / cắt / dán** (`Ctrl+C`, `Ctrl+X`, `Ctrl+V`) giữa hai thư mục lớn → xem 9.6
- [ ] **Xoá** (`Delete` → thùng rác; `Shift+Delete` → xoá vĩnh viễn): **cả hai hộp
      thoại xác nhận phải hiện và phải theo theme**
- [ ] **Tạo thư mục mới** (`Ctrl+Shift+N`), tạo file mới
- [ ] Mở file bằng app mặc định; **Open With…** để chọn app khác
- [ ] **Properties** (`Alt+Enter`): mọi tab (Basic, Permissions, Open With, Extensions)
- [ ] Tìm kiếm (`Ctrl+F`): nhập truy vấn **sai** để ô tìm kiếm sang trạng thái
      `.error` (đã style bằng `$mg-status-error`)

**Khả năng đọc với dữ liệu khó:**
- [ ] Thư mục có **> 1000 file**: cuộn mượt, không giật, thanh cuộn theo theme
- [ ] Tên file **rất dài** (> 120 ký tự): không phá bố cục hàng/lưới
- [ ] Tên file có **ký tự đặc biệt**, tiếng Việt có dấu, emoji, RTL
- [ ] **File ẩn** (`Ctrl+H`): nhãn mờ `.dim-label` vẫn **đọc được** (dùng
      `text.tertiary` α0.44 chứ không phải `text.disabled` α0.30)
- [ ] Thư mục **rỗng**: hiện thông báo trạng thái rỗng, không phải vùng trống vô nghĩa
- [ ] Kết quả tìm kiếm **rỗng**: có thông báo phân biệt được với thư mục rỗng

### 9.5 Menu và hộp thoại (3.5)

- [ ] **Menu ngữ cảnh** trên: file, thư mục, nhiều file đang chọn, nền trống, sidebar, desktop
- [ ] Menu theo đúng GTK theme (nền tối, hover rõ, separator thấy được)
- [ ] **KHÔNG mất mục menu nào do extension đóng góp.** Chạy
      `nemo --list-extensions` (hoặc kiểm tra `~/.local/share/nemo/extensions/`) rồi
      đối chiếu từng mục menu mà extension thêm vào — đây là yêu cầu tường minh
- [ ] Menu con (submenu) mở đúng hướng, không bị cắt ở mép màn hình
- [ ] **Hộp thoại xác nhận xoá** và **xác nhận thao tác quan trọng** (ghi đè file,
      xoá vĩnh viễn) phải hiện, phải theo theme, nút nguy hiểm phải phân biệt được
- [ ] Hộp thoại **Rename conflict / Skip / Replace** khi dán file trùng tên
- [ ] Hộp thoại **Properties**, **Preferences** (`Edit > Preferences`) — duyệt hết các tab
- [ ] **Điều hướng menu hoàn toàn bằng bàn phím:** phím Menu / `Shift+F10` mở menu,
      mũi tên di chuyển, `Enter` chọn, `Esc` đóng, phím tắt có gạch chân (mnemonic)
      hoạt động với `Alt`

### 9.6 Trạng thái hệ thống (3.6)

| Trạng thái | Cách tạo | Kỳ vọng |
|---|---|---|
| **Status bar** | Bật/tắt trong Preferences | **Chỉ kiểm tra nếu bản Nemo này có status bar.** Ghi lại kết quả; **không được giả định là có** |
| **Thanh nổi thay status bar** | Tắt status bar rồi sao chép thư mục lớn | `.floating-bar` hiện ở đáy khung nhìn, nền accent + chữ `#0b0c0e`, **bo 2 góc trên**, chữ đọc được |
| **Tiến trình sao chép/di chuyển** | Sao chép thư mục > 1 GB | tiến trình chạy, **nút huỷ trên thanh nổi bấm được và dừng thật** |
| **Lỗi quyền** | `mkdir /tmp/noperm && chmod 000 /tmp/noperm` rồi mở bằng Nemo | thông báo lỗi quyền hiện ra, đọc được, không phải hộp thoại trắng |
| **Ghi vào nơi không được phép** | thử dán file vào `/usr/share` với user thường | thông báo rõ ràng, không im lặng thất bại |
| **Ổ di động** | cắm/rút USB khi đang mở | sidebar cập nhật; **rút khi đang copy** → lỗi hiện rõ, không treo |
| **Vị trí mạng không truy cập được** | `smb://10.255.255.1/none` (IP không tồn tại) | báo lỗi rõ, **không treo vô hạn**, quay lại được |
| **Bookmark chết** | bookmark tới thư mục đã xoá | hiện trạng thái lỗi, không crash |
| **Pane không hoạt động (F3)** | mở 2 pane, chuyển focus qua lại | pane không hoạt động **trũng hơn và chữ mờ hơn** nhưng **vẫn đọc được**; item đang chọn trong pane đó **vẫn giữ màu selected** |
| **Icon trên desktop** | xem mục 9.7 riêng | |

### 9.7 Desktop — phần có giới hạn đã biết, phải kiểm tra riêng

> Nhãn icon trên desktop thuộc nhóm `[LOCK]` (mục 6.2): Nemo giữ ở priority 600,
> GTK 3.24 không có `!important`, nên **theme KHÔNG đổi được**. Những gì kiểm tra
> ở đây là kiểm tra **hành vi gốc của Nemo còn nguyên**, không phải kiểm tra theme.

- [ ] Icon desktop hiển thị, kéo-thả sắp xếp được, **double-click mở được**
- [ ] Nhãn icon **đọc được trên wallpaper thật của máy** (chụp ảnh desktop và đo,
      không đối chiếu với bảng ở mục 5 vì đó là wallpaper mô hình)
- [ ] **Chụp ảnh desktop với wallpaper SÁNG** (trắng/gần trắng) và đo lại nhãn chưa
      chọn: mục 5.3 dự đoán mép trên-trái glyph sẽ mờ ở **1.16:1**. Xác nhận hoặc
      bác bỏ dự đoán này bằng ảnh thật
- [ ] **Chụp ảnh desktop khi có icon đang được chọn** và đo: mục 5.1 dự đoán
      `#f5f5f5` trên mint chỉ **1.47–2.53:1** ⇒ **FAIL**. Xác nhận bằng ảnh thật.
      Đây là giới hạn **không sửa được từ theme**; chỉ sửa được bằng snippet
      `PRIORITY_USER` (mục 6.3) hoặc chấp nhận
- [ ] **Rê chuột** lên icon desktop: nhãn có sáng lên không? Đây là hành vi do
      `-NemoIconContainer-activate-prelight-icon-label` điều khiển mà **T09 cố ý
      KHÔNG ghi đè** — phải giống hệt Nemo mặc định
- [ ] Đổi tên icon **ngay trên desktop** (`F2`): ô nhập sẽ theo màu hard-code của
      Nemo (viền/chữ `#000000`, gradient trắng) vì thuộc nhóm `[LOCK]`. **Ghi nhận
      là giới hạn đã biết, không phải bug mới**
- [ ] Desktop khi **không có icon nào**
- [ ] Bật/tắt "Show desktop icons" trong Cinnamon Settings

### 9.8 App Mint khác

Mỗi app: mở, duyệt menu chính, mở một hộp thoại, đổi kích thước cửa sổ, chuyển
sang chế độ tối/sáng của hệ thống (nếu có). **Chỉ yêu cầu: không vỡ, không chữ tối
trên nền tối.**

- [ ] **xed** — mở file; thanh trạng thái `.xed-statusbar` đúng theme. **Tô màu cú
      pháp KHÔNG đổi được từ theme** (GtkSourceView tự nạp scheme riêng) — kiểm tra
      scheme mặc định có đọc được trên nền tối không, nếu không thì phải đổi
      **scheme của GtkSourceView**, không phải sửa theme
- [ ] **xreader** — mở PDF; **chế độ đảo màu `.inverted` phải còn hoạt động đúng**
      (đã cố ý không đè nền tối lên nó); chế độ thuyết trình fullscreen
      `evpresentationview` và `.white-mode`; sidebar thumbnail `evsidebarthumbnails`;
      ô nhập số trang `#page-label-entry`; **trang giấy phải SÁNG** (mô hình tài
      liệu in, chữ trong PDF là mực tối)
- [ ] **pix** — thư viện ảnh; **thư mục rỗng `.empty-view` / `.void-view`** (trạng
      thái hệ thống thật, pix tự cung cấp hook); histogram `.histogram` phải **trung
      tính về màu** (đã cố ý không dùng accent, nếu không người dùng đọc sai phơi
      sáng); `.toolbox`; slideshow `.video-player`; `.window-overlay`
- [ ] **xplayer** — phát video; vùng video `#stage` nền đen; `#logo-frame` khi chưa phát
- [ ] **xviewer** — xem ảnh; **không có selector riêng nào**, kiểm tra nó chỉ dùng
      widget GTK chung và không vỡ
- [ ] **mintupdate** — mở Trình quản lý cập nhật; **không có hook nào**, giao diện
      hoàn toàn do T06 quyết định. **Lưu ý cho T06:** mintupdate dùng nhiều hàng
      trạng thái có màu ngữ nghĩa (an toàn / nguy hiểm / nhân kernel) mà theme
      **không** nhắm riêng được ⇒ nếu muốn tô màu chúng thì phải cần hook từ phía
      app, mà hiện không có
- [ ] **mintinstall** — mở Trình quản lý phần mềm; tương tự, không có hook
- [ ] **cinnamon-settings** — mở Trung tâm điều khiển, duyệt vài module; **không có
      hook riêng nào** (chỉ `.inline-toolbar` là class GTK chung)

### 9.9 Khả năng tiếp cận (bắt buộc, không tuỳ chọn)

- [ ] **Chỉ dùng bàn phím** trong 10 phút: mở Nemo, điều hướng, chọn file, đổi tên,
      mở menu ngữ cảnh, xoá. Không lần nào bị "mất dấu" focus
- [ ] Focus ring hiện rõ trên **mọi** widget, kể cả trong icon view
- [ ] Bật **High Contrast** của GNOME/Cinnamon: theme không được phá nó
- [ ] Đổi **cỡ chữ hệ thống** lên lớn nhất: bố cục Nemo không vỡ, chữ không bị cắt
- [ ] Screen reader (Orca, nếu cài): các widget Nemo có nhãn truy cập được — **chỉ
      ghi nhận, không sửa được từ theme**

### 9.10 Cài đặt / nâng cấp / gỡ / rollback (yêu cầu §9)

- [ ] **Cài** theme theo ADR-002 vào `~/.local/share/themes/MintOS-Glass`, **không cần root**
- [ ] Chọn theme trong Cinnamon Settings → Appearance: **phải hiện trong danh sách**.
      Điều kiện đã xác minh từ T04: `cs_themes.py:1010-1016` chỉ liệt kê theme có
      `gtk-3.*/gtk.css` ⇒ **T06 phải giao file đó**, nếu không theme không hiện
- [ ] **Tài khoản MỚI** (tạo user mới rồi đăng nhập): Nemo mặc định đã theo theme,
      sidebar phản ánh đúng `user-dirs` của user đó, **không có đường dẫn hard-code
      nào của máy dev**
- [ ] **Tài khoản ĐANG TỒN TẠI đã có cấu hình riêng:** script cài đặt **KHÔNG được
      ghi đè** thiết lập cá nhân của họ. Đây là yêu cầu tường minh. Phân biệt rõ
      "mặc định cho user mới" (skel/dconf) với "cấu hình tài khoản hiện có" (không
      chạm vào)
- [ ] **Rollback về Nemo gốc:** đổi theme GTK về Mint-Y (hoặc theme gốc) trong
      Cinnamon Settings ⇒ Nemo phải trở về **đúng** giao diện gốc **ngay lập tức**,
      không cần đăng nhập lại, không còn dấu vết nào của MintOS Glass. Kiểm tra
      thêm: xoá `~/.local/share/themes/MintOS-Glass` rồi đăng nhập lại ⇒ không crash,
      GTK rơi về theme mặc định
- [ ] **Nâng cấp** theme (ghi đè phiên bản mới): Nemo không kẹt ở style cũ, không cần
      xoá cache thủ công. Nếu cần xoá cache, **ghi rõ lệnh** vào tài liệu ISO
- [ ] Xác nhận **không có file nào của hệ thống bị sửa** — toàn bộ nằm trong thư
      mục theme và (nếu dùng) `~/.config/gtk-3.0/gtk.css`

---

## 10. Việc còn lại và phụ thuộc

### 10.1 **T09 phụ thuộc cứng vào T06 — chưa được nối**

`src/gtk-3.0/sass/gtk.scss` **chưa tồn tại** (T06 chưa bắt đầu; T09 **bị cấm** tạo
nó). Hai partial này compile **đứng một mình** được (đã kiểm chứng bằng cả
libsass và dart-sass) nhưng **chưa được nối vào theme thật**.

Khi T06 giao, cần đúng **hai dòng** trong `gtk.scss` (và `gtk-dark.scss`):

```scss
@import "apps-nemo";
@import "apps-mint";
```

**Không có hai dòng này thì toàn bộ T09 không có tác dụng gì trên máy thật.**
Đây là việc của T06/T14, không phải T09 — ghi rõ để không bị rơi.

Hai partial chỉ `@import "tokens"`, **không** phụ thuộc `_colors.scss`,
`_drawing.scss`, `_common.scss` hay `_widgets.scss` của T06, nên T06 có thể nối vào
bất cứ lúc nào mà không phải sửa T09. Khi T06 giao các helper đó, nên cân nhắc
chuyển sang dùng helper chung thay vì token thô — **việc đó chưa làm** để tránh
phụ thuộc vào file chưa tồn tại.

### 10.2 Cần Agent Design Systems (Agent 1) — T09 không được sửa `design/tokens/*.json`

| # | Việc | Căn cứ |
|---|---|---|
| 1 | `nemo.desktop.label.selected.text`: `#f5f5f5` → `#0b0c0e` | đo được **1.47/1.90/2.53:1 FAIL** ở cả ba mức wallpaper (mục 5.1) |
| 2 | `nemo.desktop.label.shadow`: đổi sang shadow **không lệch** (`0 0 2px`) hoặc 4 hướng | shadow lệch 1px để hở mép glyph → **1.16:1** trên wallpaper trắng (mục 5.3) |
| 3 | `nemo.desktop.canvas.radius`: quyết `4px` hay `3px` | Nemo khoá `3px` ở priority 600 ⇒ token `4px` vô tác dụng (mục 5.4) |
| 4 | Bổ sung token ngữ nghĩa `surface.paper` / `surface.page` (trắng đục) | xreader cần nền trang giấy; hiện phải dùng primitive `$mg-color-white` (mục 7) |
| 5 | Cân nhắc tăng alpha `nemo.desktop.label.hover.background` `0.5` → `0.6` | hover chỉ đạt **3.40:1** trên wallpaper trắng, sát ngưỡng (mục 5.2) |
| 6 | **Các bug generator đã báo từ T04, vẫn chưa sửa:** `font.weight-*` ra `400px/500px/700px`; `font.size-*-pt` ra `9px/12px`; `blur.*` ra `2px/4px/6px`; **`40-motion.json` không bao giờ được emit** (`generate.py:605-616`) | vì vậy cả hai partial này phải dùng **hằng tạm thời** có ghi chú (`$nemo-w-*`, `$nemo-dur-*`, `$nemo-ease`, `$mint-w-medium`, …). Lint `no-broken-tokens` khoá không cho tham chiếu token hỏng |

### 10.3 Cần Agent GTK (Agent 3 / T06)

1. `gtk.scss` + `gtk-dark.scss` phải `@import "apps-nemo"` và `@import "apps-mint"` (mục 10.1)
2. Export đủ **5** symbol `@theme_*` (mục 3.1) — nếu thiếu, icon desktop khi được
   chọn sẽ hỏng và **T09 không sửa được**
3. Kiểm tra `tests/fixtures/gtk-public-colors.txt` (E33) có **`@borders`** không —
   `nemo-style-application.css` của 6.6.4 dùng nó (mục 3.1)
4. Sở hữu các class GTK chung: `.sidebar`, `.view`, `.linked`, `.raised`, `.error`,
   `.primary-toolbar`, `.content-view`, `.small-button`, `.close-button`,
   `.inline-toolbar`, `.documents-entry-tag`, `.title`, `.icon` — T09 cố ý **không**
   viết chúng ở dạng trần (lint `no-bare-generic` thực thi)

### 10.4 Cần Agent Platform/DevEx

1. Thêm `tools/lint/nemo_selectors.py` vào job lint của CI
2. `tools/lint/safety_paths.py:43` `SKIP_DIRS` cần thêm `.venv`/`venv` (đã báo từ T04)
3. **Lưu ý đã gặp thật trong T09:** `tests/lint/test_safety.py::test_only_two_write_roots_are_mentioned_in_tooling`
   quét **mọi chuỗi dạng nháy-then-`/…`** trong mọi file `.py` và chỉ cho phép hai
   gốc ghi. Đường dẫn **GResource** `/org/nemo/nemo-style-fallback.css` (nằm trong
   binary của Nemo, không phải đường ghi trên đĩa) đã bị bắt. T09 xử lý bằng cách
   **bỏ dấu nháy** ở phía mình và ghi chú lý do trong docstring — **không** nới cổng
   an toàn. Nếu sau này còn nhiều tool cần trích dẫn đường dẫn GResource/DBus, nên
   cân nhắc một marker miễn trừ rõ ràng hơn.

### 10.5 Cần T12 (installer/rollback)

Quyết định về snippet `PRIORITY_USER` cho nhóm `[LOCK]` (mục 6.3): có làm hay không,
và nếu làm thì **không được ghi đè** `~/.config/gtk-3.0/gtk.css` sẵn có của người dùng.

---

## 11. Tuyên bố trung thực về phạm vi kiểm chứng

**ĐÃ kiểm chứng (có bằng chứng tái lập được):**
mã nguồn Nemo 6.6.4 và 6.7.8; cơ chế ưu tiên provider; việc GTK 3.24 không có
`!important`; cơ chế nhận diện tên theme; toàn bộ style class / widget name / CSS
node name của Nemo và của 8 app Mint; 7 style property GObject; các con số tương
phản ở mục 5 (đo bằng `contrast.py` của repo, tự động kiểm tra lại trong test).

**CHƯA kiểm chứng — cần máy Mint thật:**
mọi thứ về runtime và bố cục thật ở mục 8(c) và mục 9; tương phản trên **wallpaper
thật** (mục 5 chỉ đo trên wallpaper mô hình ba mức chói); phiên bản Nemo thực tế
trên Mint 22.3 (6.6.x hay 6.7.x); liệu status bar có tồn tại ở bản đó không; liệu
các hộp thoại xác nhận có đúng như mô tả không.

**KHÔNG tuyên bố:** giao diện này "đã hoạt động trên Nemo". Nó đã **biên dịch
được**, **đủ coverage**, **đúng cơ chế đã xác minh từ mã nguồn**, và **đo được
tương phản**. Đó là bốn việc khác nhau, và chỉ bốn việc đó đã được làm.
