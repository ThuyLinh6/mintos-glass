## Task
- [ ] Task ID: `T__` — khớp allow-list trong `tests/fixtures/task-allowlists.json`
- [ ] Đã đọc mục task của mình trong `docs/plan/04-work-breakdown.md`
- [ ] Chỉ chạm file trong allow-list (CI job `allowlist` sẽ kiểm tra)

## Bằng chứng kỹ thuật
- [ ] Mọi giả định về nền tảng có `Refs: E##` trỏ tới `docs/plan/01-survey.md`
- [ ] Không có giả định mới chưa xác minh. Nếu có → đã thêm vào `docs/plan/09-verification-checklist.md`

## Kiểm thử Tầng 1 (offline — CI chạy được)
- [ ] `make check` xanh (dán log bên dưới)
- [ ] Nếu đổi token: `make report` cho thấy contrast PASS

```
(dán log)
```

## Kiểm thử Tầng 2 (trên máy Linux Mint thật)
- [ ] N/A — task này không đổi output thị giác  **HOẶC**
- [ ] Có output/ảnh từ máy người dùng tại `docs/verification/...` (dán đường dẫn)
- [ ] **Không** tuyên bố đã test trên máy thật nếu chưa có bằng chứng (docs/plan/05-testing-strategy.md §5)

## An toàn
- [ ] Không ghi ngoài `~/.local/share/themes/MintOS-Glass*` và `~/.local/state/mintos-glass/`
- [ ] Không `sudo` / `apt` / `dpkg` / tải gì về máy người dùng
- [ ] Mọi khoá gsettings chạm tới nằm trong danh sách đóng của T12
- [ ] Nếu đổi installer: đã drill rollback (PROTOCOL §2.6)

## Phạm vi CHƯA kiểm chứng
(liệt kê rõ. Để trống nghĩa là "mọi thứ đã kiểm chứng" — hiếm khi đúng.)

-
