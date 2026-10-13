# RESULTS — kết quả kiểm thử thủ công trên máy thật

> **CHÉP TỆP NÀY** thành `RESULTS-<YYYY-MM-DD>-<người chạy>.md` rồi điền.
> **KHÔNG sửa template** — nó phải giữ nguyên để lần chạy sau so sánh được.
>
> Hướng dẫn chạy: `tests/manual/PROTOCOL.md` · danh sách ảnh:
> `tests/manual/screenshot-matrix.csv` (26 bối cảnh, V3 đòi đúng 26 ảnh)
>
> ---------------------------------------------------------------------------
> BA QUY TẮC KHI ĐIỀN, quan trọng hơn bản thân cái bảng
> ---------------------------------------------------------------------------
> 1. **Ghi rõ MỨC bằng chứng** cho từng dòng: `Static` / `Build` / `Runtime` /
>    `Integration`. Bốn mức này KHÔNG được đánh đồng. "CSS biên dịch được" là
>    Build, không phải Runtime. "Trông đúng" không phải bằng chứng.
> 2. **Không ghi ĐẠT nếu không đo được.** Ghi `BLOCKED` kèm lý do và điều kiện để
>    kiểm sau. Một bảng toàn ĐẠT mà không có số đo thì vô giá trị.
> 3. **Bug mới** -> thêm vào `tests/fixtures/qa-bug-register.txt` theo định dạng 8
>    cột, ID tiếp theo, kèm bằng chứng tồn tại thật. Không mô tả bug bằng lời trong
>    tệp kết quả rồi để đó.
>
> Cột "Đã kiểm ở đợt QA tĩnh" được điền SẴN cho những mục `[T1]` đã có bằng chứng
> trong đợt này (xem `tests/fixtures/qa-bug-register.txt` và báo cáo QA). Người chạy
> trên máy thật KHÔNG cần làm lại chúng, nhưng PHẢI kiểm chứng lại nếu bản repo đã
> thay đổi kể từ đó.
> ---------------------------------------------------------------------------

**Người chạy:** ……………………………  **Ngày:** ………………
**Máy / VM:** ……………………………  **Mint:** ………………  **Cinnamon:** ………………  **Kernel:** ………………
**Màn hình:** ………………  **Scale:** ………………  **Phiên:** X11 / Wayland
**Snapshot trước khi cài:** có / không — nếu không thì **dừng lại**, mục 6 (rollback) sẽ không kiểm được

**Ba gói quyết định các câu hỏi đang mở (PROTOCOL mục 1.5):**

| Kiểm | Kết quả | Ảnh hưởng tới |
|---|---|---|
| `dpkg -l cinnamon-control-center` | ………… | Settings có trang Network/Color/Tablet không; hook `#c_box` có bao giờ được dùng không |
| `dpkg -l blueberry blueman` | ………… | nút Bluetooth có làm được không (hiện KHÔNG có applet bundled) |
| `gdk-pixbuf-query-loaders \| grep -i svg` | ………… | wallpaper SVG có hiển thị được không (rủi ro lớn nhất của T16) |

---

## Bảng kết quả — 50 tiêu chí


### 1. Giao diện (Visual)

