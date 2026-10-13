# 01 — Kết quả khảo sát

## 1. Hiện trạng repository

Khảo sát bằng `git` + `find` tại `/home/user/mintos-glass`:

```
Commit:  d01036383d08856eca23978ad5c2cb8c04a96823  "Initial commit"
Branch:  arena/0b177d6e-mintos-glass (từ main)
Remote:  https://github.com/ThuyLinh6/mintos-glass.git
Files:   1  →  README.md  (15 bytes, nội dung: "# mintos-glass")
.gitignore: KHÔNG có
Tổng dung lượng .git: 120K
```

**Kết luận: đây là dự án greenfield 100%.** Không có theme, không có CSS, không có SCSS,
không có asset, không có công cụ build, không có CI, không có LICENSE.

### Thành phần đã có / còn thiếu

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| README | ✅ có (rỗng về nội dung) | cần viết lại |
| LICENSE | ❌ thiếu | **bắt buộc** — dự án dẫn xuất từ mã GPL (xem R7) |
| .gitignore | ❌ thiếu | |
| Cinnamon theme (`cinnamon/`) | ❌ thiếu | module lớn nhất |
| GTK 3 theme (`gtk-3.0/`) | ❌ thiếu | bắt buộc để theme hiện trong Cinnamon Settings |
| GTK 4 theme (`gtk-4.0/`) | ❌ thiếu | |
| libadwaita stylesheet | ❌ thiếu | Mint **có** patch libadwaita → làm được (xem E21–E23) |
| Nemo styling | ❌ thiếu | nằm trong GTK3, không phải theme riêng |
| WM / titlebar (`metacity-1/`) | ❌ **không cần** | muffin 6.6 bỏ parser XML (E31, E32) |
| Dock | ❌ thiếu | cần quyết định D-1 |
| Assets (SVG/PNG) | ❌ thiếu | |
| Design tokens | ❌ thiếu | phải làm TRƯỚC tất cả module |
| Installer / rollback | ❌ thiếu | |
| CI / lint | ❌ thiếu | |
| Test protocol | ❌ thiếu | |
| Documentation | ❌ thiếu | bộ tài liệu này là bước đầu |

## 2. Công cụ có sẵn trong môi trường làm việc này (sandbox của agent)

Đã kiểm bằng `command -v`:

| Có | Không có |
|---|---|
| `git`, `gh`, `node`, `npm`, `python3`, `pip3`, `make`, `gcc` | `sass`/`sassc`, `meson`, `ninja`, `gsettings`, `cinnamon`, `cinnamon-settings`, `nemo`, `xvfb-run`, `glib-compile-resources` |

**Hệ quả quan trọng:** trong môi trường này **không thể chạy Cinnamon, không thể render theme,
không thể chụp màn hình, không thể đo hiệu năng.** Mọi tuyên bố về giao diện thực tế đều phải
do người dùng chạy trên máy Linux Mint và gửi lại bằng chứng. `npm`/`pip3` có thể dùng để lấy
trình biên dịch SCSS (registry.npmjs.org và pypi.org đều truy cập được) — nhưng đó là việc của Phase 1.

## 3. Bảng bằng chứng upstream

Mọi khẳng định kỹ thuật trong bộ kế hoạch này đều trỏ về một mục trong bảng dưới.
Nguồn: GitHub API (`api.github.com`) trên các repo `linuxmint/*` và `ricotz/plank`.

### 3.1 Nền tảng mục tiêu

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| E3 | Mint 22.3 "Zena" phát hành ~01/2026, base **Ubuntu 24.04.3 LTS (Noble)**, kernel 6.14, **Cinnamon 6.6.4** | 9to5linux.com, theregister.com, linuxiac.com |
| E2 | Tag Cinnamon `6.6.0` … `6.6.9` tồn tại; nhánh `6.6-maintenance` | `linuxmint/Cinnamon` tags |
| E2b | Cinnamon 6.6 có: app menu thiết kế lại, `favorites@`, `nightlight@`, OSK viết lại, per-app notification indicator, Night Light, cải thiện Wayland | tree `files/usr/share/cinnamon/applets/` @6.6.9 + tin phát hành |

