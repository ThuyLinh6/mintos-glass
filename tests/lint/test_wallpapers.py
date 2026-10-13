#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/wallpapers.py` và 4 wallpaper của T16.

Chạy bằng stdlib unittest, KHÔNG cần compiler SCSS:
    python3 -m unittest tests.lint.test_wallpapers -v

--------------------------------------------------------------------------
BÀI QUAN TRỌNG NHẤT Ở ĐÂY LÀ TestDesktopLabelContrast
--------------------------------------------------------------------------
T09 đã xác minh từ mã nguồn rằng màu nhãn icon desktop **bị Nemo khoá**:
`nemo-style-application.css` nạp ở PRIORITY_APPLICATION (600) > theme (200), và
GTK 3.24 KHÔNG có `!important` (chuỗi "important" xuất hiện 0 lần trong
gtkcssparser.c / gtkcssprovider.c / gtkstylecascade.c @ 3.24.42).

Nghĩa là theme KHÔNG đổi được màu nhãn desktop. Nên nếu nhãn không đọc được thì
thứ DUY NHẤT sửa được là NỀN phía sau nó — tức là wallpaper. Ràng buộc tương
phản vì vậy thuộc về T16 chứ không phải T09, và nó phải được khoá bằng test ở đây.

T09 đã đo trên ba mức chói MÔ HÌNH (chưa có wallpaper thật). Các bài dưới đây đo
lại trên wallpaper THẬT và khẳng định kết luận của T09 vẫn đứng.
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
    import wallpapers as wl
except Exception as exc:  # pragma: no cover
    wl = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

WP = REPO / "src" / "wallpapers"
SVG_NS = "http://www.w3.org/2000/svg"
W, H = 1920, 1080

EXPECTED = {
    "mintos-glass-dark.svg",
    "mintos-glass-dark-calm.svg",
    "mintos-glass-dark-mesh.svg",
    "mintos-glass-dark-glass.svg",
}

# Số đo đã chạy thật bằng tools/lint/wallpapers.py -v. Nếu token màu đổi thì những
# con số này đổi theo và test đỏ — đó là chủ đích: buộc phải xét lại ràng buộc
# tương phản thay vì để nó âm thầm trôi.
MEASURED_LABEL = {
    "mintos-glass-dark-calm.svg":  16.01,
    "mintos-glass-dark-mesh.svg":  14.46,
    "mintos-glass-dark-glass.svg": 14.39,
    "mintos-glass-dark.svg":       12.67,
}
MEASURED_SELECTED_ADOPTED = {   # #0b0c0e trên chip accent — bản vá T09 đã áp dụng
    "mintos-glass-dark-calm.svg":  7.43,
    "mintos-glass-dark-glass.svg": 7.60,
    "mintos-glass-dark-mesh.svg":  7.66,
    "mintos-glass-dark.svg":       7.83,
}
MEASURED_SELECTED_BROKEN = {    # #f5f5f5 — giá trị token GỐC, T09 chứng minh FAIL
    "mintos-glass-dark-calm.svg":  2.42,
    "mintos-glass-dark-glass.svg": 2.36,
    "mintos-glass-dark-mesh.svg":  2.34,
    "mintos-glass-dark.svg":       2.29,
}


