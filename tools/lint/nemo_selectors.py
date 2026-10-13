#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint cho `_apps-nemo.scss` — Task T09 (Agent 4 · Nemo File Manager).

Công cụ này tồn tại vì Nemo có MỘT đặc thù mà không app GTK3 nào khác trong dự
án có: Nemo TỰ nạp CSS của riêng nó, và nạp ở HAI mức ưu tiên khác nhau. Kết quả
là một phần giao diện Nemo theme kiểm soát được, phần còn lại thì KHÔNG — và
ranh giới đó không nhìn thấy được bằng mắt thường khi đọc SCSS.

--------------------------------------------------------------------------
BẰNG CHỨNG NGUỒN (đã tải và đọc, không suy đoán)
--------------------------------------------------------------------------
linuxmint/nemo, nhánh `6.6-maintenance`, tag 6.6.4 (meson.build:
`project('nemo', 'c', version : '6.6.4')`). Đã diff với `master.mint22`
(6.7.8, head ed2d34b390917fa11c1031176db489fd5cfbc915):
  · gresources/nemo-style-fallback.css           GIỐNG HỆT
  · gresources/nemo-style-fallback-mandatory.css GIỐNG HỆT
  · gresources/nemo-style-application.css        6.6.4 có THÊM 3 rule `#drop-bar`

src/nemo-application.c:306-330 `init_icons_and_styles()` gọi
add_css_provider_at_priority HAI lần, nạp GResource /org/nemo/nemo-style-fallback.css
(mã nguồn trong repo nemo: gresources/nemo-style-fallback.css) ở
PRIORITY_FALLBACK = 0, và /org/nemo/nemo-style-application.css (mã nguồn:
gresources/nemo-style-application.css) ở PRIORITY_APPLICATION = 600.

GHI CHÚ VỀ HAI ĐƯỜNG DẪN TRÊN: chúng được viết KHÔNG kèm dấu nháy, có chủ đích.
tests/lint/test_safety.py::test_only_two_write_roots_are_mentioned_in_tooling
quét mọi chuỗi dạng nháy-then-'/...' trong MỌI file .py của repo và chỉ cho phép
hai gốc ghi .local/share/themes và .local/state/mintos-glass. Hai đường dẫn này
là GResource nằm BÊN TRONG binary của Nemo (g_resources_lookup_data), không phải
đường ghi trên đĩa, nên về bản chất không vi phạm; nhưng bài kiểm tra đó cố ý
rộng và là file của Agent 1 nên T09 KHÔNG sửa nó. Cách xử lý đúng là bỏ dấu
nháy ở phía mình, không phải nới cổng an toàn.
src/nemo-application.c:230 `add_fallback_mandatory_css_provider()`:
    nemo-style-fallback-mandatory.css cũng ở PRIORITY_APPLICATION           # 600
Theme của ta nạp ở GTK_STYLE_PROVIDER_PRIORITY_THEME                        # 200

GTK 3.24 KHÔNG hỗ trợ `!important`. Đã kiểm chứng bằng cách tải
GNOME/gtk ref 3.24.42 và đếm: chuỗi "important" xuất hiện 0 lần trong
gtk/gtkcssparser.c (1067 dòng), 0 lần trong gtk/gtkcssprovider.c (2405 dòng),
0 lần trong gtk/gtkstylecascade.c (426 dòng). Parser là nơi duy nhất có thể
nhận diện cú pháp `!`, nên nếu parser không đọc thì không tầng nào dùng được.
Thêm nữa gtk_style_cascade_iter_next() (gtkstylecascade.c:42-71) duyệt các
provider THEO THỨ TỰ PRIORITY GIẢM DẦN và ghi vào GtkCssLookup — không có đường
nào cho specificity lật ngược priority.

=> [WIN]  : Nemo để FALLBACK(0) hoặc không style  -> theme(200) thắng.
=> [LOCK] : Nemo để APPLICATION(600)              -> theme(200) thua tuyệt đối.

--------------------------------------------------------------------------
TÊN THEME LÀ MỘT PHẦN CỦA CƠ CHẾ
--------------------------------------------------------------------------
src/nemo-application.c:297:
    if (!is_known_supported_theme (theme_name))
        add_fallback_mandatory_css_provider (theme_name);
