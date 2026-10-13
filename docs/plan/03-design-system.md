# 03 — Design system dùng chung (Design Tokens)

Mục tiêu: **một** định nghĩa màu/kích thước/blur/motion, sinh ra **năm** định dạng đầu ra.
Không module nào được hard-code giá trị màu hay bán kính.

> **TRẠNG THÁI: ĐÃ TRIỂN KHAI (T02 xong).**
> Token thật nằm ở `design/tokens/*.json`; generator là `tools/tokens/generate.py`
> (hướng dẫn: `tools/tokens/README.md`); tài liệu sinh ra ở `docs/design-system/tokens.md`.
> Các đoạn JSON trong tài liệu này là **thiết kế ban đầu** — bản chính thức là file trên đĩa.
> Ba điểm khác biệt đã phát hiện khi triển khai thật:
> 1. Thêm token `border.control` (white/black alpha ~0.36–0.45) vì `border.subtle` 12% chỉ đạt 1.43:1 —
>    không đủ 3:1 theo WCAG 1.4.11 cho ranh giới cần để nhận diện control (ví dụ viền ô nhập).
> 2. `text.on-accent` là **gray-950**, không phải trắng: trắng trên mint `#3ddc97` chỉ ~1.9:1.
> 3. Cặp contrast có thêm trường `role` (`text` / `ui` / `decorative`); đường kẻ trang trí
>    được báo cáo nhưng không chặn build, và bắt buộc có `_note` giải thích.

## 1. Ba tầng token

```
Tầng 1  PRIMITIVE   giá trị thô, không ngữ nghĩa      gray-800 = #1c1e22
Tầng 2  SEMANTIC    ngữ nghĩa UI, theo color-scheme   surface.glass.mid = rgba(gray-900, 0.72)
Tầng 3  COMPONENT   ràng buộc theo widget cụ thể      panel.background = surface.glass.high
```

Quy tắc: component chỉ trỏ semantic; semantic chỉ trỏ primitive. Không nhảy tầng, không hard-code.

## 2. Schema file token

`design/tokens/10-primitives.json` (ví dụ cấu trúc — giá trị là **đề xuất**, chờ D-2/D-3):

```json
{
  "$schema": "./token-schema.json",
  "color": {
    "gray": { "0":"#ffffff","100":"#eceef1","200":"#cfd2d7","300":"#a5a9b0",
              "400":"#7c8087","500":"#55585f","600":"#3a3d43","700":"#2a2c31",
              "750":"#232529","800":"#1c1e22","850":"#17181c","900":"#121316","950":"#0b0c0e" },
    "blue": { "400":"#6cb6ff","500":"#3b9dff","600":"#2b7fd4" },
    "mint": { "400":"#6ee7bd","500":"#3ddc97","600":"#2bb67a" },
    "red":  { "500":"#ff5f57","600":"#e04b43" },
    "amber":{ "500":"#ffbd2e" },
    "green":{ "500":"#28c840" }
  },
  "radius": { "xs":4, "sm":6, "md":8, "lg":12, "xl":16, "2xl":20, "pill":999 },
  "space":  { "0":0,"1":2,"2":4,"3":6,"4":8,"5":12,"6":16,"7":20,"8":24,"9":32 },
  "blur":   { "none":0, "sm":2, "md":4, "lg":6, "MAX_ALLOWED":6 },
  "size":   { "icon-sm":16,"icon-md":22,"icon-lg":32,"titlebar-height":34,"panel-height":30 }
}
```

> `blur.MAX_ALLOWED = 6` là **rào cứng kỹ thuật**, không phải thẩm mỹ — xem E11.
> Generator phải **từ chối** build nếu component token nào xin blur > MAX_ALLOWED.

`design/tokens/20-semantic-dark.json`:

