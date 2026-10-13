# MANIFEST — Icon theme MintOS-Glass (T15)

**Owner:** Agent D (Visual/Assets) · **Task:** T15
**Thư mục:** `src/icons/MintOS-Glass/` · **122 icon SVG + `index.theme`**
**Cập nhật (Agent 6):** thêm 47 icon `cs-*` cho System Settings — xem mục 4bis.
**Quy chuẩn thiết kế:** `docs/design-system/icon-spec.md`
**Xác minh bằng:** `tools/lint/icon_theme.py` · `tests/lint/test_icon_theme.py`
**Hợp đồng tập lõi:** `tests/fixtures/icon-theme-core.txt`

---

## 1. Cấu trúc

```
src/icons/MintOS-Glass/
├── index.theme            # khai báo theme, Directories, Inherits
├── MANIFEST.md            # tệp này
├── scalable/              # icon đầy đủ màu, Type=Scalable 16..512
│   ├── apps/       (63)   # 16 icon app + 47 icon cs-* của Settings
│   ├── places/     (14)
│   ├── devices/     (7)
│   ├── mimetypes/   (9)
│   ├── actions/    (11)
│   └── status/      (4)
└── symbolic/              # icon ĐƠN SẮC, GTK tô lại theo màu chữ
    ├── actions/     (8)
    ├── places/      (3)
    └── status/      (3)
```

**9 thư mục, 122 tệp, không thư mục rỗng.** Cả 9 đều có mặt trong `Directories`
của `index.theme` và đều có section riêng — lint kiểm hai chiều.

Dùng `scalable/<context>` (convention của icon theme thuần SVG) thay vì
`<context>/<size>` của Mint-Y. Mint-Y cần `apps/16`, `apps/22`, … `apps/256`
cộng `apps/16@2x` với `Scale=2` vì nó là theme **raster**; theme này là SVG nên
một tệp phục vụ mọi kích thước qua `Type=Scalable` + `MinSize=16` + `MaxSize=512`,
và **không cần** thư mục `@2x` lẫn khoá `Scale=2`.

---

## 2. Chuỗi kế thừa và cơ chế fallback

```
Inherits=Mint-Y,Adwaita,gnome,hicolor
```

Đây là phần **quan trọng nhất** của `index.theme`, không phải dòng trang trí.
Icon Theme Spec của freedesktop quy định bộ nạp tìm icon lần lượt qua từng theme
trong `Inherits` rồi mới tới `hicolor`. Hệ quả:

> **Một icon thiếu trong theme này KHÔNG BAO GIỜ làm ứng dụng mất biểu tượng.**
> Nó rơi xuống Mint-Y, rồi Adwaita, rồi gnome, rồi hicolor.

Vì fallback hoạt động thật, theme này **cố ý nhỏ** (75 icon) chứ không sao chép
hàng nghìn icon chỉ để "cho đủ". Chỉ vẽ những icon quyết định nhận diện thị giác
của MintOS Glass.

**Vì sao `Mint-Y` đứng đầu:** nó chắc chắn có mặt trên Linux Mint 22.3 (là icon
theme mặc định) nên cung cấp phần lớn icon còn thiếu với chất lượng tốt. Đã đọc
`usr/share/icons/Mint-Y/index.theme` của `linuxmint/mint-y-icons` @ `master` và
thấy chính Mint-Y khai báo `Inherits=Adwaita,gnome,hicolor`.

**Vì sao vẫn liệt kê tường minh `Adwaita,gnome,hicolor`:** để theme không vỡ nếu
được cài trên bản phân phối khác không có Mint-Y. Không dựa vào tính bắc cầu của
chuỗi kế thừa. `hicolor` luôn ở **cuối** vì nó là chốt chặn bắt buộc theo spec —
lint có bài `inherits-fallback` đòi đúng thứ tự đó.

---

## 3. Ánh xạ app → tên icon (lấy từ mã nguồn, không đoán)

Tiêu chí Done #3 của T15. Mỗi tên dưới đây trích từ khoá `Icon=` trong file
`.desktop` **thật** của app, đọc từ tarball mã nguồn:

