# ĐỀ XUẤT — Control Center / Quick Settings cho MintOS Glass

**Task:** T17 · **Owner:** Agent 6 (Settings & Control Center UI)
**Trạng thái:** **ĐỀ XUẤT, CHƯA TRIỂN KHAI.** Người dùng đã quyết định
(2026-10-13): *style applet có sẵn ngay + viết đề xuất, **chưa build applet mới***.
**Bằng chứng máy đọc được:** `tests/fixtures/cinnamon-settings-hooks.txt` (nhóm `APPLET`)
**Kiểm tra:** `tools/lint/settings_arch.py`

> **Không có mã applet nào được viết trong task này.** Tài liệu này là thứ phải
> được duyệt **trước khi** viết, đúng nguyên tắc 2.3 ("chỉ sửa mã nguồn Cinnamon
> khi thực sự cần thiết và phải giải thích rõ lý do") và đúng yêu cầu Scope B
> ("nếu một chức năng không đạt được bằng cơ chế có sẵn, ghi rõ giới hạn và đề xuất
> phương án **trước khi** xây thành phần tuỳ chỉnh").

---

## 1. Phân biệt hai thứ mà yêu cầu Scope B đòi tách rõ

Yêu cầu viết: *"Phân biệt rõ giữa bảng điều khiển nhanh trên panel và ứng dụng
System Settings."* Đây là kết quả khảo sát, và nó **không như mong đợi**:

| | System Settings | "Control Center" kiểu macOS |
|---|---|---|
| Là gì | App **cửa sổ**, mở ra để cấu hình | Bảng **bật/tắt nhanh** thả từ panel |
| Trong Cinnamon 6.6 | `cinnamon-settings` — có thật, 31 module | **KHÔNG TỒN TẠI** |

**Đã grep toàn bộ Cinnamon 6.6.9**: không có thành phần nào tên `quick-settings`,
`quicksettings`, hay một bảng điều khiển nhanh tương đương. Chỗ duy nhất cụm
"Control Center" xuất hiện là `cinnamon-settings.py:42`:

```python
menuComment = _("Control Center")
```

và `CONTROL_CENTER_MODULES` (`:70`) — cả hai đều trỏ tới **chính app System
Settings**, không phải một bảng quick-settings. Thêm nữa `bin/capi.py:27` đăng ký
Gio extension point tên `cinnamon-control-center-1` — cũng là app Settings, không
phải panel nhanh.

> **Kết luận phải nói thẳng:** ở Mint, **"Control Center" là tên gọi khác của System
> Settings**. Không có thành phần sẵn nào để "mở rộng" thành một bảng quick-settings
> kiểu macOS. Bất kỳ bảng nào như vậy đều là **thành phần mới**.

Vì thế Scope B có hai phần tách bạch, và chỉ một phần làm được ngay:

- **Phần làm được ngay, không viết mã mới:** style popup của các applet bundled
  (mục 3). Phần lớn **đã xong từ T04**.
- **Phần cần duyệt trước:** một applet gom nhóm (mục 5).

---

## 2. Thành phần bundled đã xác minh — và một lỗ hổng

Tất cả nằm trong `files/usr/share/cinnamon/applets/` của **chính Cinnamon**, không
phải `cinnamon-spices-applets`, nên **không cần cài thêm gì**. Đã đọc mã từng cái:

| Chức năng yêu cầu | Applet bundled | Bằng chứng API thật | Có thật? |
|---|---|---|---|
| Âm lượng + đầu ra | `sound@cinnamon.org` | `applet.js:16` `const Slider = imports.ui.slider`; `:84` `class VolumeSlider extends PopupMenu.PopupSliderMenuItem`; `:224-225` `_output.volume = …` rồi `push_volume()`; `:120-122` `removeActor`/`addActor(this._slider, {span:-1, expand:true})` | ✅ |
| **Độ sáng màn hình** | `power@cinnamon.org` | `applet.js:13` `const BrightnessBusName = "org.cinnamon.SettingsDaemon.Power.Screen"`; `:220` `class BrightnessSlider extends PopupMenu.PopupSliderMenuItem`; `:272` `_updateBrightnessLabel`; `:279` `_proxy.connectSignal('Changed', …)`; `:309-312` chuẩn hoá min/max rồi `_setBrightness(0..100)` | ✅ **đã có sẵn** |
| Wi-Fi / mạng | `network@cinnamon.org` | `applet.js` — menu mạng của applet | ✅ |
| Thông báo | `notifications@cinnamon.org` | `applet.js` | ✅ |
| Ánh sáng đêm | `nightlight@cinnamon.org` | `applet.js:7` `class NightLightSwitch extends Applet.IconApplet`; `:16-26` tự thêm mục "Configure..." vào context menu | ✅ |
| **Bluetooth** | — | **KHÔNG CÓ applet bundled nào** | ❌ |

### Bluetooth là lỗ hổng thật, và phải xử lý trung thực

Đã grep toàn bộ `files/usr/share/cinnamon/applets/`. **Không có applet Bluetooth.**
Hai tệp có nhắc tới "bluetooth" là `network@cinnamon.org/applet.js` và
`power@cinnamon.org/applet.js`, và cả hai chỉ **kiểm tra kiểu thiết bị**, không phải
một công tắc Bluetooth.

Trên Linux Mint, Bluetooth là **`blueberry`** (một gói riêng), hiện qua **systray**;
và trong System Settings nó là một **launcher tầng 3** trỏ tới `blueberry` hoặc
`blueman-manager` (bằng chứng ở
`docs/design-system/settings-architecture.md` mục 1).

> **Ràng buộc chức năng của Scope B áp dụng đúng chỗ này:** *"Không tạo nút
> Bluetooth, Wi-Fi, độ sáng hoặc âm lượng chỉ thay đổi màu sắc mà không thực hiện
> hành động tương ứng."*
>
> Nên: **KHÔNG** được vẽ một nút Bluetooth trang trí. Một nút Bluetooth thật phải
> gọi **`blueberry`** hoặc nói trực tiếp với **rfkill / BlueZ**. Cả hai đều là
> **phụ thuộc ngoài Cinnamon**, và đây chính là lý do mục 5 phải được duyệt trước
> khi viết: nó là chỗ duy nhất trong Scope B mà "tái sử dụng thành phần có sẵn"
> **không đủ**.

Trạng thái **không khả dụng** phải hiện đúng: nếu `blueberry` không có mặt hoặc
`rfkill` không liệt kê adapter nào, nút phải hiện **trạng thái không khả dụng** (mờ
+ tooltip giải thích), **không** hiện trạng thái "tắt" — vì "tắt" là một tuyên bố
sai về phần cứng.

---

## 3. Phần làm được ngay: popup applet **đã được T04 style sẵn**

Yêu cầu giao diện của Scope B (nền Dark Glass, viền nhẹ, bo góc, tương phản tốt,
trạng thái bật/tắt dễ phân biệt) áp lên popup của applet thì **phần lớn đã xong**,
vì T04 đã style đúng các class St mà mọi popup applet dùng. Đã đối chiếu với
`src/cinnamon/overrides/`:

`.popup-menu-item` (kèm `:active`, `:focus`, `:insensitive`) · `.popup-menu-content`
· `.popup-separator-menu-item` · `.popup-slider-menu-item` · `.slider` ·
`.toggle-switch` (kèm `:checked`) · `.toggle-switch-us` · `.toggle-switch-intl` ·
`.popup-subtitle-menu-item` · `.popup-menu-arrow` · `.popup-menu-icon`

Nghĩa là: **slider âm lượng của `sound@cinnamon.org`, slider độ sáng của
`power@cinnamon.org`, và menu của `network@cinnamon.org` đều đã ăn Dark Glass** thông
qua CSS của T04, **không cần viết gì thêm**.

*(Trong fixture, nhóm bằng chứng này là mục `st-classes-already-styled`; các applet
liên quan là `sound@cinnamon.org`, `power@cinnamon.org`, `network@cinnamon.org`,
`notifications@cinnamon.org`, `nightlight@cinnamon.org`, và hai mục ghi rõ khoảng
trống Bluetooth là `bluetooth` + `bluetooth-requires-external`.)*

Đây là lý do lựa chọn "style applet có sẵn" không phải là một giải pháp tạm bợ: nó
đã **hoàn tất về mặt thị giác** cho từng popup riêng lẻ.

### Cái còn thiếu — và CSS không lấp được

Thứ macOS Control Center có mà cách này **không** có là **gom nhóm**: một bảng duy
nhất chứa Wi-Fi + Bluetooth + âm lượng + độ sáng + night light, bố cục dạng module.

**CSS của St không làm được việc đó.** Đã xác minh ở T04: St **không có** `transform`,
**không có** pseudo-element, **không có** `box-sizing`, và chỉ cho **một**
`box-shadow` mỗi rule. Quan trọng hơn: CSS **không thể di chuyển actor giữa các
applet** — mỗi applet sở hữu menu riêng của nó, và việc gộp chúng là quyết định của
**mã applet**, không phải của stylesheet.

Nên khoảng cách giữa "đã có" và "giống macOS" **chỉ** có thể lấp bằng mã applet. Đó
nội dung mục 5.

### Việc cần phối hợp với Agent 2, không tự làm

Mọi thay đổi CSS cho popup applet đều nằm trong `src/cinnamon/**` — **thuộc T04
(Agent 2)**. Nếu cần bổ sung selector cho popup cụ thể (ví dụ khoảng cách giữa các
module trong menu của `sound@cinnamon.org`), **phải thống nhất quyền sở hữu với
Agent 2 trước**, theo nguyên tắc 5 của Agent 6: *"không tự ý chỉnh sửa cùng một
thành phần mà không thống nhất quyền sở hữu"*. **Task này không sửa
`src/cinnamon/**`** — allow-list của T17 cấm rõ.

---

## 4. Không có nút giả — kiểm kê từng chức năng

Bảng này là cam kết: mỗi nút trong bất kỳ phương án nào đều phải trỏ tới một hành
động thật, kèm API đã xác minh. **Không có dòng nào ở trạng thái "chỉ đổi màu".**

| Nút | Hành động thật | API đã xác minh | Trạng thái không khả dụng |
|---|---|---|---|
| Âm lượng | đổi volume đầu ra hiện tại | `sound@cinnamon.org` `VolumeSlider` → `_output.volume` + `push_volume()` (`applet.js:224-225`) | không có sink → ẩn slider, hiện nhãn |
| Đổi đầu ra | chọn sink khác | cùng applet, `_output` | chỉ 1 sink → hiện nhưng mờ |
| **Độ sáng** | đổi brightness màn hình | `power@cinnamon.org` `BrightnessSlider` → DBus `org.cinnamon.SettingsDaemon.Power.Screen` (`applet.js:13,220,312`) | proxy không trả lời / không có backlight → **hiện "không khả dụng"**, không hiện 0% |
| Wi-Fi | bật/tắt + chọn mạng | `network@cinnamon.org` (NMClient qua applet) | không có adapter → hiện trạng thái, không hiện "tắt" |
| Night light | bật/tắt | `nightlight@cinnamon.org` `NightLightSwitch` (`applet.js:7`) | — |
| Thông báo | mở/mute | `notifications@cinnamon.org` | — |
| **Bluetooth** | **cần `blueberry` hoặc rfkill/BlueZ** | **chưa có thành phần bundled** — xem mục 2 | adapter vắng → **"không khả dụng"**, cấm hiện "tắt" |
| Tiết kiệm năng lượng | đổi profile nguồn | cần xác minh tiếp API của `power@cinnamon.org` / cinnamon-settings-daemon | **CHƯA XÁC MINH** — không đưa vào cho tới khi đọc mã |

**Hai dòng cố ý để trống/chưa xác minh.** Không điền một API chưa đọc mã: yêu cầu
của Agent 6 nói rõ *"không giả định các thư viện, dịch vụ hoặc API đã có mặt nếu
chưa kiểm tra"*.

---

## 5. PHƯƠNG ÁN cần duyệt: applet gom nhóm

### 5.1 Vì sao cần duyệt

Viết một applet mới là **mã Cinnamon Shell mới**. Nó:

- thuộc vùng sở hữu của **Agent 2 (Cinnamon Shell UI)** — phải thống nhất trước;
- là **thành phần mới**, nên theo nguyên tắc 2.2 phải chứng minh rằng không đạt
  được bằng "GTK theme, CSS, biểu tượng, cấu hình hoặc tiện ích mở rộng hiện có".
  Mục 3 đã chứng minh: **CSS không gom nhóm được**, nên điều kiện này **thoả**;
- phải **bảo trì song song** với applet gốc của Cinnamon, và sẽ cần xem lại mỗi lần
  Mint cập nhật API applet.

### 5.2 Thiết kế đề xuất

**Nguyên tắc quan trọng nhất: KHÔNG nhân bản logic điều khiển.** Applet mới phải
**tái sử dụng đúng các API mà applet bundled đang dùng**, không tự viết lại cách
đọc/ghi volume hay brightness:

| Module | Tái sử dụng | Lý do |
|---|---|---|
| Âm lượng | `imports.ui.slider` + `PopupMenu.PopupSliderMenuItem`, cùng đường `_output.volume` / `push_volume()` mà `sound@cinnamon.org` dùng | đã có sẵn, đã được upstream bảo trì |
| Độ sáng | proxy DBus `org.cinnamon.SettingsDaemon.Power.Screen`, cùng `BrightnessSlider` pattern của `power@cinnamon.org` | **đã có sẵn** — không cần viết mới |
| Wi-Fi | để nguyên `network@cinnamon.org`; applet mới **không** tự quản lý NMClient | tự viết lại stack mạng là rủi ro lớn nhất và không cần thiết |
| Night light | gọi cùng cơ chế toggle của `nightlight@cinnamon.org` | đã có sẵn |
| Bluetooth | `blueberry` nếu có mặt, **nếu không** thì hiện "không khả dụng" | xem mục 2 |

**Ranh giới phải giữ:** applet mới **bổ sung**, **không thay thế**. Người dùng vẫn
giữ được `sound@cinnamon.org` / `power@cinnamon.org` / `network@cinnamon.org` trên
panel nếu muốn. **Không** tự gỡ applet nào, **không** tự ghi cấu hình panel của
người dùng — đúng ràng buộc "không ghi đè thiết lập cá nhân" đã áp dụng cho Nemo
và cho `pinned-apps` ở T11.

**Bố cục:** dạng module như yêu cầu Scope B — mỗi nhóm là một khối bo góc, viền
mảnh, nền Dark Glass; dùng đúng `.popup-menu-content` + `.popup-separator-menu-item`
đã được T04 style, để không phải thêm CSS mới.

**Màn hình nhỏ / scaling:** popup của applet Cinnamon tự giới hạn theo kích thước
màn hình; nhưng **chưa xác minh** hành vi khi bảng cao hơn vùng làm việc còn lại.
Yêu cầu Scope B nói rõ *"không để bảng điều khiển bị cắt, tràn khỏi màn hình hoặc
che mất thành phần quan trọng"* — đây là mục **bắt buộc phải kiểm trên máy thật**
trước khi coi applet là xong.

### 5.3 Rủi ro

| # | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| 1 | API applet của Cinnamon đổi giữa các bản → applet vỡ khi Mint cập nhật | Cao | chỉ dùng API mà applet bundled đang dùng; không dùng API nội bộ |
| 2 | Trùng chức năng với applet bundled → hai nơi cùng điều khiển volume/brightness, dễ lệch trạng thái | Cao | không nhân bản logic; nếu bật applet mới thì **khuyến nghị** (không tự động) gỡ bản trùng |
| 3 | Bluetooth không có backend bundled | Trung bình | hiện "không khả dụng" trung thực thay vì nút giả |
| 4 | Popup bị cắt trên màn nhỏ / scaling phân số | Trung bình | **chưa kiểm được offline** — phải kiểm trên máy thật |
| 5 | Xung đột quyền sở hữu với Agent 2 | Trung bình | thống nhất trước khi viết; T17 không sửa `src/cinnamon/**` |
| 6 | Hiệu ứng kính: popup của applet **không** có blur thật | Trung bình | xem mục 6 — không mô phỏng blur rồi tuyên bố có |

### 5.4 Khuyến nghị

**Làm mục 3 trước (gần như đã xong), hoãn mục 5 tới khi có máy thật.** Lý do: giá
trị tăng thêm của applet gom nhóm so với các popup đã được style là **bố cục**, mà
bố cục thì **không kiểm chứng được offline** (mục 5.3 rủi ro 4). Viết một applet
mà không thể kiểm tra nó có bị cắt/tràn trên màn nhỏ hay không là viết trong mù —
và vi phạm nguyên tắc *"không tuyên bố các nút điều khiển hoạt động chỉ vì mã nguồn
đã được viết"*.

Nếu vẫn muốn triển khai trước khi có máy thật, điều kiện tối thiểu là: (a) Agent 2
đồng ý quyền sở hữu; (b) chỉ dùng API đã xác minh ở mục 4; (c) chấp nhận rằng mục
"không bị cắt/tràn" sẽ ở trạng thái **chưa kiểm chứng** trong tài liệu bàn giao.

---

## 6. Hiệu ứng kính: giới hạn thật, không mô phỏng

Yêu cầu Scope D nói rõ: *"Không mô phỏng blur bằng cách đặt một màu nền bán trong
suốt rồi tuyên bố đã có hiệu ứng kính mờ."*

Trạng thái đã xác minh (từ T04):

- St **có** thuộc tính `-blur` thật (`st-theme-node.c`, khoảng dòng 2132).
- Nhưng mỗi lần paint nó trả giá `blur_size` × (`g_malloc(w*h*4)` +
  `cogl_framebuffer_read_pixels()` + `cogl_texture_new_from_data()`), và cần
  `CLUTTER_FEATURE_SHADERS_GLSL`.
- Nên dự án **không ship** thứ phụ thuộc `-blur`.

**Hệ quả cho Control Center:** popup sẽ có **nền bán trong suốt + gradient + viền**,
**không có blur thật**. Tài liệu người dùng phải mô tả đúng như vậy — "nền kính bán
trong suốt", **không** phải "kính mờ/blur". Đây cũng là lý do 4 wallpaper của T16
dùng gradient thuần và `tools/lint/wallpapers.py` có bài `no-blur-claim`.

---

## 7. Liên hệ với các phát hiện khác của T17

- **`night-light-trough-gradient`** (mục `LOCK` trong fixture): slider nhiệt độ màu
  của trang Night Light bị app khoá ở priority 600 nên **luôn** là dải trắng-cam.
  Nếu Control Center có module night light, module đó sẽ dùng
  `nightlight@cinnamon.org` (toggle) chứ **không** dựng lại slider nhiệt độ — nên
  lock này **không** ảnh hưởng tới Control Center, chỉ ảnh hưởng trang Settings.
  Chi tiết ở `docs/design-system/settings-architecture.md` mục 4.
- **`nemo-style-application-css`**: cùng một cơ chế khoá priority 600, đã phân tích
  ở `docs/testing/nemo-checklist.md`. Hai trường hợp này xác nhận một quy luật:
  **app nào tự nạp CSS ở PRIORITY_APPLICATION thì theme thua ở đó**, và GTK 3.24
  không có `!important` để cứu. Khi khảo sát bất kỳ app nào khác, việc đầu tiên cần
  grep là `add_provider` + `STYLE_PROVIDER_PRIORITY`.

---

## 8. Trạng thái kiểm chứng

### ĐÃ xác minh bằng đọc mã nguồn
- Cinnamon 6.6.9 **không có** thành phần quick-settings/control-center nào;
  "Control Center" là `menuComment` của chính `cinnamon-settings` (`:42`)
- API thật của `sound@cinnamon.org` (slider, `_output.volume`, `push_volume`)
- API thật của `power@cinnamon.org` (**có `BrightnessSlider` và DBus brightness**)
- `nightlight@cinnamon.org` là `Applet.IconApplet` toggle
- **không có** applet Bluetooth bundled; Bluetooth = `blueberry` (gói riêng)
- danh sách class St mà T04 đã style cho popup applet
- St không có `transform` / pseudo-element / `box-sizing`; `-blur` có thật nhưng
  không ship

### CHƯA kiểm chứng — cần Cinnamon 6.6 thật
| Chưa kiểm chứng | Điều kiện để kiểm |
|---|---|
| Popup đã style của sound/power/network **trông** thế nào trên máy thật | Cài theme, mở từng popup |
| Popup có bị **cắt/tràn** trên màn nhỏ hay scaling phân số không | Thử ở 1366×768 và ở scaling 1.25/1.5 |
| Trạng thái "không khả dụng" của độ sáng có hiện đúng khi không có backlight không | Thử trên máy ảo (không có backlight) và máy thật |
| `blueberry` có mặt mặc định trên Mint 22.3 không | Kiểm tra gói đã cài — **quyết định** nút Bluetooth có làm được không |
| API cho "chế độ tiết kiệm năng lượng" là gì | **chưa đọc mã** — phải khảo sát `power@cinnamon.org` và cinnamon-settings-daemon trước khi hứa |
| Applet gom nhóm (mục 5) có chạy được không | **chưa viết mã**, nên chưa có gì để kiểm |

**Không tuyên bố** bất kỳ nút điều khiển nào "hoạt động" — vì chưa có môi trường
runtime, và vì applet gom nhóm **chưa được viết**.
