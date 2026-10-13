#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/nemo_selectors.py` và `_apps-nemo.scss` (Task T09).

Chạy bằng stdlib unittest, không cần pytest:
    python3 -m unittest discover -s tests -t .
    python3 -m unittest tests.lint.test_nemo_selectors -v

Cần libsass (`pip install libsass`) hoặc dart-sass. Nếu không có, các bài cần
biên dịch sẽ SKIP chứ không PASS giả — bài học từ T04.

--------------------------------------------------------------------------
VÌ SAO CÓ CÁC BÀI "MUTATION"
--------------------------------------------------------------------------
Một lint chỉ có giá trị khi nó THẬT SỰ fail lúc code sai. Ở T04, hai bài kiểm
tra của `st_properties.py` đã pass rỗng nhiều vòng vì bug offset index
(`code.splitlines()[i-1][m.end():]` thay vì `line[m.end():]`) và vì guard
`\\(\\s*\\$` sai khi regex đã ăn mất dấu `(`. Cả hai chỉ lộ ra khi chạy lint trên
code thật. Vì vậy file này có hẳn một lớp `TestLintActuallyFails`: sửa SCSS thành
bản SAI trong thư mục tạm, rồi khẳng định lint FAIL. Nếu lint bị hỏng về sau,
lớp này đỏ trước.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "lint"))

try:
    import nemo_selectors as ns
except Exception as exc:  # pragma: no cover
    ns = None
    NS_IMPORT_ERROR = exc
else:
    NS_IMPORT_ERROR = None


def _have_compiler() -> bool:
    if ns is None:
        return False
    return ns.find_compiler() is not None


NEED_COMPILER = unittest.skipUnless(_have_compiler(),
                                    "cần libsass (pip install libsass) hoặc dart-sass")


@unittest.skipIf(ns is None, f"không import được nemo_selectors: {NS_IMPORT_ERROR}")
class TestFixtureIntegrity(unittest.TestCase):
    """Bài học T04: fixture selector từng bị hỏng theo HAI cách rất khó thấy.

    (1) Marker comment là `#` trong khi selector CSS dùng `#` cho widget name
        (`#nemo-tab-close-button`). `line.split("#", 1)` đã cắt cụt 25 selector ID
        và làm coverage báo sai CẢ HAI chiều: 425 "thiếu" giả + 487 "mới" giả
        trong khi số thật là 0 và 127.
    (2) Fixture được dựng bằng regex ad-hoc `^([^@\\s/][^{}]*)\\{` với `re.M`.
        `[^{}]` KHÔNG loại trừ newline nên nó nuốt luôn `}` của rule trước, tạo
        ra 439 mục dạng `'} #Tooltip'`.
    Cả hai được khoá ở đây.
    """

    def setUp(self):
        self.path = ns.FIXTURE
        self.assertTrue_path = self.path.exists()

    def test_fixture_exists(self):
        self.assertTrue(self.path.exists(), f"thiếu fixture: {self.path}")

    ID_SELECTOR_RE = re.compile(r"^#[A-Za-z][\w-]*(?::[\w()\-]+)?$")

    def test_hash_lines_are_selectors_not_comments(self):
        """Mọi dòng bắt đầu `#` phải là selector ID hợp lệ, KHÔNG phải comment.

        Đây là bản chất của lỗi từng làm hỏng fixture Cinnamon: marker comment là
        `#` trong khi dữ liệu chứa selector ID, nên `line.split("#", 1)` cắt cụt
        25 selector và coverage báo sai cả hai chiều (425 "thiếu" giả + 487 "mới"
        giả). Test cũ của chính bài này lại đánh đồng "dòng bắt đầu bằng #" với
        "dòng comment" và fail giả — vì `#nemo-tab-close-button` LÀ một selector.
        Nên kiểm tra đúng điều cần kiểm tra: dòng `#` phải parse ra selector ID.
        """
        raw = self.path.read_text().splitlines()
        items = set(ns.load_fixture(self.path))
        for ln in raw:
            stripped = ln.strip()
            if not stripped.startswith("#"):
                continue
            self.assertRegex(stripped, self.ID_SELECTOR_RE,
                             f"dòng bắt đầu `#` không phải selector ID hợp lệ — "
                             f"có thể là comment dùng nhầm marker: {stripped!r}")
            self.assertIn(stripped, items,
                          f"selector ID `{stripped}` bị load_fixture bỏ rơi — marker "
                          f"comment đang ăn mất nó")
        # assertNotRegex(text, regex, msg) KHÔNG nhận cờ -> nhúng `(?m)` vào pattern.
        self.assertNotRegex(self.path.read_text(), r"(?m)^#\s",
                            "fixture có dòng dạng `# chữ...` — marker comment phải "
                            "là `//`, không phải `#`")

    def test_no_polluted_entries(self):
        """Không mục nào chứa ký tự chứng tỏ regex đã nuốt ranh giới rule."""
        for s in ns.load_fixture(self.path):
            self.assertNotRegex(s, r"[{};/]", f"mục fixture bị ô nhiễm: {s!r}")
            self.assertFalse(s.startswith((" ", "\t")), f"mục fixture có whitespace đầu: {s!r}")
            self.assertNotIn("/*", s, f"mục fixture còn comment C: {s!r}")

    def test_contains_id_selectors(self):
        """Chốt hồi quy cho lỗi marker `#`: fixture PHẢI đọc được selector ID."""
        items = ns.load_fixture(self.path)
        ids = [s for s in items if s.startswith("#")]
        self.assertIn("#nemo-tab-close-button", ids,
                      "không đọc được selector ID `#nemo-tab-close-button` — gần "
                      "chắc chắn marker comment đang là `#` và đã ăn mất nó.")

    def test_bare_element_selector_present(self):
        """`nemo-desktop-icon-view` là CSS NODE NAME, selector là tên TRẦN.

        ĐÍNH CHÍNH E30: plan ghi nó là "style class". Đã xác minh
        src/nemo-desktop-icon-grid-view.c:379 dùng
        `gtk_widget_class_set_css_name(wclass, "nemo-desktop-icon-view")` — tức là
        node name, không phải class. Nếu fixture viết `.nemo-desktop-icon-view`
        thì sẽ không bao giờ khớp output.
        """
        items = ns.load_fixture(self.path)
        self.assertIn("nemo-desktop-icon-view", items)
        self.assertNotIn(".nemo-desktop-icon-view", items,
                         "E30 gọi đây là style class nhưng nó là CSS node name "
                         "(gtk_widget_class_set_css_name, "
                         "src/nemo-desktop-icon-grid-view.c:379). Selector không "
                         "được có dấu chấm.")

    def test_locked_selectors_are_documented_in_fixture(self):
        """Mọi selector bị Nemo khoá ở priority 600 phải được fixture nói rõ."""
        txt = self.path.read_text()
        for s in sorted(ns.LOCKED_BY_NEMO):
            self.assertIn(s, txt,
                          f"`{s}` bị Nemo khoá ở PRIORITY_APPLICATION(600) nhưng "
                          "fixture không ghi — người đọc SCSS sẽ tưởng theme kiểm "
                          "soát được nó.")