| App | Tên icon | Nguồn đã xác minh |
|---|---|---|
| **Nemo** | `system-file-manager` | `linuxmint/nemo` @ 6.6.4 · `nemo.desktop.in` |
| **xed** | `accessories-text-editor` | `linuxmint/xed` · `org.x.editor.desktop.in.in` |
| **Pix** | `pix` | `linuxmint/pix` · `pix.desktop.in` |
| **Xplayer** | `xplayer` | `linuxmint/xplayer` · `xplayer.desktop.in.in.in` |
| **Xreader** | `xreader` | `linuxmint/xreader` · `xreader.desktop.in.in` |
| **Xviewer** | `xviewer` | `linuxmint/xviewer` · `xviewer.desktop.in.in` |
| **Update Manager** | `mintupdate` | `linuxmint/mintupdate` · `mintupdate.desktop` |
| **Software Manager** | `mintinstall` | `linuxmint/mintinstall` · `mintinstall.desktop` |
| Software Properties | `software-properties-mint` | `mintinstall-fp-handler.desktop` |
| **Cinnamon Settings** | `preferences-desktop` | `linuxmint/Cinnamon` @ 6.6.9 · `cinnamon-settings.desktop` |

### Đính chính một giả định phổ biến

`cinnamon-settings` dùng **`preferences-desktop`**, KHÔNG phải
`preferences-system`. Nếu đặt tên theo trí nhớ thì Settings sẽ âm thầm fallback về
Mint-Y và **mất nhận diện thương hiệu mà không ai biết vì sao** — không có lỗi
nào được ghi ra. Đây đúng là loại lỗi mà yêu cầu *"không giả định phiên bản hoặc
cấu trúc khi chưa xác minh"* nhắm tới.

### Tên chuẩn freedesktop (không trích từ `.desktop`)

`utilities-terminal`, `web-browser`, `multimedia-video-player`,
`multimedia-photo-viewer`, `accessories-document-viewer`, `applets-screenshooter`
và toàn bộ nhóm `places/*`, `devices/*`, `mimetypes/*`, `actions/*` là tên theo
**Icon Naming Spec** của freedesktop — tên mà app GTK và chính Nemo dùng khi xin
icon. Có chúng thì theme không fallback ở những chỗ dễ thấy nhất.

### Vì sao một số icon có HAI tên

`xplayer` + `multimedia-video-player`, `xviewer` + `multimedia-photo-viewer`,
`xreader` + `accessories-document-viewer`: app Mint xin tên riêng của nó
(`Icon=xplayer`), nhưng app bên thứ ba cùng loại và một số menu xin tên chuẩn
freedesktop. Cung cấp cả hai để theme nhất quán bất kể đường nào được đi. Nội dung
hình **giống nhau** — không vẽ hai kiểu cho một khái niệm.

---

## 4. Danh sách 75 icon đã có

### `scalable/apps/` — 16
`system-file-manager` (Nemo) · `preferences-desktop` (Cinnamon Settings) ·
`utilities-terminal` · `accessories-text-editor` (xed) · `web-browser` ·
`xplayer` · `multimedia-video-player` · `xviewer` · `multimedia-photo-viewer` ·
`xreader` · `accessories-document-viewer` · `pix` · `mintupdate` · `mintinstall` ·
`software-properties-mint` · `applets-screenshooter`

### `scalable/places/` — 14
`folder` · `folder-open` · `user-home` · `user-desktop` · `folder-documents` ·
`folder-download` · `folder-pictures` · `folder-music` · `folder-videos` ·
`folder-templates` · `folder-publicshare` · `network-workgroup` · `user-trash` ·
`user-trash-full`

Đây là bộ icon hiện trong **sidebar của Nemo** — chỗ giao nhau trực tiếp với T09.
Yêu cầu 3.3 của Nemo liệt kê Home, Desktop, Documents, Downloads, Pictures, Music,
Videos, ổ đĩa, Network; Nemo dựng danh sách đó từ XDG user-dirs và **xin icon theo
tên chuẩn**. Theme không quyết định *danh sách* vị trí (đó là user-dirs của người
dùng), chỉ quyết định *hình* của chúng.

### `scalable/devices/` — 7
`computer` · `drive-harddisk` · `drive-harddisk-system` · `drive-removable-media` ·
`drive-optical` · `media-flash` · `printer`

### `scalable/mimetypes/` — 9
`text-x-generic` · `text-x-script` · `application-pdf` · `image-x-generic` ·
`audio-x-generic` · `video-x-generic` · `application-x-executable` ·
`package-x-generic` · `x-office-document`

Tất cả dùng chung **một hình tấm giấy** để người đọc nhận ngay "đây là tài liệu",
rồi phân biệt loại bằng **màu của nét nội dung**. Không đổi hình dạng theo loại
tệp: đổi cả hai cùng lúc thì không học được bảng mã.

