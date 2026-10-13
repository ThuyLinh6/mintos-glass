#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint cho tài nguyên SVG của Cinnamon theme — Task T05 (Agent D · Visual/Assets).

Hiện thực hoá 4 tiêu chí "Done" của T05 trong docs/plan/04-work-breakdown.md:

  1. mọi `url("…")` trong `cinnamon.css` resolve tới file TỒN TẠI;
  2. SVG well-formed (parse được bằng `xml.etree`);
  3. không SVG nào hard-code màu trùng token — phải dùng màu từ token hoặc ghi lý do;
  4. có `@2x` hoặc `viewBox` đúng để scale HiDPI.

Cộng thêm các ràng buộc từ yêu cầu của Agent 5 (mục 2 và mục 6): không tải tài
nguyên từ Internet khi chạy, không nhúng ảnh qua URL bên ngoài, tên tệp nhất quán.

--------------------------------------------------------------------------
HAI QUYẾT ĐỊNH KỸ THUẬT, đều có căn cứ đã xác minh
--------------------------------------------------------------------------
A. `url()` được phân giải THEO THƯ MỤC CỦA FILE CSS khai báo nó, không phải theo
   thư mục làm việc. Bằng chứng: `_st_theme_resolve_url` tại
   linuxmint/Cinnamon `src/st/st-theme.c:1082-1140` (đã đọc ở T04). Vì
   `cinnamon.css` đã biên dịch nằm ở GỐC theme, một url TRẦN như
   `checkbox.svg` sẽ được tìm ở `<themedir>/checkbox.svg` chứ không phải
   `<themedir>/assets/checkbox.svg`. Bài `no-bare-url` bên dưới bắt trường hợp đó.

   GHI CHÚ: phải TÁCH selector nhóm trước khi áp dụng last-wins. Nếu key theo cả
   chuỗi selector nhóm (`.check-box StBin, .check-box-2 StBin`) thì hai url khác
   nhau cùng "sống sót" và ta sẽ tưởng còn url trần trong khi thực tế không có.
   Đã dính đúng lỗi này khi khảo sát T05.

B. Trong SVG dùng `fill="#rrggbb"` + `fill-opacity` thay vì `fill="rgba(…)"`.
   librsvg hỗ trợ `rgba()` trong presentation attribute KHÔNG nhất quán giữa các
   phiên bản, còn hex + `*-opacity` thì hoạt động ở mọi bản. St render SVG qua
   librsvg nên đây là ràng buộc thật, không phải sở thích. Bài `no-rgba-in-svg`
   khoá lại.

--------------------------------------------------------------------------
VÌ SAO MÀU TRONG SVG VẪN LÀ "TỪ TOKEN"
--------------------------------------------------------------------------
St KHÔNG có CSS variable và không thể đọc SCSS token lúc runtime: SVG là tệp
riêng, được librsvg nạp và raster hoá độc lập. Nên màu BẮT BUỘC phải là literal
trong tệp SVG — không có cách nào khác.

Tiêu chí 3 của T05 vì vậy được hiện thực như sau: mọi literal màu và mọi giá trị
opacity trong SVG phải BẰNG ĐÚNG một giá trị token trong
`src/cinnamon/tokens/_tokens.scss`, và `MANIFEST.md` phải ghi rõ literal đó đến từ
token nào. Bài `colors-are-token-values` kiểm tra bằng máy; MANIFEST cho phép người
đọc tra ngược. Nếu một literal không khớp token nào thì phải nằm trong
`DOCUMENTED_EXCEPTIONS` kèm lý do, nếu không là FAIL.

Các tệp SVG được sinh ra bằng cách đọc thẳng `_tokens.scss` (không gõ tay giá trị
nào), nên mối liên hệ token -> literal là thật chứ không phải gán ngược về sau.

Chạy:  python3 tools/lint/assets.py [--verbose]
Exit 0 khi sạch. Cần libsass hoặc dart-sass để biên dịch; nếu không có thì các
bài cần CSS báo SKIP chứ không báo PASS giả.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "src" / "cinnamon" / "assets"
TOKENS = REPO / "src" / "cinnamon" / "tokens" / "_tokens.scss"
MANIFEST = ASSETS / "MANIFEST.md"

