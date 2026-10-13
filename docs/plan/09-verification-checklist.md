# 09 — Danh sách xác minh trên máy Linux Mint (chỉ đọc, không sửa gì)

Đây là phần **"ghi rõ điều cần xác minh thay vì tự bịa"**.
Agent **không** có quyền truy cập máy của bạn và **không** tự chạy những lệnh này.

Cách dùng: mở terminal trên Linux Mint 22.3, chạy từng khối lệnh, dán **nguyên văn** output vào
`docs/verification/REPORT.md` (kèm ngày giờ). Nếu một lệnh không chạy được, ghi rõ thông báo lỗi —
**đừng bỏ trống**, vì "không lấy được" cũng là thông tin quan trọng.

> ⚠️ Tất cả lệnh dưới đây **chỉ đọc**. Không có `sudo`, không `apt`, không `gsettings set`,
> không ghi file hệ thống. Lệnh duy nhất ghi file là `mkdir`/`tee` vào `/tmp` (mục 9, tuỳ chọn).

---

## 1. Hệ điều hành & phiên bản Mint

```bash
cat /etc/linuxmint/info
cat /etc/os-release
uname -a
```
**Cần xác nhận:** codename có phải `Zena` không, base có phải Ubuntu 24.04.x không, kernel bao nhiêu.

## 2. Phiên bản các thành phần theme sẽ tương tác

```bash
cinnamon --version
dpkg -l | grep -E '^ii\s+(cinnamon|cinnamon-core|cinnamon-desktop-data|muffin|nemo|mint-themes|libadwaita-1-0|gtk-4-common|libgtk-3-0t64|libgtk-4-1|cinnamon-settings-daemon|xdg-desktop-portal)\s' \
  | awk '{printf "%-32s %s\n", $2, $3}'
pkg-config --modversion gtk+-3.0 2>/dev/null || echo "pkg-config gtk+-3.0: KHÔNG có"
pkg-config --modversion gtk4       2>/dev/null || echo "pkg-config gtk4: KHÔNG có"
pkg-config --modversion libadwaita-1 2>/dev/null || echo "pkg-config libadwaita-1: KHÔNG có"
```
**Cần xác nhận:** Cinnamon có đúng 6.6.x không (kế hoạch này pin theo `6.6.9`),
Nemo bao nhiêu, `mint-themes` bao nhiêu (quyết định có `libadwaita-1.x` sẵn không),
libadwaita có phải bản Mint patch (`…mint…` trong version string) không.

## 3. Session: X11 hay Wayland

```bash
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
loginctl show-session "$XDG_SESSION_ID" -p Type -p Desktop 2>/dev/null
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-(không có)}"
```
**Vì sao cần:** hiệu ứng St/offscreen (bao gồm `-blur`) có thể hành xử khác nhau (R15).

## 4. Cấu hình theme hiện tại (baseline + giá trị rollback)

```bash
gsettings get org.cinnamon.theme name
gsettings get org.cinnamon.desktop.interface gtk-theme
gsettings get org.cinnamon.desktop.interface icon-theme
gsettings get org.cinnamon.desktop.interface cursor-theme
gsettings get org.cinnamon.desktop.interface gtk-color-scheme
gsettings get org.cinnamon.desktop.interface font-name
gsettings get org.cinnamon.desktop.interface text-scaling-factor
gsettings get org.cinnamon.desktop.wm.preferences theme
gsettings get org.cinnamon.desktop.wm.preferences button-layout
# có tồn tại schema gnome không? (quyết định mitigation cho R4)
gsettings list-keys org.gnome.desktop.interface 2>/dev/null | grep -x 'gtk-theme' \
  && gsettings get org.gnome.desktop.interface gtk-theme \
  || echo "org.gnome.desktop.interface: KHÔNG có schema hoặc không có key gtk-theme"
```
**Vì sao cần:** đây là giá trị **gốc** để snapshot rollback; và cho biết khoá `org.gnome.desktop.interface`
có tồn tại trên máy không (điều kiện để áp dụng mitigation R4).

## 5. libadwaita: theme có tới được app GTK4 không? (rủi ro R4/R5 — quan trọng nhất)

```bash
ls -1 /usr/share/themes/ | head -40
echo "--- Mint-Y có thư mục libadwaita nào? ---"
ls -1d /usr/share/themes/Mint-Y*/libadwaita-* 2>/dev/null || echo "Mint-Y: KHÔNG có thư mục libadwaita-*"
echo "--- libadwaita đã cài dò tên thư mục nào? ---"
strings /usr/lib/x86_64-linux-gnu/libadwaita-1.so.0 2>/dev/null | grep -E '^libadwaita-[0-9]' | sort -u \
  || echo "không đọc được libadwaita-1.so.0 (thử: dpkg -L libadwaita-1-0 | grep '\.so')"
echo "--- có LibAdwaita-Example không? (gói libadwaita-1-examples) ---"
ls -1 /usr/share/themes/LibAdwaita-Example/libadwaita-* 2>/dev/null || echo "LibAdwaita-Example: KHÔNG có"
```

Sau đó chạy **một app GTK4 bất kỳ đã cài sẵn** với debug bật, và dán output:
```bash
ADW_DEBUG_THEMES=1 <tên-app-gtk4> 2>&1 | head -40
```
App GTK4 thường có sẵn trên Mint: `gnome-font-viewer`, `gnome-console`, `gtk4-demo` (nếu có gói `gtk-4-examples`),
hoặc bất kỳ app Flatpak runtime GNOME. **Không cài thêm gì** — nếu không có app GTK4 nào, ghi rõ điều đó.