### `scalable/actions/` — 11
`document-new` · `document-open` · `document-save` · `edit-delete` · `edit-find` ·
`edit-copy` · `edit-paste` · `list-add` · `list-remove` · `window-close` ·
`view-refresh`

### `scalable/status/` — 4
`dialog-information` · `dialog-warning` · `dialog-error` · `dialog-question`

Yêu cầu 3.5 của Nemo nói phải tôn trọng hộp thoại xác nhận xoá và thao tác quan
trọng: `dialog-warning` / `dialog-error` / `dialog-question` chính là hình của
những hộp thoại đó.
**Ghi chú về `list-add` và `view-refresh`:** bản nháp đầu vẽ hai icon này bằng
accent `#3ddc97`. Đã đổi sang nét vẽ chuẩn `$mg-color-gray-400` vì accent chỉ đạt
**1.77:1 trên nền trắng** (đo bằng `tools/lint/contrast.py`), mà ở hai icon này
dấu `+` và mũi tên **chính là toàn bộ hình dạng** — không có đường bao nào khác
mang nghĩa thay nó. Nếu giữ accent thì chúng gần như vô hình trong hộp thoại chọn
tệp của app GTK chạy theme sáng. Lý luận đầy đủ ở `docs/design-system/icon-spec.md`
mục 4.4; ràng buộc này được khoá bằng bài
`test_line_icons_use_the_ink_colour`.

### `symbolic/` — 14
`actions/`: `document-new-symbolic` · `document-open-symbolic` ·
`edit-delete-symbolic` · `edit-find-symbolic` · `list-add-symbolic` ·
`list-remove-symbolic` · `window-close-symbolic` · `view-refresh-symbolic`
`places/`: `folder-symbolic` · `user-trash-symbolic` · `user-home-symbolic`
`status/`: `dialog-information-symbolic` · `dialog-warning-symbolic` ·
`dialog-error-symbolic`

---

## 4bis. 47 icon `cs-*` cho System Settings (Agent 6 bổ sung)

Yêu cầu Scope A của Agent 6: *"Biểu tượng danh mục đồng bộ với icon theme của
MintOS Glass."* Đây là phần hiện thực yêu cầu đó, và cũng là mục P2 mà chính T15
đã ghi là "chưa có" ở bản đầu của MANIFEST này.

### Nguồn tên — trích bằng máy theo cấu trúc bảng, không grep thô

Từ `linuxmint/Cinnamon` @ 6.6.9 (`806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18`),
`files/usr/share/cinnamon/cinnamon-settings/`:

| Nguồn | Số tên |
|---|---|
| `CATEGORIES` cột `"icon"` | **4** — `cs-cat-appearance`, `cs-cat-prefs`, `cs-cat-hardware`, `cs-cat-admin` |
| `modules/cs_*.py` → `SidePage(label, icon, …)` | **31** |
| `CONTROL_CENTER_MODULES` cột 3 | **3** — `cs-network`, `cs-color`, `cs-tablet` |
| `STANDALONE_MODULES` cột 3, chỉ lấy `cs-*` | **9** |
| **Tổng** | **47** |

### Một dương tính giả đã loại

Chuỗi **`cs-category-view`** cũng khớp mẫu `cs-*` khi grep thô, nhưng nó là **TÊN
CSS STYLE CLASS**, không phải tên icon — `cinnamon-settings.py:288`:
`context.add_class("cs-category-view")`. Đã xác nhận nó **không** xuất hiện trong
`CATEGORIES` / `CONTROL_CENTER_MODULES` / `STANDALONE_MODULES` / bất kỳ `SidePage`
nào. **Không tạo `cs-category-view.svg`.**

### 15 tên KHÔNG vẽ, có lý do

`cinnamon-settings.py` cũng tham chiếu: `mintreport`, `mintsysadm`, `mintlocale`,
`mintlocale-im`, `nvidia-settings`, `gdm-settings`, `fingwit`, `dnfdragora`,
`gpk-prefs`, `octopi`, `pamac-manager`, `system-software-install`, `yumex`,
`org.gnome.DiskUtility`, `gnome-online-accounts-gtk`.

Đó là **nhận diện của app khác** (System Information, Nvidia, trình quản lý gói của
Fedora/Arch/openSUSE…). Vẽ lại chúng vi phạm nguyên tắc ở mục 7: không vẽ lại
logo/nhận diện app bên thứ ba. Chúng fallback về Mint-Y hoặc về icon do chính app
đó cài.

