# MintOS Glass ISO Customizer — tài liệu công cụ

Công cụ lấy một ISO Linux Mint gốc, tích hợp giao diện MintOS Glass và tạo ISO mới.
Mã nguồn: `tools/iso_customizer/` (Python, chỉ thư viện chuẩn cho logic của công cụ).
Tài liệu này mô tả **đúng hành vi đã triển khai**; mọi mức kiểm chứng chưa làm được
đều ghi rõ, không suy đoán.

> **Trạng thái hiện tại (trung thực):** công cụ đã triển khai đầy đủ pipeline và đã
> qua unit test + chạy thử đầu-cuối bằng fixture ISO tổng hợp. **Chưa tạo được ISO
> MintOS Glass thật** vì (1) môi trường phát triển hiện tại thiếu `xorriso`,
> `unsquashfs`, `mksquashfs` và (2) chưa có ISO Linux Mint 22.3 thật để build/boot/cài thử.
> Giao diện GTK vẫn thiếu (chưa có `gtk.css`) nên ngay cả khi remaster chạy được,
> ISO đầu ra vẫn bị ghi rõ là thiếu thành phần GTK cho tới khi T06 hoàn thành.

---

## Mục lục

- [1. Kiến trúc module](#1-kiến-trúc-module)
- [2. Yêu cầu môi trường build](#2-yêu-cầu-môi-trường-build)
- [3. Chuẩn bị ISO nguồn](#3-chuẩn-bị-iso-nguồn)
- [4. Cách sử dụng CLI](#4-cách-sử-dụng-cli)
- [5. Quy trình build từng bước](#5-quy-trình-build-từng-bước)
- [6. Workspace, log, manifest và dọn dẹp](#6-workspace-log-manifest-và-dọn-dẹp)
- [7. Tích hợp giao diện, live session và mặc định sau cài đặt](#7-tích-hợp-giao-diện-live-session-và-mặc-định-sau-cài-đặt)
- [8. Kiểm tra kết quả (5 mức)](#8-kiểm-tra-kết-quả-5-mức)
- [9. Tái tạo quy trình trên máy đích](#9-tái-tạo-quy-trình-trên-máy-đích)
- [10. Khắc phục lỗi](#10-khắc-phục-lỗi)
- [11. Giới hạn và việc còn lại trước phát hành](#11-giới-hạn-và-việc-còn-lại-trước-phát-hành)

---

## 1. Kiến trúc module

| Module | File | Trách nhiệm |
|---|---|---|
| Source Validator | `tools/iso_customizer/source_validator.py` + `iso9660.py` | Kiểm tra file, checksum SHA-256, đọc ISO9660/El Torito bằng Python thuần, suy ra phiên bản/arch (kèm cơ sở suy ra), phát hiện `casper/filesystem.squashfs`. Không sửa ISO gốc |
| Build Environment Validator | `env_validator.py` | Kiểm tra OS/Kiến trúc/Python, công cụ remaster, đĩa trống, liệt kê bước cần root (UID 0). Không tự cài gói |
| ISO Workspace Manager | `workspace.py` | Tạo workspace riêng mỗi lần build (`source/ extract/ overlay/ staging/ package/ output/ logs/`), ghi `logs/build.log`, `manifest.json`; chỉ dọn dẹp khi có `--confirm DELETE` + kiểm tra marker |
| UI Integrator | `ui_integrator.py` | Kiểm kê thành phần thật trong repo, biên dịch Cinnamon SCSS (libsass/pysassc/dart-sass nếu có), staging cây rootfs. Thiếu thành phần → `blocked`, không bịa file |
| Debian packager | `deb.py` | Sinh gói `.deb` thuần Python (ar + tar.gz: `debian-binary`, `control.tar.gz`, `data.tar.gz`) từ cây staging |
| Live Session Configurator | `live_config.py` | Sinh XML danh sách wallpaper + dùng chung schema override hệ thống cho phiên live; không giả định tên tài khoản live |
| Installer Defaults | `installer_defaults.py` | Sinh `90_mintos-glass.gschema.override`: chỉ đặt **mặc định** cho khóa đã xác minh, chỉ khi thành phần tương ứng tồn tại; người dùng đổi được sau, không khóa, không chạm tài khoản hiện có |
| ISO Builder | `iso_builder.py` | Điều phối validate → staging → gói → extract/unsquashfs/copy/`glib-compile-schemas`/mksquashfs/repack bằng `xorriso` (giữ boot image); dừng an toàn khi thiếu bước bắt buộc |
| ISO Validator | `iso_validator.py` | Kiểm tra 5 mức, báo cáo riêng từng mức (1–3 chạy thật; 4–5 luôn báo `NOT TESTED` nếu chưa làm) |
| CLI | `cli.py`, `__main__.py` | `python3 -m tools.iso_customizer …`; mã thoát riêng theo nhóm lỗi |

Phối hợp agent: token/generator của Agent 1 được tôn trọng (theme biên dịch từ chính
`src/cinnamon/cinnamon.scss`); tích hợp Cinnamon/panel theo Agent 2 (chỉ theme shell,
không sửa applet); Nemo/GTK của Agent 3–4 bị chặn đúng trạng thái (partial chưa có entry);
icon/wallpaper/Dock theo Agent 5 (icon 122 file, 4 wallpaper đã staging; Dock là style
GWL trong theme Cinnamon, không thêm gói); Settings/Control Center của Agent 6 không đưa
vào ISO vì mới là đề xuất; lỗi chặn phát hành theo sổ QA của Agent 7
(`tests/fixtures/qa-bug-register.txt`).

## 2. Yêu cầu môi trường build

Chạy trên máy Linux (khuyến nghị chính Linux Mint 22.3 hoặc Debian/Ubuntu tương thích):

| Yêu cầu | Bắt buộc cho | Trong môi trường phát triển hiện tại |
|---|---|---|
| Python ≥ 3.11 (stdlib) | Mọi lệnh offline, validate, staging, gói .deb | ✅ Có (3.11.2) |
| SCSS compiler: libsass (`pysassc`/module `sass`) hoặc dart-sass (`sass` 1.77.8) | Biên dịch theme Cinnamon khi staging | ✅ Có (cả hai) |
| `xorriso` | Extract + repack ISO, giữ boot | ❌ Thiếu → build dừng ở mức BLOCKED |
| `unsquashfs`, `mksquashfs` (squashfs-tools) | Giải nén/nén lại live filesystem | ❌ Thiếu |
| `glib-compile-schemas` | Biên dịch schema override trong rootfs | ❌ Thiếu (optional ở bước kiểm tra môi trường, bắt buộc ở bước remaster) |
| `qemu-system-x86_64` | Boot validation (mức 4) | ❌ Thiếu |
| Đĩa trống ≥ ~4× dung lượng ISO nguồn (tối thiểu 2 GiB cho fixture) | Toàn bộ build | ✅ ~20 GiB |
| Root (UID 0) hoặc quyền tương đương | Giải nén squashfs đúng chủ sở hữu, chroot/mount nếu dùng | ⚠️ Đang chạy user thường; công cụ không tự leo quyền |

Công cụ **không** tự cài các gói trên. Người vận hành tự cài trên máy build, ví dụ trên
Debian/Linux Mint (lệnh cần quyền quản trị, công cụ không thay bạn chạy):

```bash
sudo apt update
sudo apt install xorriso squashfs-tools libglib2.0-bin qemu-system-x86
```

Tên gói phải tự đối chiếu với bản phân phối trên máy build trước khi cài.

## 3. Chuẩn bị ISO nguồn

1. Lấy ISO **Linux Mint 22.3 Cinnamon 64-bit** từ nguồn phát hành chính thức của Linux Mint
   và checksum chính thức đi kèm (trang tải của Linux Mint). Đặt file ngoài repository
   (đã có `*.iso` trong `.gitignore`; không commit ISO).
2. Đối chiếu checksum chính thức **trước** khi build — tự tính lại bằng công cụ độc lập:

```bash
sha256sum /path/to/linuxmint-22.3-cinnamon-64bit.iso
```

3. Kiểm tra bằng công cụ (không sửa file gốc):

```bash
cd mintos-glass
python3 -m tools.iso_customizer inspect-source /path/to/linuxmint-22.3-cinnamon-64bit.iso \
  --expected-sha256 <checksum-chinh-thuc>
python3 -m tools.iso_customizer check-environment
```

- `inspect-source` đạt khi: file đọc được, đúng ISO9660, có El Torito, có
  `casper/filesystem.squashfs`, phiên bản suy ra khớp 22.3. Nếu không truyền
  `--expected-sha256`, checksum của công cụ **chỉ để nhận diện/phát hiện thay đổi**,
  không chứng minh ISO chính thức — output ghi rõ điều này.
- Việc suy ra phiên bản/arch từ tên file/volume chỉ là heuristics; bằng chứng cuối cùng
  vẫn là checksum chính thức + kiểm tra trên máy đích.
- Không phải mọi ISO Mint đều tương thích: ISO khác phiên bản, bản 32-bit, hay ISO đã
  remaster bởi công cụ khác đều có thể bị từ chối. `check-environment` phải cho
  `ready_for_remaster=true` trước khi build thật; nếu trả mã thoát 3 thì dừng lại xử lý
  môi trường, đừng bỏ qua.

## 4. Cách sử dụng CLI

Chạy từ thư mục gốc repository. Không lệnh nào cần hoặc tự xin quyền quản trị;
không lệnh nào ghi đè file đầu ra đã tồn tại nếu thiếu `--force`.

```bash
python3 -m tools.iso_customizer --help
python3 -m tools.iso_customizer check-environment            # JSON + mã thoát 0/3
python3 -m tools.iso_customizer inspect-source /path/to/linuxmint.iso [--expected-sha256 HEX] [--json]

# Build đầy đủ (extract + remaster + kiểm tra mức 1–3):
python3 -m tools.iso_customizer build \
  --source /path/to/linuxmint-22.3-cinnamon-64bit.iso \
  --output /path/to/mintos-glass-22.3.iso \
  [--workspace-parent build-iso-workspaces] [--build-id ten-lan-build] \
  [--allow-partial] [--no-deb] [--force]

# Chỉ validate + staging + gói .deb + manifest (không extract/repack, dùng để kiểm tra offline):
python3 -m tools.iso_customizer build --source ... --output ... --dry-run

python3 -m tools.iso_customizer validate /path/to/mintos-glass.iso [--source-iso]
python3 -m tools.iso_customizer clean --workspace build-iso-workspaces/mintos-glass-build-<id> --confirm DELETE

make iso            # in trợ giúp CLI
make iso-check-env  # kiểm tra môi trường
```

Mã thoát: `0` thành công · `2` lỗi đầu vào (gồm từ chối ghi đè/xóa không an toàn) ·
`3` môi trường chưa sẵn sàng · `4` ISO nguồn không hợp lệ · `5` thành phần giao diện
chưa sẵn sàng · `6` bước remaster bên ngoài thất bại. Ví dụ `--allow-partial` cho phép
tiếp tục khi thiếu theme GTK, nhưng manifest và gói vẫn ghi `gtk: blocked` — ISO đó
không được mô tả là hoàn chỉnh.

## 5. Quy trình build từng bước

1. **Source validation** — tính SHA-256 ISO nguồn (ghi vào manifest), kiểm tra như Mục 3.
   ISO không tương thích → hủy trước khi tạo thay đổi nào.
2. **Environment validation** — thiếu công cụ bắt buộc thì build vẫn tạo workspace,
   staging và manifest rồi dừng `BLOCKED` (giữ workspace để chẩn đoán), không tạo ISO.
3. **UI staging** — biên dịch `cinnamon.css` (~94 KB bằng libsass), chép 15 asset
   Cinnamon, 122+ file icon theme, 4 wallpaper vào `staging/rootfs/` theo cây hệ thống
   tương đối. GTK/libadwaita ghi `blocked` (QA-09/QA-13), không tích hợp partial mồ côi.
4. **Defaults** — sinh schema override (chỉ khóa của thành phần có thật; hiện tại:
   Cinnamon theme + icon theme, chưa có `gtk-theme`) và XML danh sách wallpaper,
   chép vào staging. Sinh gói `package/mintos-glass-theme.deb` (146 file dữ liệu ở lần
   chạy thử) — gói chỉ đặt mặc định, người dùng đổi được sau khi cài.
5. **Remaster (chỉ khi môi trường đủ)** — `xorriso -osirrox` extract ISO →
   `unsquashfs` live filesystem → chép nguyên cây staging → `glib-compile-schemas`
   trong rootfs → `mksquashfs -comp xz` → `xorriso` repack với
   `-boot_image isolinux keep -boot_image any keep`, map squashfs mới và manifest vào ISO.
   Map manifest vào ISO làm thay đổi nội dung có chủ đích; ISO nguồn không bị đụng.
6. **Kiểm chứng đầu ra** — chạy ISO Validator mức 1–3, tính SHA-256 ISO ra, so checksum
   ISO nguồn trước/sau để chứng minh file gốc nguyên vẹn (`source_unchanged`).

Không truyền mạng: build chỉ dùng ISO nguồn và tài nguyên trong repo đã có sẵn.

## 6. Workspace, log, manifest và dọn dẹp

Mỗi lần build có workspace riêng `build-iso-workspaces/mintos-glass-build-<UTC hoặc build-id>/`:

```text
.mintos-glass-workspace   # marker bắt buộc để clean chịu xóa
manifest.json             # nguồn, checksum, môi trường, thành phần, các bước, kết quả
logs/build.log            # log từng bước (UTC)
staging/rootfs/           # cây file sẽ vào rootfs (cùng nội dung gói .deb)
package/mintos-glass-theme.deb
extract/iso/, extract/rootfs/, output/   # chỉ có nội dung khi remaster thật chạy
```

- Build thất bại **không** tự xóa workspace. Muốn chẩn đoán: đọc `logs/build.log` +
  `manifest.json` (`result`: `BUILT` / `DRY-RUN` / `BLOCKED` / `FAIL`).
- Rollback của quá trình build = bỏ workspace và dùng lại ISO nguồn nguyên vẹn
  (checksum trước/sau trong manifest chứng minh nguồn không đổi). Không có thao tác
  “hoàn tác trên máy host” vì công cụ không cài gì lên host.
- Dọn dẹp an toàn: `clean` bắt buộc `--confirm DELETE`, kiểm tra workspace nằm trong
  `--workspace-parent` và có marker; từ chối xóa thư mục ngoài parent dù có marker giả.
- Tái tạo: cùng ISO nguồn + cùng commit + cùng công cụ cho staging/manifest tương đương,
  nhưng **không cam kết bit-for-bit** (timestamp trong .deb/tar-gzip, metadata squashfs,
  thứ tự/metadata do `xorriso` ghi là nguồn sai khác chưa kiểm soát).

## 7. Tích hợp giao diện, live session và mặc định sau cài đặt

Vị trí đích trong rootfs (tương đối, quyền sở hữu thuộc rootfs hệ thống khi đóng gói):

| Thành phần | Vị trí | Trạng thái |
|---|---|---|
| Cinnamon Dark Glass | `usr/share/themes/MintOS-Glass/cinnamon/cinnamon.css` + `assets/` (15 SVG) | ✅ Staging được, biên dịch thật |
| Icon theme | `usr/share/icons/MintOS-Glass/` (`index.theme` + scalable/symbolic, kế thừa Mint-Y…) | ✅ Staging được |
| Wallpaper | `usr/share/backgrounds/mintos-glass/` (4 SVG) + `usr/share/gnome-background-properties/mintos-glass.xml` | ✅ Tài nguyên có; XML là cơ chế đã xác minh tồn tại bộ đọc, chưa xác minh tự áp dụng |
| Mặc định theme/icon | `usr/share/glib-2.0/schemas/90_mintos-glass.gschema.override` | ✅ Sinh được; chưa biên dịch/chứng minh trên Mint thật |
| GTK theme, khung cửa sổ, Nemo/Mint apps, GTK4/libadwaita | (chưa có vị trí vì chưa có file) | ❌ BLOCKED — T06/T08/T09/T10, QA-09/QA-13 |

**Live session:** chiến lược là đặt tài nguyên + override ở cấp hệ thống trong squashfs
nên phiên live thấy ngay khi đăng nhập và trình cài đặt sao chép sang hệ thống đích.
Công cụ không giả định tên tài khoản live, không ghi vào home của tài khoản live và không
sửa file hệ thống nào ngoài cây staging. Tên tài khoản live, cơ chế khởi tạo live session
và hành vi sao chép của đúng bản Mint 22.3 **chưa xác minh trên máy đích** — phải kiểm
bằng Boot/Installation validation trước khi tuyên bố live hiển thị đúng Glass.

**Sau cài đặt:** cùng override đặt mặc định cho người dùng mới. Override chỉ là giá trị
mặc định GSettings: người dùng đổi theme trong Settings thì thắng, nâng cấp gói không
ghi đè lựa chọn cá nhân, tài khoản hiện có không bị chép cấu hình. Wallpaper mới chỉ
được *liệt kê* (chưa đặt làm nền mặc định) vì khóa GSettings nền chưa nằm trong danh
sách khóa đã xác minh của dự án.

## 8. Kiểm tra kết quả (5 mức)

Chạy: `python3 -m tools.iso_customizer validate <iso>`. Báo cáo riêng từng mức —
qua mức dưới không suy ra qua mức trên:

| Mức | Nội dung | Đã làm được |
|---|---|---|
| 1 File | Tồn tại, kích thước hợp lý (≥100 MiB với ISO Mint), SHA-256 | ✅ (fixture nhỏ cố ý FAIL mức này) |
| 2 Structure | ISO9660 PVD, El Torito boot record, `casper/filesystem.squashfs` | ✅ bằng trình đọc thuần |
| 3 Content | Tìm theme/icon/wallpaper MintOS Glass trên cây ISO | ⚠️ Một phần: tài nguyên nằm **trong** squashfs nên phải đối chiếu thêm `manifest.json` sau khi giải nén mới kết luận đầy đủ |
| 4 Boot | Boot thử live session (QEMU/VM), chụp màn hình desktop/panel/menu | ❌ NOT TESTED — thiếu QEMU và ISO thật |
| 5 Installation | Cài thử, tạo người dùng mới, kiểm tra theme/icon/wallpaper + đổi theme + rollback | ❌ NOT TESTED — cần VM/máy Mint 22.3 |

Kết quả chạy thử bằng fixture (ISO tổng hợp 49.152 byte, không phải ISO Mint):
`inspect-source` PASS ở mức nhận diện (22.3/amd64/El Torito/squashfs);
`validate` cho L1 FAIL (quá nhỏ), L2 PASS, L3 FAIL (chưa có nội dung Glass trên bề mặt ISO),
L4/L5 NOT TESTED; `build --dry-run` staging đủ Cinnamon+icon+wallpaper+override+gói .deb;
`build` thật dừng `BLOCKED` với mã thoát 3 và giữ workspace. Không kết quả nào trong đó
được coi là build/boot/install thành công.

## 9. Tái tạo quy trình trên máy đích

Trên máy Linux Mint 22.3 (hoặc VM) có ISO chính thức đã đối chiếu checksum:

```bash
git clone https://github.com/ThuyLinh6/mintos-glass.git && cd mintos-glass
make iso-check-env                                  # phải hết "thieu cong cu bat buoc"
python3 -m tools.iso_customizer inspect-source /path/to/linuxmint-22.3-cinnamon-64bit.iso --expected-sha256 <checksum-chinh-thuc>
python3 -m tools.iso_customizer build --source /path/to/linuxmint-22.3-cinnamon-64bit.iso \
  --output ~/mintos-glass-22.3.iso --workspace-parent ~/mintos-builds --build-id mint223-001
python3 -m tools.iso_customizer validate ~/mintos-glass-22.3.iso
cat ~/mintos-builds/mintos-glass-build-mint223-001/manifest.json
```

Sau đó mới làm mức 4–5: boot ISO trong QEMU/VM (snapshot trước), kiểm tra live desktop,
cài thử vào đĩa ảo, đăng nhập người dùng mới, đổi theme qua lại, ghi kết quả vào
`tests/manual/PROTOCOL.md`. Chỉ khi có log/ảnh đó mới được nâng trạng thái trong tài liệu này.

## 10. Khắc phục lỗi

| Triệu chứng | Nguyên nhân | Xử lý |
|---|---|---|
| `check-environment` thoát 3 | Thiếu `xorriso`/squashfs-tools (như môi trường hiện tại) | Cài gói ở Mục 2 trên máy build; công cụ không tự cài |
| `inspect-source` thoát 4 | Không phải ISO9660, thiếu El Torito/squashfs, sai phiên bản hoặc checksum | Đối chiếu checksum chính thức; kiểm tra đúng file/bản 22.3 64-bit |
| `build` thoát 5 | Biên dịch SCSS lỗi hoặc thành phần bắt buộc thiếu | Đọc `logs/build.log`; `--allow-partial` chỉ khi chấp nhận ISO thiếu thành phần và ghi rõ |
| `build` thoát 3 sau khi đã staging | Môi trường chặn ở bước remaster | Giữ workspace, xem `manifest.json` (`result: BLOCKED`); cài công cụ rồi chạy lại với `--build-id` mới |
| `build` thoát 2 vì output tồn tại | Chống ghi đè | Đổi `--output` hoặc `--force` khi chắc chắn |
| `validate` L3 FAIL trên ISO build được | Nội dung nằm trong squashfs | Giải nén squashfs của ISO ra và đối chiếu `staging`/`manifest.json`; đừng kết luận thiếu chỉ từ cây ISO |
| Muốn quay lui | — | Xóa workspace bằng `clean --confirm DELETE`, dùng lại ISO nguồn (checksum trong manifest chứng minh nguyên vẹn) |

## 11. Giới hạn và việc còn lại trước phát hành

1. Cài công cụ remaster trên máy đích và chạy build thật với ISO Mint 22.3 chính thức (mức 1–3 trên ISO thật).
2. T06/T08/T09/T10 hoàn thành theme GTK + decorations + libadwaita; bỏ `--allow-partial`, sửa QA-03…QA-13 liên quan.
3. Xác minh live session: tên/cơ chế tài khoản live, schema override có được nạp, wallpaper XML có được liệt kê, Dock GWL trong live.
4. Boot validation (mức 4) và Installation validation (mức 5) trên VM có snapshot, gồm người dùng mới, đổi theme, nâng cấp gói và rollback.
5. Cân nhắc chữ ký/checksum phát hành cho ISO đầu ra (hiện chỉ có SHA-256 cục bộ) và chính sách ghi `md5sum.txt` trong ISO nếu bản Mint đích yêu cầu.
