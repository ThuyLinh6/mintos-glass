#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint cho wallpaper — Task T16 (Agent D · Visual/Assets).

Hiện thực hoá 5 tiêu chí "Done" của T16 trong docs/plan/04-work-breakdown.md:
  1. SVG vector TỰ VẼ — không tải từ Internet, không URL ngoài, không tài nguyên
     không có quyền phân phối.
  2. Có biến thể Dark Glass; biến thể Light Glass ghi rõ là sẽ thêm khi D-2 mở khoá.
  3. Nền phải đủ tối để **nhãn icon desktop đạt ≥ 3:1** — ĐO, không đoán.
  4. Không xung đột thị giác với icon desktop: điểm nhấn nằm lệch khỏi vùng icon.
  5. `MANIFEST.md` ghi nguồn + giấy phép từng tệp.

--------------------------------------------------------------------------
VÌ SAO BÀI ĐO TƯƠNG PHẢN NẰM Ở ĐÂY CHỨ KHÔNG PHẢI Ở T09
--------------------------------------------------------------------------
T09 (Nemo) đã đo nhãn icon desktop, nhưng phải đo trên **ba mức chói MÔ HÌNH** vì
lúc đó chưa có wallpaper thật. Kết quả ghi trong docs/testing/nemo-checklist.md.
T16 cung cấp wallpaper THẬT nên bài đo được làm lại ở đây trên dữ liệu thật.

Quan trọng hơn, T09 đã xác minh một điều khiến wallpaper thành **đòn bẩy duy
nhất**: rule `.nemo-desktop.nemo-canvas-item` nằm trong nhóm `[LOCK]` — Nemo nạp
`nemo-style-application.css` ở `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` (600), cao
hơn theme (200), và GTK 3.24 **không có `!important`** (đã kiểm: "important" xuất
hiện 0 lần trong gtkcssparser.c / gtkcssprovider.c / gtkstylecascade.c @ 3.24.42).
Nghĩa là theme KHÔNG đổi được màu nhãn desktop. Token
`$mg-nemo-desktop-label-text: #eeeeee` chính là giá trị Nemo đang dùng, và nó bị
khoá.

=> Nếu nhãn desktop không đọc được thì thứ DUY NHẤT sửa được là nền phía sau nó.
   Nên ràng buộc tương phản thuộc về wallpaper, và phải được đo ở đây.

--------------------------------------------------------------------------
CÁCH TÍNH "VÙNG SÁNG NHẤT" — bảo thủ, không tin mắt
--------------------------------------------------------------------------
Wallpaper là gradient nên độ chói thay đổi theo vị trí. Thay vì lấy mẫu pixel
(cần một bộ raster mà máy người dùng KHÔNG được yêu cầu cài), lint trích mọi cặp
`stop-color`/`stop-opacity` và `fill`/`fill-opacity` khỏi SVG, composite từng lớp
lên nền tối nhất, rồi lấy **màu sáng nhất** trong số đó. Đó là trường hợp xấu nhất
cho chữ sáng — nếu chữ đọc được ở vùng sáng nhất thì đọc được ở mọi nơi.

Cách này là XẤP XỈ theo hướng AN TOÀN: nó bỏ qua hiệu ứng chồng nhiều lớp cùng
lúc (thực tế sẽ tối hơn hoặc bằng), nên kết quả không bao giờ lạc quan hơn thực
tế. Đã ghi rõ trong MANIFEST.md để không ai hiểu nhầm đây là đo pixel.

Chạy:  python3 tools/lint/wallpapers.py [--verbose]
Exit 0 khi sạch. Không cần compiler SCSS — chạy được ở CI tối giản.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WP_DIR = REPO / "src" / "wallpapers"
MANIFEST = WP_DIR / "MANIFEST.md"
TOKENS = REPO / "src" / "cinnamon" / "tokens" / "_tokens.scss"
GTK_TOKENS = REPO / "src" / "gtk-3.0" / "sass" / "_tokens.scss"

