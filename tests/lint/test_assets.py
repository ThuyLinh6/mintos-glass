#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/assets.py` và 15 SVG của T05.

Chạy bằng stdlib unittest, không cần pytest:
    python3 -m unittest discover -s tests -t .
    python3 -m unittest tests.lint.test_assets -v

--------------------------------------------------------------------------
VÌ SAO CÓ LỚP TestLintActuallyFails
--------------------------------------------------------------------------
Bài học lặp lại hai lần trong dự án này: một lint CHỈ có giá trị khi nó thật sự đỏ
lúc code sai. Ở T04, `st_properties.py` đã pass rỗng nhiều vòng vì bug offset index
và vì guard `\\(\\s*\\$` sai khi regex đã ăn mất dấu `(`. Ở chính T05, bản đầu của
`assets.py` có HAI bug làm nó báo sai: (1) coi khai báo `xmlns` là tham chiếu mạng
nên FAIL cả 15 tệp; (2) `declared_sizes()` không tôn trọng last-wins nên so viewBox
48x48 với `400x120` của rule vendor ĐÃ BỊ override và báo FAIL giả cho
`trash-icon.svg`. Cả hai chỉ lộ ra khi chạy thật.

Nên lớp cuối của tệp này bẻ cong SVG thành bản SAI trong thư mục tạm rồi khẳng định
lint FAIL. Nếu `assets.py` hỏng về sau, lớp này đỏ trước.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "lint"))

try:
    import assets as al
    import st_properties as sp
except Exception as exc:  # pragma: no cover
    al = sp = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

ASSETS = REPO / "src" / "cinnamon" / "assets"
TOKENS = REPO / "src" / "cinnamon" / "tokens" / "_tokens.scss"

# 15 url() đã được T04 chốt trong tests/lint/test_cinnamon_coverage.py.
# Không chép mù: test_names_match_t04_expected_assets so với bộ thật của T04 để
# hai module không trôi ra khỏi nhau.
EXPECTED_15 = {
    "add-workspace.svg", "add-workspace-hover.svg",
    "calendar-arrow-left.svg", "calendar-arrow-left-hover.svg",
    "calendar-arrow-right.svg", "calendar-arrow-right-hover.svg",
    "checkbox.svg", "checkbox-off.svg",
    "radio.svg", "radio-off.svg",
    "toggle-on.svg", "toggle-off.svg",
    "close.svg", "trash-icon.svg", "corner-ripple.svg",
}

# viewBox -> kích thước CSS mà T04 khai báo. Lấy từ CSS đã biên dịch, không gõ tay.
EXPECTED_VIEWBOX = {
    "checkbox-off.svg": (20, 20), "checkbox.svg": (20, 20),
    "radio-off.svg": (20, 20), "radio.svg": (20, 20),
    "toggle-off.svg": (46, 26), "toggle-on.svg": (46, 26),
    "calendar-arrow-left.svg": (16, 16), "calendar-arrow-left-hover.svg": (16, 16),
    "calendar-arrow-right.svg": (16, 16), "calendar-arrow-right-hover.svg": (16, 16),
    "close.svg": (24, 24),
    "add-workspace.svg": (35, 200), "add-workspace-hover.svg": (35, 200),
    "trash-icon.svg": (48, 48), "corner-ripple.svg": (52, 52),
}

SVG_NS = "http://www.w3.org/2000/svg"


def _compiler():
    return al is not None and al.sp.find_compiler() is not None


NEED_COMPILER = unittest.skipUnless(_compiler(),
                                    "cần libsass (pip install libsass) hoặc dart-sass")


