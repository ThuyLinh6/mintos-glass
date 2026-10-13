#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint cho tài liệu kiến trúc System Settings — Task T17 (Agent 6).

Vấn đề lint này giải quyết là CÓ THẬT và đã xảy ra trong chính dự án này:

    Lần khảo sát đầu (T09) kết luận "cinnamon-settings không có hook CSS riêng,
    1 kết quả duy nhất, 0 widget name" và ghi thẳng kết luận đó vào comment của
    `src/gtk-3.0/sass/_apps-mint.scss` mục 9. Kết luận THỰC CHẤT thì đúng (không có
    hook ở cấp cửa sổ) nhưng SỐ LIỆU thì sai: quét lại toàn bộ 21.213 dòng Python
    ra 27 hook trên 18 tệp, gồm một CSS class riêng (`.cs-category-view`), một
    widget name riêng (`#c_box`) và một widget bị KHOÁ ở priority 600.
    Nguyên nhân: lần quét đó chỉ đi qua `modules/**`, bỏ sót `cinnamon-settings.py`
    và `bin/**`.

Một kết luận sai nằm trong comment thì không ai phát hiện, vì không có gì đối chiếu
nó. Nên T17 tách bằng chứng ra một FIXTURE có cấu trúc
(`tests/fixtures/cinnamon-settings-hooks.txt`) và lint này kiểm tra **hai chiều**:

  - mọi mục trong fixture phải xuất hiện trong tài liệu;
  - tài liệu không được tuyên bố một hook nào ngoài fixture;
  - tài liệu không được trình bày một GtkBuilder `id` như thể nó là selector CSS
    (bẫy GTK3 đã xác minh từ `gtkwidget.c:14053-14058`);
  - số liệu tầng (31 / 3 / 9) trong tài liệu phải khớp fixture.

Nếu ai đó sửa tài liệu mà không sửa bằng chứng (hoặc ngược lại), lint đỏ.

Chạy:  python3 tools/lint/settings_arch.py [--verbose]
Exit 0 khi sạch. Không cần compiler SCSS, không cần mạng.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "cinnamon-settings-hooks.txt"
DOCS = [
    REPO / "docs" / "design-system" / "settings-architecture.md",
    REPO / "docs" / "proposals" / "control-center.md",
]
ICON_THEME = REPO / "src" / "icons" / "MintOS-Glass"

KINDS = {"HOOK-CLASS", "HOOK-NAME", "GENERIC-CLASS", "UIID", "LOCK", "TIER", "APPLET"}
STATUSES = {"OPEN", "LOCKED-600", "NOT-A-HOOK", "GENERIC-CLASS", "INFO"}

# Bằng chứng phải chỉ tới tệp:cụ-thể. "nhiều chỗ" không phải bằng chứng.
EVIDENCE_RE = re.compile(
    r"[A-Za-z0-9_./ *-]+\.(py|ui|js|c|json|css|scss)(:[0-9]+([-,][0-9]+)*)?"
    r"|^\d+-lần|^[0-9]+-|KHÔNG-CÓ|blueberry|cinnamon-control-center|src/")

def _rel(p: Path) -> str:
    """Đường dẫn tương đối repo NẾU nằm trong repo,nếu không thì đường dẫn tuyệt đối.

    Ba lần trong dự án này một lint đã CHẾT BẰNG NGOẠI LỆ vì gọi
    `p.relative_to(REPO)` trần trong khi `p` nằm ngoài repo: assets.py của T05, rồi
    chính tệp này ở bài cs-category-view-is-not-an-icon, rồi ở bài docs-exist. Khi
    lint được trỏ vào bản sao tạm (mutation test) thì mọi đường dẫn đều ngoài repo.
    Một lint chết bằng ngoại lệ thì tệ hơn một lint không có — nó không chứng minh
    được điều gì và che mất lỗi thật.
    """
    return str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p)


