# PROTOCOL — kiểm thử thủ công trên Linux Mint 22.3 / Cinnamon 6.6

**Task:** T13 · **Owner:** Agent J (QA)
**Trạng thái:** **BLOCKED** — chưa có máy Linux Mint 22.3 / Cinnamon 6.6 thật hoặc VM.
Tệp này là **checklist tái hiện được** để người CÓ môi trường phù hợp chạy sau,
đúng yêu cầu Phase 3 của Agent 7.

**Phạm vi phủ:** toàn bộ **50 tiêu chí** của `docs/plan/07-acceptance-criteria.md`
(V1–V15, F1–F16, P1–P9, R1–R10).
**Kết quả ghi vào:** `tests/manual/RESULTS-template.md` (chép thành
`tests/manual/RESULTS-<ngày>-<người chạy>.md`, **không sửa** template).
**Ảnh:** đặt tên theo `tests/manual/screenshot-matrix.csv` (26 bối cảnh, V3 đòi đúng
26 ảnh).

---

## 0. PHÂN BỔ THEO TẦNG — đọc trước khi chạy

`07-acceptance-criteria.md` gắn nhãn tầng cho từng tiêu chí. Đợt QA này đã kiểm được
toàn bộ phần `[T1]`; phần còn lại **bắt buộc** phải có máy thật.

| Tầng | Số tiêu chí | Trạng thái sau đợt QA này |
|---|---|---|
| `[T1]` offline/CI | **14** | Đã kiểm: **8 ĐẠT · 4 MỘT PHẦN · 1 KHÔNG ĐẠT (V2) · 1 CHỜ (P7)** |
| `[T2]` bắt buộc máy thật | **25** | **CHƯA KIỂM — BLOCKED** |
| `[T1+T2]` cả hai | **11** | Phần `[T1]` đã kiểm; phần `[T2]` **BLOCKED** |

> **36/50 tiêu chí (72%) không thể xác minh nếu không có máy thật.** Đây là con số
> quyết định khuyến nghị cuối cùng của báo cáo QA. Đừng đọc "361 tests OK" thành
> "theme chạy được".

### 0.1 Bốn mức bằng chứng — KHÔNG được đánh đồng

Mọi kết quả ghi vào RESULTS phải nêu rõ mức:

| Mức | Nghĩa | Đợt này đạt được? |
|---|---|---|
| **Static** | kiểm cấu trúc, cú pháp, tham chiếu, quy tắc, cấu hình | ✅ đã làm |
| **Build** | biên dịch/đóng gói thành công trong môi trường thật sự có sẵn | ✅ một phần (SCSS biên dịch được; **`dist/` chưa tạo được**) |
| **Runtime** | chạy thành phần trên môi trường mục tiêu và quan sát hành vi | ❌ **BLOCKED** |
| **Integration** | nhiều thành phần hoạt động cùng nhau trên môi trường mục tiêu | ❌ **BLOCKED** |

---

## 1. Điều kiện tiên quyết

1. Linux Mint **22.3** (base Ubuntu 24.04.3), Cinnamon **6.6**. Ghi lại số phiên bản
   thật: `cinnamon --version`, `cat /etc/linuxmint/info`, `uname -r`.
2. **Tài khoản người dùng thường, KHÔNG root.** Toàn bộ dự án thiết kế theo ADR-002
   (cài ở `~/.local/share/themes/`, không cần root). Nếu buộc phải dùng root để cài
   thì đó là **bug**, ghi lại chứ không bỏ qua.
3. Snapshot VM **trước khi** cài, để bước rollback (mục 6) có điểm quay về.
4. Ghi lại cấu hình màn hình: độ phân giải, **scale factor** (1.0 / 1.25 / 1.5 / 2.0),
   số monitor. V13 và P4 phụ thuộc các giá trị này.
5. Xác nhận gói có sẵn hay không — **quyết định 3 câu hỏi đang mở của đợt QA**:
   ```
   dpkg -l cinnamon-control-center      # -> quyết định QA-09/#c_box có dùng được không
   dpkg -l blueberry blueman            # -> quyết định nút Bluetooth có làm được không
   gdk-pixbuf-query-loaders | grep -i svg   # -> quyết định wallpaper SVG có hiển thị không
   ```
   Ghi cả ba kết quả vào RESULTS. Đây là **điều kiện để kiểm** của ba mục chưa xác
   minh quan trọng nhất.