@NEED_COMPILER
@unittest.skipIf(ns is None, f"không import được nemo_selectors: {NS_IMPORT_ERROR}")
class TestNemoStylesheet(unittest.TestCase):
    """Kiểm tra `_apps-nemo.scss` trên CSS ĐÃ BIÊN DỊCH THẬT, không đọc source."""

    @classmethod
    def setUpClass(cls):
        cls.sass = ns.SCSS
        if not cls.sass.exists():
            raise unittest.SkipTest(f"chưa có {cls.sass}")
        cls.css, cls.compiler = ns.compile_scss(cls.sass)
        if cls.css is None:
            raise unittest.SkipTest("không compile được")
        cls.selectors = ns.output_selectors(cls.css)
        cls.props = {}
        for sel, decls in ns.parse_rules(cls.css):
            for p, v in decls:
                cls.props.setdefault(p.lower(), []).append(sel)

    def test_compiles_with_libsass_or_dart_sass(self):
        self.assertGreater(len(self.css), 1000)
        self.assertIn("sass", self.compiler.lower())

    def test_full_coverage_of_fixture(self):
        """Done criterion #1 của T09: phủ MỌI selector trong fixture."""
        want = ns.load_fixture(ns.FIXTURE)
        self.assertTrue(want, "fixture rỗng")
        missing = [s for s in want if s not in self.selectors]
        self.assertEqual(missing, [], f"thiếu {len(missing)} selector bắt buộc")

    def test_output_has_no_accidental_extras(self):
        """Số liệu neo: để phát hiện thay đổi ngoài ý muốn ở lần chạy sau."""
        want = set(ns.load_fixture(ns.FIXTURE))
        extra = sorted(self.selectors - want)
        # 29 selector ngoài fixture là hợp lệ (trạng thái :hover/:selected/:rtl,
        # nút trong floating-bar/path-bar, row sidebar, ...). Con số này được neo
        # để nếu ai thêm selector mới thì phải CỐ Ý cập nhật bài kiểm tra.
        self.assertGreaterEqual(len(extra), 20,
                                f"chỉ có {len(extra)} selector ngoài fixture — có "
                                "phải SCSS đã bị rút gọn mất không?")

    def test_all_six_disk_full_properties_present(self):
        """Done criterion #1: đủ cả 6 -NemoPlacesTreeView-disk-full-*.

        Đây là chỗ DUY NHẤT theme điều khiển được chỉ báo dung lượng ổ đĩa, vì
        Nemo để chúng ở PRIORITY_FALLBACK(0) (src/nemo-application.c:317) nên
        theme(200) thắng. Tên property đã đối chiếu với
        gtk_widget_class_install_style_property tại
        libnemo-private/nemo-places-tree-view.c:43,50,57,64,71,78.
        """
        for p in ns.DISK_FULL_PROPS:
            self.assertIn(p.lower(), self.props,
                          f"thiếu `{p}` trong CSS đã compile")
            self.assertIn(".places-treeview", self.props[p.lower()],
                          f"`{p}` phải nằm trên `.places-treeview`")

    def test_does_not_override_prelight_icon_label(self):
        """Done criterion #2 của T09 — ràng buộc CỨNG.

        `-NemoIconContainer-activate-prelight-icon-label` là style property boolean
        đăng ký tại libnemo-private/nemo-icon-container.c:4861-4866
        (`g_param_spec_boolean("activate_prelight_icon_label", ..., G_PARAM_READABLE)`).
        Nó điều khiển HÀNH VI (nhãn icon có sáng lên khi rê chuột không), không
        phải màu sắc. Ghi đè nó là đổi chức năng gốc của Nemo.
        """
        self.assertNotIn(ns.FORBIDDEN_PROP.lower(), self.props,
                         "CẤM ghi đè -NemoIconContainer-activate-prelight-icon-label")
        self.assertNotIn(ns.FORBIDDEN_PROP.lower(), self.css.lower())

    def test_no_important_anywhere(self):
        """GTK 3.24 KHÔNG hỗ trợ `!important`.

        Đã kiểm chứng: GNOME/gtk ref 3.24.42 — chuỗi "important" xuất hiện 0 lần
        trong gtk/gtkcssparser.c (1067 dòng), 0 lần trong gtk/gtkcssprovider.c
        (2405 dòng), 0 lần trong gtk/gtkstylecascade.c (426 dòng). Parser là nơi
        duy nhất có thể nhận diện cú pháp `!`, nên nếu parser không đọc thì không
        tầng nào phía sau dùng được. Và gtk_style_cascade_iter_next()
        (gtkstylecascade.c:42-71) duyệt provider theo priority GIẢM DẦN.
        => `!important` vừa vô nghĩa vừa tạo ảo tưởng rằng nó thắng được
           nemo-style-application.css ở PRIORITY_APPLICATION(600).
        """
        self.assertNotRegex(self.css, r"!\s*important")
        self.assertNotRegex(ns.SCSS.read_text(), r"^\s*[^/\s].*!\s*important", re.M)

    def test_no_broken_generator_tokens(self):
        """Không dùng token mà tools/tokens/generate.py đang sinh sai.

        generate.py:215 `UNITLESS_KEYS = {"blur"}` nên font-weight ra
        `400px/500px/700px` — không hợp lệ cho GTK3 (cần Pango weight thuần số).
        NS_UNIT không có nhánh "font" nên `font.size-*-pt` ra `9px/12px`.
        `blur.*` ra `2px/4px/6px` (phải unitless).
        `40-motion.json` KHÔNG BAO GIỜ được emit vì generate.py:605-616 chỉ
        flatten primitives/component/semantic nên không có `$mg-duration-*`.
        Tất cả đã báo Agent Design Systems; dùng hằng tạm thời có ghi chú thay vì
        tham chiếu token hỏng.
        """
        src = self.sass.read_text()
        for i, line in enumerate(src.splitlines(), 1):
            code = line.split("//", 1)[0]
            m = ns.BROKEN_TOKEN_RE.search(code)
            self.assertIsNone(m, f"{self.sass.name}:{i} dùng token hỏng `{m.group(0) if m else ''}`")

    def test_no_hardcoded_colors(self):
        src = self.sass.read_text()
        bad = []
        for i, line in enumerate(src.splitlines(), 1):
            code = line.split("//", 1)[0]
            if not code.strip() or code.lstrip().startswith(("@", "$", "//")):
                continue
            m = ns.HARDCODED_RE.search(code)
            if m and not (m.group(0).startswith(("rgba(", "hsla(", "alpha("))
                        and re.match(r"\s*\$", code[m.end():])):
                bad.append(f"{i}: {code.strip()[:70]}")
        self.assertEqual(bad, [], "màu hard-code, phải qua token:\n" + "\n".join(bad))

    def test_no_gtk3_invalid_properties(self):
        """`-gtk-icon-size` KHÔNG tồn tại trong GTK 3.24.

        GTK3 chỉ có -gtk-icon-source/-gtk-icon-palette/-gtk-icon-shadow/
        -gtk-icon-effect/-gtk-icon-transform/-gtk-icon-style. Cỡ icon là property
        `icon-size` của widget image, đặt trong code chứ không qua theme.
        Đây là lỗi đã từng viết thật trong bản nháp đầu của file này.
        """
        for sel, decls in ns.parse_rules(self.css):
            for p, _ in decls:
                for badprop in ns.GTK3_INVALID_PROPS:
                    self.assertFalse(p.lower().startswith(badprop),
                                     f"`{p}` trong `{sel}` không tồn tại trong GTK 3.24")

    def test_no_bare_generic_gtk_class(self):
        """Không phát ra class GTK chung ở dạng TRẦN.

        Theme GTK3 compile thành MỘT gtk.css dùng cho MỌI app. Viết `.sidebar {}`
        trần trong partial của Nemo là áp đặt quy tắc của Nemo lên mọi app GTK3
        khác — đúng cái "stylesheet riêng cạnh tranh" mà yêu cầu phối hợp Agent 3
        cấm, và Agent 3 yêu cầu "dùng selector hẹp hơn khi có thể".
        `.sidebar`, `.view`, `.linked`, `.raised`, `.error`, `.primary-toolbar`
        thuộc sở hữu của T06.
        """
        for sel in sorted(self.selectors):
            first = sel.split()[0]
            for cls in ns.GENERIC_GTK_CLASSES:
                self.assertFalse(
                    first == cls or first.startswith(cls + ":") or first.startswith(cls + "."),
                    f"`{sel}` phát ra class GTK chung `{cls}` ở dạng trần — phải "
                    f"scope lại, ví dụ `.nemo-window {sel}`")

    def test_sidebar_rows_really_have_nemo_ancestor(self):
        """Khẳng định dương tính cho quy tắc scope ở bài trên."""
        self.assertIn(".nemo-window .sidebar", self.selectors)
        self.assertIn(".nemo-window .nemo-places-sidebar", self.selectors)
        self.assertNotIn(".sidebar", self.selectors)

    def test_inactive_pane_and_entry_and_floating_bar_all_styled(self):
        """Ba selector này KHÔNG được ai style hộ — ta phải tự viết.

        src/nemo-application.c:297 chỉ nạp nemo-style-fallback-mandatory.css khi
        `!is_known_supported_theme(theme_name)`. Mà :245
        `supported_theme_hints[] = {"mint","arc","numix","matcha"}`, :259 casefold
        tên theme, :267 khớp bằng `g_strstr_len` (SO KHỚP CHUỖI CON).
        "MintOS-Glass" -> "mintos-glass" -> CHỨA "mint" -> TRUE -> Nemo KHÔNG nạp
        fallback-mandatory. Nên `.nemo-inactive-pane`, `.nemo-window-pane
        widget.entry`, `.floating-bar` sẽ rơi về GTK mặc định (nền sáng) nếu ta
        bỏ sót — vỡ giao diện tối ngay giữa cửa sổ.
        """
        for s in (".nemo-inactive-pane",
                  ".nemo-window .nemo-inactive-pane .view:not(:selected)",
                  ".nemo-window .nemo-window-pane widget.entry",
                  ".floating-bar"):
            self.assertIn(s, self.selectors, f"thiếu `{s}` — không có fallback nào style hộ")

    def test_output_contains_nemo_substring(self):
        """Lớp kiểm tra thứ hai của Nemo, src/nemo-application.c:186.

        Nếu theme không lọt hint tên, Nemo serialize CSS của theme
        (`gtk_css_provider_to_string`) rồi tìm chuỗi con "nemo"; không thấy thì in
        "The theme appears to have no nemo support. Adding some..." và nạp
        fallback-mandatory ở PRIORITY_APPLICATION(600).
        """
        self.assertIn("nemo", self.css)

    def test_locked_selectors_written_on_purpose(self):
        """Khối [LOCK] phải có mặt và phải bằng đúng danh sách đã xác minh.

        Nemo nạp nemo-style-application.css ở PRIORITY_APPLICATION(600) >
        PRIORITY_THEME(200) (src/nemo-application.c:320-321), và GTK 3.24 không có
        `!important`, nên các selector này KHÔNG thắng được trên desktop. Chúng
        vẫn được viết ra vì ba lý do có thật: (a) `.nemo-canvas-item` không kèm
        `.nemo-desktop` là canvas item trong cửa sổ thường, nơi Nemo chỉ khoá
        border-radius; (b) làm giá trị mặc định cho biến thể Light Glass; (c) sẽ
        có hiệu lực ngay nếu nạp ở PRIORITY_USER(800) qua
        ~/.config/gtk-3.0/gtk.css — cơ chế chuẩn của GTK3, không cần fork Nemo.
        """
        written = {s for s in self.selectors if s in ns.LOCKED_BY_NEMO}
        self.assertEqual(written, ns.LOCKED_BY_NEMO,
                         "khối [LOCK] lệch với danh sách đã xác minh từ "
                         "gresources/nemo-style-application.css")
        self.assertEqual(len(written), 16)

    def test_canvas_radius_conflict_is_recorded(self):
        """Xung đột token đã ĐO, không được im lặng bỏ qua.

        $mg-nemo-desktop-canvas-radius = 4px nhưng nemo-style-application.css:19
        khoá `border-radius: 3px` ở PRIORITY_APPLICATION(600). Trên desktop, 3px
        thắng và token 4px KHÔNG có tác dụng. Đã ghi trong fixture, trong SCSS và
        trong docs/testing/nemo-checklist.md — cần Agent Design Systems quyết.
        """
        src = self.sass.read_text()
        self.assertIn("nemo-desktop-canvas-radius", src)
        self.assertRegex(src, r"3px", "phải ghi lại giá trị 3px mà Nemo khoá")


