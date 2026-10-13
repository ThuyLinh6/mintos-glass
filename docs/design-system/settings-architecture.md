# Kiến trúc System Settings của Cinnamon 6.6 — và theme với tới được những gì

**Task:** T17 · **Owner:** Agent 6 (Settings & Control Center UI)
**Bằng chứng máy đọc được:** `tests/fixtures/cinnamon-settings-hooks.txt`
**Kiểm tra:** `tools/lint/settings_arch.py` · `tests/lint/test_settings_arch.py`
**Nguồn:** `linuxmint/Cinnamon` @ 6.6.9, commit `806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18`,
`files/usr/share/cinnamon/cinnamon-settings/` (21 213 dòng Python, 31 module) ·
`GNOME/gtk` @ 3.24.42 (`gtk/gtkbuilder.c`, `gtk/gtkwidget.c`)

> **Tài liệu này tồn tại vì một kết luận sai đã từng được ghi vào repo.**
> Lần khảo sát đầu (T09) kết luận *"cinnamon-settings không có hook CSS riêng, 1 kết
> quả duy nhất, 0 widget name"* và ghi thẳng vào comment của
> `src/gtk-3.0/sass/_apps-mint.scss` mục 9. Kết luận **thực chất** thì đúng — không
> có hook ở **cấp cửa sổ** — nhưng **số liệu** thì sai: quét lại toàn bộ ra **27 hook
> trên 18 tệp**, gồm một CSS class riêng, một widget name riêng và một widget **bị
> khoá** ở priority 600. Nguyên nhân: lần quét đó chỉ đi qua `modules/**`, bỏ sót
> `cinnamon-settings.py` và `bin/**`.
>
> Một kết luận sai nằm trong comment thì không ai phát hiện. Nên bằng chứng được
> tách ra fixture có cấu trúc và `tools/lint/settings_arch.py` đối chiếu **hai chiều**
> giữa fixture và tài liệu này.

---

## 1. Phát hiện kiến trúc quan trọng nhất: Settings KHÔNG phải một app đồng nhất

Yêu cầu Scope A liệt kê các trang ưu tiên: Appearance, Display, Keyboard, Mouse,
Sound, **Network**, **Bluetooth**, Power, Backgrounds, Notifications, Windows,
Workspaces, **Users**. Khảo sát cho thấy các trang đó thuộc **ba tầng với ba chủ sở
hữu khác nhau**, và theme chỉ sở hữu được một tầng.

### Tầng 1 — 31 module Python (theme với tới được, qua T06)

`accessibility` `actions` `applets` `backgrounds` `calendar` `default` `desklets`
`desktop` `display` `effects` `extensions` `fonts` `general` `gestures` `hotcorner`
`info` `keyboard` `mouse` `nightlight` `notifications` `panel` `power` `privacy`
`screensaver` `sound` `startup` `themes` `thunderbolt` `user` `windows` `workspaces`

Mỗi trang dựng UI bằng **widget GTK chung** (`Gtk.Box`, `Gtk.TreeView`,
`Gtk.ListBox`, `Gtk.Scale`, `Gtk.Switch`, `Gtk.ComboBoxText`…) qua các helper trong
`bin/SettingsWidgets.py` và `bin/TreeListWidgets.py`. Nên giao diện của chúng do
**GTK theme lõi (T06)** quyết định, không cần và không thể nhắm riêng.

**Bao gồm:** Appearance/Themes, Display, Keyboard, Mouse & Touchpad, Sound, Power
Management, Backgrounds, Notifications, Windows, Workspaces — tức **10 trong 13**
trang ưu tiên.

### Tầng 2 — 3 panel C từ **một gói khác** (theme chỉ chạm được vùng chứa)

`CONTROL_CENTER_MODULES` (`cinnamon-settings.py:70-75`) khai báo đúng ba trang:

| Trang | `mod_id` | Icon | Category |
|---|---|---|---|
| **Network** | `network` | `cs-network` | `hardware` |
| Color | `color` | `cs-color` | `hardware` |
| Graphics Tablet | `wacom` | `cs-tablet` | `hardware` |