```json
{
  "surface": {
    "base":        { "value":"{color.gray.900}", "alpha":1.00 },
    "glass.low":   { "value":"{color.gray.900}", "alpha":0.55 },
    "glass.mid":   { "value":"{color.gray.850}", "alpha":0.72 },
    "glass.high":  { "value":"{color.gray.800}", "alpha":0.86 },
    "elevated.1":  { "value":"{color.gray.850}", "alpha":0.92 },
    "elevated.2":  { "value":"{color.gray.800}", "alpha":0.96 },
    "solid":       { "value":"{color.gray.850}", "alpha":1.00 },
    "selected":    { "value":"{color.blue.500}", "alpha":1.00 },
    "hover":       { "value":"{color.gray.0}",   "alpha":0.07 },
    "active":      { "value":"{color.gray.0}",   "alpha":0.12 }
  },
  "border": {
    "hairline":    { "value":"{color.gray.0}", "alpha":0.08 },
    "subtle":      { "value":"{color.gray.0}", "alpha":0.12 },
    "strong":      { "value":"{color.gray.0}", "alpha":0.20 },
    "highlight":   { "value":"{color.gray.0}", "alpha":0.10 },
    "focus":       { "value":"{color.blue.400}", "alpha":0.85 }
  },
  "text": {
    "primary":     { "value":"{color.gray.0}", "alpha":0.92 },
    "secondary":   { "value":"{color.gray.0}", "alpha":0.66 },
    "tertiary":    { "value":"{color.gray.0}", "alpha":0.44 },
    "disabled":    { "value":"{color.gray.0}", "alpha":0.30 },
    "on-accent":   { "value":"{color.gray.0}", "alpha":1.00 },
    "link":        { "value":"{color.blue.400}", "alpha":1.00 }
  },
  "status": {
    "accent":      "{color.blue.500}",
    "success":     "{color.green.500}",
    "warning":     "{color.amber.500}",
    "error":       "{color.red.500}",
    "badge":       "{color.red.500}"
  },
  "shadow": {
    "sm": { "y":1,  "blur":2,  "color":"#000000", "alpha":0.30 },
    "md": { "y":4,  "blur":12, "color":"#000000", "alpha":0.36 },
    "lg": { "y":10, "blur":28, "color":"#000000", "alpha":0.44 },
    "xl": { "y":18, "blur":48, "color":"#000000", "alpha":0.52 }
  }
}
```

`design/tokens/30-component.json` (trích):

```json
{
  "cinnamon.panel":            { "background":"surface.glass.high", "border":"border.hairline",
                                 "height":"size.panel-height", "blur":"blur.none",
                                 "note":"KHÔNG bật blur cho panel full-width — E11" },
  "cinnamon.menu":             { "background":"surface.glass.mid", "radius":"radius.lg",
                                 "border":"border.subtle", "shadow":"shadow.lg", "blur":"blur.md" },
  "cinnamon.windowlist.active":{ "background":"surface.selected",  "radius":"radius.sm" },
  "cinnamon.osd":              { "background":"surface.glass.low", "radius":"radius.xl", "blur":"blur.lg" },
  "cinnamon.notification":     { "background":"surface.elevated.2","radius":"radius.lg", "shadow":"shadow.lg" },
  "cinnamon.dialog":           { "background":"surface.elevated.1","radius":"radius.xl", "shadow":"shadow.xl" },

  "gtk.titlebar":              { "background":"surface.glass.high","height":"size.titlebar-height",
                                 "border-bottom":"border.hairline" },
  "gtk.button":                { "radius":"radius.md", "background":"surface.hover" },
  "gtk.button.default":        { "background":"surface.selected", "text":"text.on-accent" },
  "gtk.entry":                 { "radius":"radius.md", "background":"surface.base", "border":"border.subtle" },
  "gtk.sidebar":               { "background":"surface.glass.mid" },
  "gtk.selection":             { "background":"surface.selected" },

  "nemo.desktop.label":        { "text":"#eeeeee", "shadow":"1px 1px rgba(0,0,0,0.8)",
                                 "note":"giữ tương đương nemo-style-application.css để không giảm độ đọc" },
  "nemo.places.diskfull":      { "bar-width":2, "bar-radius":1, "max-length":70 },

  "adwaita.window.controls":   { "close":"status.error", "minimize":"status.warning", "maximize":"status.success" },

  "plank.dock":                { "fill-start":"surface.glass.mid", "fill-end":"surface.glass.high",
                                 "roundness-top":"radius.lg", "line-width":1,
                                 "indicator-size":5, "icon-shadow-size":1 }
}
```

`design/tokens/40-motion.json`:

```json
{ "duration": { "instant":0, "fast":90, "base":160, "menu":180, "slow":240, "dialog":300 },
  "easing":   { "standard":"cubic-bezier(0.2, 0.0, 0.0, 1.0)", "decelerate":"cubic-bezier(0.0, 0.0, 0.2, 1.0)" },
  "_note":    "St/Cinnamon CHỈ hỗ trợ transition-duration (E36) — easing chỉ dùng cho GTK3/GTK4." }
```

`design/tokens/50-a11y.json`:

```json
{ "contrast": { "body-text":4.5, "large-text":3.0, "ui-component":3.0 },
  "min-target-px": 24,
  "min-icon-px": 16,
  "focus-visible": true,
  "high-contrast-variant": true }
```

## 3. Generator: một nguồn → năm định dạng

`tools/tokens/generate.py` (Python 3 stdlib, không dependency) sinh ra:

| Đầu ra | Dùng cho | Định dạng |
|---|---|---|
| `src/cinnamon/tokens/_tokens.scss` | Cinnamon | `$mg-surface-glass-mid: rgba(23,24,28,0.72);` |
| `src/gtk-3.0/sass/_tokens.scss` | GTK3 | như trên |
| `src/gtk-4.0/sass/_tokens.scss` | GTK4 | như trên |
| `src/libadwaita/tokens.css` | libadwaita | `@define-color mg_surface_glass_mid rgba(23,24,28,0.72);` |
| `src/dock/plank/MintOS-Glass/dock.theme` | Plank | `FillStartColor=23;;24;;28;;184` (E35) |
| `docs/design-system/tokens.md` + `tokens-preview.css` | tài liệu | bảng + swatch |
| `design/tokens.lock.json` | CI | SHA-256 của toàn bộ token → phát hiện drift |

