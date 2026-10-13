#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/lint/st_properties.py — kiểm tra tĩnh CSS sinh ra cho Cinnamon/St.

Vì sao cần công cụ này
----------------------
St (thư viện widget của Cinnamon) KHÔNG phải một trình duyệt. Nó parse CSS bằng
libcroco rồi tự ánh xạ từng property trong `src/st/st-theme-node.c`. Hệ quả:

  * Property lạ bị BỎ QUA TRONG IM LẶNG — không cảnh báo, không lỗi.
  * Một số property có ngữ pháp NGƯỢC với CSS chuẩn. Ví dụ đã xác minh:
      `st_theme_node_get_transition_duration()`  st-theme-node.c:2317
        -> `st_theme_node_lookup_double(node, "transition-duration", ...)`  :2332
        -> :841 `if (term->type != TERM_NUMBER ||
                      term->content.num->type != NUM_GENERIC) continue;`
      nghĩa là St CHỈ nhận SỐ TRẦN. `transition-duration: 100ms` bị bỏ qua.
  * `st_theme_node_lookup_shadow()` :3348-3400 trả về đúng MỘT `StShadow *`,
      nên `box-shadow: a, b` (nhiều shadow) là KHÔNG hợp lệ.
  * `font_weight_from_term()` :2680 cũng yêu cầu NUM_GENERIC, nên
      `font-weight: 700px` bị bỏ qua.

Những lỗi này không thể phát hiện bằng mắt hay bằng trình duyệt; chỉ có đọc mã
nguồn C hoặc chạy trên máy Mint thật. Công cụ này đóng băng các kết luận đó
thành kiểm tra tự động chạy được trong CI, không cần Cinnamon.

Các kiểm tra
------------
  1. properties      mọi property phải nằm trong tests/fixtures/st-allowed-properties.txt
  2. forbid-blur     không có `-blur:` và không có `background-bumpmap:`
  3. duration-unit   `transition-duration` phải là số trần (cấm `ms`/`s`)
  4. font-weight     `font-weight` phải là số trần hoặc normal|bold|bolder|lighter
  5. single-shadow   mỗi `box-shadow` chỉ được có MỘT shadow
  6. coverage        mọi selector trong tests/fixtures/cinnamon-6.6-selectors.txt
                     phải có mặt trong output (ràng buộc E6: theme phải hoàn chỉnh)
  7. assets          mọi url() HIỆU LỰC (sau cascade, last-wins) phải trỏ tới
                     file tồn tại
  8. hardcoded       tầng override không được hard-code màu (#hex / rgb() / hsl()
                     / tên màu CSS) — phải đi qua token
  9. dead-vendor     các property đã chứng minh là CHẾT trong St (opacity) chỉ
                     được xuất hiện đúng số lần theme gốc có; ta không được thêm

Cách dùng
---------
  python3 tools/lint/st_properties.py                 # kiểm tra tất cả
  python3 tools/lint/st_properties.py --check properties,coverage
  python3 tools/lint/st_properties.py --css dist/.../cinnamon.css   # bỏ qua bước compile
  python3 tools/lint/st_properties.py --pending-assets tests/fixtures/pending-assets.txt
  python3 tools/lint/st_properties.py --json

Exit code: 0 = tất cả đạt (hoặc được SKIP có lý do), 1 = có lỗi, 2 = không chạy
được (thiếu trình biên dịch và không có --css).

Công cụ này KHÔNG bịa kết quả: nếu không tìm được trình biên dịch SCSS và không
được đưa sẵn file CSS, nó in SKIP và trả exit code 2 để CI phân biệt được với
"pass".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

ENTRY = REPO / "src" / "cinnamon" / "cinnamon.scss"
OVERRIDES = REPO / "src" / "cinnamon" / "overrides"
ASSETS_DIR = REPO / "src" / "cinnamon"
FIXTURE_PROPS = REPO / "tests" / "fixtures" / "st-allowed-properties.txt"
FIXTURE_SELECTORS = REPO / "tests" / "fixtures" / "cinnamon-6.6-selectors.txt"