**Cần xác nhận:** chuỗi `Looking for theme '<TÊN>' in '<ĐƯỜNG DẪN>'` — tên theme nó tìm có đúng tên
trong `org.cinnamon.desktop.interface gtk-theme` không, và nó dò thư mục `libadwaita-1.5` hay `libadwaita-1.0`.

## 6. Cấu trúc theme Cinnamon mặc định đã cài

```bash
ls -l /usr/share/cinnamon/theme/
echo "--- có bao nhiêu selector trong theme mặc định? ---"
grep -cE '^\s*[.#a-zA-Z&][^{]*\{' /usr/share/cinnamon/theme/cinnamon.css 2>/dev/null || echo "không đọc được cinnamon.css"
echo "--- theme mặc định có dùng -blur không? ---"
grep -n -- '-blur' /usr/share/cinnamon/theme/cinnamon.css 2>/dev/null || echo "KHÔNG có -blur trong theme mặc định"
echo "--- applet đang bật ---"
gsettings get org.cinnamon enabled-applets 2>/dev/null
```
**Vì sao cần:** xác nhận E4/E7 trên máy thật và lấy danh sách applet đang chạy (phạm vi screenshot matrix).

## 7. Nemo: xác nhận selector & CSS nhúng

```bash
nemo --version 2>/dev/null || dpkg -l nemo | awk '/^ii/{print $3}'
ls -1 /usr/share/nemo/ 2>/dev/null | head
gsettings list-recursively org.nemo.desktop 2>/dev/null | head -30
```
**Vì sao cần:** phiên bản Nemo thật (E2b2 chưa chốt), và các khoá desktop-icon hiện tại
(màu chữ icon desktop) — ta **không** đổi chúng, chỉ cần biết để test tương phản.

## 8. Toolchain & môi trường sẵn có (quyết định installer làm được gì)

```bash
for c in python3 pysassc sassc sass inkscape optipng rsvg-convert glib-compile-resources \
         plank dconf-editor ffmpeg pidstat; do
  command -v $c >/dev/null 2>&1 && echo "CÓ   $c -> $(command -v $c)" || echo "KHÔNG $c"
done
python3 -c "import gi; gi.require_version('Gio','2.0'); from gi.repository import Gio; print('PyGObject Gio: OK')" 2>&1
dpkg -l plank 2>/dev/null | awk '/^ii/{print "plank đã cài, version "$3}' || echo "plank: chưa cài (→ KHÔNG dùng phương án Plank)"
fc-list : family 2>/dev/null | tr ',' '\n' | sort -u | head -30
```
**Vì sao cần:**
- `pysassc`/`sassc` có sẵn → build theme ngay trên máy người dùng được.
- PyGObject `Gio` OK → installer dùng API thay vì shell out `gsettings`.
- `plank` **chưa cài** → chốt D-1 theo hướng không dùng Plank (ràng buộc "không cài phần mềm").
- Danh sách font → chốt token `font-family` (không được đoán).

## 9. (Tuỳ chọn) Snapshot đầy đủ để làm baseline rollback

```bash
mkdir -p /tmp/mintos-glass-baseline
gsettings list-recursively > /tmp/mintos-glass-baseline/gsettings.txt
dconf dump /org/cinnamon/  > /tmp/mintos-glass-baseline/cinnamon.dconf
dconf dump /org/nemo/      > /tmp/mintos-glass-baseline/nemo.dconf
ls -l /tmp/mintos-glass-baseline/
```
Giữ thư mục này cho tới khi drill rollback (PROTOCOL §2.6) hoàn tất.

## 10. Ảnh chụp baseline (bắt buộc để so sánh "trước/sau")

Chụp và lưu vào `docs/verification/baseline/`:
1. Desktop đầy đủ (panel + applet đang bật).
2. App menu đang mở.
3. Một cửa sổ Nemo (icon view) + một cửa sổ có titlebar.
4. `cinnamon-settings` trang Themes.
5. Một app GTK4 (nếu có).

---

## Bảng đối chiếu: thông tin cần → quyết định bị chặn

| Mục | Nếu kết quả là… | Thì… |
|---|---|---|
| 1 | không phải 22.3 / không phải Cinnamon 6.6 | Dừng: kế hoạch này pin theo 6.6.9, phải khảo sát lại |
| 2 | `mint-themes` < 2.2.4 | Máy chưa có tham chiếu `libadwaita-*` → T10 phải tự dò tên thư mục (R5) |
| 2 | libadwaita **không** có chữ `mint` trong version | Máy dùng libadwaita Ubuntu gốc → **không theme được app GTK4**, phải hạ phạm vi T10 |
| 3 | Wayland | Thêm test matrix Wayland; cân nhắc tắt biến thể Blur cho tới khi đo xong |
| 4 | `org.gnome.desktop.interface` không tồn tại | Mitigation R4 bằng gsettings không khả thi → phải dựa vào portal |
| 5 | `ADW_DEBUG_THEMES` báo tìm theme khác tên | R4 thành hiện thực → kích hoạt ADR-003 |
| 5 | dò `libadwaita-1.0` chứ không phải `-1.5` | Đổi tên thư mục đích trong T10 |
| 6 | theme mặc định **có** dùng `-blur` | Đánh giá lại A6 (blur có thể an toàn hơn dự đoán) |
| 8 | `plank` chưa cài | Chốt D-1 = grouped-window-list; bỏ nhánh Plank |
| 8 | không có `pysassc`/`sassc` | Bắt buộc commit `dist/` (A8) — người dùng không tự build được |
| 8 | PyGObject Gio lỗi | Installer phải fallback sang binary `gsettings` |

Điền xong 10 mục này → cập nhật `docs/plan/08-risks.md` (đổi xác suất của R4, R5, R6, R13, R15 từ "ước lượng"
thành "đã xác minh") rồi mới bắt đầu T03/T04.