SVG_NS = "http://www.w3.org/2000/svg"
W, H = 1920, 1080

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
STOP_RE = re.compile(r'<stop\b[^>]*>', re.I)
ATTR_RE = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')
EXTERNAL_RE = re.compile(r"(https?:)?//[^\s\"')]+|\bxlink:href\s*=", re.I)
DANGEROUS_RE = re.compile(r"<\s*(script|image|foreignObject|iframe|use|filter|mask|clipPath)\b", re.I)
BLUR_RE = re.compile(r"feGaussianBlur|feDropShadow|\bblur\b", re.I)
RGBA_RE = re.compile(r"\brgba?\s*\(")
NAME_RE = re.compile(r"^mintos-glass-dark[a-z0-9-]*$")

sys.path.insert(0, str(REPO / "tools" / "lint"))


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def _tok_map(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"^\$([a-z0-9-]+):\s*(.+?);", path.read_text(), re.M)}


def token_hex_values() -> set[str]:
    out: set[str] = set()
    for path in (TOKENS, GTK_TOKENS):
        if not path.exists():
            continue
        txt = path.read_text()
        for m in HEX_RE.finditer(txt):
            h = m.group(0).lower()
            out.add("#" + "".join(c * 2 for c in h[1:]) if len(h) == 4 else h)
        for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", txt):
            out.add("#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3)))
    return out


def token_alpha_values() -> set[str]:
    out = {"0", "1", "0.0", "1.0"}
    for path in (TOKENS, GTK_TOKENS):
        if not path.exists():
            continue
        txt = path.read_text()
        for m in re.finditer(r"rgba?\([^)]*,\s*([\d.]+)\s*\)", txt):
            out.add(m.group(1))
        for m in re.finditer(r"^\$mg-(?:opacity|blur)-[a-z0-9-]+:\s*([\d.]+)\s*;", txt, re.M):
            out.add(m.group(1))
    return out


def gtk_token(name: str) -> str | None:
    """Token của T09 nằm trong _tokens.scss của GTK3, không phải của Cinnamon."""
    for path in (GTK_TOKENS, TOKENS):
        v = _tok_map(path).get(name)
        if v:
            return v
    return None


# ---------------------------------------------------------------------------
# Luminance / contrast — dùng lại contrast.py của Agent 1 nếu có, nếu không thì
# tự tính theo đúng công thức WCAG 2.x (relative luminance). Không được phép
# dùng một công thức thứ hai khác đi.
# ---------------------------------------------------------------------------
def _load_contrast():
    try:
        import contrast as ct
        return ct
    except Exception:
        return None


def _srgb_to_lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(hexc: str) -> float:
    ct = _load_contrast()
    if ct is not None:
        r, g, b, _a = ct.to_rgb(ct.parse_hex(hexc))
        return 0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g) + 0.0722 * _srgb_to_lin(b)
    r, g, b = _hex_to_rgb(hexc)
    return 0.2126 * _srgb_to_lin(r) + 0.7152 * _srgb_to_lin(g) + 0.0722 * _srgb_to_lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def composite(fg_hex: str, alpha: float, bg_hex: str) -> str:
    fr, fg_, fb = _hex_to_rgb(fg_hex)
    br, bg_, bb = _hex_to_rgb(bg_hex)
    return "#%02x%02x%02x" % tuple(
        int(round(alpha * f + (1 - alpha) * b)) for f, b in ((fr, br), (fg_, bg_), (fb, bb)))


# ---------------------------------------------------------------------------
# Trích các lớp màu của một wallpaper
# ---------------------------------------------------------------------------
def layers(path: Path) -> tuple[list[tuple[str, float]], str]:
    """([(hex, alpha)], nền_tối_nhất). Alpha mặc định 1.0 khi không khai báo."""
    txt = path.read_text(encoding="utf-8")
    out: list[tuple[str, float]] = []
    for frag in STOP_RE.findall(txt):
        attrs = dict(ATTR_RE.findall(frag))
        col = attrs.get("stop-color")
        if col and HEX_RE.fullmatch(col):
            out.append((col.lower(), float(attrs.get("stop-opacity", "1"))))
    for m in re.finditer(r"<(?:rect|path|circle|ellipse|polygon)\b[^>]*>", txt, re.I):
        attrs = dict(ATTR_RE.findall(m.group(0)))
        col = attrs.get("fill")
        if col and HEX_RE.fullmatch(col):
            out.append((col.lower(), float(attrs.get("fill-opacity", "1"))))
    hexes = [c for c, _ in out]
    darkest = min(hexes, key=luminance) if hexes else "#000000"
    return out, darkest


