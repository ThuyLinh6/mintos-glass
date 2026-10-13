# MANIFEST — Icon theme MintOS-Glass (T15)

**Owner:** Agent D (Visual/Assets) · **Task:** T15
**Thư mục:** `src/icons/MintOS-Glass/` · **75 icon SVG + `index.theme`**
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
│   ├── apps/       (16)
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

**9 thư mục, 75 tệp, không thư mục rỗng.** Cả 9 đều có mặt trong `Directories`
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

## 5. Icon CHƯA có, và chúng fallback về đâu

Ghi rõ để không ai tưởng theme này đủ. **Tất cả** mục dưới đây fallback qua
`Inherits=Mint-Y,Adwaita,gnome,hicolor`, tức là vẫn hiện icon, chỉ là icon của
Mint-Y chứ không phải của MintOS Glass.

| Chưa có | Số lượng ước tính | Fallback | Ghi chú |
|---|---|---|---|
| **Icon panel / status của applet** | ~40 | Mint-Y | **CỐ Ý KHÔNG LÀM.** Xem mục 6. |
| Icon 31 module của Cinnamon Settings (`cs-actions`, `cs-applets`, `cs-backgrounds`, …) | 31 | Mint-Y | Đã đếm thật: có **31** file `cinnamon-settings-*.desktop` trong Cinnamon 6.6.9, mỗi file một icon `cs-*`. Làm bộ này là việc của vòng mở rộng P2. |
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
| Cinnamon/Nemo có **nhận diện** theme này trong danh sách icon không | Cài vào `~/.local/share/icons/MintOS-Glass/`, chạy `gtk-update-icon-cache`, mở Settings → Themes → Icons |
| `Inherits` có fallback đúng như suy luận từ spec không | Bỏ thử một icon khỏi theme, xem nó có hiện bằng hình Mint-Y không |
| GTK có tô lại icon `-symbolic` đúng màu chữ không | Xem toolbar Nemo ở theme sáng và theme tối |
| SVG có raster sắc ở 16px không (nét 1.5 có bị mờ/nhoè không) | Xem list view của Nemo ở icon size 16 |
| librsvg trên Mint 22.3 có hỗ trợ hết các path/arc đã dùng không | Xem từng icon; arc `a` và `A` là phần rủi ro nhất |
| Icon có hiện đúng trong hộp thoại chọn tệp của app GTK không | Mở File → Open trong xed |
| `Size=24` có phải lựa chọn tối ưu cho `Type=Scalable` không, hay nên là 48/64 | So ở 16px và 256px |

Điểm rủi ro cao nhất là **kích thước nhỏ**: lưới 24 với nét 1.5 khi scale xuống
16px cho nét ~1px, có thể mờ. Đây là lý do cần kiểm bằng mắt trên máy thật trước
khi coi bộ icon này là xong — và là lý do tập lõi giữ hình **đơn giản, ít chi
tiết** thay vì vẽ cầu kỳ.