@unittest.skipIf(ns is None, f"không import được nemo_selectors: {NS_IMPORT_ERROR}")
class TestDesktopLabelContrast(unittest.TestCase):
    """Done criterion #3 của T09: tương phản nhãn icon desktop >= 3:1, ĐO chứ không đoán.

    Giới hạn trung thực: yêu cầu gốc nói "đo trên một wallpaper mẫu". Không có máy
    Mint thật (cổng T00) nên không chụp được ảnh desktop thật. Thay vào đó đã đo
    trên BA mức chói wallpaper chặn hai đầu (trắng / trung tính / đen) — wallpaper
    thật là ảnh có dải chói nằm trong khoảng đó. Đo bằng chính
    `tools/lint/contrast.py` của repo (composite source-over + WCAG relative
    luminance), không tự viết lại công thức.

    Kết quả đo được ghi trong docs/testing/nemo-checklist.md.
    """

    @classmethod
    def setUpClass(cls):
        try:
            sys.path.insert(0, str(REPO / "tools" / "lint"))
            import contrast as ct
        except Exception as exc:  # pragma: no cover
            raise unittest.SkipTest(f"không import được contrast.py: {exc}")
        cls.ct = ct
        cls.WALLPAPERS = ((255, 255, 255), (128, 128, 128), (0, 0, 0))

    def _ratio(self, fg_hex_or_rgba, bg_rgba, wall):
        ct = self.ct
        bd = ct.to_rgb(wall, 1.0)
        surf = ct.composite(bg_rgba, bd) if bg_rgba is not None else bd
        fg = (ct.to_rgb(ct.parse_hex(fg_hex_or_rgba), 1.0)
              if isinstance(fg_hex_or_rgba, str) else fg_hex_or_rgba)
        return ct.contrast_ratio(fg, surf), surf

    def _token(self, name):
        m = re.search(rf"^\${re.escape(name)}:\s*(.+?);",
                      (REPO / "src/gtk-3.0/sass/_tokens.scss").read_text(), re.M)
        self.assertIsNotNone(m, f"không tìm thấy token ${name}")
        return m.group(1).strip()

    def _rgba_token(self, name):
        """'rgba(61, 220, 151, 0.8)' -> (61,220,151,0.8)"""
        v = self._token(name)
        m = re.match(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)$", v)
        self.assertIsNotNone(m, f"${name} không phải rgba(): {v!r}")
        return self.ct.to_rgb((int(m.group(1)), int(m.group(2)), int(m.group(3))), float(m.group(4)))

    def test_selected_label_fails_with_the_token_value(self):
        """GHI NHẬN KẾT QUẢ ĐO: token selected-text FAIL ở CẢ BA mức wallpaper.

        Bài này cố ý khẳng định token đang SAI, để con số không bị quên và để nó
        ĐỎ ngay khi Agent Design Systems sửa token (lúc đó phải xoá bài này và
        bật bài test_uses_on_accent_for_selected_label lên thành khẳng định token).
        """
        sel_bg = self._rgba_token("mg-nemo-desktop-label-selected-background")
        sel_fg = self.ct.to_rgb(self.ct.parse_hex(self._token("mg-nemo-desktop-label-selected-text")), 1.0)
        ratios = [self.ct.contrast_ratio(sel_fg, self.ct.composite(sel_bg, self.ct.to_rgb(w, 1.0)))
                  for w in self.WALLPAPERS]
        self.assertTrue(all(r < 3.0 for r in ratios),
                        f"token selected-text giờ đã đạt 3:1 ({ratios}) — tốt! Xoá bài "
                        "test này và khẳng định giá trị mới ở bài dưới.")
        self.assertEqual(ratios, [1.47, 1.90, 2.53],
                         "con số đo được đã thay đổi — kiểm tra lại contrast.py hoặc token")

    def test_stylesheet_uses_on_accent_not_the_failing_token(self):
        """SCSS phải dùng $mg-text-on-accent cho nhãn selected trên desktop."""
        src = ns.SCSS.read_text()
        block = re.search(r"\.nemo-desktop\.nemo-canvas-item:selected\s*\{([^}]*)\}", src)
        self.assertIsNotNone(block, "không tìm thấy rule .nemo-desktop.nemo-canvas-item:selected")
        self.assertIn("$mg-text-on-accent", block.group(1),
                      "phải dùng $mg-text-on-accent; $mg-nemo-desktop-label-selected-text "
                      "(#f5f5f5) đo được 1.47/1.90/2.53:1 — FAIL ở cả ba mức wallpaper")
        self.assertNotIn("nemo-desktop-label-selected-text", block.group(1))

    def test_on_accent_passes_on_all_three_wallpapers(self):
        """Phương án thay thế phải PASS thật, không chỉ 'tốt hơn'."""
        sel_bg = self._rgba_token("mg-nemo-desktop-label-selected-background")
        on_accent = self.ct.to_rgb(self.ct.parse_hex(self._token("mg-text-on-accent")), 1.0)
        ratios = [self.ct.contrast_ratio(on_accent, self.ct.composite(sel_bg, self.ct.to_rgb(w, 1.0)))
                  for w in self.WALLPAPERS]
        for r, w in zip(ratios, self.WALLPAPERS):
            self.assertGreaterEqual(r, 3.0, f"chỉ đạt {r}:1 trên wallpaper {w}")
        self.assertEqual(ratios, [12.23, 9.46, 7.10])

    def test_offset_shadow_leaves_the_glyph_edge_unprotected(self):
        """Shadow LỆCH 1px để hở mép trên-trái của glyph -> FAIL trên wallpaper sáng.

        Đã đo: chữ #eeeeee trên wallpaper trắng, ở mép KHÔNG có shadow = 1.16:1.
        Shadow không lệch (0 0 2px) sẽ che cả mép = 10.89:1. Đây là đề xuất đổi
        token, không phải lỗi của T09 (T09 không được sửa design/tokens/*.json).
        """
        label = self.ct.to_rgb(self.ct.parse_hex(self._token("mg-nemo-desktop-label-text")), 1.0)
        white = self.ct.to_rgb((255, 255, 255), 1.0)
        exposed = self.ct.contrast_ratio(label, white)
        self.assertLess(exposed, 3.0,
                        f"mép glyph không shadow trên wallpaper trắng = {exposed}:1 — "
                        "nếu con số này >= 3 thì kết luận về shadow lệch không còn đúng")
        shadowed = self.ct.contrast_ratio(label, self.ct.composite(self.ct.to_rgb((0, 0, 0), 0.8), white))
        self.assertGreaterEqual(shadowed, 3.0)

    def test_hover_label_passes_on_all_three_wallpapers(self):
        """Trạng thái hover: Nemo tắt text-shadow nên chỉ còn nền rgba(0,0,0,0.5)."""
        hover_bg = self._rgba_token("mg-nemo-desktop-label-hover-background")
        label = self.ct.to_rgb(self.ct.parse_hex(self._token("mg-nemo-desktop-label-text")), 1.0)
        for w in self.WALLPAPERS:
            surf = self.ct.composite(hover_bg, self.ct.to_rgb(w, 1.0))
            self.assertGreaterEqual(self.ct.contrast_ratio(label, surf), 3.0,
                                    f"hover FAIL trên wallpaper {w}")


