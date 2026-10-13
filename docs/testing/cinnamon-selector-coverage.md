# Cinnamon 6.6 — kiểm tra độ phủ selector và tính hợp lệ của property

> Task: T04 · Owner: Agent C (Cinnamon Shell UI)
> Trạng thái: **đã chạy thật trong sandbox này**, không có bước nào giả lập.
> Ngày: 2026-10-13

Tài liệu này trả lời một câu hỏi duy nhất: **làm sao biết theme Cinnamon của ta
không thiếu gì và không chứa khai báo chết, khi không có máy Linux Mint để chạy
thử?**

Câu trả lời: suy ra từ **mã nguồn C** của St và từ **chính theme gốc**, rồi đóng
băng thành fixture + lint chạy offline trong CI.

---

## 1. Vì sao độ phủ selector là ràng buộc cứng (E6)

St nạp CSS của Mint làm `fallback_stylesheet`. Theo doc của
`PROP_FALLBACK_STYLESHEET` trong `src/st/st-theme.c`, stylesheet đó:

- **không cascade** với stylesheet của theme người dùng, và
- chỉ được áp dụng khi stylesheet người dùng **không trả về property nào**, và
- phải đặt cờ `important`.

Hệ quả: theme bên thứ ba **không được kế thừa** bất cứ thứ gì từ theme Mint.
Thiếu một selector nghĩa là widget đó **mất style hoàn toàn**, chứ không phải
"rơi về giao diện gốc". Đây là lý do T04 fork toàn bộ
`data/theme/cinnamon-sass` @6.6.9 vào `src/cinnamon/vendor/` thay vì chỉ viết
phần khác biệt (ADR-001 phương án A).

## 2. Hai fixture đóng băng

| File | Nội dung | Số mục |
|---|---|---|
| `tests/fixtures/cinnamon-6.6-selectors.txt` | mọi selector theme gốc Cinnamon 6.6 sinh ra | 527 |
| `tests/fixtures/st-allowed-properties.txt` | mọi property St thật sự parse | 161 |

Cả hai là **fixture đóng băng**, không sinh tự động trong CI, vì chúng phải suy
ra từ mã nguồn C của Cinnamon chứ không phải từ CSS của ta. Header mỗi file ghi
đủ commit nguồn và quy trình tái lập.

Nguồn: Cinnamon tag `6.6.9`, commit
`806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18`, lấy qua
`codeload.github.com/linuxmint/Cinnamon/tar.gz/<sha>` — cùng ref với
`src/cinnamon/vendor/cinnamon-6.6-sass/` (xem `VENDOR.md` ở đó).

### 2.1. Marker comment của fixture là `//`, không phải `#`

Selector CSS dùng `#` cho ID: `#notification`, `#Tooltip`, `#LookingGlassDialog`,
`#altTabPopup`, `#panel:highlight`, `.expo-workspace-thumbnail-frame#active`.
Nếu fixture dùng `#` làm comment thì 25 selector ID bị ăn mất.

Đây là **lỗi đã xảy ra thật** và đã sửa: bản đầu tiên của
`st_properties.load_fixture()` cắt inline comment bằng `line.split("#", 1)`, và
fixture được sinh bằng regex `^([^@\s/][^{}]*)\{` với `re.M` — mà `[^{}]` **không
loại trừ dấu xuống dòng**, nên nó nuốt cả `}` của rule trước. Kết quả: 439 mục
bẩn dạng `'} #Tooltip'`, và bài kiểm tra coverage báo sai **cả hai chiều**
(439 "thiếu" giả + 484 "mới" giả, trong khi số thật là 0 và 73).

Bài học được khoá bằng test: `TestCoverageOfStockSelectors::test_fixture_is_not_polluted`
và `::test_fixture_marker_is_not_hash`.

## 3. Chín kiểm tra của `tools/lint/st_properties.py`