sys.path.insert(0, str(REPO / "tools" / "lint"))
import st_properties as sp  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# Kích thước CSS khai báo cho từng asset, lấy từ CSS ĐÃ BIÊN DỊCH của T04.
# Dùng để kiểm tra viewBox có khớp hay không (tiêu chí 4 của T05: scale HiDPI).
# Một asset có thể được dùng ở NHIỀU kích thước (close.svg: 22px và 26px) — khi
# đó viewBox chỉ cần cùng TỶ LỆ, vì `background-size: contain` tự scale.
# ---------------------------------------------------------------------------
URL_RE = re.compile(r'url\(\s*"([^"]+)"\s*\)|url\(\s*\'([^\']+)\'\s*\)')
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
OPACITY_ATTR_RE = re.compile(r'\b(fill-opacity|stroke-opacity|stop-opacity|opacity)\s*=\s*"([^"]+)"')
LENGTH_ATTR_RE = re.compile(r'\b(width|height)\s*=\s*"([^"]+)"')
VIEWBOX_RE = re.compile(r'\bviewBox\s*=\s*"([^"]+)"')
EXTERNAL_RE = re.compile(r"(https?:)?//[^\s\"')]+|\bxlink:href\s*=|\shref\s*=\s*[\"'](?!(#|data:))", re.I)
DANGEROUS_RE = re.compile(r"<\s*(script|image|foreignObject|iframe|use)\b", re.I)
RGBA_RE = re.compile(r"\brgba?\s*\(")


# ---------------------------------------------------------------------------
# Literal KHÔNG khớp token nào thì phải có mặt ở đây KÈM LÝ DO.
# Rỗng là trạng thái lý tưởng: mọi giá trị đều tra ngược được về token.
# ---------------------------------------------------------------------------
DOCUMENTED_EXCEPTIONS: dict[str, dict[str, str]] = {
    # "corner-ripple.svg": {"0.55": "..." },
}


def token_color_values() -> set[str]:
    """Mọi giá trị màu hex xuất hiện trong _tokens.scss (đã chuẩn hoá lowercase)."""
    out: set[str] = set()
    for m in HEX_RE.finditer(TOKENS.read_text()):
        h = m.group(0).lower()
        if len(h) == 4:  # #rgb -> #rrggbb
            h = "#" + "".join(c * 2 for c in h[1:])
        out.add(h)
    # rgba(r,g,b,a) trong token -> cả hex của bộ ba và chính chuỗi rgba
    for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", TOKENS.read_text()):
        out.add("#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3)))
    return out


def token_alpha_values() -> set[str]:
    """Mọi giá trị alpha/opacity trần xuất hiện trong _tokens.scss."""
    out: set[str] = set()
    txt = TOKENS.read_text()
    for m in re.finditer(r"rgba?\([^)]*,\s*([\d.]+)\s*\)", txt):
        out.add(m.group(1))
    # token opacity.* / blur.* là số trần
    for m in re.finditer(r"^\$mg-(?:opacity|blur)-[a-z0-9-]+:\s*([\d.]+)\s*;", txt, re.M):
        out.add(m.group(1))
    # 0 và 1 luôn hợp lệ (đầu/cuối của gradient, tắt hẳn)
    out |= {"0", "1", "0.0", "1.0"}
    return out


def effective_urls() -> dict[tuple[str, str], str]:
    """url() HIỆU LỰC sau cascade, key theo (SELECTOR ĐƠN, property).

    PHẢI tách selector nhóm: St tách selector nhóm trước khi so khớp, nên last-wins
    chỉ có nghĩa trên selector đơn.
    """
    css, _ = sp.compile_css()
    if css is None:
        return {}
    eff: dict[tuple[str, str], str] = {}
    for sel, decls in sp.parse_rules(css):
        for prop, value in decls:
            m = URL_RE.search(value)
            if not m:
                continue
            url = m.group(1) or m.group(2)
            for simple in sp.split_selectors(sel):
                eff[(simple, prop)] = url
    return eff


def declared_sizes() -> dict[str, list[tuple[str, float | None, float | None]]]:
    """url -> [(selector, width_px, height_px)] CHỈ từ rule CÒN HIỆU LỰC.

    PHẢI tôn trọng last-wins theo selector đơn. Bản đầu của hàm này gom mọi rule
    có url trùng tên tệp, nên nó lấy cả `width:400px; height:120px` của rule
    vendor cho `.window-close-area` — rule đã bị override của T04
    (`assets/trash-icon.svg`, 48x48) đè lên — rồi báo viewBox lệch tỷ lệ. Đó là
    FAIL giả sinh ra bởi chính lint.
    """
    css, _ = sp.compile_css()
    if css is None:
        return {}

    def px(v: str | None) -> float | None:
        if not v:
            return None
        m = re.fullmatch(r"([\d.]+)px", v.strip())
        return float(m.group(1)) if m else None

    # last-wins theo (selector đơn, property) — đúng cách St cascade
    win: dict[tuple[str, str], tuple[str, float | None, float | None]] = {}
    for sel, decls in sp.parse_rules(css):
        d = dict(decls)
        for prop, value in d.items():
            m = URL_RE.search(value)
            if not m:
                continue
            url = m.group(1) or m.group(2)
            for simple in sp.split_selectors(sel):
                win[(simple, prop)] = (url, px(d.get("width")), px(d.get("height")))

    out: dict[str, list[tuple[str, float | None, float | None]]] = {}
    for (simple, _prop), (url, w, h) in win.items():
        out.setdefault(url, []).append((simple, w, h))
    return out


def parse_svg(path: Path):
    """(root, text) hoặc raise. `xml.etree` là yêu cầu tường minh trong tiêu chí 2."""
    text = path.read_text(encoding="utf-8")
    return ET.fromstring(text), text


def svg_geometry(root) -> tuple[float, float, float | None, float | None]:
    """(vb_w, vb_h, attr_w, attr_h)."""
    vb = root.get("viewBox")
    if not vb:
        raise ValueError("thiếu viewBox")
    parts = re.split(r"[\s,]+", vb.strip())
    if len(parts) != 4:
        raise ValueError(f"viewBox sai định dạng: {vb!r}")
    x, y, w, h = (float(p) for p in parts)
    if x != 0 or y != 0:
        raise ValueError(f"viewBox phải bắt đầu ở 0 0, đang là {vb!r}")
    aw, ah = root.get("width"), root.get("height")
    def num(v):
        if v is None:
            return None
        m = re.fullmatch(r"([\d.]+)(px)?", v.strip())
        return float(m.group(1)) if m else None
    return w, h, num(aw), num(ah)


def findings(verbose: bool = False,
             assets_dir: Path | None = None) -> list[tuple[str, str, str]]:
    """`assets_dir` cho phép trỏ lint vào một bản sao tạm — cần để viết mutation
    test (xem tests/lint/test_assets.py). Mặc định là thư mục thật của repo."""
    root = assets_dir if assets_dir is not None else ASSETS
    manifest = root / "MANIFEST.md" if assets_dir is not None else MANIFEST
    f: list[tuple[str, str, str]] = []
    if not root.is_dir():
        return [("FAIL", "assets-dir", f"thiếu thư mục {root}")]

    svgs = sorted(p for p in root.glob("*.svg"))
    if not svgs:
        f.append(("FAIL", "assets-dir", "không có SVG nào trong assets/"))

    # 0 ------------------------------------------------------------------
    # Tên tệp nhất quán: lowercase kebab-case, không space, không dấu.
    for p in svgs:
        stem = p.stem
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", stem):
            f.append(("FAIL", "naming", f"{p.name}: tên tệp phải là lowercase kebab-case"))

    # 1 ------------------------------------------------------------------
    # Tiêu chí 1: mọi url() hiệu lực resolve tới file tồn tại.
    eff = effective_urls()
    sizes = declared_sizes()
    if not eff:
        f.append(("SKIP", "resolve",
                  "không có compiler (libsass/dart-sass) -> bỏ qua bài kiểm tra "
                  "dựa trên CSS đã biên dịch"))
    else:
        for url in sorted({u for u in eff.values()}):
            # St resolve theo thư mục của file CSS khai báo url đó. cinnamon.css
            # nằm ở src/cinnamon/, nên "assets/x.svg" -> src/cinnamon/assets/x.svg.
            # Khi được truyền assets_dir (mutation test) thì resolve theo bản sao đó.
            base = (root if assets_dir is not None
                    else (REPO / "src" / "cinnamon"))
            target = (base / Path(url).name).resolve() if assets_dir is not None \
                else (REPO / "src" / "cinnamon" / url).resolve()
            if not target.exists():
                where = (target.relative_to(REPO)
                         if target.is_relative_to(REPO) else target)
                f.append(("FAIL", "resolve",
                          f"`url(\"{url}\")` trong cinnamon.css không resolve: "
                          f"thiếu {where}"))
            if not url.startswith("assets/"):
                f.append(("FAIL", "no-bare-url",
                          f"`url(\"{url}\")` là url TRẦN. cinnamon.css nằm ở gốc "
                          "theme và _st_theme_resolve_url (src/st/st-theme.c:"
                          "1082-1140) resolve theo thư mục của file CSS, nên St sẽ "
                          f"tìm ở <themedir>/{url} chứ không phải "
                          f"<themedir>/assets/{url}. Hãy ghi `assets/{url}`."))
        if verbose:
            print(f"  · {len(set(eff.values()))} url hiệu lực trên "
                  f"{len(eff)} cặp (selector, property)", file=sys.stderr)

    # Ngược lại: file nào nằm trong assets/ mà KHÔNG được CSS nào dùng?
    used = {Path(u).name for u in set(eff.values())} if eff else set()
    for p in svgs:
        if used and p.name not in used:
            f.append(("WARN", "unused-asset",
                      f"{p.name} không được url() nào trong cinnamon.css dùng — "
                      "hoặc là asset chết, hoặc T04 chưa ghi selector trỏ tới nó"))

    # 2 ------------------------------------------------------------------
    # Tiêu chí 2 + 4: well-formed, viewBox đúng, khớp tỷ lệ CSS khai báo.
    geom: dict[str, tuple[float, float]] = {}
    for p in svgs:
        try:
            root, text = parse_svg(p)
        except ET.ParseError as exc:
            f.append(("FAIL", "well-formed", f"{p.name}: XML không parse được — {exc}"))
            continue
        except Exception as exc:
            f.append(("FAIL", "well-formed", f"{p.name}: {type(exc).__name__}: {exc}"))
            continue
        if root.tag != f"{{{SVG_NS}}}svg":
            f.append(("FAIL", "well-formed",
                      f"{p.name}: thẻ gốc phải là <svg> với namespace "
                      f"{SVG_NS}, đang là {root.tag!r}"))
        try:
            vbw, vbh, aw, ah = svg_geometry(root)
        except ValueError as exc:
            f.append(("FAIL", "hidpi-viewbox", f"{p.name}: {exc}"))
            continue
        geom[p.name] = (vbw, vbh)
        if aw is None or ah is None:
            f.append(("WARN", "hidpi-viewbox",
                      f"{p.name}: nên có width/height để librsvg biết kích thước "
                      "nội tại khi `background-size: contain`"))
        elif (aw, ah) != (vbw, vbh):
            f.append(("FAIL", "hidpi-viewbox",
                      f"{p.name}: width/height ({aw}x{ah}) lệch viewBox ({vbw}x{vbh})"
                      " — 1 đơn vị SVG phải bằng 1px ở 1x để HiDPI scale sắc"))
        # viewBox phải khớp TỶ LỆ với kích thước CSS khai báo
        for url, uses in sizes.items():
            if Path(url).name != p.name:
                continue
            for sel, w, h in uses:
                if w is None or h is None:
                    continue
                if abs((vbw / vbh) - (w / h)) > 0.01:
                    f.append(("FAIL", "hidpi-viewbox",
                              f"{p.name}: viewBox {vbw}x{vbh} lệch tỷ lệ với "
                              f"{w}x{h}px mà CSS khai báo cho `{sel}` — "
                              "`background-size: contain` sẽ để lại khoảng trống "
                              "hoặc cắt hình"))

    # 3 ------------------------------------------------------------------
    # Tiêu chí 3: mọi literal màu / opacity phải tra ngược được về token.
    colors, alphas = token_color_values(), token_alpha_values()
    for p in svgs:
        try:
            _, text = parse_svg(p)
        except Exception:
            continue
        exc = DOCUMENTED_EXCEPTIONS.get(p.name, {})
        for m in HEX_RE.finditer(text):
            h = m.group(0).lower()
            if len(h) == 4:
                h = "#" + "".join(c * 2 for c in h[1:])
            if h not in colors and h not in exc:
                f.append(("FAIL", "colors-are-token-values",
                          f"{p.name}: màu `{m.group(0)}` không khớp giá trị token nào "
                          f"trong {TOKENS.relative_to(REPO)} và không có trong "
                          "DOCUMENTED_EXCEPTIONS. SVG không đọc được SCSS token lúc "
                          "runtime nên literal là bắt buộc, nhưng literal đó PHẢI "
                          "bằng một giá trị token và phải ghi trong MANIFEST.md."))
        for m in OPACITY_ATTR_RE.finditer(text):
            v = m.group(2).strip()
            if v not in alphas and v not in exc:
                f.append(("FAIL", "colors-are-token-values",
                          f"{p.name}: {m.group(1)}=\"{v}\" không khớp alpha/opacity "
                          "token nào (opacity.*, hoặc alpha trong rgba() của token) "
                          "và không có trong DOCUMENTED_EXCEPTIONS"))

    # 4 ------------------------------------------------------------------
    # An toàn + không phụ thuộc mạng (yêu cầu mục 2 và mục 6 của Agent 5).
    for p in svgs:
        try:
            _, text = parse_svg(p)
        except Exception:
            continue
        # Bỏ khai báo namespace TRƯỚC khi quét: xmlns="http://www.w3.org/2000/svg"
        # là BẮT BUỘC trong mọi tệp SVG hợp lệ và không phải tham chiếu mạng.
        # Bản đầu của lint này báo FAIL cho cả 15 tệp vì lý do đó.
        scan_text = re.sub(r'\sxmlns(?::[\w-]+)?\s*=\s*"[^"]*"', '', text)
        for m in EXTERNAL_RE.finditer(scan_text):
            frag = m.group(0)
            if frag.startswith("#"):
                continue
            f.append(("FAIL", "no-external-refs",
                      f"{p.name}: tham chiếu ra ngoài `{frag.strip()[:60]}` — tài "
                      "nguyên không được tải từ Internet khi chạy"))
        for m in DANGEROUS_RE.finditer(text):
            tag = m.group(1).lower()
            # <use> chỉ hợp lệ khi trỏ tới fragment NỘI BỘ; đã bị EXTERNAL_RE bắt
            # nếu trỏ ra ngoài. Ở đây chặn luôn vì 15 asset này không cần nó.
            f.append(("FAIL", "no-external-refs",
                      f"{p.name}: chứa thẻ <{tag}> — không cần thiết cho asset St và "
                      "làm tăng rủi ro/bề mặt tấn công"))
        if RGBA_RE.search(text):
            f.append(("FAIL", "no-rgba-in-svg",
                      f"{p.name}: dùng rgba() trong SVG. librsvg hỗ trợ rgba() trong "
                      "presentation attribute không nhất quán giữa các phiên bản; "
                      "hãy dùng fill=\"#rrggbb\" + fill-opacity."))

    # 5 ------------------------------------------------------------------
    # MANIFEST: mọi SVG phải được ghi lại, và không ghi file không tồn tại.
    if not manifest.exists():
        f.append(("FAIL", "manifest", f"thiếu {manifest}"))
    else:
        mtxt = manifest.read_text()
        listed = set(re.findall(r"([a-z0-9-]+\.svg)", mtxt))
        actual = {p.name for p in svgs}
        for n in sorted(actual - listed):
            f.append(("FAIL", "manifest", f"{n} chưa được ghi trong MANIFEST.md"))
        for n in sorted(listed - actual):
            f.append(("FAIL", "manifest",
                      f"MANIFEST.md nhắc tới {n} nhưng tệp không tồn tại"))
        # MANIFEST phải ghi được token nguồn cho từng file
        for n in sorted(actual):
            if n in mtxt and "mg-" not in mtxt:
                f.append(("WARN", "manifest",
                          "MANIFEST.md không nhắc token $mg-* nào — tiêu chí 3 của "
                          "T05 yêu cầu ghi lý do/nguồn màu"))

    if verbose and geom:
        print(f"  · {len(svgs)} SVG well-formed, viewBox: "
              + ", ".join(f"{k}={int(v[0])}x{int(v[1])}" for k, v in sorted(geom.items())[:4])
              + " …", file=sys.stderr)
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint assets SVG của Cinnamon theme (T05)")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()
    print("assets · src/cinnamon/assets/")
    f = findings(verbose=a.verbose)
    fails = [x for x in f if x[0] == "FAIL"]
    warns = [x for x in f if x[0] == "WARN"]
    skips = [x for x in f if x[0] == "SKIP"]
    for sev, cid, msg in f:
        print(f"  [{sev}] {cid}: {msg}")
    if skips and not fails:
        print(f"SKIP một phần — {len(skips)} bài cần compiler")
    if fails:
        print(f"FAIL — {len(fails)} lỗi, {len(warns)} cảnh báo")
        return 1
    print(f"OK — 0 lỗi" + (f", {len(warns)} cảnh báo" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