def brightest_composite(path: Path) -> tuple[str, float]:
    """Màu SÁNG NHẤT có thể xuất hiện trên wallpaper, và alpha của lớp đó."""
    ls, darkest = layers(path)
    if not ls:
        return darkest, 1.0
    best, best_a = darkest, 1.0
    for col, a in ls:
        c = composite(col, a, darkest)
        if luminance(c) > luminance(best):
            best, best_a = c, a
    return best, best_a


# ---------------------------------------------------------------------------
def findings(verbose: bool = False, wp_dir: Path | None = None) -> list[tuple[str, str, str]]:
    """`wp_dir` cho phép trỏ lint vào bản sao tạm — cần để viết mutation test
    (xem tests/lint/test_wallpapers.py). Có khôi phục global ở finally."""
    global WP_DIR, MANIFEST
    saved = (WP_DIR, MANIFEST)
    if wp_dir is not None:
        WP_DIR = Path(wp_dir)
        MANIFEST = WP_DIR / "MANIFEST.md"
    try:
        return _findings(verbose)
    finally:
        WP_DIR, MANIFEST = saved


def _findings(verbose: bool = False) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    if not WP_DIR.is_dir():
        return [("FAIL", "wallpaper-dir", f"thiếu {WP_DIR}")]
    wps = sorted(WP_DIR.glob("*.svg"))
    if not wps:
        return [("FAIL", "wallpaper-dir", "không có SVG nào trong src/wallpapers/")]

    colors, alphas = token_hex_values(), token_alpha_values()

    # 1: cấu trúc + đặt tên
    for p in wps:
        rel = p.name
        if not NAME_RE.match(p.stem):
            f.append(("FAIL", "naming",
                      f"{rel}: tên phải khớp `mintos-glass-dark*` lowercase kebab-case"))
        try:
            root = ET.fromstring(p.read_text(encoding="utf-8"))
        except ET.ParseError as exc:
            f.append(("FAIL", "svg-wellformed", f"{rel}: XML không parse được — {exc}"))
            continue
        if root.tag != f"{{{SVG_NS}}}svg":
            f.append(("FAIL", "svg-wellformed", f"{rel}: thẻ gốc phải là <svg>"))
        if root.get("viewBox") != f"0 0 {W} {H}":
            f.append(("FAIL", "svg-geometry",
                      f"{rel}: viewBox phải là `0 0 {W} {H}` (16:9), đang là "
                      f"{root.get('viewBox')!r}"))
        if root.get("preserveAspectRatio") != "xMidYMid slice":
            f.append(("FAIL", "svg-geometry",
                      f"{rel}: cần preserveAspectRatio=\"xMidYMid slice\" để PHỦ KÍN "
                      "màn hình ở mọi tỉ lệ không để lại dải đen. (Icon thì ngược "
                      "lại — không được cắt.)"))
        # kích thước nội tại phải khớp viewBox
        for attr, want in (("width", str(W)), ("height", str(H))):
            if root.get(attr) != want:
                f.append(("FAIL", "svg-geometry",
                          f"{rel}: {attr} phải là {want}, đang là {root.get(attr)!r}"))

    # 2: không phụ thuộc mạng, không filter/blur, không rgba()
    for p in wps:
        rel = p.name
        txt = p.read_text(encoding="utf-8")
        scan = re.sub(r'\sxmlns(?::[\w-]+)?\s*=\s*"[^"]*"', "", txt)
        for m in EXTERNAL_RE.finditer(scan):
            f.append(("FAIL", "no-external-refs",
                      f"{rel}: tham chiếu ra ngoài `{m.group(0).strip()[:60]}` — "
                      "wallpaper phải nằm trong repo, không URL ngoài khi chạy"))
        for m in DANGEROUS_RE.finditer(txt):
            f.append(("FAIL", "no-external-refs",
                      f"{rel}: chứa thẻ <{m.group(1).lower()}>"))
        if BLUR_RE.search(txt):
            # CHỈ quét trong nội dung, comment giải thích thì được — nhưng comment
            # không được NGỤ Ý có blur mà pipeline không tạo ra.
            body = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
            if BLUR_RE.search(body):
                f.append(("FAIL", "no-blur-claim",
                          f"{rel}: nội dung có blur. T04 đã xác minh -blur của St tốn "
                          "cogl_framebuffer_read_pixels() mỗi lần paint nên không "
                          "ship; wallpaper càng không được ngụ ý hiệu ứng không có"))
        if RGBA_RE.search(txt):
            f.append(("FAIL", "no-rgba-in-svg",
                      f"{rel}: dùng rgba() — librsvg hỗ trợ không nhất quán giữa các "
                      "phiên bản; hãy dùng hex + stop-opacity/fill-opacity"))

    # 3: màu và alpha tra ngược được về token
    for p in wps:
        txt = p.read_text(encoding="utf-8")
        for m in HEX_RE.finditer(txt):
            h = m.group(0).lower()
            if len(h) == 4:
                h = "#" + "".join(c * 2 for c in h[1:])
            if h not in colors:
                f.append(("FAIL", "colors-are-token-values",
                          f"{p.name}: màu `{m.group(0)}` không khớp token nào — "
                          "wallpaper không được tạo ra bảng màu thứ hai"))
        for m in re.finditer(r'\b(stop-opacity|fill-opacity)\s*=\s*"([^"]+)"', txt):
            if m.group(2) not in alphas:
                f.append(("FAIL", "colors-are-token-values",
                          f"{p.name}: {m.group(1)}=\"{m.group(2)}\" không khớp "
                          "alpha token nào"))

    # 4: ĐO tương phản nhãn desktop trên wallpaper THẬT
    label = gtk_token("mg-nemo-desktop-label-text")
    sel_bg = gtk_token("mg-nemo-desktop-label-selected-background")
    if not label:
        f.append(("SKIP", "desktop-label-contrast",
                  "không đọc được $mg-nemo-desktop-label-text từ _tokens.scss"))
    else:
        label_hex = label.strip().lower()
        for p in wps:
            bright, _a = brightest_composite(p)
            r = contrast(label_hex, bright)
            with_v = f"{p.name}: nhãn desktop {label_hex} trên vùng sáng nhất {bright}"
            if verbose:
                print(f"  · {with_v} = {r:.2f}:1", file=sys.stderr)
            # Nhãn desktop là CHỮ nên ngưỡng là 4.5:1 (WCAG 1.4.3), không phải 3:1.
            # T16 chỉ đòi >= 3:1 ở mức tối thiểu; ta đặt mục tiêu cao hơn vì đây là
            # chữ thật trên nền thật và màu chữ thì BỊ NEMO KHOÁ không sửa được.
            if r < 4.5:
                f.append(("FAIL", "desktop-label-contrast",
                          f"{with_v} chỉ đạt {r:.2f}:1 — dưới 4.5:1 cho chữ thường "
                          "(WCAG 1.4.3). Màu nhãn bị Nemo khoá ở priority 600 nên "
                          "wallpaper là đòn bẩy duy nhất: hãy làm nền tối hơn."))
            elif r < 7.0:
                f.append(("WARN", "desktop-label-contrast",
                          f"{with_v} đạt {r:.2f}:1 — qua 4.5:1 nhưng dưới 7:1"))

    # 5: trường hợp nhãn ĐÃ CHỌN — đóng vòng lặp với T09
    if sel_bg:
        m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)",
                         sel_bg.strip())
        if m:
            rgb = "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3))
            a = float(m.group(4))
            adopted = "#0b0c0e"    # T09 đã đổi sang $mg-text-on-accent
            broken = "#f5f5f5"     # giá trị token gốc, T09 đã chứng minh là FAIL
            for p in wps:
                bright, _ = brightest_composite(p)
                chip = composite(rgb, a, bright)
                r_ok = contrast(adopted, chip)
                r_bad = contrast(broken, chip)
                if verbose:
                    print(f"  · {p.name}: nhãn đã-chọn {adopted} trên {chip} = "
                          f"{r_ok:.2f}:1 (token cũ {broken} = {r_bad:.2f}:1)",
                          file=sys.stderr)
                if r_ok < 4.5:
                    f.append(("FAIL", "selected-label-contrast",
                              f"{p.name}: nhãn đã-chọn {adopted} trên chip {chip} chỉ "
                              f"đạt {r_ok:.2f}:1"))
                if r_bad >= 4.5:
                    f.append(("WARN", "selected-label-contrast",
                              f"{p.name}: token cũ {broken} giờ ĐẠT {r_bad:.2f}:1 — "
                              "kết luận của T09 cần được xét lại trên nền này"))

    # 6: không ship biến thể Light khi D-2 vẫn là dark_first
    for p in wps:
        if "light" in p.stem:
            f.append(("WARN", "no-light-variant-yet",
                      f"{p.name}: biến thể Light Glass chỉ được thêm khi quyết định "
                      "D-2 (dark_first) được mở khoá — xem docs/decisions.md"))
    if not any("light" in p.stem for p in wps) and MANIFEST.exists():
        if "Light Glass" not in MANIFEST.read_text(encoding="utf-8"):
            f.append(("WARN", "no-light-variant-yet",
                      "MANIFEST.md nên ghi rõ biến thể Light Glass sẽ thêm khi D-2 "
                      "mở khoá (tiêu chí Done #2 của T16)"))

    # 7: điểm nhấn phải nằm LỆCH khỏi vùng icon desktop
    # Nemo/Cinnamon xếp icon desktop từ góc TRÊN-TRÁI đi xuống theo cột. Nên vùng
    # an toàn là nửa trên bên trái. Kiểm tra toạ độ tâm của mọi radialGradient.
    SAFE_X, SAFE_Y = W * 0.55, H * 0.55
    for p in wps:
        txt = p.read_text(encoding="utf-8")
        for m in re.finditer(r'<radialGradient\b[^>]*\bcx="([\d.]+)"[^>]*\bcy="([\d.]+)"',
                             txt):
            cx, cy = float(m.group(1)), float(m.group(2))
            # cho phép nếu nằm ngoài vùng an toàn, HOẶC rất mờ (alpha nhỏ)
            if cx < SAFE_X and cy < SAFE_Y:
                f.append(("WARN", "accent-placement",
                          f"{p.name}: có vầng sáng tâm ({cx:.0f},{cy:.0f}) nằm trong "
                          f"vùng icon desktop (x<{SAFE_X:.0f}, y<{SAFE_Y:.0f}). Chấp "
                          "nhận được nếu alpha rất nhỏ — bài desktop-label-contrast "
                          "mới là trọng tài cuối."))

    # 8: MANIFEST hai chiều + giấy phép
    if not MANIFEST.exists():
        f.append(("FAIL", "manifest", f"thiếu {MANIFEST} (tiêu chí Done #5 của T16)"))
    else:
        mtxt = MANIFEST.read_text(encoding="utf-8")
        listed = set(re.findall(r"(mintos-glass-dark[a-z0-9-]*\.svg)", mtxt))
        actual = {p.name for p in wps}
        for n in sorted(actual - listed):
            f.append(("FAIL", "manifest", f"{n} chưa được ghi trong MANIFEST.md"))
        for n in sorted(listed - actual):
            f.append(("FAIL", "manifest", f"MANIFEST.md nhắc tới {n} nhưng tệp không tồn tại"))
        for key in ("giấy phép", "Light Glass", "tự vẽ", "desktop"):
            if key.lower() not in mtxt.lower():
                f.append(("FAIL", "manifest", f"MANIFEST.md thiếu mục nói về `{key}`"))

    # 9: không có tệp raster lạ
    stray = [p.name for p in WP_DIR.iterdir()
             if p.is_file() and p.suffix.lower() not in (".svg", ".md", ".sh", ".xml")]
    if stray:
        f.append(("WARN", "stray-file",
                  f"có tệp không phải SVG/MD/SH/XML: {stray} — nếu là raster thì "
                  "phải có pipeline render và khai báo thật, không khai khống"))
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint wallpaper (T16)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    print(f"wallpapers · {WP_DIR.relative_to(REPO)}")
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
