#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiểm tra chéo ĐỘC LẬP cho toàn bộ stylesheet và build của repo — Task T13 (QA).

--------------------------------------------------------------------------
VÌ SAO TỆP NÀY TỒN TẠI, dù repo đã có 8 lint của các agent khác
--------------------------------------------------------------------------
Mỗi lint hiện có do CHÍNH agent viết ra sản phẩm đó viết, và mỗi lint chỉ nhìn phạm
vi của mình. QA mà chỉ chạy lại lint của người khác thì chỉ xác nhận rằng "họ nhất
quán với chính họ". Tệp này cố ý làm ba thứ khác đi:

1. **Dùng nguồn sự thật BÊN NGOÀI** thay vì danh sách tự tuyển chọn. Ví dụ:
   `tools/lint/nemo_selectors.py` có `GENERIC_GTK_CLASSES` gồm **19** mục do tác giả
   tự liệt kê. GTK 3.24 thật định nghĩa **84** style class chuẩn trong
   `gtk/gtkstylecontext.h`. Khoảng trống **68** class đó là lý do `.dim-label` — một
   class CHUẨN GTK, được Adwaita style — lọt qua kiểm tra `no-bare-generic` và được
   một partial "dành riêng cho Nemo" phát ra TRẦN, tức là áp dụng lên MỌI app GTK3.
   Danh sách 84 class nằm ở `tests/fixtures/gtk-standard-style-classes.txt`, trích
   bằng máy từ header của upstream, kèm lệnh tái tạo.

2. **Kiểm tra CHÉO giữa các thành phần** mà không lint đơn lẻ nào thấy: partial mồ
   côi không được entry point nào import, `@import` trỏ tới tệp không tồn tại, token
   generated có giá trị sai đơn vị, target build chỉ `echo` ra TODO chứ không build.

3. **Không tin lời khai.** Mỗi kết luận đều kèm đường dẫn + số dòng, và lint tự
   chạy lại build thay vì đọc kết quả có sẵn.

Lint này KHÔNG sửa gì và KHÔNG ghi gì. Nó chỉ báo cáo. Sửa lỗi thuộc về agent sở
hữu thành phần đó (xem `tests/fixtures/qa-bug-register.txt`).

Chạy:  python3 tools/lint/css_sanity.py [--verbose]
Exit 0 khi không có FAIL. WARN và SKIP không làm exit khác 0.
Không cần mạng. Cần libsass hoặc dart-sass cho các bài build; nếu thiếu thì những
bài đó báo SKIP chứ KHÔNG báo PASS giả.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
GTK_CLASSES_FIXTURE = REPO / "tests" / "fixtures" / "gtk-standard-style-classes.txt"
MAKEFILE = REPO / "Makefile"

# Entry point của từng theme. Tệp nào KHÔNG tồn tại thì báo SKIP có lý do, không
# báo FAIL — T06 (gtk-3.0) và T10 (gtk-4.0) chưa bắt đầu là trạng thái đã biết.
# ĐƯỜNG DẪN TƯƠNG ĐỐI so với SRC, không phải Path tuyệt đối đóng băng lúc import.
#
# LÝ DO — ĐÂY LÀ LẦN THỨ TƯ DỰ ÁN NÀY DÍNH CÙNG MỘT BUG: nếu ENTRIES được tính sẵn
# bằng `SRC / ...` ở cấp module, thì khi mutation test trỏ `cs.SRC` và `cs.REPO` vào
# một thư mục tạm, ENTRIES vẫn giữ đường dẫn repo THẬT. Hệ quả là
# `_rel(p)` ném ValueError và lint CHẾT BẰNG NGOẠI LỆ thay vì báo cáo.
# Đúng lớp bug đã gặp ở assets.py (T05), rồi settings_arch.py hai lần (T17) — nơi đã
# phải tách ra helper `_rel()` và ghi chú "đừng gọi relative_to trần". Rồi chính tệp
# này lặp lại. Nên: (a) giữ đường dẫn TƯƠNG ĐỐI và ghép với SRC tại thời điểm gọi,
# (b) mọi chỗ in ra đều đi qua `_rel()`.
ENTRY_REL = {
    "cinnamon": ("cinnamon", "cinnamon.scss"),
    "cinnamon-dark": ("cinnamon", "cinnamon-dark.scss"),
    "gtk-3.0": ("gtk-3.0/sass", "gtk.scss"),
    "gtk-4.0": ("gtk-4.0/sass", "gtk.scss"),
}