ALL_CHECKS = (
    "properties",
    "forbid-blur",
    "duration-unit",
    "font-weight",
    "single-shadow",
    "coverage",
    "assets",
    "hardcoded",
    "dead-vendor",
)

# --------------------------------------------------------------------------- #
# Đã chứng minh là CHẾT trong St nhưng theme gốc Cinnamon 6.6 vẫn phát ra.
# Ta không sửa được vì vendor phải giữ nguyên văn; thay vào đó ta CHẶN không
# cho tầng override phát ra thêm, bằng cách so số lần xuất hiện với baseline.
# --------------------------------------------------------------------------- #
DEAD_IN_ST = {
    "opacity": {
        "baseline": 2,
        "evidence": (
            'Chuỗi "opacity" không tồn tại trong src/st/st-theme-node.c. '
            "grep toàn bộ src/st/ chỉ trúng st-texture-cache.c:84 và :859 — đó "
            "là tên GObject property của texture cache, không phải thuộc tính CSS. "
            "Theme gốc vẫn viết `.appmenu-category-button-greyed StIcon { opacity: 0.5 }` "
            "và `.menu-category-button-greyed StIcon { opacity: 0.5 }` (2 lần) -> khai báo chết. "
            "Tầng override thay bằng alpha thật trên `color` (_30-menus-startmenu.scss)."
        ),
    },
    "border-style": {
        "baseline": 1,
        "evidence": (
            "do_border_property() src/st/st-theme-node.c:1244-1300 chỉ tiêu thụ ident "
            "`solid` BÊN TRONG shorthand `border:`; StThemeNode không có trường "
            "border_style (grep 'border_style' trong st-theme-node.c/.h = 0). "
            "Vendor viết `border-style: solid` rời cho .vkeyboard-key (1 lần) -> chết."
        ),
    },
}

# --------------------------------------------------------------------------- #
# Cấm theo chính sách, dù St có hỗ trợ thật.
# --------------------------------------------------------------------------- #
POLICY_FORBIDDEN = {
    "-blur": (
        "St có `-blur` thật (src/st/st-theme-node.c:2132) nhưng "
        "src/st/st-background-effect.c chạy blur_size vòng lặp, mỗi vòng "
        "g_malloc(w*h*4) + cogl_framebuffer_read_pixels() (đọc ngược GPU->CPU) "
        "+ cogl_texture_new_from_data(), cho MỖI LẦN PAINT, và cần "
        "CLUTTER_FEATURE_SHADERS_GLSL. Chưa đo được trên máy Mint thật (T00 "
        "chưa chạy) nên KHÔNG ship. 'Glass' của dự án là alpha + gradient + "
        "hairline, KHÔNG phải blur — và không được mô tả là blur."
    ),
    "background-bumpmap": (
        "St hỗ trợ (src/st/st-theme-node.c:2064) nhưng cần asset bumpmap riêng. "
        "Không dùng ở Phase 1."
    ),
}

FONT_WEIGHT_OK = {"normal", "bold", "bolder", "lighter", "inherit"}
COLOR_KEYWORDS = {
    "black", "silver", "gray", "grey", "white", "maroon", "red", "purple",
    "fuchsia", "green", "lime", "olive", "yellow", "navy", "blue", "teal",
    "aqua", "orange", "aliceblue", "antiquewhite", "crimson", "cyan",
    "magenta", "gold", "indigo", "ivory", "khaki", "lavender", "linen",
    "orchid", "peru", "pink", "plum", "salmon", "sienna", "snow", "tan",
    "tomato", "violet", "wheat", "chocolate", "coral", "cornflowerblue",
    "darkblue", "darkgray", "darkgrey", "darkred", "deeppink", "firebrick",
    "forestgreen", "gainsboro", "ghostwhite", "goldenrod", "greenyellow",
    "honeydew", "hotpink", "indianred", "lawngreen", "lightblue", "lightgray",
    "lightgrey", "midnightblue", "mintcream", "mistyrose", "moccasin",
    "navajowhite", "oldlace", "olivedrab", "orangered", "palegreen",
    "paleturquoise", "papayawhip", "peachpuff", "powderblue", "rosybrown",
    "royalblue", "saddlebrown", "sandybrown", "seagreen", "seashell",
    "skyblue", "slateblue", "slategray", "slategrey", "springgreen",
    "steelblue", "thistle", "turquoise", "whitesmoke", "yellowgreen",
}
# Giá trị hợp lệ không phải màu, được phép xuất hiện trần.
NON_COLOR_IDENTS = {
    "none", "transparent", "inherit", "solid", "hidden", "dotted", "dashed",
    "double", "groove", "ridge", "inset", "outset", "auto", "center", "left",
    "right", "top", "bottom", "contain", "cover", "repeat", "no-repeat",
    "repeat-x", "repeat-y", "horizontal", "vertical", "radial", "normal",
    "italic", "oblique", "bold", "bolder", "lighter", "small-caps", "underline",
    "line-through", "overline", "uppercase", "lowercase", "capitalize",
    "symbolic", "requested", "full-color", "fullcolor", "middle", "baseline",
    "start", "end", "space-around", "space-between", "space-evenly",
    "stretch", "visible", "hidden", "scroll", "always", "pointer", "default",
}


