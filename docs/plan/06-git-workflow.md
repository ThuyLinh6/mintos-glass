# 06 — Quy trình Git: branch, review, tích hợp, rollback

## 1. Mô hình nhánh

```
main                      ← luôn ở trạng thái có thể release; protected
 └─ integration           ← gom nhiều module để test trên máy thật trước khi vào main
     ├─ feat/T04-cinnamon-core
     ├─ feat/T06-gtk3-core
     ├─ fix/T09-nemo-floating-bar
     ├─ spike/T03-import-overlay
     └─ chore/T01-ci
```

| Loại nhánh | Tiền tố | Ví dụ | Vòng đời |
|---|---|---|---|
| Tính năng theo task | `feat/` | `feat/T10-libadwaita` | ≤ 5 ngày, 1 task, 1 PR |
| Sửa lỗi | `fix/` | `fix/T08-titlebar-height` | ≤ 2 ngày |
| Thí nghiệm | `spike/` | `spike/T03-import-overlay` | ≤ 2 ngày, kết thúc bằng ADR |
| Hạ tầng | `chore/` | `chore/T01-ci` | ≤ 3 ngày |
| Tích hợp | `integration` | — | dài hạn, reset từ `main` sau mỗi lần merge |

**Quy tắc:**
1. Một nhánh = một task ID = một PR. Không gộp task.
2. Không commit trực tiếp vào `main`.
3. Không force-push nhánh đã có review; dùng commit mới.
4. Rebase lên `main` trước khi merge (lịch sử thẳng, dễ bisect lỗi thị giác).
5. `dist/` **được commit** (A8) nhưng chỉ do nhánh sở hữu task build tương ứng cập nhật,
   và CI phải xác nhận nó khớp `src/`.
6. Không commit: ảnh chụp màn hình > 2 MB, binary toolchain, `node_modules/`, font.

## 2. Quy ước commit

```
<type>(<task>): <mô tả ≤ 72 ký tự>

<thân: tại sao, không phải làm gì>

Refs: E8, E11
Task: T04
```

`type` ∈ `feat | fix | refactor | style | docs | test | chore | build | spike | revert`.
Dòng `Task:` **bắt buộc** — `tools/lint/allowlist.py` đọc nó để biết allow-list nào áp dụng.
`Refs: E##` trỏ tới bảng bằng chứng trong `01-survey.md` — bắt buộc khi commit chứa giả định kỹ thuật.

## 3. Cổng CI (mọi PR)

| # | Job | Chặn merge nếu |
|---|---|---|
| 1 | `lint-allowlist` | PR chạm file ngoài allow-list của `Task:` |
| 2 | `build-scss` (libsass) | biên dịch lỗi |
| 3 | `build-scss` (dart-sass) | biên dịch lỗi **hoặc** output lệch ngữ nghĩa so với libsass |
| 4 | `lint-st-properties` | có property St không tồn tại |
| 5 | `lint-cinnamon-coverage` | thiếu selector so với Cinnamon 6.6 |
| 6 | `lint-gtk-colors` | thiếu `@define-color` public (E33) hoặc `@theme_*` (E29) |
| 7 | `lint-nemo` / `lint-muffin-decorations` / `lint-plank` / `lint-libadwaita` | thiếu selector/file bắt buộc |
| 8 | `lint-assets` | `url()` mồ côi, SVG malformed |
| 9 | `lint-contrast` | vi phạm WCAG AA ở cặp text×surface |
| 10 | `tokens-drift` | file generated không khớp token |
| 11 | `generated-up-to-date` | `dist/` cũ hơn `src/` |
| 12 | `safety-paths` | tooling chứa `/usr`, `sudo`, `apt`, `dpkg` |
| 13 | `pytest` | bất kỳ test Tầng 1 nào fail |

Job 1 là cơ chế **thực thi** yêu cầu "xác định tệp mỗi nhiệm vụ được phép tạo hoặc sửa".

## 4. Review

### 4.1 CODEOWNERS (định tuyến tự động)
```
/design/tokens/                  @agent-design-systems
/src/cinnamon/vendor/            @lead           # cần 2 approval
/src/cinnamon/                   @agent-cinnamon
/src/gtk-3.0/sass/_decorations.scss   @agent-gtk
/src/gtk-3.0/sass/_apps-nemo.scss     @agent-apps
/src/gtk-3.0/                    @agent-gtk
/src/gtk-4.0/ /src/libadwaita/   @agent-gtk4
/src/dock/                       @agent-dock
/tools/cli/                      @lead @agent-tooling   # 2 approval bắt buộc
/tools/lint/                     @agent-qa
/tests/                          @agent-qa
/docs/                           @agent-docs
/LICENSE /NOTICE.md              @lead
```