### 3.2 Engine theme Cinnamon (St) — tag `6.6.9`

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| E4 | Theme mặc định build từ SCSS: `data/theme/cinnamon-sass/` → `cinnamon.css`, compiler `find_program('pysassc','sassc')` (**libsass**), cài vào `pkgdatadir/theme` = `/usr/share/cinnamon/theme/` | `data/theme/cinnamon-sass/meson.build` |
| E4b | Cấu trúc SCSS upstream: `cinnamon.scss` + `_colors.scss` + `_drawing.scss` + `_common.scss` + `_widgets.scss` + `widgets/` (17 partial: alttab, applets, base, calendar, deprecated, desklet, dialogs, expo, ibus-popup, keyboard, menus, notifications, osd, panel, startmenu, switch-check, windowlist). Tổng 2385 dòng | `data/theme/cinnamon-sass/**` |
| E5 | `loadTheme()`: stylesheet của user được `theme.load_stylesheet()`; theme mặc định chỉ là `new St.Theme({ fallback_stylesheet: _defaultCssStylesheet })` | `js/ui/main.js` (≈ dòng 358, 786-800) |
| E6 | **Fallback stylesheet là non-cascading**, chỉ áp dụng khi stylesheet user không trả về property nào **và** StWidget có `important` | `src/st/st-theme.c` — doc comment `PROP_FALLBACK_STYLESHEET` (≈ dòng 169-181) |
| E7 | Thứ tự tìm theme Cinnamon: `$XDG_DATA_HOME/themes/<n>/cinnamon/cinnamon.css` → `~/.themes/<n>/cinnamon/cinnamon.css` → `<system data dirs>/themes/<n>/cinnamon/cinnamon.css`. Thư mục theme cũng được thêm vào `Gtk.IconTheme` search path | `js/ui/themeManager.js` `_findTheme()` |
| E8 | **St hỗ trợ backdrop blur thật**: property `-blur` (integer length) | `src/st/st-theme-node.c:2132` |
| E9 | St hỗ trợ `-bumpmap: url(...)` (displacement map) | `src/st/st-theme-node.c:2064` |
| E10 | Blur gắn vào `StWidget` khi `theme_node->background_blur > 0`, dùng `StBackgroundBlurEffect` (kế thừa `ClutterOffscreenEffect`, GLSL box blur) | `src/st/st-widget.c:1610-1618`, `src/st/st-background-effect.c` |
| E11 | **Chi phí blur**: `for (int i = 0; i < self->blur_size; i++)` — mỗi vòng `size = w*h*4; data = g_malloc(size); cogl_framebuffer_read_pixels(...); cogl_texture_new_from_data(...)` | `src/st/st-background-effect.c:117-150` |
| E12 | Blur cần `CLUTTER_FEATURE_SHADERS_GLSL`; nếu không có thì `g_message` và return FALSE | `src/st/st-background-effect.c:109-115` |
| E13 | St **có** hỗ trợ `@import` runtime, resolve qua `_st_theme_resolve_url()` | `src/st/st-theme.c:892-936` |
| E36 | Theme 6.6.9 dùng **85 property CSS** khác nhau (liệt kê ở §4 bên dưới) | phân tích `data/theme/cinnamon-sass/**` |
| E14 | 33 applet bundled: a11y, calendar, cornerbar, expo, **favorites**, grouped-window-list, inhibit, keyboard, menu, network, **nightlight**, notifications, on-screen-keyboard, panel-launchers, power, printers, recent, removable-drives, scale, separator, settings, settings-example, show-desktop, slideshow, sound, spacer, systray, trash, user, window-list, windows-quick-list, workspace-switcher, xapp-status, xrandr | tree `files/usr/share/cinnamon/applets/` @6.6.9 |
| E15 | Cinnamon = **GPL-2.0-or-later**; thư viện `st` = **LGPL-2.1-or-later** | `README.rst` (mục License), header `src/st/st-theme-node.c` |