---

## 2. Cài đặt

```
# KHÔNG chạy với quyền root.
mkdir -p ~/.local/share/themes ~/.local/share/icons
cp -r <repo>/dist/MintOS-Glass        ~/.local/share/themes/
cp -r <repo>/src/icons/MintOS-Glass   ~/.local/share/icons/
gtk-update-icon-cache ~/.local/share/icons/MintOS-Glass
```

> **CHẶN NGAY TỪ BƯỚC NÀY:** `dist/` hiện **không tồn tại** vì `make scss` chỉ
> `echo` ra một dòng TODO (QA-10) và `src/gtk-3.0/sass/gtk.scss` chưa có (QA-09).
> Nên **không thể chạy protocol này cho tới khi QA-09 và QA-10 được sửa.**
> Nếu bạn đang đọc và `dist/` vẫn chưa có: dừng lại, ghi `BLOCKED` cho toàn bộ mục
> 2 trở đi, và chuyển bug về T06/T01. Đừng tự tay biên dịch rồi coi như đã đóng gói
> — kết quả đó không phản ánh quy trình thật.

**Kiểm tra sau khi cài:**
- [ ] `~/.local/share/themes/MintOS-Glass/cinnamon/cinnamon.css` tồn tại
- [ ] `~/.local/share/themes/MintOS-Glass/gtk-3.0/gtk.css` tồn tại (**điều kiện V2**)
- [ ] `~/.local/share/icons/MintOS-Glass/index.theme` tồn tại
- [ ] **không** có tệp nào được ghi ngoài hai đường trên (F2):
      kiểm bằng `find ~ -newer <mốc thời gian> -type f` sau khi cài

---

## 3. Nhóm Giao diện — V1 → V15

| ID | Tầng | Cách kiểm | Bằng chứng phải thu | ĐẠT khi |
|---|---|---|---|---|
| **V1** | T2 | Settings → Themes; xem cả **3** mục Themes / GTK / Icons | ảnh `01-settings-themes.png` | `MintOS-Glass` hiện ở cả ba |
| **V2** | T1 | `ls dist/MintOS-Glass/gtk-3.0/gtk.css` | đường dẫn + `ls` | tệp tồn tại. **HIỆN TẠI: KHÔNG ĐẠT** (QA-09) |
| **V3** | T1+T2 | chụp đủ **26 bối cảnh** trong `screenshot-matrix.csv`, soi từng ảnh tìm nền đen/trắng thô hoặc chữ mất | 26 ảnh + bảng đối chiếu | 0 widget không được style |
| **V4** | T1 | `python3 -m unittest tests.lint.test_cinnamon_coverage` | log | 527 selector vendor có đủ. **ĐÃ ĐẠT** |
| **V5** | T1 | `python3 tools/lint/st_properties.py` | log | 0 property St không hợp lệ. **ĐÃ ĐẠT** |
| **V6** | T1 | như V5 (bài `hardcoded`) | log | 0 màu/radius hard-code. **ĐÃ ĐẠT** |
| **V7** | T1+T2 | `python3 tools/lint/contrast.py` **+** đo trên ảnh chụp thật (lấy mẫu màu bằng công cụ đo, không ước lượng bằng mắt) | log + ảnh + số đo | text×surface ≥ 4.5:1, UI ≥ 3:1. **MỘT PHẦN**: đã biết token `nemo.desktop.label.selected.text #f5f5f5` FAIL 2.29–2.53:1 |
| **V8** | T1+T2 | với mỗi control tương tác, đưa chuột qua / bấm / Tab tới / tắt control, chụp 4+2 trạng thái | ảnh theo cặp | đủ normal/hover/active/focus + `:insensitive` + `:backdrop` |
| **V9** | T1+T2 | chỉ áp dụng nếu D-2 mở khoá Light | — | **HIỆN TẠI: N/A** (D-2 = dark_first) |
| **V10** | T2 | đặt lần lượt 4 wallpaper của T16, xem nhãn icon desktop trên nền sáng nhất và tối nhất của mỗi cái | 8 ảnh + số đo | đọc được trên cả hai. Đã ĐO trước: nhãn `#eeeeee` đạt 12.67–16.01:1 |
| **V11** | T2 | chụp titlebar SSD (muffin) và CSD (GTK) cạnh nhau | ảnh ghép | cùng chiều cao, cùng vị trí nút, cùng bán kính. **CHƯA CÓ mã SSD** — T08 chưa làm, nên dự kiến KHÔNG ĐẠT |
| **V12** | T1+T2 | đổi `ButtonLayout` sang quy ước macOS, chụp; rồi **đổi lại** và chụp | 2 ảnh + gsetting trước/sau | nút theo layout đã bật, và **không tự đổi** layout của người dùng |
| **V13** | T2 | chụp cùng một widget ở scale 1.0 / 1.25 / 2.0 | 3 ảnh | asset sắc ở cả ba. Rủi ro đã biết: nét 1.5 trên lưới 24 ở 16px |
| **V14** | T1 | `python3 tools/lint/st_properties.py` (bài `forbid-blur`) | log | không có `-blur` trong biến thể chuẩn. **ĐÃ ĐẠT** |
| **V15** | T2 | xem nội dung dài: thu nhỏ cửa sổ Settings/Nemo, mở danh sách dài | ảnh | không tràn, không cắt, scrollbar đúng |