@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestAssetInventory(unittest.TestCase):
    def test_directory_exists_with_15_svgs(self):
        self.assertTrue(ASSETS.is_dir(), f"thiếu {ASSETS}")
        svgs = sorted(p.name for p in ASSETS.glob("*.svg"))
        self.assertEqual(len(svgs), 15, f"không đúng 15 SVG: {svgs}")

    def test_names_match_t04_expected_assets(self):
        """Hai module phải nói CÙNG một danh sách, không được trôi ra khỏi nhau.

        T04 chốt `EXPECTED_ASSETS` trong tests/lint/test_cinnamon_coverage.py từ
        url() của CSS đã biên dịch. T05 giao tệp. Nếu hai danh sách lệch nhau thì
        hoặc là CSS trỏ tới tệp không tồn tại, hoặc là có tệp chết.
        """
        try:
            sys.path.insert(0, str(REPO / "tests" / "lint"))
            import test_cinnamon_coverage as t04
        except Exception as exc:
            self.skipTest(f"không import được test_cinnamon_coverage: {exc}")
        self.assertEqual({Path(a).name for a in t04.EXPECTED_ASSETS}, EXPECTED_15)
        self.assertEqual(sorted(p.name for p in ASSETS.glob("*.svg")), sorted(EXPECTED_15))

    def test_no_png_or_raster_files(self):
        """T04 đã chuyển corner-ripple.png -> .svg để không cần bộ encode PNG.

        Tiêu chí 4 của T05 cho chọn "@2x HOẶC viewBox đúng"; dự án chọn viewBox,
        nên KHÔNG được có tệp raster nào lẫn vào — nếu có thì phải có pipeline
        render và phải khai báo @2x thật, không khai báo khống.
        """
        others = [p.name for p in ASSETS.iterdir() if p.suffix.lower() != ".svg"
                  and p.name != "MANIFEST.md"]
        self.assertEqual(others, [], f"có tệp không phải SVG: {others}")

    def test_naming_is_lowercase_kebab_case(self):
        for p in ASSETS.glob("*.svg"):
            self.assertRegex(p.stem, r"^[a-z0-9]+(-[a-z0-9]+)*$",
                             f"{p.name} không đúng quy ước lowercase kebab-case")

    def test_no_at2x_claims_without_files(self):
        """Không khai báo khả năng mà tài nguyên không đáp ứng (yêu cầu mục 5)."""
        for p in ASSETS.glob("*.svg"):
            self.assertNotRegex(p.name, r"@2x|@3x",
                                "tên có @2x nhưng không có pipeline raster")
        man = (ASSETS / "MANIFEST.md")
        if man.exists():
            txt = man.read_text()
            for m in re.finditer(r"([a-z0-9-]+@2x\.svg)", txt):
                self.assertTrue((ASSETS / m.group(1)).exists(),
                                f"MANIFEST nhắc {m.group(1)} nhưng tệp không tồn tại")


@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestSvgWellFormed(unittest.TestCase):
    """Tiêu chí 2 của T05: parse được bằng `xml.etree`."""

    def test_every_svg_parses(self):
        for p in sorted(ASSETS.glob("*.svg")):
            with self.subTest(asset=p.name):
                try:
                    root = ET.fromstring(p.read_text(encoding="utf-8"))
                except ET.ParseError as exc:
                    self.fail(f"{p.name} không parse được: {exc}")
                self.assertEqual(root.tag, f"{{{SVG_NS}}}svg",
                                 f"{p.name}: thẻ gốc phải là <svg> có namespace SVG")

    def test_viewbox_matches_expected(self):
        for p in sorted(ASSETS.glob("*.svg")):
            with self.subTest(asset=p.name):
                root = ET.fromstring(p.read_text(encoding="utf-8"))
                vbw, vbh, aw, ah = al.svg_geometry(root)
                self.assertEqual((vbw, vbh), EXPECTED_VIEWBOX[p.name],
                                 f"{p.name}: viewBox lệch kích thước đã chốt")
                self.assertEqual((aw, ah), (vbw, vbh),
                                 f"{p.name}: width/height phải bằng viewBox để "
                                 "1 đơn vị SVG = 1px ở 1x (HiDPI scale sắc)")

    def test_no_filters_or_masks(self):
        """librsvg hỗ trợ <filter> nhưng chi phí raster cao và kết quả khác nhau
        giữa phiên bản. Bóng đổ trong bộ asset này dùng gradient + opacity."""
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            for tag in ("<filter", "<mask", "feGaussianBlur", "<clipPath"):
                with self.subTest(asset=p.name, tag=tag):
                    self.assertNotIn(tag, txt)