Chúng **không phải code Python của cinnamon-settings**. `bin/capi.py:27` đăng ký
`Gio.io_extension_point_register("cinnamon-control-center-1")` rồi nạp các `.so` từ
`/usr/lib`, `/usr/lib64`, `/usr/lib/<multiarch>`, `/usr/lib/<machine>` — đường con
`cinnamon-control-center-1/panels`.

**Nếu gói `cinnamon-control-center` không được cài**, `capi.py:57/65` in ra
`"Could not load/find <id> module; is the cinnamon-control-center package installed?"`
và trang đó **biến mất khỏi Settings**. Đó không phải lỗi của theme và theme không
sửa được.

### Tầng 3 — launcher sang app **khác hẳn** (theme không kiểm soát)

`STANDALONE_MODULES` (`cinnamon-settings.py:77+`). Mỗi dòng là một lệnh thực thi,
không phải một trang:

| Trang | Lệnh thật | Icon | Category |
|---|---|---|---|
| **Bluetooth** | `blueberry` **hoặc** `blueman-manager` | `cs-bluetooth` | `hardware` |
| Printers | `system-config-printer` | `cs-printer` | `hardware` |
| **Users and Groups** | `cinnamon-settings-users` | `cs-user-accounts` | `admin` |
| Login Window | `pkexec lightdm-settings` (hoặc `gdm-settings`) | `cs-login` | `admin` |
| Firewall | `gufw` **hoặc** `firewall-config` | `cs-firewall` | `admin` |
| Languages | `mintlocale` | `cs-language` | `prefs` |
| Input Method | `mintlocale-im` | `cs-input-method` | `prefs` |
| Driver Manager | `cinnamon-driver-manager` | `cs-drivers` | `admin` |
| Software Sources | `pkexec mintsources` | `cs-sources` | `admin` |
| System Information | `mintreport` | `mintreport` | `hardware` |
| System Administration | `pkexec mintsysadm` | `mintsysadm` | `admin` |

Cộng các nhánh thay thế theo distro: `nvidia-settings`, `fingwit`, `dnfdragora`,
`gpk-application`, `octopi`, `pamac-manager`, `yumex`,
`gnome-online-accounts-gtk`, `org.gnome.DiskUtility`, `system-software-install`.

> **Hệ quả phải nói thẳng:** trong danh sách trang ưu tiên của yêu cầu Scope A,
> **Network = tầng 2**, **Bluetooth = tầng 3**, và **Users** bị tách đôi
> (`cs_user.py` là tầng 1, còn "Users and Groups" là tầng 3 → app khác).
> **Ba trang được yêu cầu ưu tiên lại là ba trang theme KHÔNG sở hữu.**
> Mọi cam kết về giao diện của ba trang đó phải được hiểu là cam kết về **icon**
> (đã làm ở T15/T17) và về **GTK theme chung nếu app đó cũng dùng GTK3**, chứ không
> phải cam kết về bố cục trang.

### Trang Night Light: tầng 1 nhưng có một widget bị khoá

Xem mục 4 — đây là trường hợp duy nhất theme **thua** ngay trong tầng 1.

---

## 2. Hook CSS có thật: đúng **ba**

Quét toàn bộ 21 213 dòng Python của `cinnamon-settings` với mẫu
`add_class` / `remove_class` / `set_name` / `set_css_name` cho **27 hook trên 18
tệp**. Trong đó chỉ **ba** là riêng của app này:

| Hook | CSS selector | Bằng chứng | Trạng thái | Nó là cái gì |
|---|---|---|---|---|
| `cs-category-view` | `.cs-category-view` | `cinnamon-settings.py:288` | **OPEN** | `GtkScrolledWindow` chứa **sidebar danh mục** |
| `c_box` | `#c_box` | `bin/SettingsWidgets.py:286` | **OPEN** | `Gtk.Box` **đựng 3 panel C** của tầng 2 |
| `night-light-temperature` | `.night-light-temperature` | `modules/cs_nightlight.py:50` | **LOCKED-600** | slider nhiệt độ màu — xem mục 4 |