### 3.3 GTK / libadwaita

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| E17 | Cấu trúc Mint-Y tham chiếu (`mint-themes` @master, v2.4.2): `src/Mint-Y/{cinnamon/sass, gtk-2.0, gtk-3.0/sass+assets, gtk-4.0/sass+assets, libadapta-1.5, libadwaita-1.5, libadwaita-1.7, libadwaita-1.9, metacity-1, openbox-3, variations/<Color>}` | tree `linuxmint/mint-themes` |
| E18 | Mint build bằng **libsass**: `pysassc ./sass/gtk.scss gtk.css` | `src/Mint-Y/gtk-3.0/parse-sass.sh` |
| E19 | Cinnamon Settings **chỉ liệt kê theme GTK nếu tồn tại `gtk-3.*/gtk.css`** (`theme_dir.glob("gtk-3.*")`) | `files/usr/share/cinnamon/cinnamon-settings/modules/cs_themes.py:1010-1016` |
| E19b | Thư mục theme được quét: `~/.themes`, `$XDG_DATA_HOME/themes`, `<system data dirs>/themes` | `cs_themes.py:30-33` |
| E20 | `cs_themes.py` ghi: `org.cinnamon.desktop.interface` → `gtk-theme`, `icon-theme`, `cursor-theme`; `org.cinnamon.theme` → `name`. **Không** ghi `org.gnome.desktop.interface` | `cs_themes.py:190-192, 609-612, 978-1004` |
| E33 | Các `@define-color` public mà app khác phụ thuộc: `accent_color`, `theme_fg_color`, `theme_text_color`, `theme_bg_color`, `theme_base_color`, `theme_selected_bg_color`, `theme_selected_fg_color`, `fg_color`, `text_color`, `bg_color`, `base_color`, `selected_bg_color`, `selected_fg_color`, `insensitive_bg_color`, `insensitive_fg_color`, `insensitive_base_color`, `theme_unfocused_{fg,text,bg,base}_color`, `borders`, `unfocused_borders`, `warning_color`, `error_color`, `success_color`, `placeholder_text_color`, `content_view_bg`, `wm_*` (title, bg, highlight, border, shadow, button/icon close…) | `src/Mint-Y/gtk-3.0/sass/_colors-public.scss` |
| E34 | Mẫu `index.theme`: `[Desktop Entry] Type=X-GNOME-Metatheme` + `[X-GNOME-Metatheme] GtkTheme= / MetacityTheme= / IconTheme= / CursorTheme= / ButtonLayout=` | `files/usr/share/themes/Mint-Y/index.theme` |
| E16 | `mint-themes` (Mint-X/Mint-Y) = **GPL-3+** | `mint-themes/debian/copyright` |
| **E21** | **Mint patch libadwaita để hỗ trợ theme.** Nhánh `master` = `libadwaita-1 (1.5.0-2mint3) zara`. Code: `version_dir = g_strdup_printf("libadwaita-%d.%d", ADW_MAJOR_VERSION, ADW_MINOR_VERSION)` rồi `g_build_filename(parent_dir, version_dir, base_file)` → với libadwaita 1.5 thì thư mục là **`libadwaita-1.5/`** | `linuxmint/libadwaita@master src/adw-style-manager.c:200-202`; `debian/changelog` |
| E22 | File bắt buộc trong `libadwaita-1.5/`: `base.css`, `base-hc.css`, `defaults-light.css`, `defaults-dark.css`, `assets/`. Thứ tự tìm: `$XDG_DATA_HOME/themes` → `~/.themes` → system data dirs. Debug: biến môi trường **`ADW_DEBUG_THEMES=1`** | `libadwaita` README.md @24.04; `src/adw-style-manager.c:158-270` |
| E23 | Khuyến nghị chính thức từ upstream: *"To minimize potential issues it is recommended to only change the colors and the style of the window controls."* | `libadwaita` README.md |
| E24 | Nguồn theme name cho libadwaita: env debug → **portal** → gsettings **`org.gnome.desktop.interface gtk-theme`** → legacy. Legacy impl đặt `has_theme_name = FALSE` (không cung cấp tên theme) | `src/adw-settings.c:171-198`, `src/adw-settings-impl-gsettings.c:102-138`, `src/adw-settings-impl-legacy.c:81` |
| **E25** | **RỦI RO**: Cinnamon ghi `org.cinnamon.desktop.interface gtk-theme`, libadwaita đọc `org.gnome.desktop.interface gtk-theme` (hoặc portal). Hai khoá khác nhau → app GTK4/libadwaita có thể không thấy theme | E20 + E24 |