| # | Kiểm tra | Căn cứ mã nguồn | Kết quả chạy thật |
|---|---|---|---|
| 1 | `properties` — không có property lạ | fixture §2 + `src/st/st-theme-node.c` | ✓ 94 property, tất cả hợp lệ |
| 2 | `forbid-blur` — không có `-blur`, `background-bumpmap` | `st-theme-node.c:2132`, `:2064` + `st-background-effect.c` | ✓ 0 khai báo |
| 3 | `duration-unit` — `transition-duration` phải là **số trần** | `st-theme-node.c:2317` → `:2332` → `:841` | ✓ 29 hợp lệ, 0 vi phạm mới |
| 4 | `font-weight` — số trần hoặc keyword | `font_weight_from_term()` `:2680-2692` | ✓ 0 sai |
| 5 | `single-shadow` — mỗi rule chỉ MỘT `box-shadow` | `st_theme_node_lookup_shadow()` `:3348-3400` trả về một `StShadow*` | ✓ 55 khai báo, 0 vi phạm |
| 6 | `coverage` — đủ 527 selector gốc | ràng buộc E6 ở §1 | ✓ 527/527 |
| 7 | `assets` — mọi `url()` hiệu lực resolve được | `_st_theme_resolve_url()` `st-theme.c:1087-1123` | · 15 PENDING T05 |
| 8 | `hardcoded` — tầng override không hard-code màu | quy ước design token | ✓ 0 literal, 0 primitive rò rỉ |
| 9 | `dead-vendor` — không thêm property đã chết | xem §5 | ✓ `opacity` 2/2, `border-style` 1/1 |

Chạy:

```bash
python3 tools/lint/st_properties.py                     # tất cả
python3 tools/lint/st_properties.py --check coverage    # một kiểm tra
python3 tools/lint/st_properties.py --json              # cho CI
```

Exit code: `0` = đạt, `1` = có lỗi, `2` = **không chạy được** (thiếu trình biên
dịch SCSS và không có `--css`). Mã `2` tách riêng để CI không bao giờ nhầm
"không chạy được" với "pass".

## 4. Bốn ràng buộc cú pháp của St ngược với CSS chuẩn

Đây là phần quan trọng nhất của tài liệu. Cả bốn đều **không thể phát hiện bằng
mắt hay bằng trình duyệt** — St bỏ qua khai báo sai trong im lặng.

### 4.1. `transition-duration` phải là SỐ TRẦN

```c
/* src/st/st-theme-node.c:2317 */
int st_theme_node_get_transition_duration (StThemeNode *node)
  ...
  st_theme_node_lookup_double (node, "transition-duration", FALSE, &value);   /* :2332 */

/* :823 */
gboolean st_theme_node_lookup_double (...)
  ...
  if (term->type != TERM_NUMBER || term->content.num->type != NUM_GENERIC)    /* :841 */
      continue;
```

Docstring `:2315` ghi rõ giá trị trả về là *"transition duration in
milliseconds"*. Vậy:

- `transition-duration: 150;` → **hoạt động** (150 ms)
- `transition-duration: 150ms;` → **bị bỏ qua trong im lặng** (`NUM_TIME_MS`)

Theme gốc Cinnamon 6.6 **tự mâu thuẫn**: `widgets/_expo.scss:15,19` viết `150`
(đúng), còn `_common.scss:114` viết `100ms` (sai) — nghĩa là transition của
`.popup-menu-item` trong theme gốc **thực tế không chạy**. Tầng override đặt lại
giá trị đúng cho cả ba selector trong nhóm, kể cả `.popup-sub-menu .popup-menu-item`
có specificity (0,2,0) cao hơn `.popup-menu-item` (0,1,0).

GTK3/GTK4 thì **ngược lại**: bắt buộc phải có `ms`.

### 4.2. `font-weight` phải là SỐ TRẦN hoặc keyword

`font_weight_from_term()` (`:2680`) cũng yêu cầu `NUM_GENERIC`, nên
`font-weight: 700px` bị bỏ qua.