class Finding:
    __slots__ = ("check", "severity", "message", "where")

    def __init__(self, check: str, severity: str, message: str, where: str = "") -> None:
        self.check = check
        self.severity = severity
        self.message = message
        self.where = where

    def as_dict(self) -> dict:
        return {
            "check": self.check,
            "severity": self.severity,
            "where": self.where,
            "message": self.message,
        }

    def __str__(self) -> str:
        loc = f" ({self.where})" if self.where else ""
        return f"[{self.severity}] {self.check}{loc}: {self.message}"


# --------------------------------------------------------------------------- #
# Biên dịch
# --------------------------------------------------------------------------- #
# Toolchain dev (libsass, dart-sass) đặt NGOÀI cây repo. Lý do:
# `tools/lint/safety_paths.py:43` có SKIP_DIRS = {.git, __pycache__, node_modules,
# docs, tests, design, .github} — KHÔNG có `.venv`/`venv`, nên một venv nằm
# trong repo sẽ bị lint đó quét và báo 31 vi phạm giả từ chính mã nguồn của pip.
# Đã báo cho Agent Platform/DevEx để thêm `.venv`/`venv` vào SKIP_DIRS; cho tới
# khi đó, toolchain sống ở $MINTOS_TOOLCHAIN (mặc định ~/.mintos-toolchain).
TOOLCHAIN = Path(os.environ.get("MINTOS_TOOLCHAIN", str(Path.home() / ".mintos-toolchain")))


def find_compiler() -> tuple[str, str] | None:
    """Trả về (tên, cách gọi). Ưu tiên libsass vì Mint build bằng pysassc."""
    try:
        import sass  # type: ignore

        return ("libsass", "python:sass")
    except Exception:
        pass
    candidates = [
        Path(os.environ["MINTOS_SASS_BIN"]) if os.environ.get("MINTOS_SASS_BIN") else None,
        TOOLCHAIN / "node_modules" / ".bin" / "sass",
        REPO / "node_modules" / ".bin" / "sass",
    ]
    for c in candidates:
        if c and c.exists():
            return (f"sass ({c.parent.parent.parent.name or 'local'})", f"exec:{c}")
    for exe in ("sass", "sassc"):
        path = shutil.which(exe)
        if path:
            return (exe, f"exec:{path}")
    return None


def compile_css(verbose: bool = False) -> tuple[str | None, str]:
    """Biên dịch ENTRY. Trả về (css, compiler_name); css=None nếu không compile được."""
    comp = find_compiler()
    if comp is None:
        return None, "none"
    name, how = comp
    if how == "python:sass":
        import sass  # type: ignore

        css = sass.compile(filename=str(ENTRY), output_style="expanded")
        if verbose:
            print(f"  · compiled với libsass {sass.libsass_version} -> {len(css)} bytes", file=sys.stderr)
        return css, name
    exe = how.split(":", 1)[1]
    out = REPO / ".tmp-lint-cinnamon.css"
    proc = subprocess.run(
        [exe, "--no-source-map", "--style=expanded", str(ENTRY), str(out)],
        cwd=str(REPO), capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"{name} thất bại:\n{proc.stdout}\n{proc.stderr}")
    css = out.read_text()
    out.unlink(missing_ok=True)
    if verbose:
        print(f"  · compiled với {name} -> {len(css)} bytes", file=sys.stderr)
    return css, name