### 4.2 Checklist PR (bắt buộc, trong `PULL_REQUEST_TEMPLATE.md`)
```markdown
## Task
- [ ] Task ID: T__ — khớp allow-list trong tests/fixtures/task-allowlists.json
- [ ] Đã đọc docs/plan/04-work-breakdown.md mục task của mình

## Bằng chứng kỹ thuật
- [ ] Mọi giả định về nền tảng đều có Refs: E## (01-survey.md)
- [ ] Không có giả định mới chưa xác minh; nếu có → đã thêm vào 09-verification-checklist.md

## Kiểm thử Tầng 1 (offline)
- [ ] make lint xanh  (dán log)
- [ ] build bằng cả libsass và dart-sass  (dán log)

## Kiểm thử Tầng 2 (on-target)
- [ ] N/A (task không đổi output thị giác)  HOẶC
- [ ] Đã có output/ảnh từ máy người dùng tại docs/verification/... (dán link)
- [ ] KHÔNG tuyên bố đã test trên máy thật nếu chưa có bằng chứng

## An toàn
- [ ] Không ghi ngoài ~/.local/share/themes và ~/.local/state/mintos-glass
- [ ] Không dùng sudo/apt/dpkg
- [ ] Mọi khoá gsettings chạm tới đều nằm trong danh sách đóng của T12
- [ ] Rollback đã được drill (nếu PR này làm thay đổi hành vi installer)

## Phạm vi chưa kiểm chứng
- (liệt kê rõ — để trống nghĩa là "mọi thứ đã kiểm chứng", hiếm khi đúng)
```

### 4.3 Quy tắc 2-approval
Bắt buộc với: `src/cinnamon/vendor/**` (vendor mã GPL), `tools/cli/**` (an toàn hệ thống),
`LICENSE`, `NOTICE.md`, và bất kỳ PR nào **thêm** `-blur` vào output.

## 5. Tích hợp

1. Task merge vào `main` khi CI xanh + đủ approval.
2. Trước mỗi đợt test trên máy thật: tạo/reset `integration` từ `main`, build `dist/`, đóng gói tarball.
3. Người dùng cài từ `integration` build, chạy `tests/manual/PROTOCOL.md`, dán kết quả vào
   `docs/verification/REPORT-<ngày>.md` trên chính nhánh `integration`.
4. Chỉ khi P1–P6 của protocol đạt (đặc biệt P6 rollback) → tag release.
5. Tag: `v0.MINOR.PATCH`. `v0.x` cho tới khi đủ tiêu chí nghiệm thu §1–§4 của `07-acceptance-criteria.md`.

### Lịch phát hành đề xuất
| Bản | Nội dung | Điều kiện |
|---|---|---|
| `v0.1.0` | Cinnamon theme (biến thể chuẩn, không blur) + GTK3 core | T04, T05, T06, T07 xong; P1–P4 pass trên ≥1 máy |
| `v0.2.0` | + Nemo, + WM decorations, + installer/rollback | T08, T09, T12; P6 pass |
| `v0.3.0` | + GTK4/libadwaita | T10; kết quả `ADW_DEBUG_THEMES` rõ ràng |
| `v0.4.0` | + Dock, + light/dark đủ cặp | T11, D-2 chốt |
| `v0.5.0` | + biến thể `-Blur` (opt-in) | P5 pass với số đo thật |
| `v1.0.0` | toàn bộ tiêu chí nghiệm thu | đủ 4 nhóm tiêu chí + không còn Blocker/Critical |

## 6. Quy trình rollback (2 cấp)

### Cấp 1 — rollback cấu hình (người dùng, < 10 giây)
```
python3 -m tools.cli.mintos_glass rollback
```
Khôi phục snapshot gsettings/dconf, xoá theme khỏi `~/.local/share/themes/`.

### Cấp 2 — rollback khẩn cấp khi CLI hỏng (không phụ thuộc code của ta)
Tài liệu hoá trong README, **chỉ dùng lệnh có sẵn của Mint**:
```
gsettings set org.cinnamon.theme name "Mint-Y"
gsettings set org.cinnamon.desktop.interface gtk-theme "Mint-Y-Dark"   # hoặc giá trị trong snapshot
gsettings set org.cinnamon.desktop.wm.preferences theme "Mint-Y"
rm -rf ~/.local/share/themes/MintOS-Glass*
cinnamon --replace &    # hoặc logout/login
```
> Giá trị "Mint-Y"/"Mint-Y-Dark" là **ví dụ** — phải lấy từ snapshot của chính máy đó (T00 mục 8),
> không được hard-code trong tài liệu hướng dẫn cuối cùng.

### Cấp 3 — revert mã nguồn
`git revert <sha>` trên nhánh tương ứng; không dùng `reset --hard` trên nhánh đã push.

## 7. Điều kiện "được phép merge vào main"

- [ ] CI xanh toàn bộ 13 job.
- [ ] Không tăng số lượng `-blur` trong `dist/` so với `main` (trừ khi có ADR + 2 approval).
- [ ] Không có file mới ngoài allow-list.
- [ ] Nếu PR đổi output thị giác: có **ít nhất 1 ảnh chụp từ máy thật** trong `docs/verification/`.
- [ ] `dist/` đã rebuild và khớp `src/`.
- [ ] Không có defect Blocker/Critical đang mở liên quan module này.