---

## 4. Nhóm Chức năng — F1 → F16

| ID | Tầng | Cách kiểm | ĐẠT khi |
|---|---|---|---|
| **F1** | T1 | `git diff --stat` so với upstream Cinnamon/Nemo: xác nhận **0** tệp applet, 0 tệp schema, 0 tệp mã C bị sửa | **ĐÃ ĐẠT** — chỉ có CSS + asset + tài liệu |
| **F2** | T1 | `python3 tools/lint/safety_paths.py` + kiểm tra thực tế sau khi cài (mục 2) | **ĐÃ ĐẠT** ở mức static; phần thực tế cần máy thật |
| **F3** | T1 | `grep -rE 'apt\|dpkg\|sudo' src/ dist/` — phải rỗng; và xác nhận quá trình cài không hỏi mật khẩu | **ĐÃ ĐẠT** ở mức static |
| **F4** | T2 | **BLOCKER TỰ ĐỘNG.** Đăng nhập lại, mở panel/menu/notification, duyệt file, đổi theme, đăng nhập lại lần nữa | desktop khởi động được và dùng được bình thường |
| **F5** | T1+T2 | trong Nemo: mở thư mục, đổi chế độ icon/list, mount và unmount một USB, xoá một tệp, đổi tên, kéo-thả | mọi thao tác hoạt động **y như theme mặc định** |
| **F6** | T2 | GWL: bấm mở app, chuyển giữa các cửa sổ của cùng app, ghim/bỏ ghim, menu chuột phải, Super+số | không mất khả năng chuyển cửa sổ / ghim / quản lý cửa sổ |
| **F7** | T1+T2 | mở **từng trang** Settings thuộc tầng 1 (31 trang), đổi một thiết lập, đóng, mở lại xem có lưu không | mọi trang mở được và **lưu được cấu hình** |
| **F8** | T1 | `grep -rn 'NemoIconContainer-activate-prelight' src/` — chỉ được ra comment | **ĐÃ ĐẠT** (chỉ có ở `_apps-nemo.scss:505`, là comment) |
| **F9** | T2 | **BLOCKER TỰ ĐỘNG.** applet: sound (đổi volume, đổi đầu ra), power (slider độ sáng), network (bật/tắt Wi-Fi), notifications | **mỗi nút tác động chức năng THẬT**, không chỉ đổi màu |
| **F10** | T2 | Settings → Night Light: kéo slider nhiệt độ màu | **ĐÃ BIẾT TRƯỚC SẼ LỆCH TÔNG**: dải trắng→cam bị app khoá ở priority 600 (`cs_nightlight.py:31-53`). Chức năng phải chạy; **màu sắc sai là giới hạn đã ghi, không phải bug mới** |
| **F11** | T2 | Settings → Network / Color / Graphics Tablet có hiện không | phụ thuộc gói `cinnamon-control-center` (mục 1.5). Nếu không hiện → ghi rõ, **không đổ lỗi cho theme** |
| **F12** | T1+T2 | mở 3 app tầng 3 từ Settings: Bluetooth, Printers, Users and Groups | app mở được. **Giao diện của chúng KHÔNG do theme này kiểm soát** — ghi nhận thực tế, không chấm ĐẠT/KHÔNG ĐẠT cho phần nhìn |
| **F13** | T2 | chọn `MintOS-Glass` làm icon theme; mở menu, Nemo, Settings, hộp thoại chọn tệp | icon hiện đúng ở cả bốn nơi; icon thiếu thì fallback về Mint-Y chứ **không biến mất** |
| **F14** | T2 | kiểm 47 icon `cs-*` + 4 icon danh mục trên lưới trang chính **và** trong list/sidebar ở cỡ nhỏ | đúng icon, không rơi về Mint-Y. Rủi ro đã biết: nét 1.4–1.5 ở 16px |
| **F15** | T2 | đổi theme sang theme mặc định rồi đổi lại; đăng xuất/đăng nhập | trạng thái đúng sau mỗi lần đổi |
| **F16** | T2 | chạy thử trên phiên Wayland nếu có, và trên phiên X11 | ghi rõ kết quả từng phiên; **không suy diễn** từ phiên này sang phiên kia |