24 hook còn lại là **class GTK chung**, không phải hook riêng: `view` (7 lần),
`dim-label` (8 lần), `linked` (3), `inline-toolbar` (2), `primary-toolbar` (2),
`raised`, `image-button`, `gtkstyle-fallback`, `destructive-action`. Style chúng là
style **mọi app GTK khác** nên thuộc T06 và phải cân nhắc toàn hệ thống — không
được ghi vào một partial "dành cho Settings".

### `.cs-category-view` — sidebar

`cinnamon-settings.py:285-289`:

```python
self.side_view_sw = self.builder.get_object("side_view_sw")   # GtkScrolledWindow
context = self.side_view_sw.get_style_context()
context.add_class("cs-category-view")
context.add_class("view")
```

Yêu cầu Scope A *"thanh điều hướng hoặc danh mục cài đặt ở bên trái"* trỏ đúng vào
widget này. Selector dùng được: `.cs-category-view` hoặc `.cs-category-view.view`.

### `#c_box` — cách duy nhất chạm tới tầng 2

`bin/SettingsWidgets.py:283-289` (trong `CCModule.process()`):

```python
c_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 2)
c_box.set_vexpand(False)
c_box.set_name("c_box")
self.sidePage.add_widget(c_box)
```

Đây là `Gtk.Box.set_name()` = `gtk_widget_set_name()` **thật**, nên CSS nhắm được
bằng `#c_box`. Nó là container **duy nhất** mà theme có thể dùng để tác động lên
vùng chứa các trang Network / Color / Graphics Tablet — bản thân nội dung ba trang
đó là widget C do gói khác biên dịch.

Chỉ nên dùng `#c_box` cho **khoảng cách / nền / bo góc của vùng chứa**, không cố
style widget con bên trong: cấu trúc con là của `cinnamon-control-center`, có thể
khác giữa các phiên bản, và ta chưa đọc mã gói đó.

---

## 3. BẪY GTK3: GtkBuilder `id` KHÔNG phải widget name

`cinnamon-settings.ui` có **17 object có id** và `themes.ui` có **11**. Trông rất
giống hook CSS, nhưng **không phải**. Bằng chứng từ `GNOME/gtk` @ 3.24.42:

```
gtk/gtkbuilder.c:606-612   object_set_name(object, name)
                             -> if (GTK_IS_BUILDABLE(object))
                                    gtk_buildable_set_name(GTK_BUILDABLE(object), name);
gtk/gtkbuilder.c:620       _gtk_builder_add_object() gọi object_set_name(object, id)
gtk/gtkwidget.c:14043      iface->set_name = gtk_widget_buildable_set_name
gtk/gtkwidget.c:14053-14058
    gtk_widget_buildable_set_name (GtkBuildable *buildable, const gchar *name)
    {
      g_object_set_qdata_full (G_OBJECT (buildable), quark_builder_set_name,
                               g_strdup (name), g_free);
    }
```

Nó **chỉ lưu qdata**, **không** gọi `gtk_widget_set_name()`. Mà CSS của GTK khớp
`#name` theo **widget name**. Nên các id sau đây **vô hình với CSS**:

`main_box` `top_bar` `toolbutton1` `header_stack` `hbox2` `search_box` `box2`
`button_back` `image1` `stack_switcher` `main_stack` `side_view_sw` `viewport2`
`category_box` `content_box_sw` `viewport1` `content_box`

và trong `themes.ui`: `page_simplified` `color_label` `mixed_button` `dark_button`
`light_button` `color_box` `customize_button` `style_combo`.

> **GTK4 thì KHÁC** — builder id **có** thành widget name. Nên bẫy này sẽ đảo ngược
> ở T10 (GTK4/libadwaita). `tools/lint/settings_arch.py` có bài
> `docs-no-uiid-as-selector` chặn tài liệu viết các id này như selector, để không ai
> "sửa" tài liệu theo hướng sai rồi áp dụng cho GTK3.

### Hệ quả cho yêu cầu Scope A