@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestColoursTraceToTokens(unittest.TestCase):
    """Tiêu chí 3 của T05.

    St KHÔNG đọc được SCSS token lúc runtime: SVG là tệp riêng, librsvg nạp và
    raster hoá độc lập, không có CSS variable. Nên literal là BẮT BUỘC. Cách thoả
    mãn tiêu chí 3 một cách trung thực: mọi literal phải BẰNG ĐÚNG một giá trị
    token, và MANIFEST.md ghi rõ literal đó đến từ token nào.
    """

    def test_no_documented_exceptions(self):
        """Bảng ngoại lệ phải RỖNG — mọi giá trị đều tra ngược được về token."""
        self.assertEqual(al.DOCUMENTED_EXCEPTIONS, {},
                         "DOCUMENTED_EXCEPTIONS không rỗng: có literal nằm ngoài hệ "
                         "token. Hãy xin Agent Design Systems bổ sung token thay vì "
                         "thêm ngoại lệ cho qua chuyện.")

    def test_every_hex_is_a_token_value(self):
        colors = al.token_color_values()
        self.assertGreater(len(colors), 20, "token_color_values() trả về quá ít — kiểm tra lại")
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            for m in al.HEX_RE.finditer(txt):
                h = m.group(0).lower()
                if len(h) == 4:
                    h = "#" + "".join(c * 2 for c in h[1:])
                with self.subTest(asset=p.name, colour=m.group(0)):
                    self.assertIn(h, colors,
                                  f"{p.name}: {m.group(0)} không khớp giá trị token nào")

    def test_every_opacity_is_a_token_alpha(self):
        alphas = al.token_alpha_values()
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            for m in al.OPACITY_ATTR_RE.finditer(txt):
                with self.subTest(asset=p.name, attr=m.group(1), value=m.group(2)):
                    self.assertIn(m.group(2).strip(), alphas,
                                  f"{p.name}: {m.group(1)}=\"{m.group(2)}\" không khớp "
                                  "alpha/opacity token nào")

    def test_no_rgba_function_in_attributes(self):
        """librsvg hỗ trợ rgba() trong presentation attribute KHÔNG nhất quán giữa
        các phiên bản; hex + `*-opacity` thì luôn hoạt động."""
        for p in sorted(ASSETS.glob("*.svg")):
            with self.subTest(asset=p.name):
                self.assertNotRegex(p.read_text(encoding="utf-8"), r"\brgba?\s*\(")

    def test_accent_glyph_uses_dark_not_white(self):
        """Quyết định đã ĐO: glyph trên nền accent phải tối.

        #0b0c0e trên #3ddc97 = 11.07:1 PASS; #ffffff trên #3ddc97 = 1.77:1 FAIL.
        Cố ý lệch macOS (knob trắng) vì yêu cầu dự án cấm hy sinh tương phản để bắt
        chước. Ngưỡng 3:1 cho đối tượng đồ hoạ (WCAG 1.4.11).
        """
        try:
            import contrast as ct
        except Exception as exc:
            self.skipTest(f"không import được contrast.py: {exc}")
        on_accent = ct.to_rgb(ct.parse_hex("#0b0c0e"))
        white = ct.to_rgb(ct.parse_hex("#ffffff"))
        accent = ct.to_rgb(ct.parse_hex("#3ddc97"))
        self.assertGreaterEqual(ct.contrast_ratio(on_accent, accent), 3.0)
        self.assertLess(ct.contrast_ratio(white, accent), 3.0,
                        "nếu trắng trên accent đã đạt 3:1 thì kết luận thiết kế phải xét lại")
        for name in ("checkbox.svg", "radio.svg", "toggle-on.svg"):
            txt = (ASSETS / name).read_text()
            self.assertIn("#0b0c0e", txt, f"{name} phải dùng glyph/knob tối trên accent")

    def test_close_glyph_contrast_measured(self):
        """✕ trên nền status-error: #0b0c0e = 6.55:1 PASS, #ffffff = 2.99:1 FAIL."""
        try:
            import contrast as ct
        except Exception as exc:
            self.skipTest(f"không import được contrast.py: {exc}")
        err = ct.to_rgb(ct.parse_hex("#ff5f57"))
        self.assertGreaterEqual(ct.contrast_ratio(ct.to_rgb(ct.parse_hex("#0b0c0e")), err), 3.0)
        self.assertLess(ct.contrast_ratio(ct.to_rgb(ct.parse_hex("#ffffff")), err), 3.0)
        txt = (ASSETS / "close.svg").read_text()
        self.assertIn("#ff5f57", txt)
        self.assertIn("#0b0c0e", txt)