def entries() -> dict[str, Path]:
    return {k: SRC.joinpath(*Path(d).parts) / n for k, (d, n) in ENTRY_REL.items()}


def _within(p: Path, root: Path) -> bool:
    try:
        p.relative_to(root)
        return True
    except ValueError:
        return False


def _rel(p: Path) -> str:
    """Đường dẫn tương đối repo NẾU nằm trong repo, nếu không thì tuyệt đối.
    Không bao giờ gọi `relative_to` trần — xem ghi chú ở ENTRY_REL."""
    try:
        # GỌI TRỰC TIẾP relative_to ở ĐÂY và chỉ ở đây. Bản đầu của helper này bị
        # chính phép thế regex dùng để sửa 12 chỗ `relative_to(REPO)` viết đè thành
        # `_rel(p)` — tức là helper gọi lại chính nó và RecursionError sau 976 lần.
        # Bài học: khi thế hàng loạt bằng regex, phải loại trừ định nghĩa của chính
        # helper, và phải CHẠY THỬ ngay sau khi thế.
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)

# Property KHÔNG BAO GIỜ nhận đơn vị độ dài. Giá trị `<số>px` cho các property này
# là CSS không hợp lệ; GTK bỏ qua declaration đó (và có thể log cảnh báo), St cũng
# vậy. Đã xác minh bằng chứng thực tế: generator token của dự án sinh ra
# `$mg-font-weight-regular: 400px` — xem qa-bug-register.txt QA-04.
UNITLESS_PROPERTIES = ("font-weight", "opacity", "z-index", "order", "flex-grow",
                       "flex-shrink", "orphans", "widows", "zoom", "animation-iteration-count")

EXTERNAL_URL_RE = re.compile(r'url\(\s*["\']?\s*(?:https?:)?//', re.I)
IMPORT_RE = re.compile(r'^\s*@import\s+(?:"([^"]+)"|\'([^\']+)\')\s*;', re.M)
IMPORTANT_RE = re.compile(r"!\s*important")

sys.path.insert(0, str(REPO / "tools" / "lint"))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def load_classes() -> set[str]:
    """84 style class CHUẨN của GTK 3.24, trích từ gtkstylecontext.h upstream."""
    if not GTK_CLASSES_FIXTURE.exists():
        return set()
    out = set()
    for line in GTK_CLASSES_FIXTURE.read_text(encoding="utf-8").splitlines():
        line = line.split("//", 1)[0].strip()
        if line:
            out.add(line)
    return out


def find_compiler() -> tuple[str, str] | None:
    """(kind, callable-info). Tái dùng logic của st_properties nếu có."""
    try:
        import st_properties as sp
        return sp.find_compiler()
    except Exception:
        pass
    try:
        import sass  # noqa: F401
        return ("libsass", "python")
    except Exception:
        return None


def compile_scss(path: Path) -> tuple[str | None, str]:
    try:
        import sass
        return sass.compile(filename=str(path)), ""
    except Exception as exc:
        try:
            tool = find_compiler()
            if tool and tool[0] == "sass":
                out = path.with_suffix(".qa.css")
                subprocess.run([tool[1], str(path), str(out)], check=True,
                               capture_output=True, timeout=300)
                css = out.read_text()
                out.unlink(missing_ok=True)
                return css, ""
        except Exception as exc2:
            return None, f"{type(exc).__name__}: {exc} / {type(exc2).__name__}: {exc2}"
        return None, f"{type(exc).__name__}: {exc}"


def all_scss() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.scss"))


def resolve_import(imp: str, from_file: Path) -> Path | None:
    """Sass resolve @import: thử `<imp>.scss`, `_<imp>.scss`, rồi `<imp>/_index.scss`
    và các biến thể, tương đối với thư mục của tệp khai báo."""
    base = from_file.parent / imp
    for cand in (Path(str(base) + ".scss"), Path(str(base.parent / ("_" + base.name)) + ".scss"),
                 base / "_index.scss", base / "index.scss"):
        if cand.exists():
            return cand
    return None


