# VENDOR — Cinnamon 6.6 stock theme SCSS

File trong thư mục này là **bản sao nguyên trạng (pristine)** từ upstream.
**KHÔNG sửa tay.** Mọi tùy biến nằm ở `src/cinnamon/overrides/`.

## Nguồn

| Trường | Giá trị |
|---|---|
| Repository | `https://github.com/linuxmint/Cinnamon` |
| Đường dẫn gốc | `data/theme/cinnamon-sass/` |
| Tag | `6.6.9` |
| Tag object SHA | `f3d2b747dfcccd1852590dbec0d237fbe6226532` |
| **Commit SHA** | `806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18` |
| Commit date | 2026-07-20T11:28:24Z |
| Cách lấy | `curl -sSL https://codeload.github.com/linuxmint/Cinnamon/tar.gz/806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18` rồi giải nén, chép `data/theme/cinnamon-sass/*.scss` và `widgets/*.scss` |
| Ngày vendor | 2026-10-13 |
| Đã kiểm tra | `diff -r` với upstream → **giống hệt từng byte** (chỉ loại `meson.build`, không cần cho build của ta) |

## Giấy phép

- Cinnamon: **GPL-2.0-or-later** — `README.rst` mục License: *"Cinnamon is distributed under the terms of
  the GNU General Public License, version 2 or later."* (`COPYING` là bản GPLv2).
- Thư viện engine theme `src/st/`: **LGPL-2.1-or-later** (header `src/st/st-theme-node.c`).
  Ta **không** sao chép mã C của `st`; chỉ đọc để lập danh sách property hợp lệ
  (`tests/fixtures/st-allowed-properties.txt`). Danh sách tên property là thông tin chức năng,
  không phải biểu đạt được bảo hộ.
- Repo MintOS Glass chọn **GPL-3.0-or-later** (tương thích upward với GPL-2.0-or-later).
  Xem `docs/adr/ADR-007-licensing.md` và `NOTICE.md`.

## Vì sao phải vendor (không viết theme từ số 0)

Đã xác minh từ mã nguồn Cinnamon `6.6.9`:

- `js/ui/main.js → loadTheme()` nạp stylesheet của user, còn
  `/usr/share/cinnamon/theme/cinnamon.css` chỉ là `fallback_stylesheet`.
- `src/st/st-theme.c`, doc comment của `PROP_FALLBACK_STYLESHEET`:
  *"Fallback stylesheet - non-cascading. It is applied only if the user-selected stylesheets
  fail to return any properties, and the StWidget has its `important` property set."*

⇒ Theme Cinnamon của bên thứ ba **bắt buộc phải hoàn chỉnh**. Vendor sass của chính Cinnamon 6.6
là cách duy nhất đảm bảo phủ hết selector (kể cả phần mới của 6.6: `.appmenu*`,
`favorites@`, `nightlight@`, screensaver, OSK) mà không đoán.

## Kiểm chứng integrity

SHA-256 của từng file lúc vendor. Chạy lại để kiểm tra:

```bash
python3 tools/lint/vendor_integrity.py
```