# --------------------------------------------------------------------------- #
# Parse CSS
# --------------------------------------------------------------------------- #
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
DECL_RE = re.compile(r"(?m)^\s*(-?[a-zA-Z][a-zA-Z0-9-]*)\s*:\s*([^;]*?)\s*;")


def parse_rules(css: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """[(selector_normalised, [(prop, value), ...]), ...] theo thứ tự xuất hiện."""
    out = []
    for m in RULE_RE.finditer(css):
        sel = m.group(1)
        sel = re.sub(r"/\*.*?\*/", "", sel, flags=re.S)
        sel = re.sub(r"\s+", " ", sel).strip()
        if not sel or sel.startswith("@"):
            continue
        decls = [(p, v) for p, v in DECL_RE.findall(m.group(2))]
        out.append((sel, decls))
    return out


def split_selectors(sel: str) -> list[str]:
    return [re.sub(r"\s+", " ", s).strip() for s in sel.split(",") if s.strip()]


def depth0_commas(value: str) -> int:
    depth = 0
    n = 0
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            n += 1
    return n


def load_fixture(path: Path) -> list[str]:
    """Đọc fixture dạng "mỗi dòng một mục", bỏ qua dòng comment.

    QUAN TRỌNG: marker comment của fixture là `//`, KHÔNG phải `#`, vì selector
    CSS dùng `#` cho ID: `#notification`, `#Tooltip`, `#LookingGlassDialog`,
    `#altTabPopup`, `#panel:highlight`, `.expo-workspace-thumbnail-frame#active`.
    Bản đầu tiên của công cụ này dùng `#` và `line.split("#", 1)`, kết quả là
    25 selector ID bị cắt cụt và bài kiểm tra coverage báo sai CẢ HAI chiều
    (425 "thiếu" giả + 487 "mới" giả, trong khi số thật là 0 và 127).
    Phát hiện bằng cách chạy thật, không phải bằng đọc code.
    """
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        out.append(stripped)
    return out


# --------------------------------------------------------------------------- #
# Các kiểm tra
# --------------------------------------------------------------------------- #
def check_properties(rules, findings: list[Finding]) -> None:
    allowed = set(load_fixture(FIXTURE_PROPS))
    if not allowed:
        findings.append(Finding("properties", "ERROR", f"không đọc được fixture {FIXTURE_PROPS}"))
        return
    seen: dict[str, int] = {}
    for sel, decls in rules:
        for prop, _ in decls:
            seen[prop] = seen.get(prop, 0) + 1
    unknown = sorted(p for p in seen if p not in allowed and p not in DEAD_IN_ST)
    for p in unknown:
        findings.append(Finding(
            "properties", "ERROR",
            f"property `{p}` ({seen[p]} lần) không có trong St — sẽ bị BỎ QUA TRONG IM LẶNG. "
            f"Đối chiếu tests/fixtures/st-allowed-properties.txt.",
        ))
    if not unknown:
        print(f"  ✓ properties: {len(seen)} property khác nhau, tất cả hợp lệ với St", file=sys.stderr)


def check_forbid_blur(css: str, rules, findings: list[Finding]) -> None:
    hits = []
    for sel, decls in rules:
        for prop, value in decls:
            if prop in POLICY_FORBIDDEN:
                hits.append((sel, prop, value))
    for sel, prop, value in hits:
        findings.append(Finding(
            "forbid-blur", "ERROR",
            f"`{prop}: {value}` trong `{sel}`. {POLICY_FORBIDDEN[prop]}",
        ))
    # quét cả chuỗi thô để bắt trường hợp nằm trong comment bị strip sai
    raw = re.findall(r"(?m)^\s*-blur\s*:", css)
    if raw and not hits:
        findings.append(Finding("forbid-blur", "ERROR", f"tìm thấy {len(raw)} khai báo `-blur` thô"))
    if not hits and not raw:
        print("  ✓ forbid-blur: 0 khai báo -blur, 0 background-bumpmap", file=sys.stderr)


# Baseline: theme gốc Cinnamon 6.6 phát ra đúng MỘT khai báo
# `transition-duration` có đơn vị, tại vendor/_common.scss:114 (`100ms`), áp cho
# nhóm `.popup-combobox-item, .popup-sub-menu .popup-menu-item, .popup-menu-item`.
# Khai báo đó CHẾT trong St (xem DEAD_IN_ST) và ta không xoá được vì vendor phải
# nguyên văn; tầng override đặt lại giá trị đúng (số trần) cho CẢ BA selector
# trong nhóm, kể cả selector lồng có specificity cao hơn.
DURATION_UNIT_BASELINE = 1


def check_duration_unit(rules, findings: list[Finding]) -> None:
    bad = []
    ok = 0
    for sel, decls in rules:
        for prop, value in decls:
            if prop != "transition-duration":
                continue
            v = value.strip()
            if re.fullmatch(r"-?\d+(\.\d+)?", v):
                ok += 1
            else:
                bad.append((sel, v))
    extra = bad[DURATION_UNIT_BASELINE:]
    for sel, v in extra:
        findings.append(Finding(
            "duration-unit", "ERROR",
            f"`transition-duration: {v}` trong `{sel}` — St chỉ nhận SỐ TRẦN. "
            "st_theme_node_lookup_double() (src/st/st-theme-node.c:841) bỏ qua mọi term "
            "không phải NUM_GENERIC, nên `100ms` = KHÔNG có transition. "
            "Docstring st_theme_node_get_transition_duration() (:2315) ghi giá trị là milliseconds.",
            sel,
        ))
    # Nguồn SCSS của tầng override tuyệt đối không được viết đơn vị.
    src_bad = []
    if OVERRIDES.exists():
        for f in sorted(OVERRIDES.glob("_*.scss")):
            code = re.sub(r"//.*", "", f.read_text())
            for i, line in enumerate(code.splitlines(), 1):
                if re.search(r"transition-duration\s*:\s*[^;]*\d\s*(ms|s)\b", line):
                    src_bad.append(f"{f.name}:{i}: {line.strip()[:90]}")
    for where in src_bad:
        findings.append(Finding(
            "duration-unit", "ERROR",
            f"tầng override viết transition-duration kèm đơn vị: {where}", where,
        ))
    note = (f" (trong đó {len(bad)} là khai báo chết kế thừa từ vendor, "
            f"baseline={DURATION_UNIT_BASELINE})" if bad else "")
    print(f"  {'✓' if not extra and not src_bad else '✗'} duration-unit: "
          f"{ok} khai báo hợp lệ, {len(extra)} vi phạm mới{note}", file=sys.stderr)


def check_font_weight(rules, findings: list[Finding]) -> None:
    bad = []
    for sel, decls in rules:
        for prop, value in decls:
            if prop != "font-weight":
                continue
            v = value.strip()
            if v in FONT_WEIGHT_OK or re.fullmatch(r"\d{3}", v):
                continue
            bad.append((sel, v))
    for sel, v in bad:
        findings.append(Finding(
            "font-weight", "ERROR",
            f"`font-weight: {v}` trong `{sel}` — font_weight_from_term() "
            "(src/st/st-theme-node.c:2680-2692) yêu cầu NUM_GENERIC (số trần) hoặc "
            "normal|bold|bolder|lighter. Có đơn vị (vd `700px`) thì khai báo bị bỏ qua.",
            sel,
        ))
    print(f"  {'✓' if not bad else '✗'} font-weight: {len(bad)} khai báo sai", file=sys.stderr)


def check_single_shadow(rules, findings: list[Finding]) -> None:
    bad = []
    total = 0
    for sel, decls in rules:
        for prop, value in decls:
            if not prop.endswith("box-shadow"):
                continue
            total += 1
            if depth0_commas(value) > 0:
                bad.append((sel, prop, value))
    for sel, prop, value in bad:
        findings.append(Finding(
            "single-shadow", "ERROR",
            f"`{prop}: {value}` trong `{sel}` — St chỉ hỗ trợ MỘT box-shadow mỗi rule: "
            "st_theme_node_lookup_shadow() (src/st/st-theme-node.c:3348-3400) trả về đúng "
            "một StShadow*, không phải danh sách. Dùng `border` cho hairline thay vì "
            "cộng thêm inset shadow (xem overrides/_00-globals.scss).",
            sel,
        ))
    print(f"  {'✓' if not bad else '✗'} single-shadow: {total} khai báo, {len(bad)} vi phạm", file=sys.stderr)


def check_coverage(rules, findings: list[Finding]) -> None:
    fixture = load_fixture(FIXTURE_SELECTORS)
    if not fixture:
        findings.append(Finding("coverage", "ERROR", f"không đọc được fixture {FIXTURE_SELECTORS}"))
        return
    have = set()
    for sel, _ in rules:
        for s in split_selectors(sel):
            have.add(s)
    missing = [s for s in fixture if s not in have]
    for s in missing:
        findings.append(Finding(
            "coverage", "ERROR",
            f"selector gốc của Cinnamon 6.6 KHÔNG có trong output: `{s}`. "
            "Vi phạm ràng buộc E6: CSS của Mint chỉ là fallback_stylesheet KHÔNG cascade, "
            "nên thiếu selector = widget đó mất style hoàn toàn.",
            s,
        ))
    print(f"  {'✓' if not missing else '✗'} coverage: {len(fixture) - len(missing)}/{len(fixture)} "
          f"selector gốc có mặt; output có {len(have)} selector", file=sys.stderr)


def effective_urls(rules) -> dict[tuple[str, str], str]:
    """url() HIỆU LỰC sau cascade: last-wins theo (simple_selector, property)."""
    eff: dict[tuple[str, str], str] = {}
    for sel, decls in rules:
        for s in split_selectors(sel):
            for prop, value in decls:
                if "url(" in value:
                    eff[(s, prop)] = value
    return eff


def check_assets(rules, pending: set[str], findings: list[Finding]) -> None:
    eff = effective_urls(rules)
    urls = sorted({u for v in eff.values() for u in re.findall(r'url\("([^"]+)"\)', v)})
    missing = [u for u in urls if not (ASSETS_DIR / u).exists()]
    unexpected = sorted(pending - set(missing))
    # `src/cinnamon/assets/` thuộc T05 (Agent D). Nếu THƯ MỤC CHƯA TỒN TẠI thì
    # T05 chưa bắt đầu -> báo PENDING, không phải ERROR: T04 chỉ chịu trách
    # nhiệm chốt đúng tập url() trong CSS, không phải vẽ SVG.
    # Nếu thư mục ĐÃ tồn tại mà thiếu file thì đó là ERROR thật (T05 giao thiếu).
    t05_not_started = not (ASSETS_DIR / "assets").is_dir()
    for u in missing:
        sev = "PENDING" if (u in pending or t05_not_started) else "ERROR"
        note = ""
        if sev == "PENDING":
            note = (" — PENDING T05: thư mục src/cinnamon/assets/ chưa tồn tại, "
                    "thuộc quyền Agent D (docs/plan/04-work-breakdown.md T05). "
                    "T04 đã chốt đúng tập 15 url(); xem "
                    "tests/lint/test_cinnamon_coverage.py::TestAssets.")
        findings.append(Finding(
            "assets", sev,
            f'url("{u}") không resolve: thiếu file {ASSETS_DIR / u}. '
            "St phân giải url() tương đối với THƯ MỤC của file CSS "
            "(_st_theme_resolve_url, src/st/st-theme.c:1087-1123: "
            "g_path_get_dirname(base_filename) + g_file_resolve_relative_path)." + note,
            u,
        ))
    for u in unexpected:
        findings.append(Finding(
            "assets", "ERROR",
            f"`{u}` vẫn nằm trong danh sách pending nhưng ĐÃ tồn tại — hãy xoá nó khỏi "
            "file pending để danh sách không phình ra mãi.",
            u,
        ))
    print(f"  {'✓' if not missing else '·'} assets: {len(urls)} url() hiệu lực, "
          f"{len(missing) - len(pending & set(missing))} thiếu thật, "
          f"{len(pending & set(missing))} đang chờ T05", file=sys.stderr)


HARDCODE_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\("
)


def check_hardcoded(findings: list[Finding]) -> None:
    """Tầng override (src/cinnamon/overrides/) không được hard-code màu.

    Ngoại lệ DUY NHẤT: overrides/_00-globals.scss, vì nó là tầng ánh xạ
    token -> biến vendor và có phép tham chiếu primitive $mg-color-* khi token
    semantic chưa có. Nó vẫn bị cấm viết literal hex/rgb.
    """
    if not OVERRIDES.exists():
        findings.append(Finding("hardcoded", "ERROR", f"thiếu thư mục {OVERRIDES}"))
        return
    offenders: list[str] = []
    literal_total = 0
    primitive_refs: dict[str, int] = {}
    for f in sorted(OVERRIDES.glob("_*.scss")):
        text = f.read_text()
        # bỏ comment để không đếm ví dụ trong ghi chú
        code = re.sub(r"//.*", "", text)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
        for i, line in enumerate(code.splitlines(), 1):
            for m in HARDCODE_RE.finditer(line):
                tok = m.group(0)
                if tok.startswith(("rgb", "hsl")):
                    # `rgba($token, $alpha)` là HỢP LỆ: đối số thứ nhất là biến.
                    # LƯU Ý: phải cắt theo offset TRONG DÒNG. Bản đầu tiên của hàm
                    # này dùng `code.splitlines()[i-1][m.end():]`, tức lấy offset
                    # của cả chuỗi `code` đem index vào một dòng -> bắt nhầm 28
                    # khai báo hợp lệ. Phát hiện bằng cách chạy thật.
                    # HARDCODE_RE đã nuốt dấu `(`, nên `rest` bắt đầu NGAY TẠI
                    # đối số thứ nhất. Bản vá trước đó vẫn đòi thêm một dấu `(`
                    # nữa nên bắt nhầm 27 khai báo hợp lệ dạng
                    # `rgba($mg-status-error, $mg-opacity-hover)`.
                    rest = line[m.end():]
                    if re.match(r"\s*\$", rest):
                        continue
                offenders.append(f"{f.name}:{i}: {line.strip()[:110]}")
                literal_total += 1
        if f.name != "_00-globals.scss":
            for m in re.finditer(r"\$mg-color-[a-z0-9-]+", code):
                primitive_refs[m.group(0)] = primitive_refs.get(m.group(0), 0) + 1
    for o in offenders:
        findings.append(Finding(
            "hardcoded", "ERROR",
            f"màu hard-code trong tầng override: {o}. Phải dùng token $mg-* "
            "(rgba($token, $alpha) thì được).",
        ))
    for name, n in sorted(primitive_refs.items()):
        findings.append(Finding(
            "hardcoded", "ERROR",
            f"primitive `{name}` được tham chiếu {n} lần NGOÀI _00-globals.scss. "
            "Chỉ tầng ánh xạ globals mới được chạm primitive; các tầng còn lại "
            "phải dùng token semantic/component.",
        ))
    if not offenders and not primitive_refs:
        print(f"  ✓ hardcoded: 0 literal màu, 0 tham chiếu primitive ngoài _00-globals", file=sys.stderr)
    else:
        print(f"  ✗ hardcoded: {literal_total} literal màu, {len(primitive_refs)} primitive rò rỉ",
              file=sys.stderr)


def check_dead_vendor(rules, findings: list[Finding]) -> None:
    for prop, meta in DEAD_IN_ST.items():
        n = sum(1 for _, decls in rules for p, _ in decls if p == prop)
        if n > meta["baseline"]:
            findings.append(Finding(
                "dead-vendor", "ERROR",
                f"`{prop}` xuất hiện {n} lần, vượt baseline {meta['baseline']} của theme gốc. "
                f"Tầng override KHÔNG được thêm khai báo chết. Bằng chứng: {meta['evidence']}",
            ))
        elif n < meta["baseline"]:
            print(f"  · dead-vendor: `{prop}` {n}/{meta['baseline']} (thấp hơn baseline — tốt, "
                  f"nghĩa là override đã che được một phần)", file=sys.stderr)
        else:
            print(f"  · dead-vendor: `{prop}` {n}/{meta['baseline']} — chỉ từ vendor, "
                  f"override không thêm (property này CHẾT trong St)", file=sys.stderr)


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--css", help="dùng file CSS đã biên dịch sẵn thay vì tự compile")
    ap.add_argument("--check", help=f"chỉ chạy các kiểm tra này, phân cách bằng dấu phẩy. Mặc định: tất cả. Có sẵn: {','.join(ALL_CHECKS)}")
    ap.add_argument("--pending-assets", help="file chứa danh sách asset đang chờ T05 (mỗi dòng một đường dẫn url())")
    ap.add_argument("--json", action="store_true", help="in kết quả dạng JSON")
    ap.add_argument("--forbid-blur", action="store_true", help="tương đương --check forbid-blur (giữ cho khớp tài liệu cũ)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    wanted = list(ALL_CHECKS)
    if args.check:
        wanted = [c.strip() for c in args.check.split(",") if c.strip()]
        unknown = [c for c in wanted if c not in ALL_CHECKS]
        if unknown:
            print(f"LỖI: kiểm tra không tồn tại: {unknown}. Có sẵn: {ALL_CHECKS}", file=sys.stderr)
            return 2
    if args.forbid_blur:
        wanted = ["forbid-blur"]

    if args.css:
        css = Path(args.css).read_text()
        compiler = f"prebuilt:{args.css}"
    else:
        css, compiler = compile_css(verbose=args.verbose or not args.quiet)
        if css is None:
            msg = ("KHÔNG CHẠY ĐƯỢC: không tìm thấy trình biên dịch SCSS "
                   "(libsass/`sass`/`sassc`) và không được đưa --css. "
                   "Đây là SKIP, không phải PASS. Cài `pip install libsass` "
                   "hoặc chạy `make cinnamon-css` trước.")
            if args.json:
                print(json.dumps({"status": "skip", "reason": msg}, ensure_ascii=False))
            else:
                print(msg, file=sys.stderr)
            return 2

    pending: set[str] = set()
    if args.pending_assets:
        p = Path(args.pending_assets)
        if p.exists():
            pending = {l.split("#", 1)[0].strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")}
        else:
            print(f"CẢNH BÁO: không thấy {args.pending_assets}", file=sys.stderr)

    rules = parse_rules(css)
    findings: list[Finding] = []

    if not args.quiet:
        print(f"st_properties.py — input: {compiler}, {len(css)} bytes, {len(rules)} rule", file=sys.stderr)

    if "properties" in wanted:
        check_properties(rules, findings)
    if "forbid-blur" in wanted:
        check_forbid_blur(css, rules, findings)
    if "duration-unit" in wanted:
        check_duration_unit(rules, findings)
    if "font-weight" in wanted:
        check_font_weight(rules, findings)
    if "single-shadow" in wanted:
        check_single_shadow(rules, findings)
    if "coverage" in wanted:
        check_coverage(rules, findings)
    if "assets" in wanted:
        check_assets(rules, pending, findings)
    if "hardcoded" in wanted:
        check_hardcoded(findings)
    if "dead-vendor" in wanted:
        check_dead_vendor(rules, findings)

    errors = [f for f in findings if f.severity == "ERROR"]
    pendings = [f for f in findings if f.severity == "PENDING"]

    if args.json:
        print(json.dumps({
            "status": "fail" if errors else "ok",
            "compiler": compiler,
            "bytes": len(css),
            "rules": len(rules),
            "errors": [f.as_dict() for f in errors],
            "pending": [f.as_dict() for f in pendings],
        }, ensure_ascii=False, indent=1))
    else:
        for f in pendings:
            print(str(f), file=sys.stderr)
        for f in errors:
            print(str(f), file=sys.stderr)
        print("", file=sys.stderr)
        if errors:
            print(f"FAIL — {len(errors)} lỗi"
                  + (f", {len(pendings)} đang chờ T05" if pendings else ""), file=sys.stderr)
        else:
            print(f"OK — 0 lỗi"
                  + (f" ({len(pendings)} mục đang chờ T05 assets)" if pendings else ""), file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