Yêu cầu bắt buộc của generator:
1. **Deterministic**: cùng input → cùng byte output (sort key, không timestamp).
2. **Fail-fast**: token component tham chiếu semantic không tồn tại → exit 1.
3. **Clamp blur** ở `MAX_ALLOWED`; nếu component xin lớn hơn → exit 1 kèm tên token.
4. **Kiểm contrast** ở tầng semantic (text × surface) theo `50-a11y.json`; vi phạm → warning, và **error** nếu vi phạm `body-text`.
5. Xuất cả 2 scheme (dark/light) nếu D-2 = cả hai.
6. Màu Plank phải là **số nguyên 0–255** và alpha = round(a×255) — không phải hex.

## 4. Ràng buộc nền tảng mà design system PHẢI tôn trọng

| Nền tảng | Được | Không được | Hệ quả thiết kế |
|---|---|---|---|
| **St / Cinnamon** (E36, E8, E11) | `background-color: rgba()`, `background-gradient-*`, `border`, `border-radius` (4 góc riêng), `box-shadow`, `padding/margin`, `width/height/min/max`, `font-*`, `text-align`, `transition-duration`, `icon-size`, `-blur`, `-bumpmap`, `-st-icon-style`, `-slider-*`, `-arrow-*`, `-barlevel-*`, `spacing*`, `selected-color`, `selection-background-color`, `caret-*` | `var()`, `calc()`, `@media`, `flex/grid`, `transform`, `filter`, `backdrop-filter`, `linear-gradient()` chuẩn, `transition-timing-function`, `opacity` | Mọi phép màu phải tính **lúc biên dịch** (hàm SCSS). Không có easing → animation Cinnamon chỉ đổi duration. Dùng `rgba` thay `opacity` |
| **GTK3** (E33, E29) | `@define-color`, `alpha()`, `shade()`, `mix()`, `-gtk-gradient`, `-gtk-icon-source`, `-gtk-scaled` | — | **Bắt buộc** export đủ `@theme_*` (E29) và đủ bộ public (E33), nếu không Nemo và app Mint khác vỡ |
| **GTK4/libadwaita** (E22, E23) | `defaults-{light,dark}.css` = `@define-color`; `base.css` = widget style; `base-hc.css` bắt buộc | sửa layout sâu, đổi cấu trúc widget | Chỉ đổi **màu + window controls**. `base-hc.css` thiếu ⇒ libadwaita bỏ qua toàn bộ theme khi user bật high-contrast |
| **Muffin** (E32) | `window.background.ssd`, `decoration`, `headerbar.titlebar.horizontal.default-decoration`, `label.title`, `.button.titlebutton` | metacity XML | Chiều cao/padding của `.default-decoration` **quyết định kích thước titlebar thật** (E32b) — phải đo, không đoán |
| **Plank** (E35) | INI, màu `R;;G;;B;;A` | CSS | Generator phải chuyển đổi; alpha 0–255 |

## 5. Ngôn ngữ thị giác đề xuất ("Glass")

Chưa chốt — cần D-2/D-3. Đề xuất mặc định:

- **Nền tối ấm trung tính** (gray-900/850), không đen tuyệt đối → tránh "crushed black" trên IPS.
- **Ba mức glass** (low/mid/high) thay vì một mức: panel & titlebar = high, menu & OSD = mid, dialog = elevated.
- **Hairline border 1px, trắng 8–12%** trên mép trên của mọi bề mặt nâng → mô phỏng viền kính macOS.
- **Bán kính phân cấp**: menu/OSD 12–16, nút/entry 8, chip/badge 6, window 10 (cần đo muffin thật).
- **Shadow theo 4 bậc** (sm/md/lg/xl) gắn với độ nâng, không dùng shadow cho phần tử phẳng.
- **Accent duy nhất**, không dùng accent cho text thường.
- **Không blur** ở panel/windowlist; blur ≤ 4 ở menu/OSD **và chỉ trong biến thể opt-in**.

## 6. Định nghĩa "Done" cho tầng design system (T02)

1. 7 file token JSON hợp lệ theo schema, có schema file để validate.
2. `make tokens` sinh đủ 7 đầu ra, byte-identical khi chạy lại 2 lần.
3. `make lint-tokens` pass: không drift, không blur vượt trần, contrast AA đạt cho mọi cặp text×surface semantic.
4. `docs/design-system/tokens.md` render bảng đầy đủ, có ví dụ sử dụng cho **cả 5 nền tảng**.
5. Có tài liệu "cách thêm một token mới" (3 bước) để agent khác không phải hỏi.
