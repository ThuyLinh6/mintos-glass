# mintos-glass

Bộ giao diện desktop phong cách macOS hiện đại cho **Linux Mint 22.3 "Zena"** (Cinnamon 6.6).

Mục tiêu: **cải tiến giao diện, giữ nguyên chức năng hệ thống.** Dự án không viết lại Cinnamon,
không thay thế desktop environment, không patch mã nguồn hệ thống.

---

## Trạng thái hiện tại

> **Giai đoạn 0 — Khảo sát & Lập kế hoạch. CHƯA có mã theme.**

Repository đang ở trạng thái greenfield (commit `d010363`, chỉ có file README này).
Toàn bộ nội dung hiện có là **tài liệu kế hoạch**, chưa có stylesheet, asset hay công cụ cài đặt.

Mọi khẳng định kỹ thuật trong kế hoạch đều được đối chiếu với mã nguồn upstream thật
(`linuxmint/Cinnamon` @ `6.6.9`, `linuxmint/muffin` @ `6.6.3`, `linuxmint/nemo`,
`linuxmint/mint-themes`, `linuxmint/libadwaita`, `ricotz/plank`) và có trích dẫn đường dẫn file/dòng.

## Đọc kế hoạch

Bắt đầu từ **[docs/plan/README.md](docs/plan/README.md)**.

| Tài liệu | Nội dung |
|---|---|
| [01-survey.md](docs/plan/01-survey.md) | Khảo sát repo + **bảng 37 bằng chứng upstream** |
| [02-architecture.md](docs/plan/02-architecture.md) | Kiến trúc, cấu trúc thư mục, 7 quyết định ADR |
| [03-design-system.md](docs/plan/03-design-system.md) | Design token 3 tầng, generator, ràng buộc từng nền tảng |
| [04-work-breakdown.md](docs/plan/04-work-breakdown.md) | 15 task, đồ thị phụ thuộc, phân công 11 agent, **allow-list file từng task** |
| [05-testing-strategy.md](docs/plan/05-testing-strategy.md) | CI offline (chạy được thật) + protocol trên máy người dùng |
| [06-git-workflow.md](docs/plan/06-git-workflow.md) | Branch, 13 cổng CI, review, tích hợp, 3 cấp rollback |
| [07-acceptance-criteria.md](docs/plan/07-acceptance-criteria.md) | Tiêu chí nghiệm thu: Visual / Functional / Performance / Rollback |
| [08-risks.md](docs/plan/08-risks.md) | 16 rủi ro + 5 lo ngại đã bị loại trừ nhờ khảo sát |
| [09-verification-checklist.md](docs/plan/09-verification-checklist.md) | 10 mục cần xác minh trên máy thật (lệnh chỉ đọc) |

## Ba phát hiện định hình kiến trúc

1. **Theme Cinnamon của bên thứ ba phải HOÀN CHỈNH.** Cinnamon nạp stylesheet mặc định chỉ ở vai trò
   `fallback_stylesheet` mà theo `src/st/st-theme.c` là *non-cascading* — chỉ áp dụng khi stylesheet
   người dùng không trả về property nào **và** widget có cờ `important`. Không thể viết theme "ghi đè vài chỗ".
2. **Cinnamon 6.6 có backdrop blur thật (`-blur`) nhưng rất đắt.** `src/st/st-background-effect.c` chạy
   `blur_size` vòng lặp, mỗi vòng đọc ngược framebuffer GPU→CPU rồi tải lại texture.
   → Mặc định tắt blur; "glass" đạt được bằng rgba + gradient + hairline border + shadow.
3. **Muffin 6.6 không đọc `metacity-1/metacity-theme-3.xml`.** `MetaTheme` chỉ còn là struct rỗng;
   khung cửa sổ được vẽ bằng **GTK3 CSS** (`window.background.ssd > decoration > headerbar.titlebar.default-decoration`).
   → Không cần module metacity; module WM nằm trong GTK3.

## Nguyên tắc an toàn bất biến

1. Chỉ ghi vào `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`.
2. Không `sudo`, không `apt`/`dpkg`, không sửa file trong `/usr`, `/etc`.
3. Mọi khoá gsettings bị đổi đều được snapshot trước và khôi phục bằng **một** lệnh.
4. Không tuyên bố "đã kiểm thử" khi chưa có output thật.
5. Chưa xác minh thì ghi vào checklist, không đoán.

## Việc cần làm tiếp theo (chờ xác nhận phạm vi)

1. Chạy `docs/plan/09-verification-checklist.md` trên máy Linux Mint và điền `docs/verification/REPORT.md`.
2. Chốt 4 quyết định D-1…D-4 (dock, biến thể, accent, vị trí cài).
3. Chốt ADR-001 (nền Cinnamon) và ADR-007 (giấy phép — dự kiến GPL-3.0-or-later).
4. Khi đó mới bắt đầu T01 (scaffold + CI) và T02 (design tokens).

## Giấy phép

Chưa có `LICENSE` — sẽ được thêm ở task T01. Dự kiến **GPL-3.0-or-later** vì theme dẫn xuất từ
`data/theme/cinnamon-sass` của Cinnamon (GPL-2.0-or-later). Xem ADR-007 và rủi ro R7.