> **Ảnh hưởng trực tiếp tới token do Agent 1 sinh.** `design/tokens/10-primitives.json`
> khai báo `font.weight-bold: 700` (không đơn vị, đúng), nhưng
> `tools/tokens/generate.py:215` —
> `unit = "" if leaf in UNITLESS_KEYS else PX_KEY_OVERRIDE.get(leaf, "px")` —
> với `UNITLESS_KEYS = {"blur"}` và `NS_UNIT` không có nhánh `"font"`, đã emit
> `$mg-font-weight-bold: 700px;`. **Biến đó vô tác dụng trên St.**
> Đã báo Agent Design Systems; T04 dùng hằng tạm `$mg-w-bold: 700` trong
> `overrides/_00-globals.scss` và khoá bằng
> `test_no_broken_tokens_referenced`.

### 4.3. Mỗi rule chỉ MỘT `box-shadow`

`st_theme_node_lookup_shadow()` trả về đúng **một** `StShadow *`, không phải danh
sách. `box-shadow: inset 0 1px 0 A, 0 10px 28px B;` là **không hợp lệ**.

Hệ quả thiết kế: viền kính (hairline) phải dùng `border`, không dùng inset
box-shadow, khi rule đó đã có drop shadow. Chỉ bề mặt **không** có drop shadow
(panel) mới được dùng inset box-shadow làm hairline. Đã đóng gói thành mixin
`mg-glass()` / `mg-edge()` trong `overrides/_00-globals.scss`.

### 4.4. `border-style` viết rời là NO-OP

`do_border_property()` (`:1244-1300`) chỉ tiêu thụ ident `solid` **bên trong**
shorthand `border:`; `StThemeNode` không có trường `border_style` nào
(`grep 'border_style' src/st/st-theme-node.{c,h}` = 0 kết quả). Vendor vẫn viết
`border-style: solid` rời cho `.vkeyboard-key` → chết. T04 dùng shorthand.

## 5. Property chết trong theme gốc — bằng chứng và cách xử lý

| Property | Vendor dùng ở đâu | Bằng chứng nó chết | Cách T04 xử lý |
|---|---|---|---|
| `opacity` | `.appmenu-category-button-greyed StIcon`, `.menu-category-button-greyed StIcon` (`opacity: 0.5`) | chuỗi `"opacity"` **không tồn tại** trong `src/st/st-theme-node.c`; grep toàn bộ `src/st/` chỉ trúng `st-texture-cache.c:84,859` — đó là tên GObject property của texture cache, không phải CSS | thay bằng alpha thật trên `color: $mg-text-disabled` |
| `border-style` | `.vkeyboard-key` | xem §4.4 | dùng shorthand `border: 1px solid …` |
| `tranparentize()` | `widgets/_dialogs.scss:68` → `.end-session-dialog .dialog-list .dialog-list-title` | **sai chính tả** hàm `transparentize`. Cả libsass lẫn dart-sass đẩy nguyên chuỗi lạ ra CSS (kiểm chứng: `vendor.css:1005` và `vendor-dart.css:866` đều chứa `tranparentize(...)`), St không parse được → tiêu đề cảnh báo "End session" của theme gốc **không có nền** | viết lại bằng `rgba($mg-status-warning, $mg-opacity-hover)` |
| `icon-size: 1.2 em` | `widgets/_applets.scss:130` → `.sound-player StButton:small StIcon` | có **dấu cách** giữa số và đơn vị → CSS coi là 2 token; St nhận `NUM_GENERIC` và theo `:977-984` in `g_warning("length values must specify a unit")` rồi trả `VALUE_NOT_FOUND` | sửa thành `1.2em` |

Hai mục đầu không xoá được (vendor phải nguyên văn) nên lint kiểm tra theo
**baseline**: `opacity` đúng 2 lần, `border-style` đúng 1 lần — tầng override
không được làm tăng số đó.

## 6. Selector chết — đã loại, kèm bằng chứng

Viết selector không tồn tại cũng là CSS chết và cũng im lặng. Đã grep toàn bộ
`js/`, `files/usr/share/cinnamon/{applets,desklets}` và `src/st/` của commit
`806c1a4e`:

| Selector | Kết quả | Kết luận |
|---|---|---|
| `.osd-window` | 0 | OSD thật là `.info-osd`, `.media-keys-osd`, `.workspace-switch-osd`, `.resize-popup` |
| `.modal-dialog` | 0 | dialog thật là `.dialog` (`js/ui/dialog.js:68,148`) + `.end-session-dialog`, `.prompt-dialog`, `.run-dialog`, `.polkit-dialog-*`, `.audio-device-selection-dialog` |
| `.keyboard-key` | 0 | Cinnamon 6.6 dùng `.vkeyboard-key` + `#virtual-keyboard` |
| `.appmenu-item` | 0 | đã gỡ khỏi danh sách focus |
| `.device-box`, `.device-labels`, `.primary-label`, `.device-icon` | 0 | họ selector chết của theme gốc; họ thật là `.audio-selection-*` (`js/ui/audioDeviceSelection.js:111,122`). Giữ lại **chỉ để đủ coverage**, đã ghi chú tại chỗ |
| `StLabel:selected`, `StBoxLayout:selected` | `:selected` có thật (`st-widget.c:2901`, theo `ATK_STATE_SELECTED`) nhưng không bao giờ khớp trên StLabel/StBoxLayout trần | đã gỡ; selection thật đi qua `selection-background-color`/`selected-color` của StEntry (`st-entry.c:283,289`) |

Ngược lại, những selector **trông lạ nhưng có thật** và đã được giữ:
`.search-entry` / `.search-entry-icon` (`menu@cinnamon.org/applet.js`),
`.toggle-switch-us` / `.toggle-switch-intl` (`js/ui/popupMenu.js`),
`.menu-context-menu`, `.popup-inactive-menu-item` (`js/ui/popupMenu.js`),
`StScrollBar StButton#vhandle` / `#hhandle` (`src/st/st-scroll-bar.c` đặt *name*,
không phải style class).

Pseudo-class do chính St thêm, đã xác minh trong `src/st/`:
`hover` (`st-widget.c:1840`), `focus` (`:701`), `insensitive` (`:1502`),
`active` (`st-button.c:132`), `checked` (`st-button.c:661`),
`selected` (`st-widget.c:2901`, theo `ATK_STATE_SELECTED`).

Toàn bộ 73 selector T04 thêm ngoài theme gốc đều có bằng chứng từng mục trong
`tests/lint/test_cinnamon_coverage.py::NEW_SELECTORS`, và test
`test_new_selectors_are_exactly_the_frozen_allowlist` fail theo **cả hai chiều**:
thêm selector mới chưa biện minh → fail; để lại mục không còn dùng → fail.

## 7. `url()` và đường dẫn asset

```c
/* src/st/st-theme.c:1087 */
_st_theme_resolve_url (StTheme *theme, CRStyleSheet *base_stylesheet, const char *url)
  ...
  dirname  = g_path_get_dirname (base_filename);
  stylesheet = g_file_new_for_path (dirname);
  resource = g_file_resolve_relative_path (stylesheet, url);
```

`url()` được phân giải **tương đối với thư mục của file CSS khai báo nó**. CSS
biên dịch ra `cinnamon/cinnamon.css`, nên `url("assets/x.svg")` →
`cinnamon/assets/x.svg`.

Theme gốc dùng **tên trần** (`url("toggle-off.svg")`, `url("corner-ripple.png")`).
T04 ghi đè toàn bộ về `assets/`. Sau cascade (last-wins theo
`(simple_selector, property)`), tập url() hiệu lực còn đúng **15** mục:

```
assets/add-workspace.svg          assets/checkbox-off.svg   assets/radio-off.svg
assets/add-workspace-hover.svg    assets/checkbox.svg       assets/radio.svg
assets/calendar-arrow-left.svg    assets/close.svg          assets/toggle-off.svg
assets/calendar-arrow-left-hover.svg  assets/corner-ripple.svg  assets/toggle-on.svg
assets/calendar-arrow-right.svg       assets/trash-icon.svg
assets/calendar-arrow-right-hover.svg
```

`corner-ripple.png` được thay bằng SVG để không cần bộ encode PNG và để đổi màu
được theo scheme.