@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestNoExternalDependencies(unittest.TestCase):
    """Yêu cầu mục 2 và mục 6: không tải tài nguyên từ Internet khi chạy,
    không nhúng ảnh qua URL bên ngoài."""

    def test_no_script_image_or_use_tags(self):
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            for tag in ("<script", "<image", "<foreignObject", "<iframe", "<use"):
                with self.subTest(asset=p.name, tag=tag):
                    self.assertNotIn(tag, txt)

    def test_only_external_looking_string_is_the_xmlns(self):
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            urls = set(re.findall(r"https?://[^\s\"')]+", txt))
            with self.subTest(asset=p.name):
                self.assertEqual(urls, {SVG_NS},
                                 f"{p.name} tham chiếu URL ngoài namespace SVG: {urls}")

    def test_no_href_attributes_at_all(self):
        """`href`/`xlink:href` chỉ cần khi có <use>; bộ này không có <use>."""
        for p in sorted(ASSETS.glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            self.assertNotIn("xlink:", txt)
            for m in re.finditer(r'\shref\s*=\s*"([^"]*)"', txt):
                with self.subTest(asset=p.name):
                    self.assertTrue(m.group(1).startswith("#"),
                                    f"{p.name}: href trỏ ra ngoài `{m.group(1)}`")

    def test_gradient_ids_are_unique_across_the_set(self):
        """Id trùng nhau giữa các tệp thì vô hại (mỗi tệp parse riêng), NHƯNG nếu
        sau này ghép vào sprite sheet thì sẽ đụng nhau. Đặt id có tiền tố `mg`."""
        ids = []
        for p in sorted(ASSETS.glob("*.svg")):
            ids += re.findall(r'\sid="([^"]+)"', p.read_text(encoding="utf-8"))
        self.assertEqual(len(ids), len(set(ids)), f"id trùng nhau: {ids}")
        for i in ids:
            self.assertTrue(i.startswith("mg"), f"id `{i}` nên có tiền tố mg để tránh đụng")


@NEED_COMPILER
@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestUrlsFromCompiledCss(unittest.TestCase):
    """Tiêu chí 1 của T05: mọi url() trong cinnamon.css resolve tới file tồn tại."""

    def test_every_effective_url_resolves(self):
        eff = al.effective_urls()
        self.assertTrue(eff, "không trích được url() nào từ CSS đã biên dịch")
        urls = sorted(set(eff.values()))
        self.assertEqual(len(urls), 15, f"không đúng 15 url hiệu lực: {urls}")
        for u in urls:
            with self.subTest(url=u):
                # _st_theme_resolve_url (src/st/st-theme.c:1082-1140) resolve theo
                # THƯ MỤC CỦA TỆP CSS khai báo url đó. cinnamon.css nằm ở gốc theme.
                self.assertTrue((REPO / "src" / "cinnamon" / u).exists(),
                                f"{u} không tồn tại so với gốc theme")

    def test_no_bare_urls_win_the_cascade(self):
        """url TRẦN sẽ được St tìm ở GỐC THEME, không phải trong assets/.

        Vendor dùng url trần (`checkbox.svg`); T04 đã ghi đè hết sang `assets/…`.
        Nếu một url trần còn thắng cascade thì asset sẽ không bao giờ hiện ra, và
        St KHÔNG có tầng fallback cascade (PROP_FALLBACK_STYLESHEET là
        non-cascading, đã xác minh ở T04).
        """
        bare = sorted({u for u in al.effective_urls().values() if "/" not in u})
        self.assertEqual(bare, [], f"url trần vẫn thắng cascade: {bare}")

    def test_no_effective_url_points_outside_assets_dir(self):
        for u in sorted(set(al.effective_urls().values())):
            with self.subTest(url=u):
                self.assertTrue(u.startswith("assets/"), f"{u} không nằm trong assets/")

    def test_viewbox_ratio_matches_css_declaration(self):
        """`background-size: contain` sẽ để khoảng trống hoặc cắt hình nếu lệch tỷ lệ.

        Chỉ so với rule CÒN HIỆU LỰC: vendor khai báo 400x120 cho
        `.window-close-area` nhưng T04 đã override thành 48x48.
        """
        sizes = al.declared_sizes()
        geom = {}
        for p in ASSETS.glob("*.svg"):
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            vbw, vbh, _, _ = al.svg_geometry(root)
            geom[p.name] = (vbw, vbh)
        for url, uses in sizes.items():
            name = Path(url).name
            if name not in geom:
                continue
            vbw, vbh = geom[name]
            for sel, w, h in uses:
                if w is None or h is None:
                    continue
                with self.subTest(asset=name, selector=sel):
                    self.assertAlmostEqual(vbw / vbh, w / h, delta=0.01,
                                           msg=f"{name} viewBox {vbw}x{vbh} lệch tỷ lệ "
                                               f"với {w}x{h}px của `{sel}`")

    def test_trash_icon_is_measured_against_the_override_not_the_vendor(self):
        """Hồi quy cho bug của chính lint: so với rule đã bị đè -> FAIL giả."""
        sizes = al.declared_sizes()
        uses = sizes.get("assets/trash-icon.svg", [])
        self.assertTrue(uses, "không thấy .window-close-area trong declared_sizes()")
        dims = {(w, h) for _sel, w, h in uses}
        self.assertEqual(dims, {(48.0, 48.0)},
                         f"declared_sizes() đang trả về cả kích thước của rule vendor "
                         f"đã bị override: {dims}")


@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestManifest(unittest.TestCase):
    def setUp(self):
        self.path = ASSETS / "MANIFEST.md"

    def test_manifest_exists(self):
        self.assertTrue(self.path.exists(), f"thiếu {self.path} (allow-list của T05)")

    def test_two_way_consistency(self):
        txt = self.path.read_text()
        listed = set(re.findall(r"([a-z0-9-]+\.svg)", txt))
        actual = {p.name for p in ASSETS.glob("*.svg")}
        self.assertEqual(actual - listed, set(), "SVG chưa được ghi trong MANIFEST")
        self.assertEqual(listed - actual, set(), "MANIFEST nhắc tới tệp không tồn tại")

    def test_every_colour_literal_is_documented_with_a_token(self):
        """MANIFEST phải cho người đọc tra ngược literal -> token."""
        txt = self.path.read_text()
        used = set()
        for p in ASSETS.glob("*.svg"):
            used |= {m.group(0).lower() for m in al.HEX_RE.finditer(p.read_text())}
        for h in sorted(used):
            with self.subTest(colour=h):
                self.assertIn(h, txt.lower(),
                              f"màu {h} dùng trong SVG nhưng MANIFEST không ghi token nguồn")

    def test_manifest_records_the_measured_contrast_decisions(self):
        txt = self.path.read_text()
        for needle in ("11.07", "1.77", "6.55", "2.99"):
            with self.subTest(value=needle):
                self.assertIn(needle, txt,
                              "MANIFEST phải ghi con số tương phản đã ĐO, không ghi "
                              "kết luận chung chung")


@NEED_COMPILER
@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test trên bản sao tạm. Không ghi gì vào repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-assets-mutant-"))
        for p in ASSETS.iterdir():
            shutil.copy2(p, self.tmp / p.name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, findings, severity="FAIL"):
        return {cid for sev, cid, _ in findings if sev == severity}

    def test_baseline_is_clean(self):
        f = al.findings(assets_dir=self.tmp)
        fails = [(c, m) for s, c, m in f if s == "FAIL"]
        self.assertEqual(fails, [], f"bản sao của assets/ thật mà đã FAIL: {fails}")

    def _break(self, name, transform):
        p = self.tmp / name
        old = p.read_text()
        new = transform(old)
        self.assertNotEqual(old, new, f"đột biến không đổi gì {name} — bài test vô nghĩa")
        p.write_text(new)
        return self._ids(al.findings(assets_dir=self.tmp))

    def test_detects_malformed_xml(self):
        ids = self._break("checkbox.svg", lambda s: s.replace("</svg>", ""))
        self.assertIn("well-formed", ids)

    def test_detects_off_token_colour(self):
        ids = self._break("radio.svg", lambda s: s.replace("#3ddc97", "#ff00aa"))
        self.assertIn("colors-are-token-values", ids)

    def test_detects_off_token_opacity(self):
        ids = self._break("toggle-off.svg", lambda s: s.replace('fill-opacity="0.12"',
                                                                'fill-opacity="0.31"'))
        self.assertIn("colors-are-token-values", ids)

    def test_detects_missing_viewbox(self):
        ids = self._break("close.svg", lambda s: re.sub(r'\sviewBox="[^"]*"', '', s))
        self.assertIn("hidpi-viewbox", ids)

    def test_detects_viewbox_attr_mismatch(self):
        """viewBox đổi nhưng width/height không đổi -> 1 đơn vị SVG != 1px."""
        ids = self._break("close.svg", lambda s: s.replace('viewBox="0 0 24 24"',
                                                           'viewBox="0 0 48 48"'))
        self.assertIn("hidpi-viewbox", ids)

    def test_detects_rgba_in_attributes(self):
        ids = self._break("checkbox-off.svg",
                          lambda s: s.replace('fill="#17181c"', 'fill="rgba(23,24,28,1)"'))
        self.assertIn("no-rgba-in-svg", ids)

    def test_detects_external_reference(self):
        """xmlns phải được MIỄN (nó là khai báo namespace bắt buộc), nhưng một URL
        thật sự trỏ ra ngoài thì phải bị bắt. Bản đầu của lint bắt nhầm cả 15 tệp
        vì không phân biệt hai thứ này."""
        ids = self._break("radio.svg",
                          lambda s: s.replace("</svg>",
                                              '  <image href="https://example.com/x.png"/>\n</svg>'))
        self.assertIn("no-external-refs", ids)

    def test_detects_script_tag(self):
        ids = self._break("radio-off.svg",
                          lambda s: s.replace("</svg>", "  <script>x</script>\n</svg>"))
        self.assertIn("no-external-refs", ids)

    def test_detects_bad_filename(self):
        (self.tmp / "checkbox-off.svg").rename(self.tmp / "CheckBox_Off.svg")
        ids = self._ids(al.findings(assets_dir=self.tmp))
        self.assertTrue({"naming", "resolve", "manifest"} & ids,
                        f"đổi tên tệp sai quy ước mà lint không bắt: {ids}")

    def test_detects_missing_manifest_entry(self):
        man = self.tmp / "MANIFEST.md"
        man.write_text(man.read_text().replace("corner-ripple.svg", "corner-ripple-OLD.svg"))
        ids = self._ids(al.findings(assets_dir=self.tmp))
        self.assertIn("manifest", ids)

    def test_detects_missing_asset(self):
        (self.tmp / "toggle-on.svg").unlink()
        ids = self._ids(al.findings(assets_dir=self.tmp))
        self.assertIn("resolve", ids)
        self.assertIn("manifest", ids)

    def test_detects_empty_assets_dir(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        f = al.findings(assets_dir=empty)
        self.assertIn("assets-dir", self._ids(f))


@NEED_COMPILER
@unittest.skipIf(al is None, f"không import được tools/lint/assets.py: {IMPORT_ERROR}")
class TestT04LintIsNowFullySatisfied(unittest.TestCase):
    """T05 tồn tại để gỡ hai thứ đang treo bên T04. Khẳng định đã gỡ thật."""

    def test_st_properties_check_assets_is_clean(self):
        """`st_properties` không có hàm `findings_for()` công khai — findings được
        dựng bên trong `main()`. Nên gọi thẳng `check_assets()`, đúng hàm mà T05 gỡ."""
        css, _ = sp.compile_css()
        self.assertIsNotNone(css, "không biên dịch được cinnamon.css")
        found: list = []
        # `pending` là tập file được phép thiếu khi thư mục assets/ chưa tồn tại
        # (cơ chế T04 thêm để không FAIL khi T05 chưa hạ cánh). Truyền tập RỖNG
        # để khẳng định không còn gì phải khoan dung nữa.
        sp.check_assets(sp.parse_rules(css), set(), found)
        bad = [(x.check, x.severity, x.message) for x in found
               if x.severity in ("ERROR", "PENDING")]
        self.assertEqual(bad, [],
                         f"check_assets của T04 vẫn chưa sạch sau T05: {bad[:3]}")

    def test_st_properties_main_exits_zero(self):
        """Kiểm tra đầu-cuối: chính lệnh mà CI và `make check` sẽ chạy."""
        import subprocess
        proc = subprocess.run([sys.executable, str(REPO / "tools/lint/st_properties.py")],
                              cwd=str(REPO), capture_output=True, text=True, timeout=300)
        self.assertEqual(proc.returncode, 0,
                         f"st_properties.py exit {proc.returncode}\n"
                         f"stdout: {proc.stdout[-800:]}\nstderr: {proc.stderr[-800:]}")
        self.assertNotIn("PENDING", proc.stdout,
                         "st_properties vẫn in mục PENDING chờ T05")


if __name__ == "__main__":
    unittest.main(verbosity=2)