### 3.4 Nemo

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| E26 | Nemo ship CSS riêng trong gresource: `nemo-style-application.css` (71 dòng), `nemo-style-fallback.css` (21), `nemo-style-fallback-mandatory.css` (36) | `nemo/gresources/` @`master.mint22` |
| E27 | Selector desktop icon: `.nemo-window.nemo-desktop-window notebook/paned`, `.nemo-desktop-window(:backdrop)`, `.nemo-canvas-item`, `.nemo-desktop`, `.nemo-desktop.nemo-canvas-item{,:hover,:selected}`, `.nemo-desktop.view .entry{,:selected}`; custom property `-NemoIconContainer-activate-prelight-icon-label` | `nemo-style-application.css` |
| E28 | Selector sidebar: `.places-treeview{,:selected,:hover,:selected:hover}` + `-NemoPlacesTreeView-disk-full-{bg-color,fg-color,bar-width,bar-radius,bottom-padding,max-length}` | `nemo-style-fallback.css` |
| E29 | **Nemo fallback phụ thuộc theme export**: `@theme_bg_color`, `@theme_fg_color`, `@theme_selected_bg_color`, `@theme_selected_fg_color`, `@theme_unfocused_bg_color`. Selector: `.nemo-window .nemo-inactive-pane .view:not(:selected)`, `.nemo-window .nemo-window-pane widget.entry`, `.floating-bar` | `nemo-style-fallback-mandatory.css` |
| E30 | Style class đăng ký trong code: `nemo-window` (`src/nemo-window.c:1999`), `nemo-places-sidebar` (`src/nemo-places-sidebar.c:4161`), `nemo-desktop`, `nemo-desktop-icon-view`; sidebar box nhận `GTK_STYLE_CLASS_SIDEBAR` (`src/nemo-window.c:428`) | `nemo@master.mint22` |
| E2b2 | Nemo `master.mint22` khai báo `version: '6.7.8'` trong `meson.build` → bản cài trên Mint 22.3 có thể là 6.6.x, **cần xác minh** | `nemo/meson.build` |

### 3.5 Muffin (window manager) / khung cửa sổ

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| **E31** | muffin 6.6.3: `src/meta/theme.h` chỉ còn `typedef struct _MetaTheme MetaTheme;` + 3 hàm new/free/get_default → **không có parser metacity XML**. `src/ui/` chỉ có `frames.c, theme.c, ui.c`. `debian/control` **không** có `libmetacity` | `linuxmint/muffin` @ tag `6.6.3` |
| **E32** | Khung cửa sổ vẽ bằng GTK3 CSS: `meta_theme_create_style_info()` gọi `gtk_css_provider_get_named(theme_name, variant)` với `theme_name` lấy từ `GtkSettings:gtk-theme-name`, rồi dựng widget path: `window` + `.background` + `.ssd` → `decoration` → `headerbar` + `.titlebar` + `.horizontal` + `.default-decoration` → `label` + `.title` | `muffin/src/ui/theme.c:1073+` @6.6.3 |
| E32b | `MetaStyleInfo` = mảng `GtkStyleContext *styles[META_STYLE_ELEMENT_LAST]`; layout lấy `get_min_size()` / `get_padding_and_border()` từ CSS → **kích thước titlebar do CSS quyết định** | `muffin/src/ui/theme-private.h:180-186`, `theme.c:318-320` |

### 3.6 Dock

| ID | Phát hiện | Bằng chứng |
|---|---|---|
| E35 | Plank theme = 1 file `<theme>/dock.theme`, 2 section: `[PlankTheme]` (TopRoundness, BottomRoundness, LineWidth, OuterStrokeColor, FillStartColor, FillEndColor, InnerStrokeColor) và `[PlankDockTheme]` (HorizPadding, TopPadding, BottomPadding, ItemPadding, IndicatorSize, IconShadowSize, UrgentBounceHeight, LaunchBounceHeight, FadeOpacity, ClickTime, UrgentBounceTime, LaunchBounceTime, ActiveTime, SlideTime, FadeTime, HideTime, GlowSize, GlowTime, GlowPulseTime, UrgentHueShift, ItemMoveTime, CascadeHide, BadgeColor). Màu dạng `R;;G;;B;;A` (0-255) | `ricotz/plank data/themes/Default/dock.theme` |
| E35b | Plank có sẵn trong kho Ubuntu (universe) nhưng **chưa xác minh đã cài trên máy người dùng** → bắt buộc detect, không tự cài | — |