### Phụ thuộc T05

`src/cinnamon/assets/` thuộc **T05 (Agent D — Visual/Assets)**, không thuộc T04
(`docs/plan/04-work-breakdown.md`: T05 được phép tạo `src/cinnamon/assets/**/*.svg`,
và **cấm** chạm `src/cinnamon/**/*.scss`). Vì vậy:

- lint báo 15 mục này là **PENDING**, không phải ERROR, khi thư mục
  `src/cinnamon/assets/` **chưa tồn tại** (= T05 chưa bắt đầu);
- nếu thư mục đã tồn tại mà thiếu file → **ERROR** thật (T05 giao thiếu);
- test `TestAssets::test_assets_are_pending_t05_not_silently_absent` **SkipTest**
  với lý do rõ ràng, không biến thành pass.

T04 đã chốt xong phần của mình: tập 15 url() đúng và không còn url tên trần nào
sống sót sau cascade.

## 8. Hai trình biên dịch: kết quả đo được

Cả hai đều build sạch `src/cinnamon/cinnamon.scss`:

| Compiler | Phiên bản | Kết quả | Kích thước |
|---|---|---|---|
| libsass (pysassc — toolchain Mint dùng, E18) | libsass 3.6.6 / `libsass 0.23.0` | OK | 93 030 B |
| dart-sass | 1.77.8 (dart2js 3.4.4) | OK, exit 0 | ~92,9 kB |

**Hai compiler cho ra byte KHÁC nhau.** Khác biệt đo được (không phải suy đoán):

| Vị trí | libsass | dart-sass |
|---|---|---|
| `.device-box .device-icon` | `icon-size: 1.637em` | `icon-size: 1.636em` |
| `.popup-device-menu-item` | `spacing: .5em` | `spacing: 0.5em` |
| `.workspace-switch-osd-indicator` | `padding: 2.66667px` | `padding: 2.6666666667px` |
| màu | `#a0a0a0` | `rgb(160, 160, 160)` |

Khác biệt **làm tròn** (`1.637em` vs `1.636em`) là thật, không chỉ là format.
Vì Mint build bằng libsass, **libsass là bản có thẩm quyền**; dart-sass dùng để
bắt cú pháp sắp bị loại bỏ. Test
`TestDualCompilerAgreement::test_both_compilers_produce_same_selector_set` chỉ so
**tập selector** (không so byte) — đúng mức ADR-004 yêu cầu.

dart-sass 1.77.8 phát `DEPRECATION WARNING: Using / for division` cho
`to-em()` (`vendor/_drawing.scss:4`) và `fontsize()` (`:12`); Dart Sass 2.0 sẽ bỏ
hẳn. Đây là bằng chứng cho ADR-004: **phải khoá phiên bản dart-sass**, không nâng
cấp mù quáng. Vendor được giữ nguyên văn nên cảnh báo này không sửa được từ phía
ta; layer override của T04 **không** phát ra cảnh báo nào.

## 9. Phân loại kiểm tra

| Loại | Nội dung | Trạng thái |
|---|---|---|
| **(a) Suy ra được từ mã nguồn** | 4 ràng buộc cú pháp §4, property chết §5, selector chết §6, cách phân giải `url()` §7, `-blur` tốn kém bao nhiêu | **Đã làm**, có trích dẫn dòng |
| **(b) Tự động hoá được trong CI** | 9 kiểm tra §3, coverage 527 selector, dual-compiler, vendor SHA-256, hardcoded-color | **Đã làm và đã chạy**: `make check` → 70 test, OK, 1 skip |
| **(c) Bắt buộc phải có Mint 22.3 / Cinnamon 6.6 thật** | theme có nạp không; glass α0.86 đọc được trên wallpaper sáng không; dock underline có đúng không; chi phí `-blur` nếu bật; font nào khả dụng; chiều cao panel 30px có đủ không | **CHƯA làm được** — sandbox không có Cinnamon/muffin/gsettings |

### Điều kiện mở khoá cho (c)

Cần một trong hai:

1. Người dùng chạy T00 (`docs/plan/09-verification-checklist.md`) trên máy Mint
   22.3 thật, dán output vào `docs/verification/REPORT.md`; **hoặc**
2. CI có job chạy trong container có Cinnamon 6.6 (chưa tồn tại; cần
   `linuxmint/cinnamon` build được hoặc image Mint 22.3).

Cho tới khi đó, **mọi khẳng định về giao diện thực tế đều chưa được xác minh**
và tài liệu này không đưa ra khẳng định nào như vậy.

## 10. Lệnh đã chạy thật trong sandbox này

```
python3 tools/lint/st_properties.py            -> OK — 0 lỗi (15 mục đang chờ T05 assets)
make check                                     -> OK — make check xanh
python3 -m unittest discover -s tests -t . -v  -> Ran 70 tests ... OK (skipped=1)
```

Toolchain dev nằm **ngoài** cây repo, ở `$MINTOS_TOOLCHAIN` (mặc định
`~/.mintos-toolchain`), gồm venv có `libsass 0.23.0` và `node_modules` có
`sass@1.77.8`. `package.json` + `package-lock.json` trong repo chỉ để **khoá phiên
bản**, không chứa code.

Lý do phải đặt bên ngoài: `tools/lint/safety_paths.py:43` có
`SKIP_DIRS = {.git, __pycache__, node_modules, docs, tests, design, .github}` —
**không có** `.venv`/`venv`, nên một venv nằm trong repo bị lint đó quét và báo
31 vi phạm giả từ chính mã nguồn của pip. Đã báo Agent Platform/DevEx; khuyến nghị
thêm `.venv`, `venv` vào `SKIP_DIRS`.

## 11. Việc còn lại trước khi tích hợp ISO

1. **T05** — 15 SVG trong `src/cinnamon/assets/` (Agent D). Đã chốt spec ở §7.
2. **Agent Design Systems** — sửa `tools/tokens/generate.py`:
   - `font.weight-*` phải emit **không đơn vị** (§4.2);
   - `font.size-*-pt` phải emit `pt`, không phải `px` (St hỗ trợ `pt`:
     `st-theme-node.c:1019` `case POINTS: num->val * multiplier * (resolution/72.)`);
   - `blur.*` primitive đang bị gắn `px` (`$mg-blur-sm: 2px`) trong khi blur phải
     là số trần;
   - `40-motion.json` **không bao giờ được emit**: `generate.py:605-616` chỉ flatten
     `10-primitives.json`, `30-component.json`, `20-semantic-<scheme>.json`. File
     motion có trong `TOKEN_FILES` (dòng 50, tức **có** tham gia tính lock) nhưng
     không vào pipeline phân giải → `duration.*` và `cinnamon_transition.*` biến mất
     khỏi mọi stylesheet, trong khi `make tokens-check` vẫn báo OK. `duration` cũng
     cần đơn vị **khác nhau theo target**: `ms` cho GTK, số trần cho Cinnamon.
3. **Agent Platform/DevEx** — thêm `.venv`, `venv` vào `SKIP_DIRS` của
   `tools/lint/safety_paths.py`; và cân nhắc đưa `python3 tools/lint/st_properties.py`
   vào job `scss` của `.github/workflows/ci.yml` (job đó đã tự kích hoạt vì
   `src/cinnamon/cinnamon.scss` nay đã tồn tại).
4. **NOTICE.md** — registry vendor vẫn rỗng; cần điền mục Cinnamon 6.6 sass
   (GPL-2.0-or-later, `src/st` LGPL-2.1-or-later). Thuộc T01 nên T04 không tự sửa;
   nội dung đã có sẵn trong `src/cinnamon/vendor/cinnamon-6.6-sass/VENDOR.md`.
5. **Chiều cao panel** — token `$mg-cinnamon-panel-height: 30px` **không** áp bằng
   CSS. Cinnamon lấy chiều cao từ gsetting `org.cinnamon panel-height`. Phải đặt ở
   tầng cấu hình người dùng / first-login (thuộc T12), không phải trong stylesheet.
