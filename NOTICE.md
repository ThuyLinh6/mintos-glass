# NOTICE — nguồn gốc bên thứ ba và giấy phép

Trạng thái: **chưa vendor bất kỳ mã bên thứ ba nào.** File này là sổ theo dõi;
mỗi lần thêm mã vendor phải cập nhật ở đây **trong cùng commit**.

## Giấy phép của repo

Dự kiến **GPL-3.0-or-later**. Lý do và phân tích đầy đủ:
[`docs/adr/ADR-007-licensing.md`](docs/adr/ADR-007-licensing.md).

> ⚠️ File `LICENSE` **chưa** được thêm. Nó **bắt buộc phải có trước khi** task T04
> vendor `data/theme/cinnamon-sass` của Cinnamon vào `src/cinnamon/vendor/`.
> Hiện tại repo chỉ chứa tài liệu và công cụ do chính dự án viết, chưa có tác phẩm dẫn xuất.

## Sổ theo dõi mã vendor

| Đường dẫn trong repo | Nguồn upstream | Ref / commit | Giấy phép upstream | Trạng thái |
|---|---|---|---|---|
| *(trống)* | — | — | — | chưa vendor gì |

### Mẫu dòng sẽ điền ở T04

| `src/cinnamon/vendor/cinnamon-6.6-sass/` | `github.com/linuxmint/Cinnamon` `data/theme/cinnamon-sass/` | tag `6.6.9`, commit SHA đầy đủ | GPL-2.0-or-later (Cinnamon) · LGPL-2.1-or-later (`src/st`) | pristine, không sửa tay |

Bằng chứng giấy phép upstream (đã xác minh 2026-10-13):
- `linuxmint/Cinnamon` `README.rst` mục License: *"Cinnamon is distributed under the terms of the
  GNU General Public License, version 2 or later."* → `COPYING` là GPLv2.
- Header `linuxmint/Cinnamon/src/st/st-theme-node.c`: *"GNU Lesser General Public License …
  either version 2.1 of the License, or (at your option) any later version."*
- `linuxmint/mint-themes/debian/copyright`: `License: GPL-3+`.

## Những thứ KHÔNG lấy từ đâu cả (tự viết)

| Đường dẫn | Ghi chú |
|---|---|
| `design/tokens/*.json` | Design token do dự án định nghĩa. Bảng màu gray/mint là giá trị thiết kế, không sao chép từ theme nào. |
| `tools/tokens/generate.py` | Generator, Python stdlib. |
| `tools/lint/contrast.py` | Công thức WCAG 2.1 (relative luminance + contrast ratio) là công thức chuẩn công khai, tự triển khai; có self-test đối chiếu 3 giá trị chuẩn. |
| `tools/lint/safety_paths.py` | Tự viết. |
| `tests/**` | Tự viết. |
| `docs/**` | Tự viết; các trích dẫn upstream có ghi rõ đường dẫn file/dòng trong `docs/plan/01-survey.md`. |

## Dữ liệu tham chiếu đã đọc nhưng KHÔNG sao chép

Để lập kế hoạch, các file upstream sau đã được **đọc** qua GitHub API và phân tích
(không lưu bản sao vào repo):

- `linuxmint/Cinnamon@6.6.9`: `data/theme/cinnamon-sass/**`, `src/st/st-theme-node.c`,
  `src/st/st-theme.c`, `src/st/st-widget.c`, `src/st/st-background-effect.{c,h}`,
  `js/ui/main.js`, `js/ui/themeManager.js`, `data/theme/cinnamon-sass/meson.build`,
  `files/…/cs_themes.py`, `data/org.cinnamon.gschema.xml`, `README.rst`, `COPYING`
- `linuxmint/muffin@6.6.3`: `src/meta/theme.h`, `src/ui/theme.c`, `src/ui/theme-private.h`,
  `src/ui/frames.c`, `debian/control`, `meson.build`
- `linuxmint/nemo@master.mint22`: `gresources/nemo-style-*.css`, `src/nemo-window.c`,
  `src/nemo-places-sidebar.c`, `meson.build`
- `linuxmint/mint-themes@master`: cấu trúc thư mục, `src/Mint-Y/gtk-3.0/sass/_colors-public.scss`,
  `src/Mint-Y/gtk-3.0/parse-sass.sh`, `files/usr/share/themes/Mint-Y/index.theme`, `debian/{changelog,copyright}`
- `linuxmint/libadwaita@master` và `@24.04`: `README.md`, `src/adw-style-manager.c`,
  `src/adw-settings*.c`, `debian/{changelog,patches/series}`
- `linuxmint/cinnamon-desktop@master.mint22`: `schemas/org.cinnamon.desktop.interface.gschema.xml.in`,
  `schemas/org.cinnamon.desktop.wm.preferences.gschema.xml.in`
- `ricotz/plank`: `data/themes/Default/dock.theme`

Trích dẫn chi tiết từng phát hiện: [`docs/plan/01-survey.md`](docs/plan/01-survey.md) §3 (E1–E37).

## Font và ảnh tham chiếu

- **Không** đóng gói font. Token `font.family` đang ở trạng thái `unverified: true`
  và bị generator bỏ qua cho tới khi xác minh bằng `fc-list` trên máy thật
  (`docs/plan/09-verification-checklist.md` mục 8).
- **Không** commit ảnh chụp giao diện macOS hay ảnh có bản quyền vào `design/reference/`.
  Chỉ ghi chú mô tả bằng chữ.