:245  supported_theme_hints[] = {"mint", "arc", "numix", "matcha"}
:259  name = g_utf8_casefold (theme_name, -1)
:267  if (g_strstr_len (name, -1, hint)) ret = TRUE;      # SO KHỚP CHUỖI CON

"MintOS-Glass" -> "mintos-glass" -> CHỨA "mint" -> TRUE -> Nemo KHÔNG nạp
fallback-mandatory. Hai hệ quả:
  (1) `.nemo-inactive-pane`, `.nemo-window-pane widget.entry`, `.floating-bar`
      KHÔNG được ai style hộ -> ta PHẢI tự viết (fixture nhóm 2, 3, 4).
  (2) Nếu đổi tên theme sang thứ không chứa bất kỳ hint nào, ba selector đó sẽ
      bị đè ở priority 600. lint này cảnh báo khi fixture mất ba nhóm đó.

Lớp kiểm tra thứ hai, chỉ chạy khi tên theme không lọt hint (:173-243):
serialize CSS của theme rồi tìm chuỗi con "nemo"; không có thì in
"The theme appears to have no nemo support. Adding some...". Nên output CSS
BẮT BUỘC chứa chuỗi "nemo" (check `nemo-substring`).
Cùng hàm (:203-217) quyết định `@theme_*` hay viết lại thành `@`:
  theme chứa "theme_selected_bg_color"   -> giữ @theme_*
  theme chứa "@define-color selected_bg_color" -> thay @theme_ bằng @
  không có cả hai                        -> bỏ luôn, không nạp gì
