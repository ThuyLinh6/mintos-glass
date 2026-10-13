# Quyết định phạm vi (đã chốt với người dùng ngày 2026-10-13)

Bốn câu hỏi quyết định trong `docs/plan/README.md` đã được trả lời.
File này là bản ghi có hiệu lực; nếu sau này đổi ý thì **sửa ở đây** và cập nhật ADR liên quan.

| ID | Câu hỏi | Quyết định | Hệ quả |
|---|---|---|---|
| **T00** | Có chạy được 10 mục xác minh trên máy Linux Mint ngay không? | **Chưa.** Người dùng sẽ chạy sau. Chỉ đạo: *"Hãy lập kế hoạch/CI offline trước."* | Mọi task phụ thuộc thông tin máy thật bị **gate**. Ưu tiên tuyệt đối cho phần offline: tokens, generator, lint, CI, test. Xem §"Thứ tự thực thi đã điều chỉnh" bên dưới. |
| **D-1** | Dock: hướng nào? | **Style applet `grouped-window-list@cinnamon.org` có sẵn.** Không dùng Plank ở Phase 1. | T11 thu hẹp: chỉ tài liệu cấu hình + token ánh xạ vào CSS Cinnamon (T04). `emitters_disabled` trong `00-meta.json` đã tắt output `dock.theme`. **Không cài gói nào.** |
| **D-2** | Phạm vi biến thể màu? | **Dark trước, Light sau.** | Light vẫn được **định nghĩa đầy đủ** trong `20-semantic-light.json` (để CI kiểm tra parity ngay từ đầu) nhưng `emit: false` → chưa sinh file, chưa build, chưa test thị giác. Phase 2 bật lên bằng 1 cờ. |
| **D-3** | Màu accent? | **Xanh Mint `#3ddc97`.** | Đã đưa vào `10-primitives.json → color.mint.500`. Hệ quả thiết kế quan trọng: chữ trên accent phải là **màu tối** (`text.on-accent = gray.950`), vì trắng trên `#3ddc97` chỉ ~1.9:1 → trượt AA. Có test khoá quyết định này (`test_on_accent_text_is_not_white_on_mint`). |
| **D-4** | Vị trí cài đặt? | *(không hỏi — áp dụng khuyến nghị có bằng chứng)* `~/.local/share/themes/MintOS-Glass` | Xem ADR-002 trong `docs/plan/02-architecture.md`. Bằng chứng: cả Cinnamon (`themeManager.js`), Cinnamon Settings (`cs_themes.py`) và libadwaita đã patch (`adw-style-manager.c`) đều quét đường dẫn user-level **trước** `/usr/share/themes`. Không cần root, rollback = xoá 1 thư mục. |

## Thứ tự thực thi đã điều chỉnh (do T00 bị hoãn)

Kế hoạch gốc trong `docs/plan/04-work-breakdown.md` có đường găng
`T00 → T01 → T02 → T03 → T04 → …`. Vì T00 bị hoãn, ta **đẩy lên trước** mọi việc
không cần máy thật, và **gate** phần còn lại.

```
LÀM NGAY (offline, có bằng chứng chạy được trong sandbox)
  T01  scaffold + CI + allow-list          ← XONG một phần (thiếu allowlist.py + task-allowlists.json)
  T02  design tokens + generator + contrast ← XONG (39 test xanh, `make check` OK)
  T13  test harness (phần offline)          ← XONG một phần (contrast + safety + token;
                                              thiếu st_properties.py / css_sanity.py)
  T12  installer/rollback CLI + test        ← viết được 100% offline (test bằng mock),
                                              chỉ khoan chạy trên máy thật

BỊ GATE — chờ kết quả T00
  T03  spike @import overlay        (cần máy thật để xác minh _st_theme_resolve_url)
  T04  Cinnamon theme               (cần biết Cinnamon version thật + session type)
  T06  GTK3 core                    (cần gtk3 version thật)
  T08  WM decorations               (cần ĐO chiều cao titlebar — E32b)
  T10  GTK4/libadwaita              (cần biết dir name thật + ADW_DEBUG_THEMES)
  T11  Dock                         (cần biết applet đang bật)
```

Việc gate này được **ghi thành dữ liệu**, không chỉ thành lời:
`design/tokens/00-meta.json → target.verified_on_target = false`, và 4 token
(`size.titlebar-height`, `gtk.titlebar.height`, `font.family`, `font.size-base-pt`)
đang mang cờ `"unverified": true` nên generator **từ chối emit** chúng.
Có test khoá: `test_target_is_marked_unverified`, `test_unverified_tokens_are_not_emitted`.

## Những gì đã XONG và có bằng chứng

| Hạng mục | Bằng chứng |
|---|---|
| Khảo sát repo + 37 mục bằng chứng upstream | `docs/plan/01-survey.md` (đường dẫn file/dòng cụ thể) |
| Bộ kế hoạch 9 tài liệu | `docs/plan/` |
| Design tokens 3 tầng (7 file JSON + schema) | `design/tokens/` |
| Generator (5 định dạng output, deterministic) | `make tokens` → 6 file; `test_deterministic_output` |
| Cổng contrast WCAG | đã bắt được **3 lỗi thật** trong bản token đầu tiên và đã sửa nguyên nhân gốc |
| Safety-path lint | `make safety` |
| CI workflow | `.github/workflows/ci.yml` |
| 39 test Tầng 1 (xanh) | `make check` → `Ran 39 tests … OK` |

## Việc kế tiếp (chờ xác nhận)

1. **T12** — viết installer/rollback CLI + test offline (mock gsettings). Không chạy trên máy thật.
2. **T13** — mở rộng test harness: `st_properties.py` (allow-list property St, fixture đã có trong
   `docs/plan/01-survey.md` §4), `css_sanity.py`, `generated_up_to_date.py`.
3. **T04 (một phần)** — có thể vendor `cinnamon-sass` @6.6.9 và dựng khung `overrides/` + CI coverage
   ngay bây giờ, nhưng **chưa** tinh chỉnh thị giác cho tới khi có T00.
   ⚠️ Việc này tạo ~2400 dòng mã GPL vendor vào repo → cần `LICENSE` trước (ADR-007).
4. **T00** — khi nào bạn sẵn sàng: chạy `docs/plan/09-verification-checklist.md`,
   dán output vào `docs/verification/REPORT.md`.