@NEED_COMPILER
@unittest.skipIf(ns is None, f"không import được nemo_selectors: {NS_IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test: lint PHẢI đỏ khi SCSS sai. Nếu lint hỏng, lớp này đỏ trước.

    Mỗi bản đột biến được chép vào thư mục tạm CÙNG VỚI `_tokens.scss` để
    `@import "tokens"` phân giải được. Không ghi gì vào repo.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-nemo-mutant-"))
        shutil.copy2(REPO / "src/gtk-3.0/sass/_tokens.scss", self.tmp / "_tokens.scss")
        self.orig = ns.SCSS.read_text()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mutate(self, transform) -> list[tuple[str, str, str]]:
        mutated = transform(self.orig)
        self.assertNotEqual(mutated, self.orig, "đột biến không thay đổi gì — bài test vô nghĩa")
        path = self.tmp / "_apps-nemo.scss"
        path.write_text(mutated)
        return ns.findings_for(path, ns.FIXTURE)

    def _ids(self, findings, severity="FAIL"):
        return {cid for sev, cid, _ in findings if sev == severity}

    def test_baseline_is_clean(self):
        """Bản gốc phải sạch, nếu không các bài dưới đây pass vô nghĩa.

        Không đi qua `_mutate` vì helper đó khẳng định đầu vào CÓ thay đổi — với
        bản gốc thì khẳng định ấy sai. Đây là bug của chính bài test này ở lần
        chạy đầu, không phải bug của lint.
        """
        path = self.tmp / "_apps-nemo.scss"
        path.write_text(self.orig)
        self.assertEqual(self._ids(ns.findings_for(path, ns.FIXTURE)), set())

    def test_detects_important(self):
        """Đột biến phải HỢP LỆ về cú pháp SCSS.

        Bản đầu của bài này chèn `!important` TRƯỚC tên property, libsass báo lỗi
        cú pháp và lint chết bằng exception — nghĩa là bài test không hề kiểm tra
        điều nó định kiểm tra. `!important` phải đi SAU giá trị, đúng như một
        lập trình viên thật sẽ viết nhầm.
        """
        f = self._mutate(lambda s: s.replace("border-bottom-width: 0;",
                                             "border-bottom-width: 0 !important;", 1))
        self.assertIn("no-important", self._ids(f))

    def test_detects_forbidden_prelight_label(self):
        f = self._mutate(lambda s: s.replace(
            ".nemo-desktop {\n  background-color: transparent;",
            ".nemo-desktop {\n  background-color: transparent;\n"
            "  -NemoIconContainer-activate-prelight-icon-label: false;", 1))
        self.assertIn("no-prelight-label", self._ids(f))

    def test_detects_missing_disk_full_property(self):
        f = self._mutate(lambda s: s.replace(
            "  -NemoPlacesTreeView-disk-full-max-length: $mg-nemo-places-disk-full-max-length;\n", "", 1))
        self.assertIn("disk-full-props", self._ids(f))

    def test_detects_bare_generic_class(self):
        f = self._mutate(lambda s: s + "\n.sidebar { background-color: $mg-surface-base; }\n")
        ids = self._ids(f)
        self.assertIn("no-bare-generic", ids,
                      "lint không bắt được `.sidebar` trần — nó sẽ rò rỉ sang mọi "
                      "app GTK3 và giẫm lên T06")

    def test_detects_missing_required_selector(self):
        f = self._mutate(lambda s: s.replace(".floating-bar {\n", ".floating-bar-x {\n", 1))
        self.assertIn("coverage", self._ids(f))

    def test_detects_hardcoded_color(self):
        f = self._mutate(lambda s: s.replace(
            "  background-color: $mg-surface-base;\n", "  background-color: #121316;\n", 1))
        self.assertIn("no-hardcoded-color", self._ids(f))

    def test_detects_broken_token(self):
        f = self._mutate(lambda s: s.replace(
            "  font-weight: $nemo-w-medium;", "  font-weight: $mg-font-weight-medium;", 1))
        self.assertIn("no-broken-tokens", self._ids(f))

    def test_detects_invalid_gtk_property(self):
        f = self._mutate(lambda s: s.replace(
            "  color: $mg-text-tertiary;\n}", "  color: $mg-text-tertiary;\n  -gtk-icon-size: 16px;\n}", 1))
        self.assertIn("gtk3-property-blocklist", self._ids(f))

    def test_lint_does_not_crash_on_uncompilable_scss(self):
        """SCSS hỏng cú pháp phải cho FAIL có id `compile`, không phải traceback.

        Một lint crash trên input sai thì tệ hơn lint không tồn tại: CI đỏ vì
        exception, thông báo lỗi khó đọc, và người sửa không biết lỗi nằm ở đâu.
        """
        path = self.tmp / "_apps-nemo.scss"
        path.write_text("@import \"tokens\";\n.nemo-window { background-color: ;\n")
        f = ns.findings_for(path, ns.FIXTURE)
        ids = {cid for sev, cid, _ in f if sev == "FAIL"}
        self.assertIn("compile", ids,
                      "lint không báo FAIL `compile` cho SCSS hỏng cú pháp")

    def test_detects_polluted_fixture(self):
        """Hồi quy cho lỗi fixture Cinnamon: mục dạng `'} #Tooltip'`."""
        bad = self.tmp / "bad-fixture.txt"
        bad.write_text("// marker ok\n.nemo-window\n} #nemo-tab-close-button\n")
        f = ns.findings_for(ns.SCSS, bad)
        self.assertIn("fixture-integrity", self._ids(f))


@unittest.skipIf(ns is None, f"không import được nemo_selectors: {NS_IMPORT_ERROR}")
class TestMintApps(unittest.TestCase):
    """Done criterion #4 của T09 — và giới hạn THẬT của nó.

    GTK 3.24 KHÔNG đưa application ID vào CSS: GNOME/gtk ref 3.24.42,
    gtk/gtkapplicationwindow.c (1048 dòng) có 0 lần xuất hiện `application_id`.
    Đã tải và khảo sát mã nguồn thật của từng app (không suy đoán):
      xreader  CÓ hook: .xreader-window, .inverted, .page-thumbnail, .white-mode;
               node evview/evsidebarthumbnails/evpresentationview; name #page-label-entry
      pix      CÓ hook: 14 class riêng (.empty-view, .void-view, .histogram,
               .toolbox, .video-player, .window-overlay, .pix-circular-button, ...);
               widget name #GthInfoBar
      xed      CHỈ .xed-statusbar là riêng (xed/xed-statusbar.c:155); .small-button,
               .close-button, .inline-toolbar là class GTK chung
      xplayer  CHỈ widget name riêng (#stage, #logo-frame); #frame quá chung nên loại
      nemo     18 class riêng -> _apps-nemo.scss
      xviewer  KHÔNG có hook nào (48 file nguồn, 0 kết quả)
      mintupdate    KHÔNG có hook nào; app id com.linuxmint.mintupdate nhưng GTK3
                    không đưa ID vào CSS
      mintinstall   KHÔNG có hook nào
      cinnamon-settings KHÔNG có hook riêng (Cinnamon 6.6.9
                    commit 806c1a4e, chỉ .inline-toolbar là class chung)
    """

    def setUp(self):
        self.path = ns.MINT_APPS

    def test_file_exists(self):
        self.assertTrue(self.path.exists(), f"thiếu {self.path}")

    def test_every_required_app_has_an_entry(self):
        src = self.path.read_text()
        missing = [a for a in ns.MINT_APPS_REQUIRED if a not in src]
        self.assertEqual(missing, [],
                         "Done criterion #4 yêu cầu mỗi app Mint có một mục. App "
                         "không có hook thì mục đó phải ghi rõ kết quả khảo sát "
                         "kèm bằng chứng, không được bỏ trống.")

    def test_apps_without_hooks_are_documented_as_such(self):
        """4 app KHÔNG có hook phải được nói rõ, để không ai tưởng đã style chúng."""
        src = self.path.read_text()
        for app in ("xviewer", "mintupdate", "mintinstall", "cinnamon-settings"):
            self.assertRegex(src, rf"{app}[\s\S]{{0,400}}KHÔNG",
                             f"mục `{app}` phải ghi rõ là KHÔNG có hook nào, kèm "
                             "bằng chứng đã quét mã nguồn")

    @NEED_COMPILER
    def test_no_generic_class_or_generic_id(self):
        f = ns.mint_apps_findings(self.path)
        bad = [m for sev, cid, m in f if sev == "FAIL" and cid == "mint-apps-namespaced"]
        self.assertEqual(bad, [], "\n".join(bad))

    @NEED_COMPILER
    def test_no_frame_selector(self):
        """`#frame` phải bị loại: xplayer có widget name "frame" nhưng tên quá
        chung, selector ID đó sẽ trúng widget tên "frame" của bất kỳ app nào."""
        css, _ = ns.compile_scss(self.path)
        self.assertIsNotNone(css)
        self.assertNotIn("#frame", ns.output_selectors(css))

    @NEED_COMPILER
    def test_xreader_hooks_present(self):
        css, _ = ns.compile_scss(self.path)
        sels = ns.output_selectors(css)
        for s in ("evview", "evsidebarthumbnails", "evpresentationview",
                  ".xreader-window", "#page-label-entry"):
            self.assertIn(s, sels, f"thiếu hook đã xác minh của xreader: {s}")

    @NEED_COMPILER
    def test_pix_hooks_present(self):
        css, _ = ns.compile_scss(self.path)
        sels = ns.output_selectors(css)
        for s in (".empty-view", ".void-view", ".pix-circular-button", ".histogram",
                  "#GthInfoBar"):
            self.assertIn(s, sels, f"thiếu hook đã xác minh của pix: {s}")

    @NEED_COMPILER
    def test_inverted_mode_not_clobbered(self):
        """.inverted là chế độ ĐẢO MÀU trang của xreader (accessibility).

        Nếu theme tô nền tối cho `evview` mà đè lên `.inverted`, chữ tối sẽ nằm
        trên nền tối. Phải có rule riêng cho `.inverted`.
        """
        css, _ = ns.compile_scss(self.path)
        sels = ns.output_selectors(css)
        self.assertIn("evview.inverted", sels)

    @NEED_COMPILER
    def test_no_nemo_duplication(self):
        """Nemo phải chỉ có ở _apps-nemo.scss — tránh nguồn sự thật đôi."""
        css, _ = ns.compile_scss(self.path)
        nemo_sels = [s for s in ns.output_selectors(css) if "nemo" in s.lower()]
        self.assertEqual(nemo_sels, [],
                         f"_apps-mint.scss không được style Nemo: {nemo_sels}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