| Yêu cầu | Có nhắm riêng được không |
|---|---|
| "Bố cục cửa sổ hiện đại, bo góc, phân cấp thị giác" | ❌ không nhắm riêng được — làm qua T06 cho toàn hệ thống |
| "Thanh điều hướng / danh mục ở bên trái" | ✅ `.cs-category-view` |
| "Khu vực nội dung bên phải" | ❌ `content_box` là builder id, không nhắm được |
| "Biểu tượng danh mục đồng bộ icon theme" | ✅ đã làm — 47 icon `cs-*` (T15/T17) |
| "Tìm kiếm cài đặt" | ⚠️ **đã có sẵn và là thật** — xem dưới |
| "Giữ nguyên khả năng thao tác và lưu cấu hình" | ✅ không đụng code |

### Ô tìm kiếm là THẬT — không được làm giả, cũng không cần làm mới

`cinnamon-settings.py:301-304`:

```python
self.search_entry = self.builder.get_object("search_box")      # GtkEntry
self.search_entry.set_placeholder_text(_("Search"))
self.search_entry.connect("changed", self.onSearchTextChanged)
self.search_entry.connect("icon-press", self.onClearSearchBox)
```

và `:522` `text = self.strip_accents(self.search_entry.get_text().lower())` — lọc
trực tiếp theo `keywords` mà từng module khai báo (kể cả **bỏ dấu**, nên gõ
"mạng" hay "mang" đều ra). `:395` và `:746` gọi `grab_focus()`.

Vì nó là `GtkEntry` thường **không tên riêng**, theme chỉ style được như một entry
**chung** (T06). Yêu cầu *"không tạo ô tìm kiếm giả"* được thoả bằng cách **không
tạo gì cả** — ô tìm kiếm đã có và hoạt động.

---

## 4. Widget bị KHOÁ: slider nhiệt độ màu ở trang Night Light

`modules/cs_nightlight.py:31-53` — app **tự dựng** `Gtk.CssProvider` và nạp:

```css
@define-color ORANGE_100 #fff4e9;
@define-color ORANGE_500 #f37329;
@define-color base_color white;
@define-color bg_color shade (@base_color, 0.96);

.night-light-temperature trough {
    padding-top: 2px;
    padding-bottom: 2px;
    background-image: linear-gradient(to right, mix(@bg_color, @ORANGE_100, 0.5), @ORANGE_500);
}
```

rồi:

```python
context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)   # = 600
```

Theme nạp ở `GTK_STYLE_PROVIDER_PRIORITY_THEME` (**200**). GTK 3.24 **không có
`!important`** — đã kiểm: chuỗi "important" xuất hiện **0 lần** trong
`gtkcssparser.c`, `gtkcssprovider.c`, `gtkstylecascade.c` @ 3.24.42. Nên priority là
**tuyệt đối** và theme **thua**.

**Hệ quả không sửa được từ theme:** trên nền Dark Glass, slider "Color temperature"
ở trang Night Light sẽ **luôn** là dải **trắng → cam**. Nó sẽ trông lạc lõng. Đó là
sự thật, và tài liệu này ghi nó ra thay vì để người dùng tưởng theme bị lỗi.

Đây là provider **duy nhất** app tự nạp (đã grep toàn bộ `cinnamon-settings`), nên
lock chỉ giới hạn ở **một widget**.

Cơ chế này **giống hệt** lock mà T09 gặp ở Nemo (`nemo-style-application.css` cũng
ở priority 600) — cùng một nguyên nhân, cùng một đường thoát.

**Đường thoát duy nhất, CHƯA làm, cần duyệt:** nạp một khối ghi đè ở
`GTK_STYLE_PROVIDER_PRIORITY_USER` (**800**) qua tệp cấu hình GTK cấp người dùng.
Đó là thay đổi **cấu hình người dùng**, không phải theme, nên thuộc **T12**
(installer/rollback) và phải có snapshot + hoàn tác. **Không** đề xuất sửa
`cs_nightlight.py`: đó là sửa mã nguồn app hệ thống, vi phạm nguyên tắc 2.3 trừ khi
thật cần thiết, và sẽ vỡ khi Mint cập nhật.