## 4. Danh sách 85 property CSS mà theme Cinnamon 6.6.9 đang dùng

Trích tự động từ `data/theme/cinnamon-sass/**` — đây là "tập an toàn" đã được chứng minh hoạt động:

```
-active-window-background        -arrow-border-width                background-gradient-start     border-radius-topleft        min-width
-active-window-border            -arrow-border-radius               background-image                border-radius-topright       padding
-arrow-background-color          -arrow-box-shadow                  background-size                 border-right-width           padding-bottom
-arrow-base                      -arrow-rise                        border                          border-style                 padding-left
-arrow-border-color              -barlevel-active-background-color  border-bottom-width             border-top-width             padding-right
                                 -barlevel-amplify-color            border-color                    border-width                 padding-top
                                 -barlevel-amplify-separator-width  box-shadow                      box-shadow                   selected-color
                                 -barlevel-background-color         caret-color                     caret-size                   selection-background-color
                                 -barlevel-height                   color                           font-size                    spacing
                                 -boxpointer-gap                    font-style                      font-weight                  spacing-columns
                                 -cinnamon-caption-spacing          height                          icon-size                    spacing-rows
                                 -cinnamon-close-overlap            margin                          margin-bottom                text-align
                                 -gradient-end                      margin-from-right-edge-of-screen margin-left                  transition-duration
                                 -gradient-height                   margin-right                    margin-top                   width
                                 -gradient-start                    max-rows                        max-width                    min-height
                                 -inactive-window-background        -margin-horizontal              -pie-background-color
                                 -inactive-window-border            -pie-border-color               -pie-border-width
                                 -slider-active-background-color    -slider-active-border-color     -slider-background-color
                                 -slider-border-color               -slider-border-width            -slider-handle-radius
                                 -slider-height
```

**Chưa được theme mặc định dùng nhưng engine có hỗ trợ:** `-blur` (E8), `-bumpmap` (E9),
`-st-icon-style`, `-gradient-direction/-start/-end` (dạng `background-gradient-*` cũ),
`background-position`, `background-repeat`, `outline*`, `line-through`/`overline`/`underline`
trong `text-decoration`, `symbolic`/`requested`/`full-color` trong `-st-icon-style`.

**KHÔNG được St hỗ trợ** (không thấy trong `st-theme-node.c`, tuyệt đối không dùng):
`transition-timing-function`, `var()`/custom properties, `calc()`, `@media`, `flex`/`grid`,
`transform`, `filter`, `backdrop-filter`, `opacity` (dùng `rgba()`/`alpha` thay thế),
`text-shadow` có nhiều lớp, `linear-gradient()` dạng CSS chuẩn (St dùng
`background-gradient-direction/-start/-end`).

> Hàm màu runtime: GTK3 hỗ trợ `alpha()`, `shade()`, `mix()` (thấy trong `nemo-style-application.css`).
> Trong theme Cinnamon thì theme mặc định làm toàn bộ phép màu **lúc biên dịch** bằng hàm SCSS
> (`transparentize()`, `mix()`) — ta phải theo cách này, không dựa vào hàm runtime của St.

## 5. Những gì CHƯA xác minh được (không được đoán)

Chuyển toàn bộ sang `09-verification-checklist.md`. Tóm tắt:

1. Phiên bản chính xác của `cinnamon`, `nemo`, `muffin`, `mint-themes`, `libadwaita-1-0`, `gtk+-3.0`, `gtk4` trên máy người dùng.
2. Session là X11 hay Wayland (`XDG_SESSION_TYPE`) — Cinnamon 6.6 có hỗ trợ Wayland, hiệu ứng St có thể khác.
3. Backend portal nào đang chạy và nó báo theme name gì cho libadwaita (`ADW_DEBUG_THEMES=1`).
4. Thư mục libadwaita mà bản libadwaita đã cài thực sự dò: `libadwaita-1.5` hay `libadwaita-1.0` (bản cũ hơn).
5. Có sẵn `plank` không; có sẵn `sass`/`pysassc` không; font nào khả dụng.
6. Ảnh chụp thực tế của từng bề mặt UI (bắt buộc để nghiệm thu).
7. Chi phí thật của `-blur` trên GPU của người dùng.
8. Theme hiện tại đang dùng (để làm baseline so sánh và snapshot rollback).