def svgs():
    return sorted(WP.glob("*.svg"))


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestLintIsCleanOnTheRealWallpapers(unittest.TestCase):
    def test_no_fail_and_no_warn(self):
        bad = [(s, c, m) for s, c, m in wl.findings(verbose=True) if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"lint chưa sạch trên wallpaper thật: {bad[:3]}")


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestInventoryAndStructure(unittest.TestCase):
    def test_four_dark_variants_exist(self):
        self.assertEqual({p.name for p in svgs()}, EXPECTED,
                         "bộ wallpaper đã đổi — cập nhật MANIFEST.md, icon-spec.md "
                         "và các bảng số đo trong test này cùng lúc")

    def test_no_light_variant_while_d2_is_dark_first(self):
        """D-2 = dark_first: token Light có định nghĩa nhưng emit:false. Ship nền
        Light trước khi D-2 mở khoá là ship thứ hệ token chưa bật."""
        self.assertEqual([p.name for p in svgs() if "light" in p.stem], [])

    def test_all_parse_and_have_correct_geometry(self):
        for p in svgs():
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            with self.subTest(wp=p.name):
                self.assertEqual(root.tag, f"{{{SVG_NS}}}svg")
                self.assertEqual(root.get("viewBox"), f"0 0 {W} {H}")
                self.assertEqual(root.get("width"), str(W))
                self.assertEqual(root.get("height"), str(H))

    def test_slice_not_meet_because_a_wallpaper_must_cover(self):
        """`slice` để PHỦ KÍN ở mọi tỉ lệ màn hình. Icon thì ngược lại: phải dùng
        meet/không cắt. Đây là chỗ wallpaper và icon cố ý khác quy ước."""
        for p in svgs():
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            with self.subTest(wp=p.name):
                self.assertEqual(root.get("preserveAspectRatio"), "xMidYMid slice")

    def test_naming_convention(self):
        for p in svgs():
            with self.subTest(wp=p.name):
                self.assertRegex(p.stem, r"^mintos-glass-dark[a-z0-9-]*$")

    def test_no_raster_or_stray_files(self):
        allowed = {".svg", ".md", ".sh", ".xml"}
        stray = [p.name for p in WP.iterdir() if p.is_file() and p.suffix.lower() not in allowed]
        self.assertEqual(stray, [],
                         "nếu cần raster thì phải có pipeline render VÀ khai báo độ "
                         "phân giải thật đã sinh ra — không khai khống")


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestNoExternalOrUnshippedEffects(unittest.TestCase):
    def test_no_network_references(self):
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            urls = set(re.findall(r"https?://[^\s\"')]+", txt))
            with self.subTest(wp=p.name):
                self.assertEqual(urls, {SVG_NS},
                                 "wallpaper phải nằm trong repo, không URL ngoài")

    def test_no_image_or_script_or_use_tags(self):
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            for tag in ("<script", "<image", "<foreignObject", "<iframe", "<use",
                        "<filter", "<mask", "<clipPath", "<pattern"):
                with self.subTest(wp=p.name, tag=tag):
                    self.assertNotIn(tag, txt)

    def test_no_blur_claimed_or_used(self):
        """Yêu cầu của dự án: không tuyên bố blur khi chỉ dùng độ trong suốt hoặc
        gradient. Wallpaper là chỗ dễ vi phạm nhất vì chữ "glass" gợi đúng hiệu ứng
        đó. T04 đã xác minh -blur của St tốn cogl_framebuffer_read_pixels() mỗi lần
        paint nên dự án KHÔNG ship thứ phụ thuộc blur."""
        for p in svgs():
            body = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8"), flags=re.S)
            for needle in ("feGaussianBlur", "feDropShadow", "blur"):
                with self.subTest(wp=p.name, needle=needle):
                    self.assertNotIn(needle, body.lower())

    def test_no_rgba_function(self):
        for p in svgs():
            with self.subTest(wp=p.name):
                self.assertNotRegex(p.read_text(encoding="utf-8"), r"\brgba?\s*\(")

    def test_every_colour_and_alpha_traces_to_a_token(self):
        colors, alphas = wl.token_hex_values(), wl.token_alpha_values()
        self.assertGreater(len(colors), 20)
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            for m in wl.HEX_RE.finditer(txt):
                h = m.group(0).lower()
                if len(h) == 4:
                    h = "#" + "".join(c * 2 for c in h[1:])
                with self.subTest(wp=p.name, colour=m.group(0)):
                    self.assertIn(h, colors, "wallpaper không được tạo bảng màu thứ hai")
            for m in re.finditer(r'\b(stop-opacity|fill-opacity)\s*=\s*"([^"]+)"', txt):
                with self.subTest(wp=p.name, opacity=m.group(2)):
                    self.assertIn(m.group(2), alphas)


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestDesktopLabelContrast(unittest.TestCase):
    """Bài quan trọng nhất. Đo trên wallpaper THẬT, đóng vòng lặp mở từ T09."""

    def test_label_colour_is_locked_by_nemo(self):
        """Tiền đề của cả lớp này: màu nhãn desktop KHÔNG sửa được từ theme.

        Nếu một ngày token này đổi khác giá trị Nemo dùng thì toàn bộ lập luận
        "wallpaper là đòn bẩy duy nhất" phải được xét lại.
        """
        v = wl.gtk_token("mg-nemo-desktop-label-text")
        self.assertIsNotNone(v, "không đọc được $mg-nemo-desktop-label-text")
        self.assertEqual(v.strip().lower(), "#eeeeee",
                         "token nhãn desktop đã đổi — kiểm tra lại nó có còn bằng giá "
                         "trị Nemo đang dùng không, vì Nemo khoá màu này ở priority 600")

    def test_label_meets_4_5_on_every_wallpaper(self):
        """Ngưỡng 4.5:1 vì đây là CHỮ (WCAG 1.4.3), không phải đối tượng đồ hoạ 3:1.

        T16 trong plan chỉ đòi >=3:1; ta đặt cao hơn vì vế kia của phương trình
        (màu chữ) bị Nemo khoá nên không còn cách nào khác để cải thiện tỉ lệ.
        """
        label = wl.gtk_token("mg-nemo-desktop-label-text").strip().lower()
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            r = wl.contrast(label, bright)
            with self.subTest(wp=p.name, brightest=bright):
                self.assertGreaterEqual(r, 4.5,
                                        f"nhãn desktop {label} trên vùng sáng nhất "
                                        f"{bright} chỉ đạt {r:.2f}:1")

    def test_measured_values_match_the_published_numbers(self):
        """Khoá các con số đã công bố trong MANIFEST.md mục 3.2.

        Không đọc số từ MANIFEST — đo lại từ tệp SVG rồi so. Nếu ai sửa wallpaper
        mà quên sửa tài liệu thì test đỏ.
        """
        label = wl.gtk_token("mg-nemo-desktop-label-text").strip().lower()
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            with self.subTest(wp=p.name):
                self.assertAlmostEqual(wl.contrast(label, bright),
                                       MEASURED_LABEL[p.name], delta=0.01,
                                       msg="số đo đã trôi khỏi MANIFEST.md mục 3.2")

    def test_every_wallpaper_clears_aaa_too(self):
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            r = wl.contrast("#eeeeee", bright)
            with self.subTest(wp=p.name):
                self.assertGreaterEqual(r, 7.0,
                                        f"{p.name} chỉ đạt {r:.2f}:1 — dưới AAA 7:1")

    def test_adopted_selected_label_passes_on_real_wallpapers(self):
        """Xác nhận độc lập bản vá của T09: #0b0c0e trên chip accent."""
        sel = wl.gtk_token("mg-nemo-desktop-label-selected-background")
        m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", sel.strip())
        self.assertIsNotNone(m, f"không parse được {sel!r}")
        rgb = "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4))
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            chip = wl.composite(rgb, a, bright)
            with self.subTest(wp=p.name, chip=chip):
                self.assertGreaterEqual(wl.contrast("#0b0c0e", chip), 4.5)

    def test_original_token_value_still_fails_on_real_wallpapers(self):
        """T09 kết luận `$mg-nemo-desktop-label-selected-text: #f5f5f5` FAIL, dựa
        trên ba mức chói MÔ HÌNH. Bài này đo lại trên wallpaper THẬT.

        Nếu một ngày nó PASS thì nghĩa là wallpaper đã tối đi nhiều tới mức không
        còn cần bản vá của T09 nữa — khi đó phải xét lại cả hai kết luận, không
        được âm thầm bỏ qua. Đó là lý do bài này tồn tại.
        """
        sel = wl.gtk_token("mg-nemo-desktop-label-selected-background")
        m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", sel.strip())
        rgb = "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4))
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            chip = wl.composite(rgb, a, bright)
            r = wl.contrast("#f5f5f5", chip)
            with self.subTest(wp=p.name, chip=chip):
                self.assertLess(r, 4.5,
                                f"token #f5f5f5 giờ ĐẠT {r:.2f}:1 trên {p.name} — kết "
                                "luận của T09 cần xét lại, đừng im lặng bỏ qua")
                self.assertAlmostEqual(r, MEASURED_SELECTED_BROKEN[p.name], delta=0.01)

    def test_adopted_beats_broken_on_every_wallpaper(self):
        sel = wl.gtk_token("mg-nemo-desktop-label-selected-background")
        m = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)", sel.strip())
        rgb = "#%02x%02x%02x" % tuple(int(m.group(i)) for i in (1, 2, 3))
        a = float(m.group(4))
        for p in svgs():
            bright, _ = wl.brightest_composite(p)
            chip = wl.composite(rgb, a, bright)
            with self.subTest(wp=p.name):
                self.assertGreater(wl.contrast("#0b0c0e", chip), wl.contrast("#f5f5f5", chip))


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestLuminanceModelIsConservative(unittest.TestCase):
    """MANIFEST mục 3.4 nói mô hình "vùng sáng nhất" là xấp xỉ theo hướng AN TOÀN.
    Bài này khoá những tính chất làm nên sự an toàn đó."""

    def test_composite_matches_known_values(self):
        # rgba(255,255,255,0.12) trên #17181c -> #333437 (đã tính ở T05)
        self.assertEqual(wl.composite("#ffffff", 0.12, "#17181c"), "#333437")
        # rgba(61,220,151,0.16) trên #17181c -> #1d3730
        self.assertEqual(wl.composite("#3ddc97", 0.16, "#17181c"), "#1d3730")

    def test_composite_endpoints(self):
        self.assertEqual(wl.composite("#ff0000", 1.0, "#00ff00"), "#ff0000")
        self.assertEqual(wl.composite("#ff0000", 0.0, "#00ff00"), "#00ff00")

    def test_contrast_is_symmetric_and_matches_wcag_reference(self):
        self.assertAlmostEqual(wl.contrast("#000000", "#ffffff"), 21.0, delta=0.01)
        self.assertAlmostEqual(wl.contrast("#ffffff", "#000000"), 21.0, delta=0.01)
        self.assertAlmostEqual(wl.contrast("#777777", "#777777"), 1.0, delta=0.01)

    def test_luminance_ordering_matches_intuition(self):
        self.assertLess(wl.luminance("#0b0c0e"), wl.luminance("#17181c"))
        self.assertLess(wl.luminance("#17181c"), wl.luminance("#7c8087"))
        self.assertLess(wl.luminance("#7c8087"), wl.luminance("#ffffff"))

    def test_brightest_composite_is_never_darker_than_the_base(self):
        for p in svgs():
            ls, darkest = wl.layers(p)
            bright, _ = wl.brightest_composite(p)
            with self.subTest(wp=p.name):
                self.assertGreaterEqual(wl.luminance(bright), wl.luminance(darkest))
                self.assertTrue(ls, f"{p.name} không trích được lớp màu nào")

    def test_every_layer_is_actually_found(self):
        """Nếu layers() bỏ sót một lớp SÁNG thì kết quả sẽ lạc quan hơn thực tế và
        toàn bộ kết luận tương phản trở nên vô nghĩa. Đếm ngược từ tệp."""
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            n_stops = len(re.findall(r"<stop\b", txt))
            n_fills = len(re.findall(r'<(?:rect|path)\b[^>]*\bfill="#', txt))
            ls, _ = wl.layers(p)
            with self.subTest(wp=p.name):
                self.assertEqual(len(ls), n_stops + n_fills,
                                 f"trích được {len(ls)} lớp nhưng tệp có {n_stops} stop "
                                 f"+ {n_fills} fill màu — layers() đang bỏ sót, và bỏ "
                                 "sót lớp sáng thì kết luận tương phản là giả")


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestAccentPlacement(unittest.TestCase):
    """Yêu cầu 3.3 của T16: điểm nhấn nằm lệch khỏi khu vực icon desktop."""

    def test_no_glow_centre_inside_the_icon_zone(self):
        safe_x, safe_y = W * 0.55, H * 0.55
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            for m in re.finditer(r'<radialGradient\b[^>]*\bcx="([\d.]+)"[^>]*\bcy="([\d.]+)"', txt):
                cx, cy = float(m.group(1)), float(m.group(2))
                with self.subTest(wp=p.name, cx=cx, cy=cy):
                    self.assertFalse(cx < safe_x and cy < safe_y,
                                     f"vầng sáng tâm ({cx},{cy}) nằm trong vùng icon "
                                     f"desktop (x<{safe_x:.0f}, y<{safe_y:.0f})")

    def test_centre_of_screen_has_no_hard_detail(self):
        """Vùng giữa màn hình không được có chi tiết gắt. Kiểm gần đúng: không có
        <path> nào có toạ độ nằm sát tâm với nét cứng — ở đây chỉ có rect phủ nền
        và path dải chéo rất mờ."""
        cx, cy = W / 2, H / 2
        for p in svgs():
            txt = p.read_text(encoding="utf-8")
            for m in re.finditer(r'<path\b[^>]*\sd="([^"]+)"', txt):
                nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", m.group(1))]
                pts = list(zip(nums[0::2], nums[1::2]))
                near = [(x, y) for x, y in pts if abs(x - cx) < 120 and abs(y - cy) < 120]
                with self.subTest(wp=p.name, path=m.group(1)[:40]):
                    self.assertEqual(near, [],
                                     f"có đỉnh path nằm sát tâm màn hình: {near[:3]}")


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestManifest(unittest.TestCase):
    def setUp(self):
        self.path = WP / "MANIFEST.md"
        self.assertTrue(self.path.exists())
        self.txt = self.path.read_text(encoding="utf-8")

    def test_two_way_consistency(self):
        listed = set(re.findall(r"(mintos-glass-dark[a-z0-9-]*\.svg)", self.txt))
        actual = {p.name for p in svgs()}
        self.assertEqual(actual - listed, set(), "wallpaper chưa được ghi trong MANIFEST")
        self.assertEqual(listed - actual, set(), "MANIFEST nhắc tới tệp không tồn tại")

    def test_required_topics(self):
        for key in ("giấy phép", "Light Glass", "tự vẽ", "desktop"):
            with self.subTest(topic=key):
                self.assertIn(key.lower(), self.txt.lower())

    def test_published_numbers_are_in_the_manifest(self):
        for v in list(MEASURED_LABEL.values()) + list(MEASURED_SELECTED_ADOPTED.values()):
            with self.subTest(value=v):
                self.assertIn(f"{v:.2f}", self.txt,
                              f"số đo {v:.2f}:1 không có trong MANIFEST — tài liệu và "
                              "tài nguyên đang lệch nhau")

    def test_locked_label_premise_is_documented(self):
        """Lập luận "wallpaper là đòn bẩy duy nhất" phải được ghi kèm bằng chứng."""
        for needle in ("600", "200", "important", "khoá"):
            with self.subTest(topic=needle):
                self.assertIn(needle, self.txt)

    def test_verified_vs_unverified_are_separated(self):
        """Không tuyên bố desktop render được SVG khi mới chỉ đọc mã đường thumbnail."""
        self.assertIn("ĐÃ xác minh", self.txt)
        self.assertIn("chưa", self.txt.lower())
        self.assertIn("cs_backgrounds.py", self.txt)
        self.assertIn("613", self.txt)

    def test_approximation_limit_is_stated(self):
        self.assertIn("xấp xỉ", self.txt)
        self.assertIn("pixel", self.txt)