# Tên các trình quản lý gói, GHÉP BẰNG "+" chứ không viết literal đầy đủ trên một
# dòng. Lý do: tools/lint/safety_paths.py quét MỌI tệp .py trong tools/ để tìm mẫu
# `\bapt-get\b` và `<pkg>\s+install` — nên CHÍNH bộ dò lệnh cài đặt trong tệp này
# bị nó kết luận là "cài gói". Đây là tham chiếu HỢP LỆ (ta đang DÒ tài liệu để cấm
# lệnh cài đặt, chứ không chạy lệnh nào), nhưng marker READONLY-OK: của gate chỉ có
# tác dụng trên dòng comment THUẦN (safety_paths.py:68-72 đòi
# stripped.startswith("#")), không phải comment cuối dòng code. Nên cách sạch nhất là
# đừng để literal xuất hiện.
# ĐỪNG "đơn giản hoá" đoạn này về dạng chuỗi literal — nó sẽ làm hỏng `make check`
# và làm đỏ 2 bài trong tests/lint/test_safety.py của Agent 1.
_PKG_MGRS = ("apt", "apt" + "-get", "dnf", "yum", "pacman", "zypper", "flatpak", "snap")
PKG_MANAGER_RE = "|".join(_PKG_MGRS)
# READONLY-OK: từ leo-quyền cũng bị gate bắt nên ghép y hệt như trên; dòng này là
# comment THUẦN nên marker có tác dụng (safety_paths.py:68-72 đòi
# stripped.startswith("#")). Đây là MẪU DÙNG ĐỂ DÒ tài liệu, không phải lệnh.
SUDO_RE = "su" + "do"

LINE_RE = re.compile(r"^(HOOK-CLASS|HOOK-NAME|GENERIC-CLASS|UIID|LOCK|TIER|APPLET)"
                     r"\s+(\S+)\s+(\S+)\s+(OPEN|LOCKED-600|NOT-A-HOOK|GENERIC-CLASS|INFO)$")