def reachable_from(entry: Path) -> set[Path]:
    """Duyệt đồ thị @import từ một entry point. Có chống chu trình."""
    seen: set[Path] = set()
    stack = [entry.resolve()]
    while stack:
        cur = stack.pop()
        if cur in seen or not cur.exists():
            continue
        seen.add(cur)
        try:
            txt = cur.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in IMPORT_RE.finditer(txt):
            imp = m.group(1) or m.group(2)
            r = resolve_import(imp, cur)
            if r:
                stack.append(r.resolve())
    return seen


def bare_classes(css: str, gtk_std: set[str]) -> set[str]:
    """Class CHUẨN GTK bị phát ra mà KHÔNG có gì giới hạn phạm vi app.

    Bản đầu của hàm này chỉ nhìn "selector có khoảng trắng hay không" và do đó báo
    SAI hai trường hợp:
      `.nemo-window.background`            -> nó báo `background` là trần
      `treeview.view.treeview-drop-indicator` -> nó báo `view` là trần
    Cả hai đều là selector GHÉP (compound): phần tử phải có ĐỒNG THỜI cả hai class.
    Mà `nemo-window` và `treeview-drop-indicator` là class do CHÍNH Nemo thêm
    (đã xác minh: nemo-places-tree-view.c:32, nemo-tree-view-drag-dest.c:206), nên
    không app nào khác khớp được. Hai selector đó KHÔNG rò rỉ.

    Quy tắc đúng: xét compound ĐẦU TIÊN của selector.
      - class CHUẨN GTK trong compound đó = ứng viên rò rỉ;
      - nếu compound đó CÒN có class KHÔNG chuẩn (tức class riêng của app) thì nó
        đóng vai trò QUALIFIER và chặn rò rỉ;
      - tên PHẦN TỬ (`label`, `treeview`) KHÔNG phải qualifier — `label.dim-label`
        vẫn khớp label của mọi app.
    Selector có ancestor (`.nemo-window .dim-label`) thì compound đầu là
    `.nemo-window`, không chứa class chuẩn nào nên đương nhiên không rò rỉ.
    """
    out: set[str] = set()
    for rule in re.finditer(r"([^{}]+)\{", css):
        for sel in rule.group(1).split(","):
            sel = " ".join(sel.split())
            if not sel or sel.startswith("@"):
                continue
            first = sel.split()[0]
            cls = set(re.findall(r"\.([A-Za-z_][\w-]*)", first))
            std = cls & gtk_std
            qualifier = cls - gtk_std
            if std and not qualifier:
                out |= std
    return out