| File | Bytes | SHA-256 |
|---|---|---|
| `_colors.scss` | 894 | `dcde3f56ed0bc04606f8c495a4f4c01acc1aff7f400e4395b804662ddd34a26a` |
| `_common.scss` | 4163 | `63a96adf4765e512d91d8d0619846e2ead1c03adc6c4c59cef2b86e8ae1b19bb` |
| `_drawing.scss` | 4008 | `380fa6dff45699add5410e3d81fe098ca8279cda1ea71987ce1800736ca76232` |
| `_widgets.scss` | 487 | `8f3724680a4bc9d7a17c3854f1a8ee57f65e1efe173edd5e1a9d144196bc0dbd` |
| `cinnamon.scss` | 78 | `4028f85648957cb9a06da228cf14d8772a8d5dc2a576942741f29f6232a38468` |
| `widgets/_alttab.scss` | 1640 | `6e3880a03c527d3798370a23e6a423eb83cbeb9a50e4980eef9542d3fce565e3` |
| `widgets/_applets.scss` | 4419 | `0f9e0161771d09f50c6eef7cd523f40c6e0dc3109e040fb21a56baba4332b9bf` |
| `widgets/_base.scss` | 2694 | `219d567bdabbe8a1a35cd79d0b5cf895aa25bf6f257dd2d0d98bc383ef9661d1` |
| `widgets/_calendar.scss` | 3906 | `95cf9685b6a929ce3632f150375ab1fa3223f184a085cc25252e3b6d88003509` |
| `widgets/_deprecated.scss` | 2007 | `f396f8c523e177959ca8b583381b28393b45c7f80c5f32ec561cd684dd5f2f01` |
| `widgets/_desklet.scss` | 1015 | `3d8f021a2c2461f070805c2ed97490fe3780a5181883927b57c201de96fc7227` |
| `widgets/_dialogs.scss` | 3426 | `2dc9648dd01b65dd446ab41521f8c7eb0e271a1397a4df84a78bbe5ba8da852e` |
| `widgets/_expo.scss` | 1763 | `f8e948dbc85f5a85597aa10365da2a20411abab88cae8c6cceb67e512a3981da` |
| `widgets/_ibus-popup.scss` | 1154 | `1613ab275279cd3f4d749016d821b46b28abe47ab71b39ad0d108250a1f13650` |
| `widgets/_keyboard.scss` | 1693 | `a9ac0ee1cf2e92858b68a8275619e74dcdfb58e1d4c37671da5322614a6f29a0` |
| `widgets/_menus.scss` | 2961 | `031220586df66e9448b6207dccfcaa5eb0009158b3d0e03c3262baf5069ae0b9` |
| `widgets/_notifications.scss` | 1166 | `25a99e66758860c794448cde8333ae8b2f23beb482d0be222afe1e904514a9fd` |
| `widgets/_osd.scss` | 1863 | `7c8cddec9a0be3987f966b35f3bdc6c6bdece3da3bc5b5b7b96a1e05b5ccc808` |
| `widgets/_panel.scss` | 1782 | `73803b36dc2e2b0c05c991887db72e3d30affc6f188e364be30e1ffe694e0a9d` |
| `widgets/_startmenu.scss` | 4113 | `48ba74949a8f4863f46ce6be4001002121f0be3c4b7fe843db5b6567732186ab` |
| `widgets/_switch-check.scss` | 1458 | `84a2ee5c9a6eaadbfdec9c80849cf8bdbc828f69b59b6a87da7f5d612f28b050` |
| `widgets/_windowlist.scss` | 3901 | `a9759438b9b48391fe82159fcb4ff8d6be8b5a050884c52e668a25e3f8ad0789` |

Tổng: **22 file**, 2385 dòng.

## File upstream KHÔNG được vendor

| File | Lý do |
|---|---|
| `meson.build` | Chỉ dùng cho build của Cinnamon (`find_program('pysassc','sassc')`). Ta build bằng `tools/build/compile_scss.py`. |
| `data/theme/*.svg`, `*.png` | Asset của theme mặc định. Ta **tự vẽ** asset gốc trong `src/cinnamon/assets/` (không sao chép artwork GPL để tránh mơ hồ nguồn gốc — xem `NOTICE.md`). |
| `data/theme/theme-changelog.txt` | Ghi chú lịch sử, không ảnh hưởng build. |

## Cách re-base khi Mint cập nhật Cinnamon

1. Tải tarball của tag 6.6.x mới.
2. `diff -r` với thư mục này → xem selector/property nào thêm/bớt.
3. Cập nhật file ở đây, cập nhật bảng SHA-256, cập nhật `tests/fixtures/cinnamon-6.6-selectors.txt`.
4. Chạy `make check`; nếu coverage test fail → thêm selector mới vào `overrides/`.
5. Ghi commit SHA mới vào bảng trên và vào `NOTICE.md`.