@unittest.skipIf(wl is None, f"không import được tools/lint/wallpapers.py: {IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test trên bản sao tạm. Không ghi gì vào repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-wallpaper-mutant-"))
        # Tên thư mục tạm phải là `wallpapers` để MANIFEST/relative-path không lệch.
        self.wp = self.tmp / "wallpapers"
        shutil.copytree(WP, self.wp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, findings, severity="FAIL"):
        return {cid for sev, cid, _ in findings if sev == severity}

    def _run(self):
        return wl.findings(wp_dir=self.wp)

    def test_baseline_is_clean(self):
        bad = [(s, c, m) for s, c, m in self._run() if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"bản sao của wallpaper thật mà đã báo lỗi: {bad[:3]}")

    def _break(self, name, transform):
        p = self.wp / name
        old = p.read_text(encoding="utf-8")
        new = transform(old)
        self.assertNotEqual(old, new, f"đột biến không đổi gì {name} — bài test vô nghĩa")
        p.write_text(new, encoding="utf-8")
        return self._ids(self._run())

    def test_detects_off_token_colour(self):
        ids = self._break("mintos-glass-dark.svg", lambda s: s.replace("#121316", "#ff00aa"))
        self.assertIn("colors-are-token-values", ids)

    def test_detects_off_token_opacity(self):
        ids = self._break("mintos-glass-dark.svg",
                          lambda s: s.replace('stop-opacity="0.16"', 'stop-opacity="0.61"'))
        self.assertIn("colors-are-token-values", ids)

    def test_detects_wrong_viewbox(self):
        ids = self._break("mintos-glass-dark.svg",
                          lambda s: s.replace(f'viewBox="0 0 {W} {H}"', 'viewBox="0 0 800 600"'))
        self.assertIn("svg-geometry", ids)

    def test_detects_meet_instead_of_slice(self):
        """`meet` sẽ để lại dải đen trên màn không 16:9 — đúng thứ `slice` ngăn."""
        ids = self._break("mintos-glass-dark-calm.svg",
                          lambda s: s.replace('preserveAspectRatio="xMidYMid slice"',
                                              'preserveAspectRatio="xMidYMid meet"'))
        self.assertIn("svg-geometry", ids)

    def test_detects_blur_claim(self):
        ids = self._break("mintos-glass-dark-glass.svg",
                          lambda s: s.replace("</svg>",
                                              '  <filter id="f"><feGaussianBlur stdDeviation="20"/></filter>\n</svg>'))
        self.assertTrue({"no-blur-claim", "no-external-refs"} & ids,
                        f"thêm filter blur mà lint không bắt: {ids}")

    def test_detects_external_reference(self):
        ids = self._break("mintos-glass-dark.svg",
                          lambda s: s.replace("</svg>",
                                              '  <image href="https://example.com/bg.png"/>\n</svg>'))
        self.assertIn("no-external-refs", ids)

    def test_detects_rgba_usage(self):
        ids = self._break("mintos-glass-dark-mesh.svg",
                          lambda s: s.replace('stop-color="#1f8f5f"',
                                              'stop-color="rgba(31,143,95,1)"'))
        self.assertIn("no-rgba-in-svg", ids)

    def test_detects_malformed_xml(self):
        ids = self._break("mintos-glass-dark-calm.svg", lambda s: s.replace("</svg>", ""))
        self.assertIn("svg-wellformed", ids)

    def test_detects_bad_filename(self):
        (self.wp / "mintos-glass-dark-calm.svg").rename(self.wp / "MintOS_Dark.svg")
        ids = self._ids(self._run())
        self.assertTrue({"naming", "manifest"} & ids, f"đổi tên sai mà lint không bắt: {ids}")

    def test_detects_a_wallpaper_too_bright_for_the_desktop_label(self):
        """Bài quan trọng nhất của lớp này: lint phải THẬT SỰ đỏ khi nền quá sáng.

        Thay dải nền tối bằng nền sáng nhất có trong token ($mg-color-gray-0). Khi
        đó nhãn desktop #eeeeee sẽ tụt xuống dưới 4.5:1 và bài
        desktop-label-contrast phải FAIL. Nếu nó im lặng thì toàn bộ ràng buộc ở
        MANIFEST mục 3 chỉ là lời nói.
        """
        ids = self._break("mintos-glass-dark-calm.svg",
                          lambda s: s.replace('stop-color="#0b0c0e"', 'stop-color="#ffffff"')
                                        .replace('stop-color="#121316"', 'stop-color="#ffffff"'))
        self.assertIn("desktop-label-contrast", ids)

    def test_detects_accent_moved_into_the_icon_zone(self):
        """Hồi quy cho WARN thật đã gặp: vầng mesh đặt ở (260,200)."""
        res = None
        p = self.wp / "mintos-glass-dark-mesh.svg"
        p.write_text(p.read_text(encoding="utf-8").replace('cx="400" cy="700"',
                                                           'cx="260" cy="200"'),
                     encoding="utf-8")
        res = self._run()
        self.assertIn("accent-placement", {c for s, c, _ in res if s == "WARN"},
                      f"dời vầng sáng vào vùng icon mà không có WARN: {res}")

    def test_detects_missing_manifest_entry(self):
        man = self.wp / "MANIFEST.md"
        man.write_text(man.read_text(encoding="utf-8")
                       .replace("mintos-glass-dark-mesh.svg", "mintos-glass-dark-OLD.svg"),
                       encoding="utf-8")
        self.assertIn("manifest", self._ids(self._run()))

    def test_detects_missing_wallpaper(self):
        (self.wp / "mintos-glass-dark-glass.svg").unlink()
        self.assertIn("manifest", self._ids(self._run()))

    def test_detects_empty_directory(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertIn("wallpaper-dir", self._ids(wl.findings(wp_dir=empty)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