| ID | Tiêu chí (tóm tắt) | Tầng | Kết quả | Mức bằng chứng | Số đo / đường dẫn ảnh | Ghi chú |
|---|---|---|---|---|---|---|
| V1 | Theme xuất hiện trong Cinnamon Settings ở cả 3 mục: Themes, GTK, Cinnamon | T2 | ☐ | ☐ | ☐ | |
| V2 | dist/MintOS-Glass/ có gtk-3.0/gtk.css (điều kiện để hiện trong picker, E19) | T1 | KHÔNG ĐẠT · static (dist/ và src/gtk-3.0/sass/gtk.scss chưa tồn tại — QA-09/QA-10) | static | ☐ | |
| V3 | Không có widget nào không được style (nền đen/trắng thô, chữ mất) trong 26 bối | T1+T2 | ☐ | ☐ | ☐ | |
| V4 | Mọi selector của Cinnamon 6.6 stock theme đều có mặt trong output (E6) | T1 | ĐẠT · static | static | ☐ | |
| V5 | 0 property St không hợp lệ trong cinnamon.css | T1 | ĐẠT · static | static | ☐ | |
| V6 | Đúng token: không giá trị màu/bán kính hard-code ngoài design/tokens/ | T1 | ĐẠT · static | static | ☐ | |
| V7 | Contrast: text × surface ≥ 4.5:1 (body), ≥ 3:1 (large text & UI component) | T1 | MỘT PHẦN · static (token selected.text #f5f5f5 FAIL 2.29-2.53:1 đã biết) | static | ☐ | |
| V8 | Đủ 4 trạng thái cho mọi control tương tác: normal / hover / active / focus, cộ | T1+T2 | ☐ | ☐ | ☐ | |
| V9 | Dark và light (nếu D-2 = cả hai) nhất quán: cùng radius, cùng spacing, cùng hi | T1+T2 | ☐ | ☐ | ☐ | |
| V10 | Icon desktop Nemo đọc được trên wallpaper sáng và tối | T2 | ☐ | ☐ | ☐ | |
| V11 | Titlebar SSD (muffin) và CSD (GTK) cùng ngôn ngữ: cùng chiều cao, cùng vị trí  | T2 | ☐ | ☐ | ☐ | |
| V12 | Nút cửa sổ theo quy ước macOS khi bật ButtonLayout tương ứng; không tự đổi lay | T1+T2 | ☐ | ☐ | ☐ | |
| V13 | Asset sắc ở scale 1.0 / 1.25 / 2.0 | T2 | ☐ | ☐ | ☐ | |
| V14 | Không dùng -blur trong biến thể chuẩn; biến thể -Blur chỉ dùng -blur ≤ 6 và kh | T1 | ĐẠT · static | static | ☐ | |
| V15 | Theme vẫn đẹp và dùng được khi GLSL không khả dụng (E12 — blur bị bỏ qua) | T2 | ☐ | ☐ | ☐ | |

### 2. Chức năng (Functional)

| ID | Tiêu chí (tóm tắt) | Tầng | Kết quả | Mức bằng chứng | Số đo / đường dẫn ảnh | Ghi chú |
|---|---|---|---|---|---|---|
| F1 | 0 thay đổi hành vi. Theme chỉ là CSS + asset; không patch Cinnamon, không sửa  | T1 | ĐẠT · static | static | ☐ | |
| F2 | Không ghi gì ngoài ~/.local/share/themes/MintOS-Glass và ~/.local/state/mintos | T1 | ĐẠT · static | static | ☐ | |
| F3 | Không cần root, không apt/dpkg, không tải gì | T1 | ĐẠT · static | static | ☐ | |
| F4 | Toàn bộ 20 thao tác trong PROTOCOL §2.4 hoạt động y hệt trước và sau khi cài | T2 | ☐ | ☐ | ☐ | |
| F5 | 33 applet bundled (E14) hiển thị đúng, kể cả 2 applet mới của 6.6: favorites@, | T1+T2 | ☐ | ☐ | ☐ | |
| F6 | App menu mới của Cinnamon 6.6 (sidebar avatar/places/favorites, search) đủ sty | T2 | ☐ | ☐ | ☐ | |
| F7 | Nemo: icon view, list view, compact view, F3 dual-pane, rename, floating bar,  | T1+T2 | ☐ | ☐ | ☐ | |
| F8 | Không ghi đè -NemoIconContainer-activate-prelight-icon-label (giữ hành vi gốc) | T1 | ĐẠT · static | static | ☐ | |
| F9 | Khoá màn hình / screensaver: mở được, nhập được mật khẩu, unlock thành công | T2 | ☐ | ☐ | ☐ | |
| F10 | On-screen keyboard và IBus popup dùng được | T2 | ☐ | ☐ | ☐ | |
| F11 | App GTK4/libadwaita nhận theme (libadwaita-1.5/) hoặc ghi nhận rõ là không nhậ | T2 | ☐ | ☐ | ☐ | |
| F12 | base-hc.css tồn tại và high-contrast mode không làm theme bị bỏ qua | T1+T2 | ☐ | ☐ | ☐ | |
| F13 | Đổi theme sang Mint-Y rồi đổi lại MintOS-Glass hoạt động, không cần logout | T2 | ☐ | ☐ | ☐ | |
| F14 | Không phá cinnamon-settings, mintupdate, mintinstall, xed, xplayer, xreader, x | T2 | ☐ | ☐ | ☐ | |
| F15 | text-scaling-factor 1.25 và fractional scaling không làm vỡ layout | T2 | ☐ | ☐ | ☐ | |
| F16 | Cả X11 và Wayland (nếu máy hỗ trợ) đều dùng được; nếu chỉ test 1 → ghi rõ phạm | T2 | ☐ | ☐ | ☐ | |

### 3. Hiệu năng (Performance)

| ID | Tiêu chí (tóm tắt) | Tầng | Kết quả | Mức bằng chứng | Số đo / đường dẫn ảnh | Ghi chú |
|---|---|---|---|---|---|---|
| P1 | Không có lỗi/warning parse CSS trong log (Did not find color property, Unrecog | T2 | ☐ | ☐ | ☐ | |
| P2 | CPU% của cinnamon khi nghỉ ≤ baseline Mint-Y + 2 điểm % (trung vị 3 lần đo, 10 | T2 | ☐ | ☐ | ☐ | |
| P3 | Thời gian mở menu ≤ baseline + 33 ms (trung vị 10 lần) | T2 | ☐ | ☐ | ☐ | |
| P4 | Không stutter khi kéo/thả cửa sổ, khi mở Expo/Scale | T2 | ☐ | ☐ | ☐ | |
| P5 | Biến thể -Blur (-blur: 4, menu/OSD): CPU% tăng ≤ 8 điểm % so với biến thể khôn | T2 | ☐ | ☐ | ☐ | |
| P6 | Kích thước file: cinnamon.css ≤ 400 KB; gtk.css ≤ 500 KB; tổng dist/ ≤ 8 MB (k | T1 | MỘT PHẦN · static (cinnamon.css 90.8KB ĐẠT; gtk.css và dist/ KHÔNG ĐO ĐƯỢC) | static | ☐ | |
| P7 | Thời gian build theme (từ src/ → dist/) ≤ 60s trên máy dev | T1 | BLOCKED · make scss không build gì (QA-10) nên không có gì để đo | static | ☐ | |
| P8 | Không dùng -blur trên bề mặt > 600×400 px; generator từ chối token vi phạm | T1 | ĐẠT · build (check_blur_cap trả 8 lỗi khi bơm blur=99, MAX_ALLOWED=6) | static | ☐ | |
| P9 | Ghi lại cơ sở lý thuyết chi phí blur (E11) trong báo cáo perf, kèm phép tính c | T2 | ☐ | ☐ | ☐ | |

### 4. Khả năng rollback

| ID | Tiêu chí (tóm tắt) | Tầng | Kết quả | Mức bằng chứng | Số đo / đường dẫn ảnh | Ghi chú |
|---|---|---|---|---|---|---|
| R1 | rollback khôi phục chính xác toàn bộ khoá đã đổi: gsettings list-recursively d | T2 | ☐ | ☐ | ☐ | |
| R2 | Sau rollback, không còn dấu vết: ~/.local/share/themes/MintOS-Glass đã xoá | T2 | ĐẠT · static (safety_paths OK; phần thực tế cần máy thật) | static | ☐ | |
| R3 | rollback idempotent — chạy lần 2 không lỗi, không đổi gì thêm | T1+T2 | ☐ | ☐ | ☐ | |
| R4 | --dry-run có cho mọi lệnh ghi, và không tạo bất kỳ thay đổi nào | T1+T2 | ☐ | ☐ | ☐ | |
| R5 | Snapshot được tạo trước khi đổi khoá, có timestamp, lưu ở ~/.local/state/minto | T1+T2 | ☐ | ☐ | ☐ | |
| R6 | Chỉ chạm danh sách khoá đóng (5–6 khoá, xem 04-work-breakdown.md T12 ràng buộc | T1 | BLOCKED · T12 chưa tồn tại nên chưa có gì chạm khoá gsetting nào | static | ☐ | |
| R7 | Cấp 2 (rollback thủ công không cần CLI của ta) được tài liệu hoá và đã thử | T2 | ☐ | ☐ | ☐ | |
| R8 | Cài theme không làm mất theme cũ: không ghi đè, không đổi tên, không xoá bất k | T1+T2 | ☐ | ☐ | ☐ | |
| R9 | Nếu CLI crash giữa chừng, hệ thống vẫn trở về được bằng Cấp 2 | T2 | ☐ | ☐ | ☐ | |
| R10 | Toàn bộ thao tác rollback ≤ 60 giây kể từ lúc người dùng quyết định | T2 | ☐ | ☐ | ☐ | |


---

## Gate release (07-acceptance-criteria.md §5)

| Gate | Cần | Kết quả | Ghi chú |
|---|---|---|---|
| G0 → v0.1.0 | V1–V8, V14; F1–F5; P1, P6, P7; R2, R8 | ☐ | |
| G1 → v0.2.0 | thêm V9–V13; F7, F9, F13, F14; P2–P4; R1, R3–R6, R10 | ☐ | |
| G2 → v0.3.0 | thêm F11, F12 | ☐ | |
| G3 → v0.5.0 | thêm P5, P8, P9, V15 | ☐ | P8 đã ĐẠT ở mức build |
| G4 → v1.0.0 | tất cả | ☐ | |

**Blocker tự động** — bất kỳ mục nào vi phạm thì DỪNG release, rollback, mở incident:

| ID | Kết quả | Nếu vi phạm |
|---|---|---|
| F1 (0 thay đổi hành vi) | ☐ | dừng |
| F2 (không ghi ngoài 2 đường cho phép) | ☐ | dừng |
| F3 (không root, không apt/dpkg, không tải) | ☐ | dừng |
| F4 (desktop khởi động và dùng được) | ☐ | dừng + rollback |
| F9 (nút applet tác động chức năng thật) | ☐ | dừng |
| R1 (rollback xong vẫn dùng được) | ☐ | dừng |

---

## Bug phát hiện khi chạy thủ công

Thêm vào `tests/fixtures/qa-bug-register.txt`, KHÔNG chỉ ghi ở đây.

| ID mới | Mức | Thành phần | Owner (Txx) | Bằng chứng |
|---|---|---|---|---|
| | | | | |

---

## Kết luận của người chạy

- Khuyến nghị: **PASS** / **PASS WITH LIMITATIONS** / **BLOCKED**
- Lý do (phải nêu số liệu, không nêu cảm nhận):
- Những mục BLOCKED và **điều kiện cụ thể** để gỡ:
