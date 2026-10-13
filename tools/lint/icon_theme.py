#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint cho icon theme MintOS-Glass — Task T15 (Agent D · Visual/Assets).

Hiện thực hoá 7 tiêu chí "Done" của T15 trong docs/plan/04-work-breakdown.md:

  1. `index.theme` hợp lệ theo Icon Theme Spec của freedesktop; **mọi thư mục
     trong `Directories` phải tồn tại thật** và **mọi thư mục tồn tại phải được
     liệt kê** — không khai báo khả năng mà tài nguyên không đáp ứng.
  2. Chuỗi `Inherits` đảm bảo không icon nào biến mất khi theme thiếu.
  3. Tên icon lấy từ `Icon=` trong `.desktop` thật (fixture ghi kèm nguồn).
  4. Icon `*-symbolic` phải ĐƠN SẮC để GTK tô lại được theo màu chữ.
  5. SVG well-formed (`xml.etree`), có `viewBox`, không URL ngoài, không
     `<script>`/`<image>`/`<filter>`.
  6. Màu tra ngược được về token — cùng cơ chế đã áp dụng ở T05.
  7. `MANIFEST.md` ghi đủ: có gì, chưa có gì, fallback về đâu, nguồn, giấy phép.

--------------------------------------------------------------------------
BA RÀNG BUỘC KỸ THUẬT ĐÃ XÁC MINH, quyết định cấu trúc theme
--------------------------------------------------------------------------
A. `Inherits` là CHUỖI FALLBACK thật, không phải trang trí. Đã đọc
   `usr/share/icons/Mint-Y/index.theme` của linuxmint/mint-y-icons @ master:
       Inherits=Adwaita,gnome,hicolor
   và Mint-Y dùng `<context>/<size>` (apps/16, apps/22, … apps/256) CỘNG thêm
   `apps/16@2x` với `Scale=2` — tức Mint-Y là theme RASTER nhiều kích thước.
   Theme này thuần SVG nên dùng `scalable/<context>` + `Type=Scalable` với
   MinSize/MaxSize, và do đó KHÔNG cần thư mục `@2x` lẫn khoá `Scale=2`.
   `Size=16 / MinSize=16 / MaxSize=256` cho thư mục symbolic là đúng cặp giá trị
   Mint-Y đang dùng cho `apps/symbolic` và `status/symbolic`.

B. Icon `*-symbolic` được GTK tô lại theo màu chữ bằng KÊNH ALPHA của ảnh, không
   dùng màu gốc. Nên mọi hình phải cùng MỘT màu, không gradient, không màu thứ
   hai. Vi phạm thì icon thành một khối đặc mất chi tiết. Bài
   `symbolic-monochrome` khoá điều này bằng cách parse SVG thật, không đọc bằng mắt.

C. Icon KHÔNG-symbolic phải đọc được trên CẢ nền sáng lẫn nền tối, vì cùng một
   icon theme phục vụ hộp thoại chọn tệp của app GTK (nền theo theme của app)
   lẫn desktop. Đã ĐO bằng tools/lint/contrast.py trên toàn bộ thang xám:
       gray-200 #cfd2d7  trắng 1.52:1 ✗   tối 12.25:1 ✓   -> chỉ một phía
       gray-300 #a5a9b0  trắng 2.36:1 ✗   tối  7.87:1 ✓   -> chỉ một phía
       gray-400 #7c8087  trắng 3.97:1 ✓   tối  4.68:1 ✓   -> DÙNG ĐƯỢC CẢ HAI
       gray-500 #55585f  trắng 7.12:1 ✓   tối  2.61:1 ✗   -> chỉ một phía
       gray-600 #3a3d43  trắng 10.89:1 ✓  tối  1.71:1 ✗   -> chỉ một phía
       mint-500 #3ddc97  trắng 1.77:1 ✗   tối 10.51:1 ✓   -> chỉ một phía
   CHỈ gray-400 đạt >= 3:1 (WCAG 1.4.11) trên cả hai. Nên nó là màu nét vẽ mặc
   định. Bài `ink-contrast-both-backdrops` đo lại mỗi lần chạy để không ai đổi
   sang màu khác mà không biết là mình vừa phá một phía.

Chạy:  python3 tools/lint/icon_theme.py [--verbose]
Exit 0 khi sạch. Không cần compiler SCSS — lint này đọc index.theme và SVG trực
tiếp, nên chạy được ở bất kỳ đâu có Python 3 (kể cả CI tối giản).
"""

from __future__ import annotations

import argparse
import configparser
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
THEME = REPO / "src" / "icons" / "MintOS-Glass"
INDEX = THEME / "index.theme"
MANIFEST = THEME / "MANIFEST.md"
FIXTURE = REPO / "tests" / "fixtures" / "icon-theme-core.txt"
TOKENS = REPO / "src" / "cinnamon" / "tokens" / "_tokens.scss"

SVG_NS = "http://www.w3.org/2000/svg"

# Context hợp lệ theo Icon Naming Spec / Icon Theme Spec.
VALID_CONTEXTS = {"Actions", "Animations", "Applications", "Apps", "Categories",
                  "Devices", "Emblems", "Emotes", "Filesystems", "International",
                  "Mimetypes", "Places", "Status", "Stock", "Legacy"}

# Thư mục context -> Context bắt buộc. Sai Context thì bộ nạp icon lọc mất ứng
# viên dù tệp có tồn tại.
DIR_CONTEXT = {
    "apps": "Apps", "places": "Places", "devices": "Devices",
    "mimetypes": "Mimetypes", "actions": "Actions", "status": "Status",
    "categories": "Categories", "emblems": "Emblems", "emotes": "Emotes",
    "animations": "Animations", "legacy": "Legacy",
}

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
COLOUR_ATTR_RE = re.compile(
    r'\b(fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*"([^"]+)"')
EXTERNAL_RE = re.compile(r"(https?:)?//[^\s\"')]+|\bxlink:href\s*=|\shref\s*=\s*[\"'](?!(#|data:))", re.I)
DANGEROUS_RE = re.compile(r"<\s*(script|image|foreignObject|iframe|use|filter|mask|clipPath)\b", re.I)
RGBA_RE = re.compile(r"\brgba?\s*\(")
# Tên icon hợp lệ: chữ thường, số, '-', '_', '.' (Icon Naming Spec).
ICON_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

sys.path.insert(0, str(REPO / "tools" / "lint"))
import st_properties as sp  # noqa: E402  (dùng lại load_fixture — một normalisation)

load_fixture = sp.load_fixture


# ---------------------------------------------------------------------------
# Màu nền tham chiếu để đo tương phản. `surface-base` là nền tối thật của theme
# (đã kiểm trong _tokens.scss); trắng là nền sáng của app GTK dùng theme sáng.
# ---------------------------------------------------------------------------
LIGHT_BACKDROP = "#ffffff"
DARK_BACKDROP = None  # đọc từ token, xem ink_colours()


def token_hex_values() -> set[str]:
    out: set[str] = set()
    txt = TOKENS.read_text()
    for m in HEX_RE.finditer(txt):
        h = m.group(0).lower()
        if len(h) == 4:
            h = "#" + "".join(c * 2 for c in h[1:])
        out.add(h)
    for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", txt):
        out.add("#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3)))
    return out


def token_hex(name: str) -> str | None:
    m = re.search(rf"^\${re.escape(name)}:\s*(.+?);", TOKENS.read_text(), re.M)
    if not m:
        return None
    v = m.group(1).strip().lower()
    return v if re.fullmatch(r"#[0-9a-f]{6}", v) else None


def parse_index() -> tuple[configparser.ConfigParser | None, list[str]]:
    """Đọc index.theme. GKeyFile/GLib chấp nhận `#` là comment (Desktop Entry
    Spec) — `configparser` mặc định dùng `#` VÀ `;`, nên phải tắt `;` để không
    hiểu nhầm giá trị có dấu chấm phẩy."""
    problems: list[str] = []
    if not INDEX.exists():
        return None, [f"thiếu {INDEX}"]
    cp = configparser.ConfigParser(strict=False, interpolation=None,
                                   comment_prefixes=("#",), inline_comment_prefixes=None)
    cp.optionxform = str  # giữ nguyên HOA/thường của khoá (Size, Context, Type…)
    try:
        cp.read_string(INDEX.read_text(encoding="utf-8"))
    except configparser.Error as exc:
        return None, [f"index.theme không parse được: {exc}"]
    if not cp.has_section("Icon Theme"):
        problems.append("thiếu section bắt buộc `[Icon Theme]`")
    return cp, problems


def existing_dirs() -> set[str]:
    """Mọi thư mục CON có chứa ít nhất một .svg, dạng path tương đối theme root."""
    out: set[str] = set()
    for p in THEME.rglob("*.svg"):
        out.add(p.parent.relative_to(THEME).as_posix())
    return set(out)


def findings(verbose: bool = False, theme_dir: Path | None = None,
             fixture: Path | None = None) -> list[tuple[str, str, str]]:
    """`theme_dir`/`fixture` cho phép trỏ lint vào bản sao tạm — cần để viết
    mutation test (xem tests/lint/test_icon_theme.py). Mặc định là repo thật."""
    global THEME, INDEX, MANIFEST, FIXTURE
    saved = (THEME, INDEX, MANIFEST, FIXTURE)
    if theme_dir is not None:
        THEME = Path(theme_dir)
        INDEX = THEME / "index.theme"
        MANIFEST = THEME / "MANIFEST.md"
    if fixture is not None:
        FIXTURE = Path(fixture)
    try:
        return _findings(verbose)
    finally:
        THEME, INDEX, MANIFEST, FIXTURE = saved


def _findings(verbose: bool = False) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    if not THEME.is_dir():
        return [("FAIL", "theme-dir", f"thiếu {THEME}")]

    cp, problems = parse_index()
    for p in problems:
        f.append(("FAIL", "index-theme-valid", p))
    if cp is None:
        return f

    # 1 ------------------------------------------------------------------
    root = cp["Icon Theme"] if cp.has_section("Icon Theme") else {}
    for key in ("Name", "Inherits", "Directories"):
        if not root.get(key):
            f.append(("FAIL", "index-theme-valid",
                      f"`[Icon Theme]` thiếu khoá bắt buộc `{key}`"))
    name = root.get("Name", "")
    if name and name != THEME.name:
        f.append(("FAIL", "index-theme-valid",
                  f"Name={name!r} khác tên thư mục theme {THEME.name!r} — bộ nạp "
                  "icon tra theme theo TÊN THƯ MỤC, lệch nhau thì theme không "
                  "được nhận diện"))

    declared = [d.strip() for d in root.get("Directories", "").split(",") if d.strip()]
    # 2: hai chiều giữa Directories và thư mục thật
    on_disk = existing_dirs()
    for d in declared:
        if not (THEME / d).is_dir():
            f.append(("FAIL", "directories-two-way",
                      f"`Directories` liệt kê `{d}` nhưng thư mục không tồn tại — "
                      "khai báo khống khả năng (vi phạm tiêu chí Done #1 của T15)"))
        elif not list((THEME / d).glob("*.svg")):
            f.append(("FAIL", "directories-two-way",
                      f"`{d}` tồn tại nhưng RỖNG — hoặc thêm icon, hoặc bỏ khỏi "
                      "Directories; thư mục rỗng làm gtk-update-icon-cache báo lỗi"))
    for d in sorted(on_disk - set(declared)):
        n = len(list((THEME / d).glob("*.svg")))
        f.append(("FAIL", "directories-two-way",
                  f"`{d}` có {n} SVG nhưng KHÔNG được liệt kê trong `Directories` "
                  "— số icon đó sẽ VÔ HÌNH dù tệp tồn tại"))
    dupes = {d for d in declared if declared.count(d) > 1}
    for d in sorted(dupes):
        f.append(("FAIL", "directories-two-way", f"`{d}` bị liệt kê trùng trong Directories"))

    # 3: section <-> thư mục
    sections = [s for s in cp.sections() if s != "Icon Theme"]
    for d in declared:
        if not cp.has_section(d):
            f.append(("FAIL", "sections-match-directories",
                      f"thiếu section `[{d}]` cho thư mục đã liệt kê — không có "
                      "section thì Size/Context/Type không xác định và icon bị bỏ qua"))
    for s in sections:
        if s not in declared:
            f.append(("FAIL", "sections-match-directories",
                      f"section `[{s}]` tồn tại nhưng `{s}` không nằm trong "
                      "`Directories` — section chết"))

    # 4 + 5: khoá trong section, và Context khớp ngữ nghĩa thư mục
    for s in sections:
        sec = cp[s]
        for key in ("Size", "Context", "Type"):
            if not sec.get(key):
                f.append(("FAIL", "section-keys", f"`[{s}]` thiếu khoá `{key}`"))
        typ = sec.get("Type", "Fixed")
        if typ not in ("Fixed", "Scalable", "Threshold"):
            f.append(("FAIL", "section-keys", f"`[{s}]` Type={typ!r} không hợp lệ"))
        if typ == "Scalable":
            for key in ("MinSize", "MaxSize"):
                if not sec.get(key):
                    f.append(("FAIL", "section-keys",
                              f"`[{s}]` Type=Scalable nhưng thiếu `{key}` — không có "
                              "khoảng thì bộ nạp không biết scale tới đâu"))
            try:
                if int(sec["MinSize"]) > int(sec["Size"]) or int(sec["MaxSize"]) < int(sec["Size"]):
                    f.append(("FAIL", "section-keys",
                              f"`[{s}]` Size phải nằm trong [MinSize, MaxSize]"))
            except (KeyError, ValueError):
                pass
        ctx = sec.get("Context", "")
        if ctx and ctx not in VALID_CONTEXTS:
            f.append(("FAIL", "context-matches-dir",
                      f"`[{s}]` Context={ctx!r} không phải Context hợp lệ"))
        # suy ra context mong đợi từ phần cuối tên thư mục (scalable/apps -> apps)
        leaf = s.rstrip("/").split("/")[-1]
        want = DIR_CONTEXT.get(leaf)
        if want and ctx and ctx != want:
            f.append(("FAIL", "context-matches-dir",
                      f"`[{s}]` khai Context={ctx!r} nhưng thư mục là `{leaf}` "
                      f"-> phải là `{want}`. Sai Context thì bộ nạp lọc mất ứng viên"))

    # 6: Inherits phải chốt bằng hicolor
    inherits = [x.strip() for x in root.get("Inherits", "").split(",") if x.strip()]
    if not inherits:
        f.append(("FAIL", "inherits-fallback", "`Inherits` rỗng — icon thiếu sẽ BIẾN MẤT"))
    else:
        if inherits[-1] != "hicolor":
            f.append(("FAIL", "inherits-fallback",
                      f"`Inherits` phải kết thúc bằng `hicolor` (chốt chặn cuối, luôn "
                      f"tồn tại theo spec). Đang là: {inherits}"))
        # Mint-Y phải đứng trước để theme dùng được trên Mint mà không vỡ ở nơi khác
        if "Mint-Y" not in inherits:
            f.append(("WARN", "inherits-fallback",
                      "không kế thừa `Mint-Y` — trên Linux Mint 22.3 đó là theme "
                      "chắc chắn có mặt và cung cấp phần lớn icon còn thiếu"))
        if name in inherits:
            f.append(("FAIL", "inherits-fallback", "theme không được kế thừa chính nó"))

    # 7: phủ đủ tập lõi theo fixture
    want = load_fixture(FIXTURE)
    if not want:
        f.append(("FAIL", "core-coverage", f"fixture rỗng hoặc không đọc được: {FIXTURE}"))
    # Dạng khoá thống nhất: `<context>/<tên-icon>`, ví dụ `apps/xplayer` hay
    # `symbolic/actions/edit-find-symbolic`.
    #
    # PHẢI bỏ tiền tố `scalable/`: đó là chi tiết LƯU TRỮ (nói rằng thư mục chứa
    # SVG Type=Scalable), không phải một phần tên icon mà hệ thống nhìn thấy. Nếu
    # giữ lại thì fixture phải viết `scalable/apps/xplayer`, tức hợp đồng bị dính
    # vào cách sắp xếp thư mục và sẽ vỡ khi đổi layout.
    # Tiền tố `symbolic/` thì GIỮ, vì `-symbolic` là một biến thể icon khác thật sự
    # (GTK tra theo tên, và bản symbolic phải đơn sắc) — nó cần được đếm riêng.
    #
    # Hai lần sai ở đoạn này: bản đầu gộp cả ba thư mục symbolic/* thành một tiền
    # tố `symbolic/` nên mất context; bản thứ hai quên bỏ `scalable/` nên chỉ khớp
    # được 14/75 icon.
    have: set[str] = set()
    for p in THEME.rglob("*.svg"):
        rel = p.parent.relative_to(THEME).as_posix()
        if rel.startswith("scalable/"):
            rel = rel[len("scalable/"):]
        have.add(f"{rel}/{p.stem}")
    for entry in want:
        if entry not in have:
            f.append(("FAIL", "core-coverage", f"thiếu icon lõi `{entry}`"))
    if verbose:
        print(f"  · core coverage {len([e for e in want if e in have])}/{len(want)}; "
              f"tổng {len(have)} icon trên đĩa", file=sys.stderr)

    # 8-11: kiểm tra từng tệp SVG
    colors = token_hex_values()
    ink = token_hex("mg-color-gray-400")
    for p in sorted(THEME.rglob("*.svg")):
        rel = p.relative_to(THEME).as_posix()
        txt = p.read_text(encoding="utf-8")

        if not ICON_NAME_RE.match(p.stem):
            f.append(("FAIL", "naming", f"{rel}: tên icon sai quy ước `{p.stem}`"))

        try:
            rootx = ET.fromstring(txt)
        except ET.ParseError as exc:
            f.append(("FAIL", "svg-wellformed", f"{rel}: XML không parse được — {exc}"))
            continue
        if rootx.tag != f"{{{SVG_NS}}}svg":
            f.append(("FAIL", "svg-wellformed",
                      f"{rel}: thẻ gốc phải là <svg> có namespace, đang là {rootx.tag!r}"))
        vb = rootx.get("viewBox")
        if not vb:
            f.append(("FAIL", "svg-viewbox", f"{rel}: thiếu viewBox"))
        else:
            parts = re.split(r"[\s,]+", vb.strip())
            if len(parts) != 4 or [float(x) for x in parts] != [0.0, 0.0, 24.0, 24.0]:
                f.append(("FAIL", "svg-viewbox",
                          f"{rel}: viewBox phải là `0 0 24 24` (lưới thiết kế thống "
                          f"nhất), đang là `{vb}`"))
        for attr in ("width", "height"):
            if rootx.get(attr) != "24":
                f.append(("FAIL", "svg-viewbox",
                          f"{rel}: {attr} phải là 24 để 1 đơn vị SVG = 1px ở 1x, "
                          f"đang là {rootx.get(attr)!r}"))

        # không phụ thuộc mạng / không thẻ nguy hiểm
        scan = re.sub(r'\sxmlns(?::[\w-]+)?\s*=\s*"[^"]*"', "", txt)
        for m in EXTERNAL_RE.finditer(scan):
            frag = m.group(0)
            if frag.startswith("#"):
                continue
            f.append(("FAIL", "no-external-refs",
                      f"{rel}: tham chiếu ra ngoài `{frag.strip()[:60]}` — icon theme "
                      "không được tải gì từ Internet khi chạy"))
        for m in DANGEROUS_RE.finditer(txt):
            f.append(("FAIL", "no-external-refs",
                      f"{rel}: chứa thẻ <{m.group(1).lower()}> — không cần cho icon và "
                      "làm kết quả khác nhau giữa phiên bản librsvg"))
        # Không gradient ở BẤT KỲ đâu trong icon theme (icon-spec.md mục 6).
        # Symbolic thì bắt buộc đơn sắc vì GTK tô lại bằng kênh alpha; icon thường
        # thì gradient giả định một hướng sáng và một nền, nên sẽ sai trên nền khác.
        if re.search(r"<\s*(linear|radial)Gradient\b", txt, re.I):
            f.append(("FAIL", "no-gradient",
                      f"{rel}: chứa gradient — icon theme không dùng gradient ở bất "
                      "kỳ đâu (khác với corner-ripple.svg của T05, đó là asset của "
                      "Cinnamon theme chứ không phải icon)"))
        if RGBA_RE.search(txt):
            f.append(("FAIL", "no-rgba-in-svg",
                      f"{rel}: dùng rgba() — librsvg hỗ trợ không nhất quán giữa các "
                      "phiên bản; hãy dùng hex + fill-opacity/stroke-opacity"))

        # màu phải tra ngược được về token
        for m in HEX_RE.finditer(txt):
            h = m.group(0).lower()
            if len(h) == 4:
                h = "#" + "".join(c * 2 for c in h[1:])
            if h not in colors:
                f.append(("FAIL", "colors-are-token-values",
                          f"{rel}: màu `{m.group(0)}` không khớp giá trị token nào "
                          f"trong {TOKENS.relative_to(REPO)}"))

        # symbolic phải đơn sắc
        # Viết bằng startswith thay vì ghép dấu chéo vào đầu rồi tìm tiền tố
        # symbolic. Lý do: tests/lint/test_safety.py của Agent 1 bắt MỌI chuỗi có
        # nháy mở đầu bằng dấu chéo trong tools/, vì nó quét đường ghi hệ thống
        # tuyệt đối. Ở đây chỉ là kiểm tra TIỀN TỐ của một path TƯƠNG ĐỐI bên trong
        # theme, không phải đường ghi. Gate đó quét cả TEXT THÔ nên comment nhắc tới
        # chuỗi kia cũng đủ làm nó đỏ. Đã dính đúng lớp dương tính giả này ở T09 với
        # đường dẫn GResource. Sửa về phía mình, KHÔNG nới cổng của Agent 1.
        if rel.startswith("symbolic/") or p.stem.endswith("-symbolic"):
            seen = set()
            for m in COLOUR_ATTR_RE.finditer(txt):
                v = m.group(2).strip().lower()
                if v not in ("none",):
                    seen.add(v)
            if len(seen) > 1:
                f.append(("FAIL", "symbolic-monochrome",
                          f"{rel}: icon symbolic dùng {len(seen)} màu {sorted(seen)}. "
                          "GTK tô lại icon symbolic theo màu chữ bằng KÊNH ALPHA nên "
                          "mọi hình phải cùng một màu, không gradient."))
            if len(seen) == 1 and seen != {"#000000"}:
                f.append(("WARN", "symbolic-monochrome",
                          f"{rel}: icon symbolic dùng {next(iter(seen))} thay vì đen "
                          "thuần. Về chức năng vẫn chạy (GTK tô lại bằng KÊNH ALPHA "
                          "nên hue bị bỏ qua), nhưng lệch quy ước ở "
                          "docs/design-system/icon-spec.md mục 4.2"))
            if "gradient" in txt.lower():
                f.append(("FAIL", "symbolic-monochrome",
                          f"{rel}: icon symbolic chứa gradient"))
            if not p.stem.endswith("-symbolic"):
                f.append(("WARN", "symbolic-monochrome",
                          f"{rel} nằm trong thư mục symbolic nhưng tên không có hậu "
                          "tố `-symbolic` — GTK tra bản symbolic theo TÊN, không theo "
                          "thư mục"))

    # 11b: màu nét vẽ phải đạt >= 3:1 trên CẢ hai nền
    if ink:
        try:
            from contrast import parse_hex, to_rgb, contrast_ratio
            dark = token_hex("mg-surface-base") or "#121316"
            for label, bg in (("nền sáng", LIGHT_BACKDROP), ("nền tối", dark)):
                r = contrast_ratio(to_rgb(parse_hex(ink)), to_rgb(parse_hex(bg)))
                if r < 3.0:
                    f.append(("FAIL", "ink-contrast-both-backdrops",
                              f"màu nét vẽ $mg-color-gray-400 ({ink}) chỉ đạt {r:.2f}:1 "
                              f"trên {label} {bg} — dưới ngưỡng 3:1 của WCAG 1.4.11"))
            if verbose:
                dark = token_hex("mg-surface-base") or "#121316"
                a = contrast_ratio(to_rgb(parse_hex(ink)), to_rgb(parse_hex(LIGHT_BACKDROP)))
                b = contrast_ratio(to_rgb(parse_hex(ink)), to_rgb(parse_hex(dark)))
                print(f"  · nét vẽ {ink}: {a:.2f}:1 trên trắng, {b:.2f}:1 trên {dark}",
                      file=sys.stderr)
        except Exception as exc:  # pragma: no cover
            f.append(("SKIP", "ink-contrast-both-backdrops",
                      f"không import được contrast.py: {exc}"))

    # 12: MANIFEST hai chiều
    if not MANIFEST.exists():
        f.append(("FAIL", "manifest", f"thiếu {MANIFEST} (tiêu chí Done #7 của T15)"))
    else:
        mtxt = MANIFEST.read_text()
        for entry in want:
            # Lấy TÊN ICON (phần cuối), không phải cả path. Với mục symbolic thì
            # entry là `symbolic/actions/edit-find-symbolic`; MANIFEST liệt kê chúng
            # theo nhóm `actions/` rồi mới tới tên, nên tìm nguyên chuỗi
            # `actions/edit-find-symbolic` sẽ không bao giờ thấy -> 14 cảnh báo giả.
            icon = entry.rsplit("/", 1)[-1]
            if icon not in mtxt:
                f.append(("WARN", "manifest",
                          f"MANIFEST.md không nhắc `{icon}` — người đọc không tra "
                          "được icon này thuộc nhóm nào"))
        for key in ("Inherits", "fallback", "giấy phép", "chưa có"):
            if key.lower() not in mtxt.lower():
                f.append(("FAIL", "manifest",
                          f"MANIFEST.md thiếu mục nói về `{key}` — tiêu chí Done #7 "
                          "yêu cầu ghi rõ icon chưa có + fallback + giấy phép"))

    # 13: không có tệp lạ trong theme
    for p in sorted(THEME.rglob("*")):
        if p.is_file() and p.suffix.lower() not in (".svg", ".md", ".theme", ".sh"):
            f.append(("WARN", "stray-file",
                      f"{p.relative_to(THEME)}: tệp không phải SVG/MANIFEST/index.theme "
                      "— nếu là raster thì phải có pipeline render và khai báo thật"))
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint icon theme MintOS-Glass (T15)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    print(f"icon_theme · {THEME.relative_to(REPO)}")
    f = findings(verbose=a.verbose)
    fails = [x for x in f if x[0] == "FAIL"]
    warns = [x for x in f if x[0] == "WARN"]
    for sev, cid, msg in f:
        print(f"  [{sev}] {cid}: {msg}")
    if fails:
        print(f"FAIL — {len(fails)} lỗi, {len(warns)} cảnh báo")
        return 1
    print(f"OK — 0 lỗi" + (f", {len(warns)} cảnh báo" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