---

## 5. Nhóm Hiệu năng — P1 → P9

Đo bằng lệnh, **không ước lượng bằng mắt**. Ghi số thô vào RESULTS.

| ID | Tầng | Cách đo | Ngưỡng |
|---|---|---|---|
| **P1** | T2 | `cinnamon-looking-glass` → mục Perf; hoặc `journalctl -b \| grep -i cinnamon` tìm cảnh báo | không có vòng lặp redraw bất thường |
| **P2** | T2 | mở 10 cửa sổ, vào Scale, đo thời gian bằng đồng hồ bấm + quay màn hình | so sánh được với theme mặc định |
| **P3** | T2 | mở menu, lịch, notification, đo độ trễ cảm nhận và đối chiếu log | không trễ hơn theme mặc định một cách thấy được |
| **P4** | T2 | `top`/`htop` theo dõi `cinnamon` và `muffin` khi nghỉ và khi mở popup | CPU khi nghỉ không tăng so với theme mặc định |
| **P5** | T2 | bộ nhớ: `smem`/`ps -o rss` cho `cinnamon` trước và sau khi áp theme | ghi số, chưa có ngưỡng cam kết |
| **P6** | T1 | `wc -c` trên CSS đã biên dịch | `cinnamon.css` ≤ 400 KB → **ĐÃ ĐẠT: 90.8 KB**. `gtk.css` ≤ 500 KB → **KHÔNG ĐO ĐƯỢC** (chưa tồn tại). Tổng `dist/` ≤ 8 MB → **KHÔNG ĐO ĐƯỢC** |
| **P7** | T1 | `time make scss` (build `src/` → `dist/`) | ≤ 60s → **BLOCKED**: `make scss` không build gì (QA-10) nên không có gì để đo |
| **P8** | T1 | `python3 tools/tokens/generate.py --scheme all --check` và thử bơm một giá trị blur vượt trần | **ĐÃ ĐẠT** — `check_blur_cap` trả 8 lỗi khi bơm blur=99 với `MAX_ALLOWED=6`. Đã kiểm bằng thực nghiệm, không phải đọc mã |
| **P9** | T2 | đo thời gian đăng nhập từ màn hình login tới desktop sẵn sàng, so với theme mặc định | ghi số, chưa có ngưỡng cam kết |

**Chi tiết cách đo và cách đọc số:** `docs/testing/perf-benchmark.md`.

---

## 6. Nhóm Rollback — R1 → R10