### Ngôn ngữ thiết kế: line icon, KHÔNG squircle

47 icon này **cố ý khác** 16 icon app ở mục 4:

- 16 icon app là **app khởi chạy được** → squircle đặc màu, hiện ở cỡ lớn.
- 47 icon `cs-*` là **mục trong cùng một app** (Settings), hiện ở **cả** lưới trang
  chính **lẫn** list/sidebar ở cỡ nhỏ. Squircle + glyph bên trong sẽ **nhoè ở
  16-24px**.

Nên dùng đúng ngôn ngữ T15 đã thiết lập cho `mimetypes/` và `places/`: **nét
`$mg-color-gray-400` mang hình dạng** (đã đo 3.97:1 trên nền trắng và 4.68:1 trên
nền tối — đọc được trên cả hai), cộng **một chi tiết màu theo category**. Hình
dạng do nét trung tính mang, nên phần màu chỉ là mã phân loại chứ không phải thứ
người dùng dựa vào để nhận ra icon.

| Category | Hue | Token | Số icon |
|---|---|---|---|
| Appearance | mint `#3ddc97` | `$mg-status-accent` | 13 |
| Preferences | xanh `#3b9dff` | `$mg-color-blue-500` | 19 |
| Hardware | hổ phách `#ffbd2e` | `$mg-color-amber-500` | 9 |
| Administration | đỏ `#ff5f57` | `$mg-color-red-500` | 6 |

### Ranh giới trung thực về cách gán category

- Category của **3 panel C** và **9 trang standalone** lấy từ **cột 4 thật** của
  `CONTROL_CENTER_MODULES` / `STANDALONE_MODULES` (`network`/`color`/`wacom` =
  `hardware`, `bluetooth`/`printer` = `hardware`, `drivers`/`firewall`/`login`/
  `sources`/`user-accounts` = `admin`, `language`/`input-method` = `prefs`).
- Category của **31 module Python**: upstream gán qua thuộc tính `sidepage.cat`
  (`cinnamon-settings.py:356-359` so với `category["id"]`), nhưng **cơ chế gán
  không nằm trong `modules/*.py`** nên không truy ra được từ nguồn. Việc nhóm 31
  icon này theo ngữ nghĩa là **QUYẾT ĐỊNH THIẾT KẾ CỦA DỰ ÁN**, không phải tuyên bố
  về cách upstream phân loại.

### Danh sách 47 icon

**Danh mục (4):** `cs-cat-appearance` · `cs-cat-prefs` · `cs-cat-hardware` · `cs-cat-admin`

**Appearance (12):** `cs-themes` · `cs-backgrounds` · `cs-desktop-effects` ·
`cs-fonts` · `cs-panel` · `cs-desklets` · `cs-applets` · `cs-extensions` ·
`cs-nightlight` · `cs-screensaver` · `cs-desktop` · `cs-overview`

**Preferences (18):** `cs-general` · `cs-keyboard` · `cs-mouse` · `cs-sound` ·
`cs-notifications` · `cs-date-time` · `cs-default-applications` ·
`cs-startup-programs` · `cs-actions` · `cs-gestures` · `cs-workspaces` ·
`cs-windows` · `cs-privacy` · `cs-universal-access` · `cs-user` · `cs-details` ·
`cs-language` · `cs-input-method`

**Hardware (8):** `cs-display` · `cs-power` · `cs-thunderbolt` · `cs-network` ·
`cs-color` · `cs-tablet` · `cs-printer` · `cs-bluetooth`

**Administration (5):** `cs-drivers` · `cs-firewall` · `cs-login` · `cs-sources` ·
`cs-user-accounts`

*(4 + 12 + 18 + 8 + 5 = 47. Bốn icon `cs-cat-*` là icon CỦA danh mục nên đếm riêng;
các icon còn lại đếm theo category mà chi tiết màu của chúng thể hiện.)*

---

## 5. Icon CHƯA có, và chúng fallback về đâu

Ghi rõ để không ai tưởng theme này đủ. **Tất cả** mục dưới đây fallback qua
`Inherits=Mint-Y,Adwaita,gnome,hicolor`, tức là vẫn hiện icon, chỉ là icon của
Mint-Y chứ không phải của MintOS Glass.