---

## 5. Kết luận thực chất: cái gì giữ nguyên từ lần khảo sát đầu

Dù số liệu sai, **kết luận thực chất của T09 vẫn đúng và vẫn là ràng buộc chính**:

> **Không có hook ở CẤP CỬA SỔ.** Không có widget name hay style class nào gắn trên
> top-level window của cinnamon-settings. Mà GTK3 **không** phơi application-id cho
> CSS — đã kiểm ở T09: chuỗi `application_id` xuất hiện **0 lần** trong
> `gtk/gtkapplicationwindow.c` @ 3.24.42 (1048 dòng).

Nên **không có cách nào** trong một tệp `gtk.css` dùng chung để viết
"selector này chỉ áp dụng trong cửa sổ Settings". Ba hook ở mục 2 là **toàn bộ** bề
mặt nhắm riêng được, và cả ba đều ở cấp widget con.

**Hệ quả cho việc triển khai:** ~95% diện mạo của System Settings do **T06 (GTK3
core)** quyết định. **T06 chưa tồn tại** (`src/gtk-3.0/sass/gtk.scss` chưa có). Vậy
nên:

- Không thể giao "giao diện Settings nhất quán Dark Glass" ở vòng này — **nói rõ,
  không tuyên bố**.
- Phần **đã** giao được và không bị chặn: **47 icon `cs-*`** (mục 6).
- Phần **có thể** viết ngay nhưng **chưa được nối**: một partial
  `_apps-cinnamon-settings.scss` chỉ dùng `.cs-category-view` và `#c_box`. Người dùng
  đã chọn **hoãn** phần này (quyết định 2026-10-13: *icons first*), vì viết SCSS khi
  chưa có `gtk.scss` để `@import` thì chỉ tạo ra một tệp không được biên dịch vào
  đâu cả — đúng tình trạng hiện tại của `_apps-nemo.scss` và `_apps-mint.scss`.

---

## 6. Phần đã giao: 47 icon `cs-*`

Icon **không** phụ thuộc T06 — chúng đi qua icon theme, là đường độc lập. Đã làm
trong `src/icons/MintOS-Glass/scalable/apps/`, chi tiết ở
`src/icons/MintOS-Glass/MANIFEST.md` mục 4bis và
`docs/design-system/icon-spec.md` mục 8bis.

Tóm tắt: 4 icon danh mục + 31 module + 3 panel C + 9 trang standalone = **47**, tên
trích bằng máy theo **cấu trúc bảng** trong `cinnamon-settings.py` chứ không grep
thô. Line icon (không squircle) vì chúng hiện cả ở cỡ nhỏ trong list/sidebar. Nét
`gray-400` mang hình dạng (3.97:1 trên nền trắng, 4.68:1 trên nền tối), một chi tiết
màu theo category.

**Một dương tính giả đã loại:** chuỗi `cs-category-view` khớp mẫu `cs-*` khi grep
thô nhưng là **tên CSS class** (`cinnamon-settings.py:288`), **không phải** tên
icon. `tools/lint/settings_arch.py` có bài
`cs-category-view-is-not-an-icon` kiểm tra rằng **không tồn tại** tệp
`cs-category-view.svg` trong icon theme, để lỗi này không quay lại.

---

## 7. Icon danh mục và 4 category

`CATEGORIES` (`cinnamon-settings.py:62-68`) khai báo 4 danh mục, mỗi cái một icon:

| Label | `id` | Icon |
|---|---|---|
| Appearance | `appear` | `cs-cat-appearance` |
| Preferences | `prefs` | `cs-cat-prefs` |
| Hardware | `hardware` | `cs-cat-hardware` |
| Administration | `admin` | `cs-cat-admin` |

Category của từng trang nằm ở **cột 4** của `CONTROL_CENTER_MODULES` và
`STANDALONE_MODULES` (đã trích ở mục 1). Riêng **31 module Python**: upstream gán
category qua thuộc tính `sidepage.cat` (so với `category["id"]` tại
`cinnamon-settings.py:356-359`), nhưng **cơ chế gán không nằm trong
`modules/*.py`** nên **không truy ra được từ nguồn**. Việc nhóm 31 icon đó theo ngữ
nghĩa là **quyết định thiết kế của dự án**, không phải tuyên bố về cách upstream
phân loại. Ghi rõ để không ai tưởng bảng màu category suy ra từ mã nguồn.

---

## 8. Những gì KHÔNG thuộc phạm vi theme

Ghi rõ để không ai cố làm rồi tưởng là đã làm:

| Thứ | Thuộc về |
|---|---|
| Bố cục cửa sổ, sidebar, khoảng cách, typography của Settings | **T06** (GTK3 core) — chưa tồn tại |
| Widget trong 3 trang Network/Color/Wacom | gói **`cinnamon-control-center`** — chưa đọc mã |
| UI của blueberry, system-config-printer, cinnamon-settings-users, lightdm-settings, gufw, mintlocale, mintreport… | **từng app đó** — ngoài phạm vi dự án |
| Slider Night Light | **bị khoá ở priority 600** — chỉ thoát được qua cấu hình cấp người dùng (**T12**) |
| Chọn theme/icon theme lúc chạy | **gsetting** — thuộc **T12** |
| Control Center / quick settings | xem `docs/proposals/control-center.md` |

---

## 9. Trạng thái kiểm chứng

### ĐÃ xác minh bằng cách đọc mã nguồn
Toàn bộ bằng chứng file:line ở trên, và:
- 27 hook trên 18 tệp (quét toàn bộ, không chỉ `modules/**`)
- chỉ **3** hook riêng của app; **0** hook ở cấp cửa sổ
- `gtk_widget_buildable_set_name()` không gọi `gtk_widget_set_name()` (GTK 3.24.42)
- ô tìm kiếm là thật và có lọc bỏ dấu
- `cs_nightlight.py` là nơi **duy nhất** app tự nạp `CssProvider`
- ba tầng trang, kèm tên gói và lệnh thực thi của tầng 2 và 3
- 4 category + icon của chúng
- `THEMES_BLACKLIST` và điều kiện để một thư mục được liệt kê làm icon theme
  (`cs_themes.py:144-157`) — ghi ở `src/icons/MintOS-Glass/MANIFEST.md` mục 8

### CHƯA kiểm chứng — cần Cinnamon 6.6 / Mint 22.3 thật
Không có máy nên **không tuyên bố** đã kiểm:

| Chưa kiểm chứng | Điều kiện để kiểm |
|---|---|
| `.cs-category-view` và `#c_box` có **thật sự** áp dụng được không, hay còn provider nào khác chen vào | Viết một khối thử, nạp ở priority theme, mở Settings xem |
| Sidebar có đúng là `GtkScrolledWindow` đó không, hay đã bị bọc thêm | Mở GTK Inspector trên máy thật |
| 3 trang tầng 2 có **thật sự** hiện diện trên Mint 22.3 không (gói `cinnamon-control-center` có được cài mặc định không) | Kiểm tra gói đã cài; nếu không có thì ba trang đó vắng mặt và `#c_box` không bao giờ được dùng |
| Dải trắng-cam của Night Light có chói tới mức phải xử lý bằng được không | Xem trên máy thật, trong phòng tối |
| Icon `cs-*` ở cỡ thật trong lưới trang chính có đủ rõ không | Xem ở 48px và ở cỡ list/sidebar |
| Các app tầng 3 (blueberry, system-config-printer…) có theo GTK theme của ta không | Mở từng app; chúng có thể dùng toolkit hoặc theme riêng |

**Rủi ro lớn nhất cần kiểm đầu tiên:** gói `cinnamon-control-center` có được cài
mặc định trên Mint 22.3 hay không. Nếu **không**, trang Network vắng mặt hoàn toàn
và mọi mô tả về tầng 2 chỉ là lý thuyết; nếu **có**, `#c_box` là hook thật sự hữu
dụng. Chưa có cách nào xác minh offline.
