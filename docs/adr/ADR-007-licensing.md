# ADR-007 · Giấy phép của MintOS Glass

- Trạng thái: **ĐỀ XUẤT — chờ người dùng xác nhận** (chưa có file `LICENSE` trong repo)
- Ngày: 2026-10-13
- Liên quan: rủi ro R7, `NOTICE.md`, ADR-001

## Vấn đề

ADR-001 phương án A yêu cầu vendor `data/theme/cinnamon-sass` của Cinnamon vào repo.
Đó là **tác phẩm dẫn xuất**, nên giấy phép của repo bị ràng buộc.

## Bằng chứng đã xác minh (2026-10-13, qua GitHub API)

| Nguồn | Giấy phép | Bằng chứng |
|---|---|---|
| `linuxmint/Cinnamon` (toàn bộ, gồm `data/theme/cinnamon-sass/`) | **GPL-2.0-or-later** | `README.rst` mục License: *"Cinnamon is distributed under the terms of the GNU General Public License, version 2 or later. See the COPYING file for details."* + `COPYING` là bản GPLv2 |
| `linuxmint/Cinnamon/src/st/` (engine theme St) | **LGPL-2.1-or-later** | header `src/st/st-theme-node.c`: *"GNU Lesser General Public License … either version 2.1 of the License, or (at your option) any later version"* |
| `linuxmint/mint-themes` (Mint-X / Mint-Y) | **GPL-3+** | `debian/copyright`: `License: GPL-3+` |
| `linuxmint/libadwaita` (bản Mint patch) | theo upstream libadwaita (**LGPL-2.1+**) + patch của Mint | `debian/copyright` của repo đó (chưa đọc chi tiết — việc của T01 nếu ta tham chiếu) |

Lưu ý: ta **không** copy mã từ `mint-themes`, chỉ đọc để lấy cấu trúc tham chiếu
(danh sách `@define-color`, cách tổ chức thư mục, `index.theme`). Ý tưởng/cấu trúc không phải
đối tượng bản quyền, nhưng nếu sau này tham chiếu file cụ thể của mint-themes thì phải ghi công
và khi đó GPL-3+ áp dụng cho phần đó.

## Phân tích

- Cinnamon là **GPL-2.0-or-later** → được phép phân phối tác phẩm dẫn xuất theo **GPL-3.0-or-later**
  (điều khoản "or later" cho chọn phiên bản cao hơn).
- `src/st` là LGPL-2.1+ → ta chỉ **đọc** để biết property nào hợp lệ, không liên kết, không copy mã C.
  Danh sách property (fact) không phải đối tượng bản quyền.
- Nếu chọn GPL-2.0-only cho repo thì **không** thể kết hợp bất kỳ phần nào từ mint-themes (GPL-3+).
  Chọn GPL-3.0-or-later giữ cửa rộng hơn và vẫn tương thích với phần vendor từ Cinnamon.

## Quyết định đề xuất

**Repo = GPL-3.0-or-later.**

Kèm theo:
1. Thêm file `LICENSE` chứa toàn văn GNU GPL v3.0 + đoạn "or later" chuẩn.
   ⚠️ Chưa thêm vì cần lấy toàn văn chính xác; **bắt buộc thêm trước khi T04 vendor mã Cinnamon.**
2. `NOTICE.md` (đã tạo) làm sổ theo dõi: mỗi phần vendor phải ghi repo, ref, commit SHA, license.
3. `src/cinnamon/vendor/cinnamon-6.6-sass/VENDOR.md` ghi rõ license của từng file vendor.
4. Không trộn mã Cinnamon và mã mint-themes trong cùng một file, để tránh mơ hồ về nguồn gốc.
5. Phần do dự án tự viết (tokens, generator, lint, tests, docs) cũng đặt dưới GPL-3.0-or-later
   cho đơn giản; nếu muốn dual-license phần tooling (ví dụ MIT cho `tools/`) thì phải tách
   thành package riêng và khai báo rõ — **chưa đề xuất**, vì không có nhu cầu hiện tại.

## Rủi ro còn lại

| Rủi ro | Mức | Xử lý |
|---|---|---|
| Quên thêm `LICENSE` mà đã vendor mã GPL | Cao nếu không gate | Gate trong `04-work-breakdown.md` T04: không vendor khi chưa có `LICENSE`. Thêm test kiểm tra sự tồn tại của `LICENSE` trước khi cho phép thư mục `src/cinnamon/vendor/` có nội dung. |
| Asset SVG tự vẽ nhưng tham khảo hình dạng asset GPL của Mint | Trung bình | Vẽ lại từ mô tả bằng chữ, không trace/sao chép file. Ghi trong `NOTICE.md`. |
| Người dùng muốn phân phối theme như "tác phẩm của riêng mình" không kèm nguồn | — | Không được: GPL là copyleft. Phải nói rõ với người dùng trước khi release. |

## Cần người dùng xác nhận

- [ ] Đồng ý GPL-3.0-or-later cho toàn repo? (nếu không: chọn GPL-2.0-or-later, và khi đó
      **không** được dùng bất kỳ phần nào của mint-themes)
- [ ] Có muốn giữ tên "MintOS Glass" không? (tên có chứa "Mint" — nên kiểm tra có xung đột
      nhãn hiệu với Linux Mint không; Linux Mint có policy về tên phái sinh. **Chưa xác minh** —
      đưa vào `09-verification-checklist.md` như một mục phi kỹ thuật.)