| Chưa có | Số lượng ước tính | Fallback | Ghi chú |
|---|---|---|---|
| **Icon panel / status của applet** | ~40 | Mint-Y | **CỐ Ý KHÔNG LÀM.** Xem mục 6. |
| ~~Icon của Cinnamon Settings (`cs-*`)~~ | ~~31~~ → **47** | — | **ĐÃ LÀM XONG (Agent 6).** Con số 31 ở lần khảo sát đầu là ĐẾM SAI: 31 là số file `cinnamon-settings-*.desktop` (mỗi module một launcher), còn số TÊN ICON `cs-*` thật là **47** = 4 danh mục + 31 module Python + 3 panel C + 9 trang standalone. Đã trích bằng máy theo cấu trúc bảng, không grep thô. Xem mục 4bis. |
| Icon app bên thứ ba (Firefox, LibreOffice, VLC, GIMP, …) | hàng trăm | `.desktop` của app tự nhúng icon, rồi Mint-Y | App cài qua `.deb`/Flatpak thường mang icon riêng; theme không nên và không thể thay. Xem mục 7 về thương hiệu. |
| `symbolic` cho `apps/`, `devices/`, `mimetypes/` | ~30 | Mint-Y (có đủ bộ symbolic) | Chỉ làm symbolic cho actions/places/status — ba nhóm hay bị GTK xin bản symbolic nhất (panel, menu, toolbar). |
| Mimetype hiếm (`application-x-7z-compressed`, `text-x-python`, …) | hàng trăm | Mint-Y | 9 mimetype trong tập lõi là những loại gặp nhiều nhất trong list view của Nemo. |
| Icon theo kích thước cố định (16/22/32/48/…) | — | không cần | SVG `Type=Scalable` phục vụ mọi kích thước. Không sinh raster. |
| `user-trash` ở trạng thái "đang xoá" | 1 | Mint-Y | Không có trạng thái này trong Icon Naming Spec. |

---

## 6. Icon panel / status: CỐ Ý KHÔNG LÀM, và lý do

Yêu cầu 3.3 của Agent 5 nói rõ: *"Không thay thế các icon trạng thái chức năng
bằng hình ảnh trang trí không có trạng thái tương ứng."* Đây là ràng buộc kỹ
thuật thật, không phải thận trọng hình thức:

Icon Wi-Fi, Bluetooth, pin, âm lượng trên panel **không phải** là ảnh tĩnh. Mỗi
applet tự chọn tên icon theo **trạng thái đo được lúc chạy**:

- network: `network-wireless-signal-excellent` → `-good` → `-ok` → `-weak` →
  `-signal-none`, cộng `-offline`, `-acquiring`, `-no-route`
- battery: `battery-full` / `-good` / `-low` / `-critical` / `-empty`, mỗi mức lại
  có biến thể `-charging` và `-charged`
- volume: `audio-volume-high` / `-medium` / `-low` / `-muted` / `-off`

Nếu theme này cung cấp **một** ảnh `network-wireless` đẹp mà không có đủ các mức
tín hiệu, thì hoặc là applet không tìm thấy tên nó cần (rơi về Mint-Y — tức
không nhất quán), hoặc tệ hơn: tìm thấy một ảnh **không phản ánh trạng thái thật**
và người dùng đọc sai mức pin/mạng. Cả hai đều tệ hơn là không làm.

**Quyết định:** chưa ship icon panel ở vòng này. Việc này cần **phối hợp với
Agent 2 (Cinnamon shell)** để xác định chính xác tập tên icon mà các applet trong
Cinnamon 6.6 yêu cầu, trích từ mã nguồn applet chứ không đoán. Khi đó mới vẽ đủ
bộ biến thể trạng thái. Đã ghi thành việc P2 trong `docs/design-system/icon-spec.md`.

Ba icon `status/dialog-*` có trong tập lõi là **icon hộp thoại**, không phải icon
applet panel — chúng là ảnh tĩnh đúng nghĩa nên không vi phạm ràng buộc trên.

---

## 7. Thương hiệu app bên thứ ba

Yêu cầu 3.4: *"giữ khả năng nhận diện thương hiệu của ứng dụng bên thứ ba khi cần
thiết để tránh nhầm lẫn"*, và *"không sao chép nguyên xi bộ icon độc quyền của
Apple hoặc tạo tài nguyên ngụ ý MintOS Glass là sản phẩm chính thức của Apple"*.

Cách theme này thoả cả hai:

1. **Không vẽ lại logo của app bên thứ ba.** Firefox, LibreOffice, VLC, Chrome… giữ
   icon do chính app đó cài. Theme không ghi đè tên icon của chúng, nên không có
   rủi ro nhái thương hiệu hay làm mất khả năng nhận diện.
2. **Chỉ vẽ icon cho app của hệ thống mục tiêu** — Nemo, xed, Pix, Xplayer,
   Xreader, Xviewer, mintupdate, mintinstall, cinnamon-settings, terminal,
   screenshot. Đây là app mà MintOS Glass có trách nhiệm tạo giao diện nhất quán.
3. **Không sao chép hình của Apple.** App icon dùng squircle bo góc (một hình khối
   hình học phổ quát, không phải tài sản của riêng ai) nhưng **không** mô phỏng
   bất kỳ biểu tượng cụ thể nào của macOS: không Finder hai nửa xanh, không
   Launchpad tên lửa, không Preview la bàn. Hình trong bộ này là hình học tự vẽ:
   folder, gear, dấu nhắc terminal, bút chì, địa cầu, tam giác play, khung ảnh,
   cuốn sách mở, khiên có dấu kiểm, thùng rác.
4. **Không dùng tên, nhãn hay dấu hiệu nào ngụ ý Apple chứng thực.** Tên theme là
   `MintOS-Glass`. Ghi chú pháp lý về cái tên này so với chính sách đặt tên của
   Linux Mint là một câu hỏi MỞ, đã ghi trong `docs/decisions.md` từ trước — nó
   thuộc về Agent K (docs/release), không phải việc của icon theme.

### Giấy phép và nguồn của từng thành phần

| Thành phần | Nguồn | Giấy phép | Quyền phân phối |
|---|---|---|---|
| 75 file SVG | **Tự vẽ hoàn toàn** trong dự án này, bằng path dữ liệu gốc | GPL-3.0-or-later (theo `LICENSE` của repo) | ✅ toàn quyền |
| Giá trị màu | `src/cinnamon/tokens/_tokens.scss` của chính repo | GPL-3.0-or-later | ✅ |
| Cấu trúc `index.theme` | Học theo **định dạng** trong Icon Theme Spec của freedesktop và cách Mint-Y khai báo section. Chỉ học cấu trúc, **không sao chép tệp hay hình nào** | Spec là tài liệu công khai | ✅ |
| Tên icon | Icon Naming Spec của freedesktop + khoá `Icon=` trong `.desktop` của các app | Tên là dữ kiện, không phải tác phẩm | ✅ |
| Hình ảnh tải từ Internet | **KHÔNG CÓ** | — | ✅ không có gì cần xin phép |
| Ảnh raster, font, ảnh chụp | **KHÔNG CÓ** | — | ✅ |

**Không có tài nguyên bên thứ ba nào được đưa vào repo.** Mọi thứ hoặc tự vẽ,
hoặc là dữ kiện (tên icon, cấu trúc file). Nên không có nghĩa vụ ghi công nào
ngoài việc nêu nguồn tham khảo ở trên, và không có rủi ro giấy phép.

---

## 8. Trạng thái kiểm chứng

### ĐÃ kiểm chứng offline
Chạy `python3 tools/lint/icon_theme.py` và
`python3 -m unittest tests.lint.test_icon_theme`:

- `index.theme` parse được, có `[Icon Theme]` + `Name` + `Inherits` + `Directories`
- `Name` khớp tên thư mục theme
- **hai chiều** giữa `Directories` và thư mục thật: không thư mục khống, không
  thư mục mồ côi, không thư mục rỗng, không liệt kê trùng
- mọi thư mục có section, mọi section khớp một thư mục
- mỗi section đủ `Size`/`Context`/`Type`; `Type=Scalable` có `MinSize`+`MaxSize` và
  `Size` nằm trong khoảng đó
- `Context` khớp ngữ nghĩa thư mục (`scalable/apps` → `Apps`, …)
- `Inherits` kết thúc bằng `hicolor`, không tự kế thừa chính nó
- **75/75** icon lõi theo fixture tồn tại
- mọi SVG parse được bằng `xml.etree`, `viewBox="0 0 24 24"`, `width=height=24`
- không URL ngoài (khai báo `xmlns` được miễn), không
  `<script>/<image>/<filter>/<mask>/<clipPath>/<use>/<foreignObject>`
- không `rgba()` trong SVG (librsvg hỗ trợ không nhất quán giữa phiên bản)
- mọi literal màu tra ngược được về `_tokens.scss`
- icon symbolic **đơn sắc**, không gradient
- màu nét vẽ `gray-400` đạt ≥ 3:1 trên **cả** nền sáng lẫn nền tối (đo lại mỗi lần chạy)
- tên icon đúng quy ước Icon Naming Spec

### CHƯA kiểm chứng — cần Linux Mint 22.3 / Cinnamon 6.6 thật
Không có máy Mint nên **không thể** xác nhận, và **không tuyên bố** đã xác nhận:

| Chưa kiểm chứng | Điều kiện để kiểm |
|---|---|
| Cinnamon/Nemo có **nhận diện** theme này trong danh sách icon không | **Đã thu hẹp đáng kể — xem ngay dưới bảng.** Còn lại: chạy thật trên máy Mint để xác nhận end-to-end |
| `Inherits` có fallback đúng như suy luận từ spec không | Bỏ thử một icon khỏi theme, xem nó có hiện bằng hình Mint-Y không |
| GTK có tô lại icon `-symbolic` đúng màu chữ không | Xem toolbar Nemo ở theme sáng và theme tối |
| SVG có raster sắc ở 16px không (nét 1.5 có bị mờ/nhoè không) | Xem list view của Nemo ở icon size 16 |
| librsvg trên Mint 22.3 có hỗ trợ hết các path/arc đã dùng không | Xem từng icon; arc `a` và `A` là phần rủi ro nhất |
| Icon có hiện đúng trong hộp thoại chọn tệp của app GTK không | Mở File → Open trong xed |
| `Size=24` có phải lựa chọn tối ưu cho `Type=Scalable` không, hay nên là 48/64 | So ở 16px và 256px |

### Điều kiện để được LIỆT KÊ trong Settings → Themes → Icons: ĐÃ XÁC MINH TỪ MÃ

`cs_themes.py:144-157` duyệt thư mục và chấp nhận một thư mục là icon theme khi và
chỉ khi: (1) tên không nằm trong `THEMES_BLACKLIST`; (2) `<thư-mục>/index.theme`
**tồn tại**; (3) đọc **từng dòng** — gặp dòng **bắt đầu bằng** `Hidden=true` thì
loại, gặp dòng **bắt đầu bằng** `Directories=` thì nhận.

Đối chiếu `index.theme` của theme này với đúng vòng lặp đó:

| Điều kiện | Kết quả |
|---|---|
| có `index.theme` | ✅ |
| có dòng **bắt đầu bằng** `Directories=` (không thụt lề) | ✅ dòng 39 |
| không dòng nào bắt đầu bằng `Hidden=true` | ✅ |
| `mintos-glass` không nằm trong `THEMES_BLACKLIST` | ✅ |

**Parser đọc THEO DÒNG chứ không dùng GKeyFile**, nên một khoá `Directories=` bị
thụt lề hoặc nằm sau `Hidden=true` sẽ làm theme biến mất khỏi danh sách mà không có
lỗi nào được ghi ra. Đây là ràng buộc thật, không phải lý thuyết — và là lý do
`index.theme` của theme này KHÔNG thụt lề dòng `Directories=`.

Cũng đã xác minh `ICON_FOLDERS` (`cs_themes.py:26-29`) = `~/.icons`, rồi
`GLib.get_user_data_dir()/icons` (= `~/.local/share/icons`), rồi các thư mục hệ
thống — **đúng thứ tự** đường cài đặt đã ghi ở mục 9.1.

**Một xác nhận quan trọng cho `Inherits`:** `THEMES_BLACKLIST` (`cs_themes.py:35-44`)
chứa `gnome`, `hicolor`, `adwaita`, `adwaita-dark`, `highcontrast`, `epapirus`,
`ubuntu-mono*`, `humanity*`, với comment nói rõ chúng *"not meant to be used as a
theme. Provides icons to inheriting themes."* Nghĩa là blacklist chỉ ẩn chúng khỏi
**bộ chọn**, **không** vô hiệu hoá chúng làm **đích kế thừa**. Nên chuỗi
`Inherits=Mint-Y,Adwaita,gnome,hicolor` vẫn hoạt động đầy đủ dù ba trong bốn tên đó
không bao giờ hiện ra cho người dùng chọn.

Điểm rủi ro cao nhất là **kích thước nhỏ**: lưới 24 với nét 1.5 khi scale xuống
16px cho nét ~1px, có thể mờ. Đây là lý do cần kiểm bằng mắt trên máy thật trước
khi coi bộ icon này là xong — và là lý do tập lõi giữ hình **đơn giản, ít chi
tiết** thay vì vẽ cầu kỳ.

---

## 9. Đóng gói — vị trí trên đĩa và ràng buộc cho agent đóng gói (T12/T14)

Phần này viết cho **agent đóng gói**, không phải cho người dùng cuối.

### 9.1 Thư mục đích

| Trong repo | Trên máy người dùng |
|---|---|
| `src/icons/MintOS-Glass/` (toàn bộ, giữ nguyên cấu trúc con) | `~/.local/share/icons/MintOS-Glass/` |

**Cả thư mục phải được chép nguyên khối**, gồm `index.theme` và cả 9 thư mục con.
Thiếu `index.theme` thì thư mục chỉ là một đống SVG vô danh — hệ thống không nhận
diện đó là icon theme.

Đường đích là **thư mục người dùng, không cần root**, đúng ADR-002 (cùng gốc với
`~/.local/share/themes/MintOS-Glass` của Cinnamon/GTK theme). Đây là một trong hai
đường ghi duy nhất mà tooling của dự án được phép chạm; `tools/lint/safety_paths.py`
của Agent 1 khoá điều đó.

### 9.2 Sau khi chép

Cần chạy `gtk-update-icon-cache` trên thư mục theme. **T15 không tự chạy** lệnh nào
và **không** yêu cầu người dùng cài thêm gì — `gtk-update-icon-cache` thuộc gói
`gtk` vốn đã có trên Mint 22.3. Việc quyết định chạy lúc cài hay lúc build ISO là
của T12.

**Chưa xác minh** (không có máy Mint): liệu bộ nạp icon có yêu cầu cache file để
nhận diện theme, hay chỉ cần `index.theme`. Không tuyên bố.

### 9.3 Chọn làm theme mặc định

Là gsetting `org.cinnamon.desktop.interface icon-theme` → `MintOS-Glass`. Khoá này
đã được T12 liệt kê trong work-breakdown. **T15 không tự ghi gsetting** — tài liệu
chỉ nêu tên khoá.

### 9.4 Cấu trúc đã sẵn sàng để đóng gói, nhưng CHƯA có gì được đóng gói

Cần nói rõ ranh giới: T15 giao **module tài nguyên** ở trạng thái repo — đúng cấu
trúc, đúng tên, có kiểm tra tự động. T15 **không** tạo `.deb`, không tạo tarball
release, không viết installer, không dựng ISO. Đó là T12/T14.

**Chưa có trong phạm vi T15** (agent đóng gói phải biết để không tưởng là đã có):
- không có file `.desktop` hay XML đăng ký theme
- không có pipeline render PNG (`render-png.sh` nằm trong allow-list nhưng **chưa
  được tạo**, vì theme thuần SVG không cần nó — **không khai là đã có**)
- không có cơ chế chọn theme lúc first-boot

### 9.5 Hoàn tác

Xoá thư mục `~/.local/share/icons/MintOS-Glass/`. **Không có gì khác để dọn**:
không package đã cài, không file hệ thống đã sửa, không schema đã thêm, không
cache nằm ngoài thư mục đó (nếu `gtk-update-icon-cache` sinh `icon-theme.cache` thì
nó nằm **trong** thư mục theme và bị xoá cùng).

Sau khi xoá, gsetting `icon-theme` sẽ trỏ tới một theme không tồn tại → hệ thống
rơi về theme mặc định. **Chưa xác minh** Cinnamon xử lý trường hợp đó êm hay cần
đặt lại gsetting trước; thứ tự an toàn là **đặt lại gsetting rồi mới xoá thư mục**.

### 9.6 Cập nhật tài nguyên

Thêm/sửa icon: theo quy trình ở `docs/design-system/icon-spec.md` mục 9. Ràng buộc
cứng cho mọi lần cập nhật:

- mọi màu phải tra ngược được về token (lint `colors-are-token-values`)
- `index.theme` phải khớp **hai chiều** với thư mục thật (lint `directories-two-way`)
- icon `-symbolic` phải đơn sắc (lint `symbolic-monochrome`)
- phải chạy `tools/lint/icon_theme.py` — lint này **không cần compiler SCSS** nên
  chạy được ở bất kỳ đâu có Python 3, kể cả trong pipeline build ISO