| ID | Tầng | Cách kiểm | ĐẠT khi |
|---|---|---|---|
| **R1** | T2 | **BLOCKER TỰ ĐỘNG.** làm đúng trình tự rollback rồi **đăng nhập lại** | desktop vẫn khởi động và dùng được |
| **R2** | T1 | xác nhận không có tệp hệ thống nào bị sửa: `git status` sạch + không có gì ngoài `~/.local/share/{themes,icons}` | **ĐÃ ĐẠT** ở mức static |
| **R3** | T1+T2 | rollback theme Cinnamon qua Settings → Themes | về đúng theme trước đó |
| **R4** | T1+T2 | rollback GTK theme qua Settings → Themes | về đúng theme trước đó |
| **R5** | T1+T2 | rollback icon theme — **theo đúng thứ tự an toàn**: đặt lại gsetting `icon-theme` **TRƯỚC**, rồi mới xoá thư mục | không có trạng thái gsetting trỏ tới theme không tồn tại |
| **R6** | T1 | đếm số gsetting mà dự án chạm: phải ≤ 6 khoá và nằm trong danh sách đóng của T12 | **BLOCKED** — T12 chưa tồn tại nên chưa có gì chạm khoá nào |
| **R7** | T2 | xoá hoàn toàn `~/.local/share/themes/MintOS-Glass` và `~/.local/share/icons/MintOS-Glass`, đăng nhập lại | hệ thống hoạt động bình thường, không còn dấu vết |
| **R8** | T1+T2 | chạy trình cài đặt **hai lần liên tiếp** (idempotent) | kết quả giống hệt nhau, không nhân đôi, không lỗi. **BLOCKED**: chưa có trình cài đặt (QA-11) |
| **R9** | T2 | snapshot gsetting trước khi áp theme, so sau khi rollback | trùng khớp 100% |
| **R10** | T2 | tạo một **người dùng mới**, đăng nhập lần đầu | cấu hình mặc định đúng như mong muốn. **BLOCKED**: chưa có tệp cấu hình mặc định nào (QA-11) |

---

## 7. Gate chặn release (từ `07-acceptance-criteria.md` §5)

| Gate | Cần | Trạng thái sau đợt QA |
|---|---|---|
| **G0 → v0.1.0** | V1–V8, V14; F1–F5; P1, P6, P7; R2, R8 | **CHƯA ĐẠT.** Thiếu V1/V3/V8 (T2), **V2 FAIL**, F4/F5 (T2), P1 (T2), **P7 BLOCKED**, R8 BLOCKED |
| **G1 → v0.2.0** | thêm V9–V13; F7, F9, F13, F14; P2–P4; R1, R3–R6, R10 | CHƯA ĐẠT |
| **G2 → v0.3.0** | thêm F11, F12 | CHƯA ĐẠT |
| **G3 → v0.5.0** | thêm P5, P8, P9, V15 | **P8 ĐÃ ĐẠT**; còn lại CHƯA |
| **G4 → v1.0.0** | tất cả | CHƯA ĐẠT |

**Blocker tự động** (bất kỳ mục nào vi phạm → dừng release, rollback, mở incident):
F1, F2, F3, F4, F9, R1.
Trong đó **F1, F2, F3 đã ĐẠT ở mức static**; **F4, F9, R1 chưa kiểm được** vì cần
máy thật.

---

## 8. Ghi kết quả

1. Chép `RESULTS-template.md` thành `RESULTS-<YYYY-MM-DD>-<người chạy>.md`.
2. Mỗi dòng: `ID | mức bằng chứng (Static/Build/Runtime/Integration) | ĐẠT/KHÔNG/BLOCKED/N-A | số đo hoặc đường dẫn ảnh | ghi chú`.
3. Ảnh đặt tên **đúng** theo cột `file` của `screenshot-matrix.csv`.
4. **Không** ghi ĐẠT cho một mục chỉ vì "trông có vẻ đúng". Nếu không đo được, ghi
   `BLOCKED` kèm lý do.
5. Bug mới phát hiện: thêm vào `tests/fixtures/qa-bug-register.txt` theo đúng định
   dạng 8 cột, ID tiếp theo, kèm bằng chứng tồn tại thật trong repo.
