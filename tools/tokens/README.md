# tools/tokens — generator design token

Một nguồn sự thật (`design/tokens/*.json`) → nhiều định dạng stylesheet.

```bash
make tokens                 # sinh output cho scheme dark (mặc định)
make tokens SCHEME=all      # dark + light (light hiện chưa emit — D-2)
make tokens-check           # KHÔNG ghi; exit 1 nếu file generated lệch token (CI)
make report                 # in toàn bộ token đã phân giải + bảng contrast
```

Hoặc gọi trực tiếp:

```bash
python3 tools/tokens/generate.py [--scheme dark|light|all] [--check] [--report]
                                 [--out-root DIR] [--tokens-dir DIR]
```

## Output hiện tại

| File | Format | Dùng bởi |
|---|---|---|
| `src/cinnamon/tokens/_tokens.scss` | SCSS `$mg-*` | T04 — `@import` vào `src/cinnamon/cinnamon.scss` |
| `src/gtk-3.0/sass/_tokens.scss` | SCSS `$mg-*` | T06 |
| `src/gtk-4.0/sass/_tokens.scss` | SCSS `$mg-*` | T10 |
| `src/libadwaita/tokens.css` | `@define-color mg_*` | T10 — map sang tên Adwaita trong `defaults-*.css` |
| `docs/design-system/tokens.md` | Markdown | tài liệu |
| `design/tokens.lock.json` | lock hash | CI phát hiện drift |

**Chưa emit** (có chủ đích, khai báo trong `00-meta.json → emitters_disabled`):
- `src/dock/plank/MintOS-Glass/dock.theme` — D-1 chọn grouped-window-list, hoãn Plank.
- `_tokens.light.scss` — D-2 chọn dark trước.

## Quy ước đặt tên

| Đường dẫn token | Tên SCSS | Tên `@define-color` |
|---|---|---|
| `surface.glass.mid` | `$mg-surface-glass-mid` | `mg_surface_glass_mid` |
| `radius.lg` | `$mg-radius-lg` | — (chỉ emit semantic + component) |

Tiền tố `mg-` / `mg_` để không đụng biến của Cinnamon (`$bg_color`, `$accent_color`, …)
hay của Mint-Y. T04 sẽ map token của ta vào biến upstream trong
`src/cinnamon/overrides/_00-globals.scss`.

## Đơn vị khi emit

| Namespace | Đơn vị | Lý do |
|---|---|---|
| `radius`, `space`, `size`, `border-width` | `px` | St và GTK đều nhận `px` |
| `blur` | **không đơn vị** | `-blur` của St là integer length (`st-theme-node.c:2132` dùng `get_length_from_term_int`) |
| `duration` | `ms` | `transition-duration: 160ms` (stock Cinnamon 6.6 dùng dạng này) |
| `opacity.*` | số trần | đây là alpha, không phải thuộc tính CSS (St không có `opacity`) |

Shadow emit dạng dùng chung được cho cả St và GTK: `0 4px 12px rgba(0, 0, 0, 0.36)`
(St nhận 4 length `x y blur spread` + `inset`, đã đối chiếu `data/theme/cinnamon-sass`).

## Năm bảo đảm của generator

1. **Deterministic** — cùng input → cùng byte output. Có test (`test_deterministic_output`).
2. **Fail-fast** — ref không phân giải được, alpha ngoài `[0,1]`, dark/light lệch khoá → exit 1.
3. **Clamp blur** — vượt `primitives.blur.MAX_ALLOWED` là exit 1. Đây là rào cứng theo bằng chứng E11:
   `src/st/st-background-effect.c` chạy `blur_size` vòng lặp, mỗi vòng
   `g_malloc(w*h*4)` + `cogl_framebuffer_read_pixels()` + `cogl_texture_new_from_data()`, **mỗi lần paint**.
4. **Không bịa** — token có `"unverified": true` **bị bỏ qua khi emit** và in ra `// WARN …`.
   Hiện có 4 token như vậy: `size.titlebar-height`, `gtk.titlebar.height`, `font.family`,
   `font.size-base-pt`. Chúng chỉ được bật sau khi có kết quả T00/T08.
5. **Contrast AA** — mọi cặp trong `50-a11y.json` phải đạt, trừ `role: "decorative"`.

## Thêm một token mới (3 bước)

1. Thêm vào đúng tầng trong `design/tokens/*.json`
   (hex chỉ ở `10-primitives.json`; semantic/component chỉ được **trỏ**, không hard-code — có test).
2. `make tokens && make report` — đọc bảng contrast, sửa nếu FAIL.
3. `make check` — xanh thì commit cả token **và** file generated trong cùng commit.

## Thêm một cặp kiểm tra contrast

Sửa `design/tokens/50-a11y.json → contrast_pairs.<scheme>`:

```json
{ "text": "text.primary", "on": "surface.glass.mid", "min": "body-text", "role": "text" }
```

`role`:
- `text` — chữ, bắt buộc đạt ngưỡng (WCAG 1.4.3)
- `ui` — ranh giới/trạng thái cần để nhận diện control, bắt buộc 3:1 (WCAG 1.4.11)
- `decorative` — chỉ trang trí; được báo cáo nhưng **không** chặn build, và bắt buộc phải có `_note` giải thích

Mô hình đo: vì bề mặt glass **bán trong suốt** trên wallpaper không biết trước, ta composite
bề mặt lên **backdrop xấu nhất** (dark → trắng, light → đen), rồi composite chữ lên đó, rồi đo.
Xem `tools/lint/contrast.py`.