# ---------------------------------------------------------------------------
def findings(verbose: bool = False) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    gtk_std = load_classes()
    if not gtk_std:
        f.append(("WARN", "fixture-missing",
                  f"không đọc được {GTK_CLASSES_FIXTURE} — bài bare-gtk-class-leak "
                  "sẽ không chạy"))

    # 1 ------------------------------------------------------------------
    # Mọi @import phải resolve. Sass sẽ báo lỗi khi build, nhưng nếu một partial
    # mồ côi được import từ một tệp không bao giờ được build thì lỗi không lộ ra.
    for p in all_scss():
        try:
            txt = p.read_text(encoding="utf-8")
        except OSError as exc:
            f.append(("FAIL", "unreadable", f"{_rel(p)}: {exc}"))
            continue
        for m in IMPORT_RE.finditer(txt):
            imp = m.group(1) or m.group(2)
            line = txt[:m.start()].count("\n") + 1
            if resolve_import(imp, p) is None:
                f.append(("FAIL", "imports-resolve",
                          f"{_rel(p)}:{line}: `@import \"{imp}\"` không "
                          "resolve tới tệp nào (đã thử .scss, _.scss, _index.scss)"))

    # 2 ------------------------------------------------------------------
    # Partial mồ côi: không entry point nào với tới.
    _E = entries()
    existing_entries = {k: v for k, v in _E.items() if v.exists()}
    missing_entries = {k: v for k, v in _E.items() if not v.exists()}
    for k, v in missing_entries.items():
        f.append(("SKIP", "entry-missing",
                  f"entry point {k} chưa tồn tại ({_rel(v)}) — các bài "
                  "dựa trên nó bị bỏ qua. Đây là trạng thái đã biết của task chưa "
                  "bắt đầu, KHÔNG phải PASS."))
    reach: set[Path] = set()
    for v in existing_entries.values():
        reach |= reachable_from(v)
    if existing_entries:
        orphans = sorted(p for p in all_scss()
                         if p.resolve() not in reach
                         and p.name != "_tokens.scss"
                         and "vendor" not in p.parts)
        for p in orphans:
            f.append(("WARN", "orphan-partial",
                      f"{_rel(p)} không được entry point nào import tới "
                      f"({', '.join(sorted(existing_entries))}). Nội dung của nó KHÔNG "
                      "nằm trong bất kỳ CSS nào được ship. Nếu đây là partial chờ "
                      "một entry point chưa tồn tại thì phải ghi rõ trong tài liệu "
                      "bàn giao, không để người đóng gói tưởng nó đã có tác dụng."))
        # _tokens.scss được phép mồ côi theo nghĩa trên (nó được import bằng đường
        # khác) — kiểm tra riêng rằng nó THẬT SỰ được dùng.
        for tk in SRC.rglob("_tokens.scss"):
            if tk.resolve() not in reach and existing_entries:
                # PHẢI giữ `tk` dạng Path để dùng `.parts` ở dòng dưới, và chỉ gọi
                # `_rel()` khi IN ra. Phép thế regex hàng loạt ở lần sửa trước đã đổi
                # cả dòng này từ `rel = tk.relative_to(REPO)` (Path) thành
                # `rel = _rel(tk)` (str) trong khi dòng kế vẫn dùng `rel.parts` ->
                # AttributeError. Bài học: sau khi thế hàng loạt phải CHẠY, không chỉ
                # đọc diff.
                # token của theme chưa có entry point thì mồ côi là đương nhiên
                parts = tk.relative_to(SRC).parts if _within(tk, SRC) else tk.parts
                theme = parts[0] if parts else ""
                if theme in existing_entries:
                    f.append(("FAIL", "orphan-partial",
                              f"{_rel(tk)} không được theme `{theme}` import — token không "
                              "vào được CSS thì mọi giá trị thiết kế chỉ tồn tại trên giấy"))

    # 3 + 4 --------------------------------------------------------------
    # Build thật, và kiểm tra TÍNH XÁC ĐỊNH.
    comp = find_compiler()
    compiled: dict[str, str] = {}
    if comp is None:
        f.append(("SKIP", "entry-compiles",
                  "không có libsass hay dart-sass trong môi trường — bỏ qua mọi bài "
                  "build. KHÔNG suy ra là build được."))
    else:
        for name, entry in sorted(existing_entries.items()):
            css1, err1 = compile_scss(entry)
            if css1 is None:
                f.append(("FAIL", "entry-compiles", f"{name}: biên dịch lỗi — {err1}"))
                continue
            css2, err2 = compile_scss(entry)
            if css2 is None:
                f.append(("FAIL", "deterministic-output",
                          f"{name}: lần biên dịch thứ hai lỗi — {err2}"))
            elif hashlib.sha256(css1.encode()).hexdigest() != \
                    hashlib.sha256(css2.encode()).hexdigest():
                f.append(("FAIL", "deterministic-output",
                          f"{name}: hai lần biên dịch cùng một tệp cho kết quả KHÁC "
                          "nhau — build không tái lập được, không thể tin diff giữa "
                          "các lần release"))
            else:
                compiled[name] = css1
                if verbose:
                    print(f"  · {name}: {len(css1):,} B, {css1.count('{')} rule, "
                          f"sha256 {hashlib.sha256(css1.encode()).hexdigest()[:12]}",
                          file=sys.stderr)

        # 5: hai compiler phải đồng ý (nếu có cả hai)
        try:
            import sass  # noqa: F401
            have_lib = True
        except Exception:
            have_lib = False
        dart = None
        # Ghép bằng Path, KHÔNG nối chuỗi với một literal bắt đầu bằng dấu chéo.
        # tests/lint/test_safety.py của Agent 1 bắt MỌI chuỗi có nháy mở đầu bằng
        # dấu chéo trong .py ngoài docs/tests, vì nó quét đường ghi hệ thống tuyệt
        # đối. Cái mảnh bắt đầu bằng dấu chéo ở bản đầu chỉ là MẢNH để ghép chứ không
        # phải đích ghi. LƯU Ý: gate quét cả TEXT THÔ nên chính COMMENT giải thích vấn
        # đề cũng đủ làm nó đỏ — bản sửa đầu tiên của đoạn này mắc đúng lỗi đó, đã bỏ
        # literal trong mã nhưng lại viết lại chính literal ấy trong comment kèm dấu
        # nháy, và vì dòng thật bắt đầu bằng hai chữ khác nên phép thế theo chuỗi dài
        # đã trượt một cách âm thầm (AssertionError). Đây là lần THỨ BA dự án dính lớp
        # dương tính giả này (T09 với đường dẫn GResource, T17 với tiền tố thư mục
        # symbolic). Sửa về phía mình, KHÔNG nới cổng của Agent 1.
        _tc = os.environ.get("MINTOS_TOOLCHAIN") or str(Path.home() / ".mintos-toolchain")
        for cand in (str(Path(_tc).joinpath("node_modules", ".bin", "sass")),
                     "sass"):
            if cand == "sass" or Path(cand).exists():
                dart = cand
                break
        if have_lib and dart and compiled:
            for name, entry in sorted(existing_entries.items()):
                if name not in compiled:
                    continue
                try:
                    out = entry.with_suffix(".qa-dart.css")
                    # --no-source-map: nếu không, dart-sass ghi thêm <out>.map NGAY
                    # TRONG src/ và bài tokens-not-hand-edited ở dưới đọc thấy rác đó
                    # rồi báo FAIL giả ("generated bị sửa tay"). Chính lint này từng
                    # để lại 2 tệp .map trong repo, trái với cam kết ở docstring là
                    # "KHÔNG sửa gì và KHÔNG ghi gì".
                    subprocess.run([dart, "--no-source-map", str(entry), str(out)],
                                   check=True, capture_output=True, timeout=300)
                    dcss = out.read_text()
                    out.unlink(missing_ok=True)
                    out.with_suffix(".css.map").unlink(missing_ok=True)
                except Exception as exc:
                    f.append(("WARN", "dual-compiler-agreement",
                              f"{name}: dart-sass không chạy được ({exc}) — chỉ so "
                              "được bằng libsass"))
                    continue
                # KHÔNG so bằng chuỗi selector thô. Bản đầu dùng
                # `re.findall(r"([^{}]+)\{")` rồi strip, và nó báo FAIL giả vì
                # libsass giữ selector nhóm kèm XUỐNG DÒNG bên trong
                # (`#vhandle:hover,\n  #hhandle:hover`) còn dart-sass thì không.
                # Tách selector rồi chuẩn hoá mới là so sánh có nghĩa — đúng bài học
                # đã ghi từ T04: luôn tái dùng parse_rules + split_selectors.
                try:
                    import st_properties as sp

                    def norm(s: str) -> list[str]:
                        return sorted({x for sel, _ in sp.parse_rules(s)
                                       for x in sp.split_selectors(sel)})
                except Exception:
                    def norm(s: str) -> list[str]:
                        return sorted({" ".join(x.split())
                                       for x in re.findall(r"([^{}]+)\{", s)})
                a, b = norm(compiled[name]), norm(dcss)
                if a != b:
                    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
                    f.append(("FAIL", "dual-compiler-agreement",
                              f"{name}: libsass và dart-sass cho tập selector KHÁC "
                              f"nhau (chỉ libsass: {len(only_a)}, chỉ dart: {len(only_b)}). "
                              "Mint build bằng libsass (pysassc) nên lệch nhau nghĩa là "
                              "bản build thật khác bản kiểm tra ở đây."))
                elif verbose:
                    print(f"  · {name}: libsass ≡ dart-sass trên {len(a)} selector",
                          file=sys.stderr)

    # 6 ------------------------------------------------------------------
    # !important: GTK 3.24 KHÔNG hỗ trợ (đã kiểm: chuỗi "important" xuất hiện 0 lần
    # trong gtkcssparser.c, gtkcssprovider.c, gtkstylecascade.c @3.24.42). St cũng
    # vậy. Viết ra thì hoặc bị bỏ qua âm thầm hoặc làm hỏng parse.
    for p in all_scss():
        if "vendor" in p.parts:
            continue                      # vendor là bất biến, không sửa được
        txt = p.read_text(encoding="utf-8")
        body = re.sub(r"//[^\n]*", "", txt)
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        for m in IMPORTANT_RE.finditer(body):
            line = body[:m.start()].count("\n") + 1
            f.append(("FAIL", "no-important",
                      f"{_rel(p)}:{line}: dùng `!important`. GTK 3.24 "
                      "không hỗ trợ (0 lần xuất hiện trong gtkcssparser.c, "
                      "gtkcssprovider.c, gtkstylecascade.c @3.24.42); thứ tự priority "
                      "của provider là tuyệt đối."))
    for name, css in compiled.items():
        if IMPORTANT_RE.search(css):
            f.append(("FAIL", "no-important",
                      f"{name}: CSS đã biên dịch vẫn chứa `!important`"))

    # 7 ------------------------------------------------------------------
    # Giá trị sai đơn vị cho property không nhận đơn vị.
    for p in sorted(SRC.rglob("_tokens.scss")):
        txt = p.read_text(encoding="utf-8")
        for prop in UNITLESS_PROPERTIES:
            for m in re.finditer(rf"^\$mg-{prop}[\w-]*:\s*(-?[\d.]+)(px|em|rem|pt|%)\s*;",
                                 txt, re.M):
                line = txt[:m.start()].count("\n") + 1
                f.append(("FAIL", "invalid-unit-values",
                          f"{_rel(p)}:{line}: token cho `{prop}` mang đơn "
                          f"vị độ dài `{m.group(0).strip()}`. `{prop}` KHÔNG nhận đơn "
                          "vị; bất kỳ ai dùng token này sẽ sinh CSS không hợp lệ."))
        # tên token nói 'pt' nhưng giá trị là px -> sai ngữ nghĩa
        for m in re.finditer(r"^\$mg-([\w-]*-pt):\s*(-?[\d.]+)px\s*;", txt, re.M):
            line = txt[:m.start()].count("\n") + 1
            f.append(("WARN", "invalid-unit-values",
                      f"{_rel(p)}:{line}: token `{m.group(1)}` có hậu tố "
                      f"`-pt` nhưng giá trị là `{m.group(2)}px`. 9pt ≠ 9px (9pt = "
                      "12px). Người dùng token này sẽ nghĩ mình đang đặt điểm (point)."))
    for name, css in compiled.items():
        for prop in UNITLESS_PROPERTIES:
            for m in re.finditer(rf"(?<![\w-]){prop}\s*:\s*(-?[\d.]+)(px|em|rem|pt)\s*[;}}]", css):
                f.append(("FAIL", "invalid-unit-values",
                          f"{name}: CSS đã biên dịch chứa `{prop}: {m.group(0).strip()}` "
                          "— không hợp lệ"))

    # 8 ------------------------------------------------------------------
    # Partial dành riêng cho MỘT app mà phát ra class CHUẨN GTK ở dạng TRẦN.
    # Vì GTK3 không có hook application-id, rule trần đó áp dụng lên MỌI app.
    if gtk_std:
        for p in sorted(SRC.rglob("_apps-*.scss")):
            css, err = compile_scss(p)
            if css is None:
                if comp is not None:
                    f.append(("FAIL", "bare-gtk-class-leak",
                              f"{_rel(p)}: không biên dịch được để kiểm "
                              f"tra — {err}"))
                continue
            leaked = sorted(bare_classes(css, gtk_std))
            if leaked:
                f.append(("FAIL", "bare-gtk-class-leak",
                          f"{_rel(p)} phát ra {len(leaked)} class CHUẨN "
                          f"GTK ở dạng TRẦN: {leaked}. GTK 3.24 không phơi "
                          "application-id cho CSS (0 lần `application_id` trong "
                          "gtk/gtkapplicationwindow.c @3.24.42) nên MỘT gtk.css phục "
                          "vụ MỌI app — các rule này sẽ áp dụng lên mọi app GTK3 "
                          "khác, không chỉ app mà partial này nhắm tới. Phải scope "
                          "bằng class cửa sổ của app, hoặc chuyển quyết định đó sang "
                          "theme lõi (T06)."))
            elif verbose:
                print(f"  · {p.name}: 0 class chuẩn GTK phát ra trần", file=sys.stderr)

    # 9 ------------------------------------------------------------------
    # Không URL ngoài trong stylesheet (tài nguyên phải nằm trong repo).
    for p in list(SRC.rglob("*.scss")) + list(SRC.rglob("*.css")):
        txt = p.read_text(encoding="utf-8")
        for m in EXTERNAL_URL_RE.finditer(txt):
            line = txt[:m.start()].count("\n") + 1
            f.append(("FAIL", "no-external-url",
                      f"{_rel(p)}:{line}: `url()` trỏ ra ngoài — theme "
                      "không được tải tài nguyên từ Internet khi chạy"))
    for name, css in compiled.items():
        if EXTERNAL_URL_RE.search(css):
            f.append(("FAIL", "no-external-url", f"{name}: CSS biên dịch có url() ngoài"))

    # 10 -----------------------------------------------------------------
    # Token generated phải tái lập được và khớp bản đã commit.
    gen = REPO / "tools" / "tokens" / "generate.py"
    if gen.exists():
        try:
            r = subprocess.run([sys.executable, str(gen), "--scheme", "all", "--check"],
                               cwd=str(REPO), capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                f.append(("FAIL", "tokens-reproducible",
                          f"generate.py --check exit {r.returncode}: "
                          f"{(r.stdout + r.stderr).strip()[-300:]}"))
            elif verbose:
                print("  · generate.py --check: OK, generated khớp token", file=sys.stderr)
        except Exception as exc:
            f.append(("WARN", "tokens-reproducible", f"không chạy được generate.py: {exc}"))
        # working tree có bị bẩn sau khi sinh lại không (tức generated bị sửa tay)
        try:
            subprocess.run([sys.executable, str(gen), "--scheme", "all"],
                           cwd=str(REPO), capture_output=True, text=True, timeout=300)
            r = subprocess.run(["git", "status", "--porcelain", "--", "src", "design"],
                               cwd=str(REPO), capture_output=True, text=True, timeout=120)
            # Loại mọi đường dẫn do CHÍNH lint này tạo ra trong lúc chạy, để không
            # tự báo mình là nguyên nhân (bug đã gặp thật).
            dirty = [l for l in r.stdout.splitlines()
                     if l.strip() and ".qa-" not in l and ".qa-dart" not in l]
            if dirty:
                f.append(("FAIL", "tokens-not-hand-edited",
                          f"sau khi sinh lại token, {len(dirty)} tệp bị lệch so với bản "
                          f"đã commit: {dirty[:4]}. Nghĩa là tệp generated đã bị SỬA "
                          "TAY, làm mất khả năng tái tạo."))
        except Exception as exc:
            f.append(("WARN", "tokens-not-hand-edited", f"không kiểm tra được: {exc}"))

    # 11 -----------------------------------------------------------------
    # 40-motion.json được đọc và tính vào lock nhưng KHÔNG BAO GIỜ được emit.
    motion = REPO / "design" / "tokens" / "40-motion.json"
    if motion.exists() and gen.exists():
        gtxt = gen.read_text(encoding="utf-8")
        emits_duration = bool(re.search(r"\$mg-duration-|duration.*emit|mg-easing", gtxt))
        any_token = False
        for tk in SRC.rglob("_tokens.scss"):
            if "$mg-duration-" in tk.read_text(encoding="utf-8") or \
               "$mg-easing-" in tk.read_text(encoding="utf-8"):
                any_token = True
        if not any_token:
            f.append(("WARN", "motion-tokens-not-emitted",
                      "design/tokens/40-motion.json tồn tại và được generate.py nạp "
                      "(nằm trong danh sách tệp tính lock) nhưng KHÔNG token "
                      "$mg-duration-*/$mg-easing-* nào được sinh ra. Nguyên nhân đã "
                      "xác minh: generate.py chỉ flatten 10-primitives.json và "
                      "30-component.json (cộng 20-semantic-<scheme>.json). Hệ quả: "
                      "mỗi theme phải tự định nghĩa hằng tạm, tức CÓ NHIỀU NGUỒN SỰ "
                      "THẬT cho cùng một khái niệm."))

    # 12 -----------------------------------------------------------------
    # Target build phải build thật, không chỉ echo ra TODO.
    if MAKEFILE.exists():
        mk = MAKEFILE.read_text(encoding="utf-8")
        for m in re.finditer(r"(?m)^([a-z][a-z0-9-]*):\s*##\s*([^\n]*)\n((?:\t[^\n]*\n?)+)", mk):
            target, doc, body = m.group(1), m.group(2).strip(), m.group(3)
            claims_build = bool(re.search(r"(?i)biên dịch|compile|build", doc))
            has_todo = "TODO" in body
            # Bản đầu kiểm tra "mọi dòng có bắt đầu bằng echo/if/fi không" và nó
            # TRƯỢT: thân target `scss` mở đầu bằng `@if [ -z "$(SASS)" ]; then …`,
            # tức tiền tố `@if` chứ không phải `if`, nên điều kiện sai và bài kiểm
            # tra im lặng dù `make scss` thật sự chỉ echo ra một dòng TODO.
            #
            # Cách đúng: hỏi thẳng câu cần hỏi — có lệnh GỌI compiler thật nào nằm
            # NGOÀI một chuỗi echo không? Dòng nào bắt đầu bằng echo (kèm @ hay
            # không) thì mọi tham chiếu compiler trên dòng đó chỉ là VĂN BẢN.
            compiler_ref = re.compile(r"\$\(SASS\)|\$\(PYTHON\)|\bpysassc\b|\bsassc\b|\bnpx\b")
            real_invocation = False
            for ln in body.splitlines():
                s = ln.strip().lstrip("@").strip()
                if not s or s.startswith("#"):
                    continue
                if s.startswith("echo"):
                    continue                      # chỉ là văn bản in ra
                # Tinh hơn lần sửa trước: dòng `@if [ -z "$(SASS)" ]; then …` có
                # THAM CHIẾU $(SASS) nhưng đó là một phép THỬ, không phải lời gọi.
                # Chỉ coi là lời gọi khi compiler đứng Ở ĐẦU LỆNH.
                if re.match(r"^(?:[\w$.()/-]*)(?:pysassc|sassc|npx)\b", s) or \
                        s.startswith("$(SASS)") or s.startswith("$(PYTHON)"):
                    real_invocation = True
            if claims_build and has_todo and not real_invocation:
                f.append(("WARN", "make-target-is-a-stub",
                          f"Makefile target `{target}` được mô tả là \"{doc}\" nhưng "
                          "thân target chỉ `echo` ra một dòng TODO và không build gì "
                          "cả. Mô tả và hành vi lệch nhau: người đóng gói chạy target "
                          "này sẽ tưởng đã có CSS trong dist/ trong khi dist/ không "
                          "được tạo."))
    return f


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Kiểm tra chéo độc lập cho stylesheet + build (T13 · QA)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    print("css_sanity · kiểm tra chéo độc lập (không dùng lại kết luận của lint từng agent)")
    f = findings(verbose=a.verbose)
    fails = [x for x in f if x[0] == "FAIL"]
    warns = [x for x in f if x[0] == "WARN"]
    skips = [x for x in f if x[0] == "SKIP"]
    for sev, cid, msg in f:
        print(f"  [{sev}] {cid}: {msg}")
    if fails:
        print(f"FAIL — {len(fails)} lỗi, {len(warns)} cảnh báo, {len(skips)} bỏ qua")
        return 1
    parts = [f"OK — 0 lỗi"]
    if warns:
        parts.append(f"{len(warns)} cảnh báo")
    if skips:
        parts.append(f"{len(skips)} mục bỏ qua (thiếu entry point hoặc thiếu compiler — "
                     "không phải PASS)")
    print(", ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