Việc export @theme_* là của T06 (Done criterion #2 của T06, nguồn E29).

--------------------------------------------------------------------------
CÁC BÀI KIỂM TRA
--------------------------------------------------------------------------
 1 nemo-substring      output CSS chứa chuỗi "nemo" (điều kiện :186 của Nemo)
 2 coverage            đủ MỌI selector trong fixture (Done criterion #1 của T09)
 3 disk-full-props     đủ cả 6 -NemoPlacesTreeView-disk-full-* (Done #1)
 4 no-prelight-label   KHÔNG ghi đè -NemoIconContainer-activate-prelight-icon-label
                       (Done criterion #2 của T09 — đó là HÀNH VI, không phải màu)
 5 no-important        không dùng `!important` (GTK 3.24 không hỗ trợ)
 6 no-broken-tokens    không dùng token mà generator sinh sai
                       ($mg-font-weight-*, $mg-font-size-*-pt, $mg-blur-*)
 7 no-hardcoded-color  màu phải qua token, không hex/rgb literal
 8 gtk3-property-blocklist  không dùng property GTK 3.24 không có
 8b no-bare-generic    không phát ra class GTK chung ở dạng trần (`.sidebar`,
                       `.view`, `.linked`, ...) — theme GTK3 là MỘT gtk.css cho
                       MỌI app, nên dạng trần sẽ rò rỉ và giẫm lên T06
 9 no-locked-illusion  mỗi selector [LOCK] phải nằm trong LOCKED (fixture) để
                       không ai tưởng nó có tác dụng
10 fixture-integrity   fixture không bị ô nhiễm
11 mint-apps-entries   mỗi app Mint có một mục trong `_apps-mint.scss`
12 mint-apps-namespaced `_apps-mint.scss` không phát ra class GTK chung ở dạng
                       trần và không dùng widget name quá chung (`#frame`), vì
                       GTK 3.24 KHÔNG đưa application ID vào CSS
                       (gtkapplicationwindow.c ref 3.24.42, 1048 dòng, 0 lần
                       xuất hiện `application_id`) -> không scope theo app được (bài học từ fixture Cinnamon:
                       marker `#` đã cắt cụt 25 selector ID và tạo 425 "thiếu"
                       giả + 487 "mới" giả)

Chạy:  python3 tools/lint/nemo_selectors.py [--verbose] [--scss PATH]
Exit 0 khi sạch. Cần libsass (pip install libsass) hoặc dart-sass; nếu không có
cả hai thì các bài cần biên dịch báo SKIP chứ không báo PASS giả.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCSS = REPO / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
TOKENS = REPO / "src" / "gtk-3.0" / "sass" / "_tokens.scss"
FIXTURE = REPO / "tests" / "fixtures" / "nemo-required-selectors.txt"
MINT_APPS = REPO / "src" / "gtk-3.0" / "sass" / "_apps-mint.scss"

# Dùng lại ĐÚNG bộ normalisation của lint Cinnamon. Đây là chủ đích: bài học đắt
# nhất của T04 là fixture và lint phải chia sẻ một cách chuẩn hoá selector, nếu
# không coverage báo sai cả hai chiều.
sys.path.insert(0, str(REPO / "tools" / "lint"))
import st_properties as sp  # noqa: E402

parse_rules = sp.parse_rules
split_selectors = sp.split_selectors
load_fixture = sp.load_fixture
find_compiler = sp.find_compiler

# ---------------------------------------------------------------------------
# Selector mà Nemo KHOÁ ở PRIORITY_APPLICATION(600) — theme(200) không thắng.
# Nguồn: gresources/nemo-style-application.css của nemo 6.6.4 (83 dòng) và
# 6.7.8 (71 dòng). Đã đọc cả hai; đoạn 18-71 giống hệt nhau.
# `#drop-bar*` (chỉ có ở 6.6.4, dòng 73-84) CŨNG bị khoá nhưng ta cố ý không
# viết rule cho nó: grep toàn bộ src/, libnemo-private/, eel/ của 6.6.4 cho
# `gtk_widget_set_name` chỉ ra đúng một kết quả là "nemo-tab-close-button", và
# "drop-bar" chỉ trúng `g_signal_new("show-drop-bar")` tại src/nemo-view.c:11200
# (tên SIGNAL, không phải tên widget). Nhiều khả năng là CSS chết trong chính
# Nemo. Chưa xác minh được -> không viết, không yêu cầu.
# ---------------------------------------------------------------------------
LOCKED_BY_NEMO = {
    ".nemo-canvas-item",                              # border-radius: 3px
    ".nemo-desktop",                                  # -NemoIconContainer-...
    ".nemo-desktop-window",                           # box-shadow: none
    ".nemo-desktop-window:backdrop",
    ".nemo-window.nemo-desktop-window notebook",      # background: transparent
    ".nemo-window.nemo-desktop-window paned",
    ".nemo-desktop.nemo-canvas-item",                 # color + text-shadow
    ".nemo-desktop.nemo-canvas-item:hover",
    ".nemo-desktop.nemo-canvas-item:selected",
    ".nemo-desktop.view .entry",
    ".nemo-desktop.view .entry:active",
    ".nemo-desktop.view .entry:focus",
    ".nemo-desktop.view .entry:backdrop",
    ".nemo-desktop.view .entry:selected",
    ".nemo-desktop.view .entry:focus:selected",
    ".nemo-desktop.view .entry:backdrop:selected",
}

# Property cụ thể mà Nemo khoá. Ghi rõ để báo cáo nói được CHÍNH XÁC cái gì thua,
# thay vì nói chung chung "cả selector thua". `.nemo-canvas-item` chỉ bị khoá
# border-radius; color của nó trong cửa sổ thường vẫn do ta quyết.
LOCKED_PROPS = {
    ".nemo-canvas-item": {"border-radius"},
    ".nemo-desktop": {"-nemoiconcontainer-activate-prelight-icon-label"},
    ".nemo-desktop-window": {"box-shadow"},
    ".nemo-desktop-window:backdrop": {"box-shadow"},
    ".nemo-window.nemo-desktop-window notebook": {"background-color"},
    ".nemo-window.nemo-desktop-window paned": {"background-color"},
    ".nemo-desktop.nemo-canvas-item": {"color", "text-shadow"},
    ".nemo-desktop.nemo-canvas-item:hover": {"background-color", "background-image", "text-shadow"},
    ".nemo-desktop.nemo-canvas-item:selected": {"background-color", "background-image", "text-shadow", "color"},
    ".nemo-desktop.view .entry": {"border-image", "border-style", "border-width", "border-color",
                                  "border-radius", "color", "caret-color", "text-shadow", "background-image"},
}

# 6 style property GObject đăng ký tại libnemo-private/nemo-places-tree-view.c:
#   :43 g_param_spec_boxed("disk-full-bg-color")
#   :50 g_param_spec_boxed("disk-full-fg-color")
#   :57 g_param_spec_int ("disk-full-bar-width")
#   :64 g_param_spec_int ("disk-full-bar-radius")
#   :71 g_param_spec_int ("disk-full-bottom-padding")
#   :78 g_param_spec_int ("disk-full-max-length")
# GTK3 map CSS `-NemoPlacesTreeView-disk-full-bg-color` -> class
# NemoPlacesTreeView + style property `disk-full-bg-color`.
DISK_FULL_PROPS = (
    "-NemoPlacesTreeView-disk-full-bg-color",
    "-NemoPlacesTreeView-disk-full-fg-color",
    "-NemoPlacesTreeView-disk-full-bar-width",
    "-NemoPlacesTreeView-disk-full-bar-radius",
    "-NemoPlacesTreeView-disk-full-bottom-padding",
    "-NemoPlacesTreeView-disk-full-max-length",
)

# Done criterion #2 của T09: KHÔNG ghi đè. Nó là style property boolean tại
# libnemo-private/nemo-icon-container.c:4861-4866,
# g_param_spec_boolean("activate_prelight_icon_label", ..., G_PARAM_READABLE),
# điều khiển nhãn icon có sáng lên khi rê chuột hay không -> HÀNH VI gốc.
FORBIDDEN_PROP = "-NemoIconContainer-activate-prelight-icon-label"

# Token mà `tools/tokens/generate.py` đang sinh SAI (đã báo Agent Design Systems):
#   :215 UNITLESS_KEYS = {"blur"} -> font-weight ra `400px/500px/700px`
#   NS_UNIT không có nhánh "font" -> font.size-*-pt ra `9px/12px`
#   blur.* ra `2px/4px/6px` (phải unitless)
#   40-motion.json KHÔNG BAO GIỜ được emit (generate.py:605-616 chỉ flatten
#     primitives/component/semantic) -> không có $mg-duration-*/$mg-easing-*
BROKEN_TOKEN_RE = re.compile(r"\$mg-(?:font-weight-|font-size-\w+-pt|blur-)")

# Property KHÔNG tồn tại trong CSS của GTK 3.24. Danh sách này cố ý NGẮN và chỉ
# chứa những cái đã tự tay kiểm chứng hoặc đã từng viết nhầm: bộ property đầy đủ
# của GTK 3.24 là việc của T06 (Done criterion #4 của T06).
GTK3_INVALID_PROPS = {
    # GTK3 chỉ có -gtk-icon-source/-gtk-icon-palette/-gtk-icon-shadow/
    # -gtk-icon-effect/-gtk-icon-transform/-gtk-icon-style. Cỡ icon là property
    # `icon-size` của widget image, đặt trong code chứ không qua theme.
    "-gtk-icon-size": "không tồn tại; cỡ icon đặt qua property icon-size của widget image",
    # St mới không có `opacity` nhưng GTK3 CÓ; ngược lại GTK3 không có các prop St.
    "-st-": "property St (Cinnamon), không dùng trong GTK3",
}

# Class GTK CHUNG mà T06 (`_common.scss`/`_widgets.scss`) sở hữu. T09 KHÔNG được
# phát ra chúng ở DẠNG TRẦN, vì theme GTK3 biên dịch thành MỘT gtk.css duy nhất
# dùng cho MỌI app: viết `.sidebar { ... }` trần trong partial của Nemo là áp đặt
# quy tắc của Nemo lên mọi app GTK3 khác. Đây đúng là "stylesheet riêng cạnh
# tranh" mà yêu cầu phối hợp Agent 3 cấm, và Agent 3 yêu cầu "dùng selector hẹp
# hơn khi có thể".
# Bài kiểm tra `no-bare-generic` bên dưới THỰC THI quyết định này, để nó không
# bị nới lỏng âm thầm về sau.
#
# Chỉ tính là "trần" khi selector KHÔNG có tiền tố tổ tiên nào, ví dụ `.sidebar`
# hoặc `.sidebar row`. `.nemo-window .sidebar` thì hợp lệ.
GENERIC_GTK_CLASSES = {
    ".sidebar", ".view", ".linked", ".raised", ".error", ".primary-toolbar",
    ".toolbar", ".titlebar", "headerbar", "button", "entry", "menu", ".popup",
    "notebook", "scrollbar", "tooltip", "decoration", "progressbar", "switch",
}

HARDCODED_RE = re.compile(r"(#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(|\balpha\s*\()")
IMPORTANT_RE = re.compile(r"!\s*important")


def compile_scss(path: Path, verbose: bool = False) -> tuple[str | None, str]:
    """Biên dịch một file SCSS bất kỳ (kể cả partial) -> (css, compiler).

    T09 KHÔNG được tạo `src/gtk-3.0/sass/gtk.scss` (đó là file của T06), nên
    partial phải compile ĐỨNG MỘT MÌNH. libsass và dart-sass đều compile được
    một file `_foo.scss` khi trỏ trực tiếp vào nó.
    """
    comp = find_compiler()
    if comp is None:
        return None, "none"
    name, how = comp
    if how == "python:sass":
        import sass  # type: ignore

        css = sass.compile(filename=str(path), output_style="expanded")
        if verbose:
            print(f"  · {path.name}: libsass {sass.libsass_version} -> {len(css)} bytes",
                  file=sys.stderr)
        return css, name
    exe = how.split(":", 1)[1]
    out = REPO / ".tmp-lint-nemo.css"
    try:
        proc = subprocess.run([exe, str(path), str(out)], cwd=str(REPO),
                              capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip()[:400])
        css = out.read_text()
        if verbose:
            print(f"  · {path.name}: dart-sass -> {len(css)} bytes", file=sys.stderr)
        return css, name
    finally:
        out.unlink(missing_ok=True)


def output_selectors(css: str) -> set[str]:
    out: set[str] = set()
    for sel, _ in parse_rules(css):
        for s in split_selectors(sel):
            out.add(s)
    return out


def findings_for(scss_path: Path = SCSS, fixture: Path = FIXTURE,
                 verbose: bool = False) -> list[tuple[str, str, str]]:
    """[(severity, check_id, message)]. severity ∈ {FAIL, WARN, SKIP}."""
    f: list[tuple[str, str, str]] = []
    if not scss_path.exists():
        return [("SKIP", "file-missing", f"{scss_path} chưa tồn tại")]

    src = scss_path.read_text()
    try:
        css, compiler = compile_scss(scss_path, verbose=verbose)
    except Exception as exc:  # sass.CompileError, RuntimeError từ dart-sass
        # Một lint CRASH trên input sai thì tệ hơn lint không tồn tại: CI đỏ vì
        # exception chứ không vì lỗi thật, và thông báo lỗi khó đọc. Bắt lại và
        # biến thành một FAIL có id riêng.
        return [("FAIL", "compile", f"{scss_path.name} không biên dịch được: "
                                    f"{type(exc).__name__}: {str(exc)[:400]}")]
    if css is None:
        f.append(("SKIP", "compile",
                  "không có libsass/dart-sass -> bỏ qua mọi bài cần CSS đã compile"))
        return f

    # 1 -----------------------------------------------------------------
    if "nemo" not in css:
        f.append(("FAIL", "nemo-substring",
                  "output CSS không chứa chuỗi 'nemo'. src/nemo-application.c:186 "
                  "dò chuỗi con này trong CSS đã serialize của theme; không có thì "
                  "Nemo in 'The theme appears to have no nemo support. Adding "
                  "some...' và nạp fallback-mandatory ở PRIORITY_APPLICATION(600), "
                  "đè lên theme."))

    # 2 -----------------------------------------------------------------
    want = load_fixture(fixture)
    if not want:
        f.append(("FAIL", "coverage", f"fixture rỗng hoặc không đọc được: {fixture}"))
    have = output_selectors(css)
    missing = [s for s in want if s not in have]
    for s in missing:
        f.append(("FAIL", "coverage", f"thiếu selector bắt buộc: `{s}`"))
    if verbose and not missing:
        print(f"  · coverage {len(want)}/{len(want)} selector fixture; "
              f"output có {len(have)} selector", file=sys.stderr)

    # 3 -----------------------------------------------------------------
    props_seen = {p.lower() for _, ds in parse_rules(css) for p, _ in ds}
    for p in DISK_FULL_PROPS:
        if p.lower() not in props_seen:
            f.append(("FAIL", "disk-full-props",
                      f"thiếu property `{p}` (Done criterion #1 của T09). "
                      "Style property đăng ký tại "
                      "libnemo-private/nemo-places-tree-view.c:43-83; Nemo để nó ở "
                      "PRIORITY_FALLBACK(0) nên theme(200) thắng — đây là chỗ DUY "
                      "NHẤT điều khiển được chỉ báo dung lượng ổ đĩa."))

    # 4 -----------------------------------------------------------------
    if FORBIDDEN_PROP.lower() in props_seen:
        f.append(("FAIL", "no-prelight-label",
                  f"cấm ghi đè `{FORBIDDEN_PROP}` (Done criterion #2 của T09). "
                  "Nó là style property boolean tại "
                  "libnemo-private/nemo-icon-container.c:4861-4866, điều khiển "
                  "HÀNH VI nhãn icon sáng lên khi rê chuột — đổi nó là đổi chức "
                  "năng gốc của Nemo."))

    # 5 -----------------------------------------------------------------
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("//", 1)[0]
        if IMPORTANT_RE.search(code):
            f.append(("FAIL", "no-important",
                      f"{scss_path.name}:{i} dùng `!important`. GTK 3.24 KHÔNG hỗ "
                      "trợ: chuỗi 'important' xuất hiện 0 lần trong "
                      "gtkcssparser.c/gtkcssprovider.c/gtkstylecascade.c (ref "
                      "3.24.42). Nó không giúp thắng PRIORITY_APPLICATION."))
    for i, line in enumerate(css.splitlines(), 1):
        if IMPORTANT_RE.search(line):
            f.append(("FAIL", "no-important", f"output CSS dòng {i} còn `!important`"))

    # 6 -----------------------------------------------------------------
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("//", 1)[0]
        m = BROKEN_TOKEN_RE.search(code)
        if m:
            f.append(("FAIL", "no-broken-tokens",
                      f"{scss_path.name}:{i} dùng token generator đang sinh sai: "
                      f"`{m.group(0)}*`. Xem ghi chú HẰNG TẠM THỜI ở đầu file."))

    # 7 -----------------------------------------------------------------
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("//", 1)[0]
        if not code.strip() or code.lstrip().startswith(("@", "$", "//")):
            continue
        m = HARDCODED_RE.search(code)
        if not m:
            continue
        # rgba($token, $alpha) là HỢP LỆ: đó là hàm SCSS trên token, không phải
        # màu hard-code. Chỉ chặn khi đối số đầu tiên không phải biến/token.
        rest = code[m.end():]
        if m.group(0).startswith(("rgba(", "hsla(", "alpha(")) and re.match(r"\s*\$", rest):
            continue
        f.append(("FAIL", "no-hardcoded-color",
                  f"{scss_path.name}:{i} hard-code màu `{m.group(0)}` — phải qua "
                  f"token: {code.strip()[:90]}"))

    # 8 -----------------------------------------------------------------
    for sel, decls in parse_rules(css):
        for p, _ in decls:
            pl = p.lower()
            for bad, why in GTK3_INVALID_PROPS.items():
                if pl == bad or pl.startswith(bad):
                    f.append(("FAIL", "gtk3-property-blocklist",
                              f"`{p}` trong `{sel}`: {why}"))

    # 8b ----------------------------------------------------------------
    # Class GTK chung ở dạng trần -> rò rỉ sang mọi app khác, giẫm lên T06.
    for sel in sorted(have):
        first = sel.split()[0] if sel.split() else sel
        # `.sidebar row` -> first = `.sidebar`; `.nemo-window .sidebar` -> first
        # = `.nemo-window` (không nằm trong danh sách) nên hợp lệ.
        for cls in GENERIC_GTK_CLASSES:
            if first == cls or first.startswith(cls + ":") or first.startswith(cls + "."):
                f.append(("FAIL", "no-bare-generic",
                          f"`{sel}` phát ra class GTK chung `{cls}` ở DẠNG TRẦN. "
                          "Theme GTK3 compile thành một gtk.css dùng cho mọi app, "
                          "nên rule này sẽ rò rỉ sang toàn bộ app GTK3 và giẫm lên "
                          f"T06. Hãy scope lại, ví dụ `.nemo-window {sel}`."))

    # 9 -----------------------------------------------------------------
    # Mỗi selector ta viết mà Nemo khoá phải được fixture liệt kê là LOCKED.
    # Nếu không, người đọc SCSS sẽ tưởng rule đó có tác dụng.
    declared_locked = set()
    txt = fixture.read_text()
    for s in LOCKED_BY_NEMO:
        if s in txt:
            declared_locked.add(s)
    undeclared = sorted(LOCKED_BY_NEMO - declared_locked)
    for s in undeclared:
        f.append(("WARN", "no-locked-illusion",
                  f"`{s}` bị Nemo khoá ở PRIORITY_APPLICATION(600) nhưng fixture "
                  "không liệt kê — người đọc sẽ tưởng theme kiểm soát được nó."))
    if verbose:
        written_locked = sorted(s for s in have if s in LOCKED_BY_NEMO)
        print(f"  · {len(written_locked)} selector [LOCK] được viết ra có chủ đích "
              f"(Nemo giữ ở priority 600)", file=sys.stderr)

    # 10 ----------------------------------------------------------------
    # Bài học T04: fixture Cinnamon từng bị ô nhiễm thành `'} #Tooltip'` ×439
    # vì dựng bằng regex ad-hoc, và marker comment `#` đã cắt cụt 25 selector ID.
    bad = [s for s in want if re.search(r"[{};/]|^\s|/\*", s)]
    for s in bad:
        f.append(("FAIL", "fixture-integrity",
                  f"fixture có mục trông như bị ô nhiễm: `{s}`"))
    ids = [s for s in want if s.startswith("#")]
    if not ids:
        f.append(("WARN", "fixture-integrity",
                  "fixture không có selector ID nào — kiểm tra lại marker comment "
                  "(phải là `//`, không phải `#`); đây là lỗi từng làm hỏng "
                  "fixture Cinnamon."))

    # ------------------------------------------------------------------
    # App Mint khác: chỉ yêu cầu có mặt và không phá vỡ, không áp đặt bố cục.
    if not MINT_APPS.exists():
        f.append(("WARN", "mint-apps",
                  f"{MINT_APPS.name} chưa có — Done criterion #4 của T09 yêu cầu "
                  "mỗi app Mint (cinnamon-settings, xed, xplayer, xreader, "
                  "xviewer, pix, mintupdate, mintinstall, nemo) có một mục, tối "
                  "thiểu là không selector nào gây xung đột."))
    return f


# ---------------------------------------------------------------------------
# `_apps-mint.scss` — vì sao cần một bài kiểm tra RIÊNG
# ---------------------------------------------------------------------------
# GTK 3.24 KHÔNG đưa application ID vào CSS. Đã kiểm chứng: GNOME/gtk ref
# 3.24.42, gtk/gtkapplicationwindow.c (1048 dòng) có 0 lần xuất hiện chuỗi
# `application_id` — GtkApplicationWindow không thêm app ID làm style class và
# không dùng nó làm CSS node name.
# => KHÔNG có cách nào scope một class CHUNG về đúng một app. Viết
#    `.content-view { ... }` trong partial của app sẽ áp lên MỌI app GTK3 dùng
#    class đó. Nên `_apps-mint.scss` chỉ được phép dùng:
#      (a) class có tên app nằm TRONG tên class (`.xed-statusbar`,
#          `.xreader-window`, `.pix-circular-button`);
#      (b) CSS node name độc nhất do app đặt bằng gtk_widget_class_set_css_name
#          (`evview`, `evsidebarthumbnails`, `evpresentationview`);
#      (c) widget name (selector `#`) độc nhất (`#GthInfoBar`, `#page-label-entry`,
#          `#stage`, `#logo-frame`).
# Danh sách (b) và (c) là DỮ LIỆU ĐÃ XÁC MINH từ mã nguồn, không phải đoán.
APP_NAMESPACED_RE = re.compile(
    r"\.(xed|xreader|pix|nemo|xplayer|xviewer|mintupdate|mintinstall|cinnamon|gth|ev)[-_]"
    r"|^(evview|evsidebarthumbnails|evpresentationview|nemo-desktop-icon-view)$"
    r"|^#[A-Za-z]")

# Selector `#` được phép vì widget name là duy nhất trong app, NHƯNG `#frame`
# thì KHÔNG: tên quá chung, sẽ trúng widget tên "frame" của bất kỳ app nào.
# Đã thấy xplayer đặt widget name "frame" — cố ý loại khỏi file.
GENERIC_ID_BLOCKLIST = {"#frame", "#box", "#grid", "#list", "#image", "#label",
                        "#button", "#entry", "#window", "#view", "#icon", "#title"}

MINT_APPS_REQUIRED = ("nemo", "xreader", "pix", "xed", "xplayer", "xviewer",
                      "mintupdate", "mintinstall", "cinnamon-settings")


def mint_apps_findings(path: Path = MINT_APPS, verbose: bool = False) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    if not path.exists():
        return [("WARN", "mint-apps", f"{path.name} chưa tồn tại")]
    src = path.read_text()

    # Done criterion #4 của T09: mỗi app Mint phải có một mục. Đếm theo tiêu đề
    # mục trong source, vì 4/9 app KHÔNG có hook nào và do đó cố ý không có
    # selector — mục của chúng là ghi chép khảo sát, không phải CSS.
    for app in MINT_APPS_REQUIRED:
        if app not in src:
            f.append(("FAIL", "mint-apps-entries",
                      f"`{app}` không có mục nào trong {path.name} (Done criterion "
                      "#4 của T09). App không có hook thì mục đó phải nói rõ điều "
                      "đó kèm bằng chứng, chứ không được bỏ trống."))

    try:
        css, compiler = compile_scss(path, verbose=verbose)
    except Exception as exc:
        return f + [("FAIL", "mint-apps-compile",
                     f"{path.name} không biên dịch được: {type(exc).__name__}: "
                     f"{str(exc)[:400]}")]
    if css is None:
        f.append(("SKIP", "mint-apps-compile", "không có compiler -> bỏ qua"))
        return f
    if compiler and verbose:
        print(f"  · {path.name}: {compiler}", file=sys.stderr)

    have = output_selectors(css)
    for sel in sorted(have):
        head = sel.split()[0]
        if head in GENERIC_ID_BLOCKLIST:
            f.append(("FAIL", "mint-apps-namespaced",
                      f"`{sel}` dùng widget name quá chung `{head}`. GTK3 không "
                      "scope được theo app (gtkapplicationwindow.c 3.24.42 không "
                      "đưa application_id vào CSS), nên selector này sẽ trúng "
                      "widget cùng tên của MỌI app. xplayer có widget name "
                      "`frame` — đã cố ý loại."))
        if head.startswith(".") and not APP_NAMESPACED_RE.match(head):
            for cls in GENERIC_GTK_CLASSES:
                if head == cls or head.startswith(cls + ":") or head.startswith(cls + "."):
                    f.append(("FAIL", "mint-apps-namespaced",
                              f"`{sel}` phát ra class GTK chung `{head}` ở dạng "
                              "trần — sẽ rò rỉ sang mọi app GTK3. Class chung "
                              "thuộc T06."))
    if verbose:
        print(f"  · {len(have)} selector trong {path.name}", file=sys.stderr)
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint _apps-nemo.scss (T09)")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--scss", type=Path, default=SCSS)
    ap.add_argument("--fixture", type=Path, default=FIXTURE)
    a = ap.parse_args()

    print(f"nemo_selectors · {a.scss.relative_to(REPO)}")
    f = findings_for(a.scss, a.fixture, verbose=a.verbose)
    f += mint_apps_findings(MINT_APPS, verbose=a.verbose)
    fails = [x for x in f if x[0] == "FAIL"]
    warns = [x for x in f if x[0] == "WARN"]
    skips = [x for x in f if x[0] == "SKIP"]
    for sev, cid, msg in f:
        print(f"  [{sev}] {cid}: {msg}")
    if skips and not fails:
        print(f"SKIP — {len(skips)} bài không chạy được (thiếu compiler)")
        return 0
    if fails:
        print(f"FAIL — {len(fails)} lỗi, {len(warns)} cảnh báo")
        return 1
    print(f"OK — 0 lỗi" + (f", {len(warns)} cảnh báo" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