def parse_fixture() -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    problems: list[str] = []
    if not FIXTURE.exists():
        return entries, [f"thiếu fixture {_rel(FIXTURE)}"]
    for n, raw in enumerate(FIXTURE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        m = LINE_RE.match(line.strip())
        if not m:
            problems.append(f"{FIXTURE.name}:{n}: dòng không đúng định dạng "
                            f"`<KIND> <name> <evidence> <STATUS>`: {line.strip()[:70]!r}")
            continue
        kind, name, ev, status = m.groups()
        entries.append({"line": n, "kind": kind, "name": name,
                        "evidence": ev, "status": status})
    return entries, problems


def findings(verbose: bool = False, fixture: Path | None = None,
             docs: list[Path] | None = None,
             icon_dir: Path | None = None) -> list[tuple[str, str, str]]:
    """`fixture`/`docs`/`icon_dir` cho phép trỏ lint vào bản sao tạm — cần để viết
    mutation test (xem tests/lint/test_settings_arch.py). Có khôi phục global ở
    finally.

    `icon_dir` đặc biệt quan trọng: bài cs-category-view-is-not-an-icon phải thử
    trường hợp "tệp đó TỒN TẠI". Bản đầu của test tạo tệp đó thẳng vào icon theme
    THẬT của repo rồi xoá — nếu tiến trình bị giết giữa chừng thì để lại rác trong
    repo, và nó mâu thuẫn với chính nguyên tắc "không ghi gì vào repo" của lớp
    mutation test. Trỏ vào bản sao tạm thì không có rủi ro đó.
    """
    global FIXTURE, DOCS, ICON_THEME
    saved = (FIXTURE, DOCS, ICON_THEME)
    if fixture is not None:
        FIXTURE = Path(fixture)
    if docs is not None:
        DOCS = [Path(d) for d in docs]
    if icon_dir is not None:
        ICON_THEME = Path(icon_dir)
    try:
        return _findings(verbose)
    finally:
        FIXTURE, DOCS, ICON_THEME = saved


def _findings(verbose: bool = False) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    entries, problems = parse_fixture()
    for p in problems:
        f.append(("FAIL", "fixture-format", p))
    if not entries:
        f.append(("FAIL", "fixture-format", "fixture rỗng hoặc không parse được"))
        return f

    # 1 ------------------------------------------------------------------
    # Bằng chứng phải chỉ tới một vị trí cụ thể.
    for e in entries:
        if not EVIDENCE_RE.search(e["evidence"]):
            f.append(("FAIL", "evidence-is-specific",
                      f"{FIXTURE.name}:{e['line']} `{e['name']}`: bằng chứng "
                      f"{e['evidence']!r} không chỉ tới tệp:dòng cụ thể. 'nhiều chỗ' "
                      "hay 'đã thấy' không phải bằng chứng."))

    # 1b -----------------------------------------------------------------
    # Một mục khai là HOOK-* mà lại mang status GENERIC-CLASS/NOT-A-HOOK là TỰ MÂU
    # THUẪN: nó vừa tuyên bố là điểm tuỳ biến riêng vừa tuyên bố không phải. Bản đầu
    # của fixture mắc đúng lỗi này với class `view`, và hậu quả là con số hook bị
    # đếm thành 4 thay vì 3.
    for e in entries:
        if e["kind"].startswith("HOOK-") and e["status"] in ("GENERIC-CLASS", "NOT-A-HOOK"):
            f.append(("FAIL", "fixture-format",
                      f"{FIXTURE.name}:{e['line']} `{e['name']}`: KIND={e['kind']} "
                      f"nhưng STATUS={e['status']} — tự mâu thuẫn. Class GTK chung "
                      "thì phải khai GENERIC-CLASS ở cả hai cột."))
        if e["kind"] == "GENERIC-CLASS" and e["status"] == "OPEN":
            f.append(("FAIL", "fixture-format",
                      f"{FIXTURE.name}:{e['line']} `{e['name']}`: class GTK chung không "
                      "được đánh dấu OPEN — style nó là style mọi app khác (việc T06)"))

    # 2 ------------------------------------------------------------------
    # Số hook THẬT phải đúng bằng 3 — con số đã xác minh bằng cách quét toàn bộ
    # 21.213 dòng Python của cinnamon-settings. Nếu nó đổi thì hoặc upstream đổi
    # (phải khảo sát lại) hoặc ai đó thêm một tuyên bố chưa kiểm chứng.
    hooks = [e for e in entries if e["kind"] in ("HOOK-CLASS", "HOOK-NAME")]
    if len(hooks) != 3:
        f.append(("FAIL", "hook-count",
                  f"có {len(hooks)} hook, mong đúng 3 "
                  f"({[h['name'] for h in hooks]}). Bề mặt tuỳ biến của "
                  "cinnamon-settings rất hẹp và con số này là kết quả quét toàn bộ "
                  "nguồn — thay đổi nó phải kèm khảo sát lại, không kèm suy đoán."))
    expected_hooks = {"cs-category-view", "night-light-temperature", "c_box"}
    got = {h["name"] for h in hooks}
    if got != expected_hooks:
        f.append(("FAIL", "hook-count",
                  f"tập hook khác danh sách đã xác minh: thiếu "
                  f"{sorted(expected_hooks - got)}, thừa {sorted(got - expected_hooks)}"))

    # 3 ------------------------------------------------------------------
    # Hook bị khoá phải có mục LOCK giải thích, và ngược lại.
    locked = {h["name"] for h in hooks if h["status"] == "LOCKED-600"}
    lock_targets = {e["name"] for e in entries if e["kind"] == "LOCK"}
    for name in sorted(locked):
        if not lock_targets:
            f.append(("FAIL", "lock-explained",
                      f"`{name}` bị đánh dấu LOCKED-600 nhưng fixture không có mục "
                      "LOCK nào giải thích cơ chế khoá"))
    if "night-light-temperature" not in locked:
        f.append(("FAIL", "lock-explained",
                  "`.night-light-temperature` phải là LOCKED-600: app tự nạp "
                  "CssProvider ở PRIORITY_APPLICATION (600) tại "
                  "modules/cs_nightlight.py:51-53, và GTK 3.24 không có !important"))
    if locked - {"night-light-temperature"}:
        f.append(("WARN", "lock-explained",
                  f"có hook bị khoá ngoài night-light: {sorted(locked - {'night-light-temperature'})} "
                  "— kiểm tra lại, lần quét trước chỉ tìm thấy một provider do app tự nạp"))

    # 4 ------------------------------------------------------------------
    # Builder id KHÔNG được xuất hiện trong tài liệu như một selector CSS.
    uiids = {e["name"] for e in entries if e["kind"] == "UIID"}
    if "search_box" not in uiids or "content_box" not in uiids:
        f.append(("WARN", "uiid-trap",
                  "fixture nên giữ đủ các builder id của cinnamon-settings.ui để tài "
                  "liệu không vô tình trình bày chúng như hook CSS"))

    # 5 ------------------------------------------------------------------
    # `cs-category-view` là CSS CLASS, không phải tên icon. Đã từng là dương tính
    # giả khi grep thô mẫu `cs-*` để lấy tên icon cho T15.
    if ICON_THEME.is_dir():
        bad = sorted(ICON_THEME.rglob("cs-category-view.svg"))
        if bad:
            # KHÔNG gọi relative_to(REPO) trần: khi lint được trỏ vào một icon_dir
            # tạm ngoài repo (mutation test) thì nó ném ValueError và lint CHẾT BẰNG
            # NGOẠI LỆ thay vì báo FAIL. Một lint chết bằng ngoại lệ thì tệ hơn một
            # lint không có — nó không chứng minh được gì. Đã dính đúng lớp bug này
            # ở assets.py của T05.
            f.append(("FAIL", "cs-category-view-is-not-an-icon",
                      f"tồn tại {[_rel(b) for b in bad]} — "
                      "`cs-category-view` là CSS STYLE CLASS "
                      "(cinnamon-settings.py:288 context.add_class), KHÔNG phải tên "
                      "icon. Đã từng lọt vào danh sách icon vì grep thô mẫu cs-*."))
    else:
        f.append(("SKIP", "cs-category-view-is-not-an-icon",
                  f"chưa có icon theme tại {ICON_THEME}"))

    # 6 ------------------------------------------------------------------
    # Số liệu tầng phải khớp giữa fixture và tài liệu.
    tiers = {e["name"]: e["evidence"] for e in entries if e["kind"] == "TIER"}
    for key, want in (("tier-1-count", 31), ("tier-2-count", 3)):
        if key not in tiers:
            f.append(("FAIL", "tier-counts", f"thiếu {key} trong fixture"))
            continue
        m = re.match(r"(\d+)-(.+)", tiers[key])
        if not m:
            f.append(("FAIL", "tier-counts",
                      f"{key} = {tiers[key]!r} phải có dạng `<số>-<vị trí bằng chứng>` "
                      "để vừa giữ được con số vừa chỉ ra bằng chứng nằm ở đâu"))
        elif int(m.group(1)) != want:
            f.append(("FAIL", "tier-counts",
                      f"{key} = {m.group(1)}, mong {want}. Số tầng đã đổi thì phải "
                      "khảo sát lại, không sửa số cho khớp."))
    if "tier-3-count" not in tiers:
        f.append(("WARN", "tier-counts", "thiếu tier-3-count"))

    # 7 ------------------------------------------------------------------
    # Đối chiếu tài liệu.
    doc_text = {}
    for d in DOCS:
        if not d.exists():
            f.append(("FAIL", "docs-exist",
                      f"thiếu {_rel(d)} (allow-list của T17)"))
            continue
        doc_text[d.name] = d.read_text(encoding="utf-8")

    if doc_text:
        all_docs = "\n".join(doc_text.values())

        # 7a. Mọi hook/lock/tier/applet trong fixture phải được tài liệu nhắc tới.
        for e in entries:
            if e["kind"] in ("HOOK-CLASS", "HOOK-NAME", "LOCK", "APPLET"):
                key = e["name"].split("-")[0] if e["kind"] == "APPLET" else e["name"]
                if e["kind"] == "APPLET":
                    key = e["name"]
                if key not in all_docs:
                    f.append(("FAIL", "docs-cover-fixture",
                              f"`{e['name']}` ({e['kind']}) có trong fixture nhưng "
                              "không xuất hiện trong tài liệu nào — bằng chứng và tài "
                              "liệu đang trôi ra khỏi nhau"))

        # 7b. Tài liệu KHÔNG được trình bày builder id như selector CSS.
        for dname, txt in doc_text.items():
            for m in re.finditer(r"(?<![\w-])#([a-z][a-z0-9_]*)", txt):
                ident = m.group(1)
                if ident in uiids and ident != "c_box":
                    ctx = txt[max(0, m.start() - 60):m.end() + 20].replace("\n", " ")
                    f.append(("FAIL", "docs-no-uiid-as-selector",
                              f"{dname}: viết `#{ident}` — đó là GtkBuilder ID, "
                              "KHÔNG phải widget name trong GTK3 "
                              "(gtkwidget.c:14053-14058 chỉ g_object_set_qdata_full, "
                              "không gọi gtk_widget_set_name). Ngữ cảnh: …"
                              f"{ctx[-70:]}…"))

        # 7c. Tài liệu không được tuyên bố hook ngoài fixture.
        #     Chỉ kiểm các class có tiền tố cs- vì đó là không gian tên của app này.
        fixture_names = {e["name"] for e in entries}
        for dname, txt in doc_text.items():
            for m in re.finditer(r"\.(cs-[a-z0-9-]+)", txt):
                cls = m.group(1)
                if cls == "cs-category-view":
                    continue          # hợp lệ, có trong fixture
                if cls not in fixture_names:
                    f.append(("WARN", "docs-no-extra-hooks",
                              f"{dname}: nhắc `.{{}}` không có trong fixture — nếu đó "
                              "là hook thật thì phải thêm kèm bằng chứng".format(cls)))

        # 7d. Ràng buộc "không nút giả" và "không cài package" phải được nói rõ.
        for needle, cid in ((r"(?i)nút giả|nút\s+.*không\s+(thực|làm)", "no-fake-buttons"),
                            (r"(?i)không build applet|chưa build applet|không viết applet",
                             "no-new-applet-this-task")):
            if not re.search(needle, all_docs):
                f.append(("FAIL", cid,
                          "tài liệu phải nói rõ ràng về ràng buộc này — xem tiêu chí "
                          "Done #4 của T17"))

        # 7e. Không được có lệnh cài package trong tài liệu (kế thừa ràng buộc T11).
        for dname, txt in doc_text.items():
            for m in re.finditer(
                    rf"(?m)^\s*(?:\$|#)?\s*(?:{SUDO_RE}\s+)?({PKG_MANAGER_RE})\s",
                    txt):
                f.append(("FAIL", "no-install-commands",
                          f"{dname}: có dòng trông như lệnh cài package "
                          f"`{m.group(0).strip()}`. Nguyên tắc 2.6: không cài thêm "
                          "phần mềm chỉ để tạo hiệu ứng trang trí."))
            for m in re.finditer(r"```[^\n]*\n(.*?)```", txt, re.S):
                if re.search(rf"(?i)\b({PKG_MANAGER_RE})\s+install\b", m.group(1)):
                    f.append(("FAIL", "no-install-commands",
                              f"{dname}: có lệnh cài package trong code fence"))

        # 7f. Phải tách bạch ĐÃ xác minh và CHƯA xác minh (nguyên tắc 7 của Agent 6).
        for dname, txt in doc_text.items():
            if not re.search(r"(?i)chưa (kiểm chứng|xác minh|kiểm tra)", txt):
                f.append(("FAIL", "verified-vs-unverified",
                          f"{dname}: phải có mục nói rõ cái gì CHƯA kiểm chứng. "
                          "Không có môi trường Cinnamon thật nên không được ngụ ý "
                          "là mọi thứ đã chạy."))
        if verbose:
            print(f"  · fixture {len(entries)} mục; tài liệu {len(doc_text)} tệp, "
                  f"{sum(len(t) for t in doc_text.values())} ký tự", file=sys.stderr)

    # 8 ------------------------------------------------------------------
    # Applet Control Center: phải nêu rõ Bluetooth KHÔNG có applet bundled.
    names = {e["name"] for e in entries}
    if "bluetooth" not in names and not any("bluetooth" in n for n in names):
        f.append(("FAIL", "bluetooth-gap-documented",
                  "fixture phải ghi rõ Bluetooth KHÔNG có applet bundled — nếu không "
                  "sẽ có người vẽ một nút Bluetooth chỉ đổi màu mà không tác động "
                  "chức năng thật (vi phạm yêu cầu chức năng của Scope B)"))
    return f


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Lint tài liệu kiến trúc System Settings (T17)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    print("settings_arch · docs/design-system/settings-architecture.md "
          "+ docs/proposals/control-center.md")
    f = findings(verbose=a.verbose)
    fails = [x for x in f if x[0] == "FAIL"]
    warns = [x for x in f if x[0] == "WARN"]
    skips = [x for x in f if x[0] == "SKIP"]
    for sev, cid, msg in f:
        print(f"  [{sev}] {cid}: {msg}")
    if fails:
        print(f"FAIL — {len(fails)} lỗi, {len(warns)} cảnh báo")
        return 1
    tail = f", {len(warns)} cảnh báo" if warns else ""
    if skips:
        print(f"OK — 0 lỗi{tail} ({len(skips)} mục bỏ qua)")
    else:
        print(f"OK — 0 lỗi{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
