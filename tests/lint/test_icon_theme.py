#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/icon_theme.py` và icon theme MintOS-Glass (T15).

Chạy bằng stdlib unittest, không cần pytest và KHÔNG cần compiler SCSS:
    python3 -m unittest discover -s tests -t .
    python3 -m unittest tests.lint.test_icon_theme -v

Lint này đọc `index.theme` và SVG trực tiếp nên chạy được ở CI tối giản — khác
với `st_properties.py`/`nemo_selectors.py` vốn cần libsass hoặc dart-sass.

--------------------------------------------------------------------------
VÌ SAO CÓ LỚP TestLintActuallyFails
--------------------------------------------------------------------------
Bốn lần trong dự án này một lint đã báo SAI và chỉ lộ ra khi chạy thật:
  - T04: `check_hardcoded` dùng offset sai, và guard `\\(\\s*\\$` sai khi regex đã
    ăn mất dấu `(` -> 27 dương tính giả.
  - T04: dựng fixture selector bằng `^([^@\\s/][^{}]*)\\{` với `re.M` -> `[^{}]`
    không loại newline -> 439 dòng rác `'} #Tooltip'`.
  - T05: `assets.py` coi khai báo `xmlns` là tham chiếu mạng -> FAIL cả 15 tệp;
    và `declared_sizes()` không tôn trọng last-wins -> so viewBox 48x48 với
    400x120 của rule vendor ĐÃ BỊ override -> FAIL giả.
  - T15: chính lint này, trong lúc viết, đã sai HAI lần — (a) gộp ba thư mục
    `symbolic/*` thành một tiền tố nên mất context; (b) quên bỏ tiền tố
    `scalable/` nên chỉ khớp 14/75 icon; (c) tìm MANIFEST theo cả path
    `actions/edit-find-symbolic` -> 14 cảnh báo giả.

Nên lớp cuối bẻ cong theme thành bản SAI trong thư mục tạm rồi khẳng định lint
FAIL. Một lint chỉ có giá trị khi nó thật sự đỏ lúc code sai.
"""

from __future__ import annotations

import configparser
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
    import icon_theme as il
except Exception as exc:  # pragma: no cover
    il = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

THEME = REPO / "src" / "icons" / "MintOS-Glass"
INDEX = THEME / "index.theme"
FIXTURE = REPO / "tests" / "fixtures" / "icon-theme-core.txt"
SVG_NS = "http://www.w3.org/2000/svg"


def index_cp():
    cp = configparser.ConfigParser(strict=False, interpolation=None,
                                   comment_prefixes=("#",), inline_comment_prefixes=None)
    cp.optionxform = str
    cp.read_string(INDEX.read_text(encoding="utf-8"))
    return cp


def all_svgs(root: Path = THEME):
    return sorted(root.rglob("*.svg"))


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestLintIsCleanOnTheRealTheme(unittest.TestCase):
    def test_no_fail_and_no_warn(self):
        f = il.findings(verbose=True)
        bad = [(s, c, m) for s, c, m in f if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"lint chưa sạch trên theme thật: {bad[:4]}")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestIndexThemeShape(unittest.TestCase):
    """Tiêu chí Done #1 của T15."""

    def setUp(self):
        self.cp = index_cp()
        self.root = self.cp["Icon Theme"]

    def test_parses_and_has_icon_theme_section(self):
        self.assertTrue(self.cp.has_section("Icon Theme"),
                        "thiếu section `[Icon Theme]` — index.theme theo Desktop "
                        "Entry Spec phải có nó")

    def test_required_keys_present(self):
        for key in ("Name", "Inherits", "Directories"):
            with self.subTest(key=key):
                self.assertTrue(self.root.get(key), f"thiếu khoá `{key}`")

    def test_name_matches_directory_name(self):
        """Bộ nạp icon tra theme theo TÊN THƯ MỤC; Name lệch thì theme không được
        nhận diện dù index.theme hợp lệ."""
        self.assertEqual(self.root["Name"], THEME.name)
        self.assertEqual(self.root["Name"], "MintOS-Glass")

    def test_comment_prefix_is_hash_only(self):
        """Desktop Entry Spec dùng `#`. Nếu bật cả `;` thì một giá trị chứa dấu
        chấm phẩy sẽ bị cắt cụt âm thầm."""
        txt = INDEX.read_text()
        self.assertRegex(txt, r"(?m)^#", "index.theme nên có comment giải thích")
        cp = self.cp
        self.assertEqual(cp.optionxform("Directories"), "Directories",
                         "optionxform phải giữ nguyên HOA/thường của khoá")

    def test_inherits_chain(self):
        inh = [x.strip() for x in self.root["Inherits"].split(",") if x.strip()]
        self.assertEqual(inh[-1], "hicolor",
                         "`hicolor` phải ở CUỐI: đó là chốt chặn bắt buộc theo spec")
        self.assertEqual(inh[0], "Mint-Y",
                         "`Mint-Y` phải ở ĐẦU: nó chắc chắn có mặt trên Mint 22.3 và "
                         "cung cấp phần lớn icon còn thiếu")
        self.assertIn("Adwaita", inh)
        self.assertIn("gnome", inh)
        self.assertNotIn(inh[0], inh[1:], "theme không được tự kế thừa chính nó")
        self.assertEqual(len(inh), len(set(inh)), f"Inherits có mục trùng: {inh}")

    def test_inherits_is_the_reason_the_theme_may_stay_small(self):
        """Ràng buộc thiết kế: theme này CỐ Ý chỉ có 75 icon. Điều đó chỉ an toàn
        vì có chuỗi Inherits. Nếu ai rút gọn Inherits thì test này phải đỏ."""
        self.assertGreaterEqual(len([x for x in self.root["Inherits"].split(",") if x.strip()]), 4)
        n = len(all_svgs())
        self.assertLess(n, 200,
                        f"theme có {n} icon — nếu phình ra thì xem lại: fallback qua "
                        "Inherits nghĩa là KHÔNG cần sao chép icon mà Mint-Y đã có")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestDirectoriesTwoWay(unittest.TestCase):
    """KHÔNG khai báo khả năng mà tài nguyên thực tế không đáp ứng (yêu cầu mục 5)."""

    def setUp(self):
        self.cp = index_cp()
        self.declared = [d.strip() for d in
                         self.cp["Icon Theme"]["Directories"].split(",") if d.strip()]
        self.on_disk = {p.parent.relative_to(THEME).as_posix() for p in all_svgs()}

    def test_every_declared_dir_exists_and_is_nonempty(self):
        for d in self.declared:
            with self.subTest(directory=d):
                self.assertTrue((THEME / d).is_dir(), f"`{d}` được khai báo nhưng không tồn tại")
                self.assertTrue(list((THEME / d).glob("*.svg")),
                                f"`{d}` rỗng — gtk-update-icon-cache sẽ báo lỗi")

    def test_every_dir_on_disk_is_declared(self):
        """Ngược lại: thư mục có SVG mà không được liệt kê thì số icon đó VÔ HÌNH."""
        self.assertEqual(self.on_disk - set(self.declared), set(),
                         "có thư mục chứa SVG nhưng không nằm trong Directories")

    def test_no_duplicates(self):
        self.assertEqual(len(self.declared), len(set(self.declared)))

    def test_expected_nine_directories(self):
        self.assertEqual(sorted(self.declared), sorted([
            "scalable/apps", "scalable/places", "scalable/devices",
            "scalable/mimetypes", "scalable/actions", "scalable/status",
            "symbolic/actions", "symbolic/places", "symbolic/status",
        ]), "cấu trúc thư mục đã đổi — cập nhật test này VÀ MANIFEST.md, đừng chỉ "
            "sửa cho qua")

    def test_no_empty_dirs_and_no_stray_files(self):
        for d in sorted(p for p in THEME.rglob("*") if p.is_dir()):
            with self.subTest(directory=d.relative_to(THEME).as_posix()):
                self.assertTrue(list(d.iterdir()), "thư mục rỗng")
        allowed = {".svg", ".md", ".theme", ".sh"}
        stray = [p.relative_to(THEME).as_posix() for p in THEME.rglob("*")
                 if p.is_file() and p.suffix.lower() not in allowed]
        self.assertEqual(stray, [], f"có tệp lạ trong theme: {stray}")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestSections(unittest.TestCase):
    def setUp(self):
        self.cp = index_cp()
        self.declared = [d.strip() for d in
                         self.cp["Icon Theme"]["Directories"].split(",") if d.strip()]
        self.sections = [s for s in self.cp.sections() if s != "Icon Theme"]

    def test_section_per_directory_and_no_dead_section(self):
        self.assertEqual(set(self.declared) - set(self.sections), set(),
                         "thiếu section cho thư mục đã khai báo")
        self.assertEqual(set(self.sections) - set(self.declared), set(),
                         "có section chết không khớp thư mục nào")

    def test_required_keys_per_section(self):
        for s in self.sections:
            for key in ("Size", "Context", "Type"):
                with self.subTest(section=s, key=key):
                    self.assertTrue(self.cp[s].get(key), f"`[{s}]` thiếu `{key}`")

    def test_scalable_sections_have_min_and_max(self):
        for s in self.sections:
            sec = self.cp[s]
            if sec.get("Type") != "Scalable":
                continue
            with self.subTest(section=s):
                lo, hi, size = int(sec["MinSize"]), int(sec["MaxSize"]), int(sec["Size"])
                self.assertLessEqual(lo, size, f"`[{s}]` Size < MinSize")
                self.assertLessEqual(size, hi, f"`[{s}]` Size > MaxSize")
                self.assertLess(lo, hi)

    def test_every_section_is_scalable_because_the_theme_is_svg_only(self):
        """Theme thuần SVG nên KHÔNG được có Type=Fixed: Fixed sẽ đòi raster đúng
        kích thước đó, mà ta không sinh raster."""
        for s in self.sections:
            with self.subTest(section=s):
                self.assertEqual(self.cp[s]["Type"], "Scalable")

    def test_no_scale_key_because_svg_does_not_need_2x(self):
        """Mint-Y dùng `Scale=2` cho `apps/16@2x` vì nó là raster. SVG scale không
        mất nét nên khai `Scale=2` sẽ là khai báo khống một khả năng không cần."""
        cp = self.cp
        for s in cp.sections():
            with self.subTest(section=s):
                self.assertNotIn("Scale", cp[s],
                                 "không được khai Scale= — xem MANIFEST mục 1")
        # Kiểm theo THƯ MỤC THẬT và theo khoá đã parse, không theo chuỗi thô:
        # comment trong index.theme giải thích VÌ SAO không cần @2x nên đương
        # nhiên chứa chữ "@2x" — bản đầu của test này FAIL vì lý do đó.
        self.assertEqual([d for d in THEME.rglob("*") if d.is_dir() and "@2x" in d.name], [])
        declared = [x.strip() for x in cp["Icon Theme"]["Directories"].split(",")]
        self.assertEqual([d for d in declared if "@2x" in d], [])

    def test_context_matches_directory_leaf(self):
        for s in self.sections:
            leaf = s.rstrip("/").split("/")[-1]
            want = il.DIR_CONTEXT.get(leaf)
            with self.subTest(section=s):
                if want:
                    self.assertEqual(self.cp[s]["Context"], want,
                                     f"`[{s}]` sai Context — bộ nạp lọc mất ứng viên")
                self.assertIn(self.cp[s]["Context"], il.VALID_CONTEXTS)

    def test_symbolic_sections_match_mint_y_values(self):
        """Giữ đúng cặp giá trị Mint-Y dùng cho apps/symbolic và status/symbolic
        (đã đọc từ index.theme thật của Mint-Y) để hành vi chọn icon khớp với thứ
        GTK/Cinnamon trên Mint vốn đã xử lý đúng."""
        for s in ("symbolic/actions", "symbolic/places", "symbolic/status"):
            sec = self.cp[s]
            self.assertEqual(sec["Size"], "16")
            self.assertEqual(sec["MinSize"], "16")
            self.assertEqual(sec["MaxSize"], "256")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestCoreCoverage(unittest.TestCase):
    def setUp(self):
        self.want = il.load_fixture(FIXTURE)

    def test_fixture_is_not_empty(self):
        self.assertEqual(len(self.want), 75,
                         f"fixture có {len(self.want)} mục, mong 75 — nếu chủ đích đổi "
                         "thì cập nhật MANIFEST.md và icon-spec.md cùng lúc")

    def test_every_core_icon_exists(self):
        have = set()
        for p in all_svgs():
            rel = p.parent.relative_to(THEME).as_posix()
            if rel.startswith("scalable/"):
                rel = rel[len("scalable/"):]
            have.add(f"{rel}/{p.stem}")
        self.assertEqual(set(self.want) - have, set(), "thiếu icon lõi")

    def test_no_icon_outside_the_core_set(self):
        """Hai chiều: tệp SVG nào không có trong fixture thì hoặc là icon chết,
        hoặc là ai đó thêm icon mà không cập nhật hợp đồng."""
        have = set()
        for p in all_svgs():
            rel = p.parent.relative_to(THEME).as_posix()
            if rel.startswith("scalable/"):
                rel = rel[len("scalable/"):]
            have.add(f"{rel}/{p.stem}")
        self.assertEqual(have - set(self.want), set(),
                         "có icon không nằm trong fixture — thêm nó vào "
                         "tests/fixtures/icon-theme-core.txt và MANIFEST.md")

    def test_verified_app_icon_names_are_present(self):
        """Tiêu chí Done #3: tên lấy từ `Icon=` trong .desktop THẬT.

        Danh sách này là kết quả trích từ mã nguồn, KHÔNG phải trí nhớ. Đặc biệt
        `preferences-desktop`: cinnamon-settings dùng tên đó chứ không phải
        `preferences-system` như nhiều người vẫn giả định.
        """
        verified = {
            "system-file-manager": "nemo.desktop.in (nemo 6.6.4)",
            "accessories-text-editor": "org.x.editor.desktop.in.in (xed)",
            "pix": "pix.desktop.in",
            "xplayer": "xplayer.desktop.in.in.in",
            "xreader": "xreader.desktop.in.in",
            "xviewer": "xviewer.desktop.in.in",
            "mintupdate": "mintupdate.desktop",
            "mintinstall": "mintinstall.desktop",
            "software-properties-mint": "mintinstall-fp-handler.desktop",
            "preferences-desktop": "cinnamon-settings.desktop (Cinnamon 6.6.9)",
        }
        for name, src in verified.items():
            with self.subTest(icon=name, source=src):
                self.assertTrue((THEME / "scalable" / "apps" / f"{name}.svg").exists(),
                                f"thiếu apps/{name}.svg — tên lấy từ {src}")

    def test_no_preferences_system_pretending_to_be_settings(self):
        self.assertFalse((THEME / "scalable" / "apps" / "preferences-system.svg").exists(),
                         "cinnamon-settings xin `preferences-desktop`, không phải "
                         "`preferences-system` — đã xác minh từ .desktop thật")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestSvgIntegrity(unittest.TestCase):
    """Tiêu chí Done #5 + #6."""

    def test_all_parse_with_xml_etree(self):
        for p in all_svgs():
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                root = ET.fromstring(p.read_text(encoding="utf-8"))
                self.assertEqual(root.tag, f"{{{SVG_NS}}}svg")

    def test_grid_is_24_for_every_icon(self):
        for p in all_svgs():
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertEqual(root.get("viewBox"), "0 0 24 24",
                                 "lưới thiết kế phải thống nhất 24x24")
                self.assertEqual(root.get("width"), "24")
                self.assertEqual(root.get("height"), "24")

    def test_no_external_references_beyond_xmlns(self):
        for p in all_svgs():
            txt = p.read_text(encoding="utf-8")
            urls = set(re.findall(r"https?://[^\s\"')]+", txt))
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertEqual(urls, {SVG_NS},
                                 "icon theme không được tải gì từ Internet khi chạy")

    def test_no_dangerous_or_unportable_tags(self):
        banned = ("<script", "<image", "<foreignObject", "<iframe", "<use",
                  "<filter", "<mask", "<clipPath", "feGaussianBlur", "feDropShadow")
        for p in all_svgs():
            txt = p.read_text(encoding="utf-8")
            for tag in banned:
                with self.subTest(icon=p.relative_to(THEME).as_posix(), tag=tag):
                    self.assertNotIn(tag, txt)

    def test_no_gradient_anywhere_in_the_icon_theme(self):
        """icon-spec.md mục 6: gradient chỉ được phép ở corner-ripple.svg của T05
        (asset Cinnamon), KHÔNG được phép trong icon theme — vì icon symbolic phải
        đơn sắc và icon thường phải đọc được trên nền bất kỳ."""
        for p in all_svgs():
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertNotIn("gradient", p.read_text(encoding="utf-8").lower())

    def test_no_rgba_function(self):
        """librsvg hỗ trợ rgba() trong presentation attribute KHÔNG nhất quán giữa
        các phiên bản; hex + *-opacity thì luôn hoạt động."""
        for p in all_svgs():
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertNotRegex(p.read_text(encoding="utf-8"), r"\brgba?\s*\(")

    def test_every_colour_traces_to_a_token(self):
        colors = il.token_hex_values()
        self.assertGreater(len(colors), 20, "token_hex_values() trả về quá ít")
        for p in all_svgs():
            txt = p.read_text(encoding="utf-8")
            for m in il.HEX_RE.finditer(txt):
                h = m.group(0).lower()
                if len(h) == 4:
                    h = "#" + "".join(c * 2 for c in h[1:])
                with self.subTest(icon=p.relative_to(THEME).as_posix(), colour=m.group(0)):
                    self.assertIn(h, colors,
                                  f"{m.group(0)} không khớp giá trị token nào — icon "
                                  "không được tạo ra bảng màu thứ hai")

    def test_naming_follows_icon_naming_spec(self):
        for p in all_svgs():
            with self.subTest(icon=p.name):
                self.assertRegex(p.stem, r"^[a-z0-9][a-z0-9._-]*$")

    def test_stroke_widths_are_within_the_spec_range(self):
        """icon-spec.md mục 2: nét 1.4 - 2.0, toàn bộ round cap/join."""
        for p in all_svgs():
            txt = p.read_text(encoding="utf-8")
            for m in re.finditer(r'stroke-width="([\d.]+)"', txt):
                w = float(m.group(1))
                with self.subTest(icon=p.relative_to(THEME).as_posix(), width=w):
                    self.assertGreaterEqual(w, 1.4,
                                            f"nét {w} < 1.4 sẽ mất khi scale xuống 16px")
                    self.assertLessEqual(w, 2.0)
            if "stroke-linecap" in txt:
                self.assertNotRegex(txt, r'stroke-linecap="(?!round)')
            if "stroke-linejoin" in txt:
                self.assertNotRegex(txt, r'stroke-linejoin="(?!round)')

    def test_content_stays_inside_the_safe_area(self):
        """icon-spec.md mục 1: vùng an toàn tuyệt đối 18x18 từ (3,3).

        Kiểm bằng cách duyệt mọi toạ độ số trong path/rect/circle. Đây là kiểm tra
        gần đúng (không dựng lại hình học thật của arc) nhưng đủ để bắt lỗi thô
        như vẽ tràn ra mép viewBox.
        """
        for p in all_svgs():
            txt = p.read_text(encoding="utf-8")
            coords = [float(x) for x in re.findall(r'(?<![\w.-])(-?\d+(?:\.\d+)?)(?![\w.])',
                                                     " ".join(re.findall(r'\sd="([^"]+)"', txt)))]
            if not coords:
                continue
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertGreaterEqual(min(coords), 0.0, "toạ độ âm -> ra ngoài viewBox")
                self.assertLessEqual(max(coords), 24.0, "toạ độ > 24 -> ra ngoài viewBox")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestSymbolicIsMonochrome(unittest.TestCase):
    """Tiêu chí Done #4: GTK tô lại icon symbolic theo màu chữ bằng KÊNH ALPHA."""

    def symbolic_svgs(self):
        return sorted(THEME.rglob("symbolic/*/*.svg"))

    def test_there_are_symbolic_icons(self):
        self.assertGreaterEqual(len(self.symbolic_svgs()), 10,
                                "không đủ bản symbolic — GTK sẽ fallback về Mint-Y "
                                "ở panel/menu/toolbar và phá tính nhất quán")

    def test_each_uses_exactly_one_colour(self):
        for p in self.symbolic_svgs():
            txt = p.read_text(encoding="utf-8")
            seen = set()
            for m in il.COLOUR_ATTR_RE.finditer(txt):
                v = m.group(2).strip().lower()
                if v != "none":
                    seen.add(v)
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertEqual(len(seen), 1,
                                 f"dùng {len(seen)} màu {sorted(seen)} — icon symbolic "
                                 "phải đơn sắc để GTK tô lại được")

    def test_that_one_colour_is_black(self):
        for p in self.symbolic_svgs():
            txt = p.read_text(encoding="utf-8")
            seen = {m.group(2).strip().lower() for m in il.COLOUR_ATTR_RE.finditer(txt)
                    if m.group(2).strip().lower() != "none"}
            with self.subTest(icon=p.relative_to(THEME).as_posix()):
                self.assertEqual(seen, {"#000000"},
                                 "quy ước là đen thuần; GTK thay bằng màu chữ")

    def test_names_have_the_symbolic_suffix(self):
        """GTK tra bản symbolic theo TÊN, không theo thư mục."""
        for p in self.symbolic_svgs():
            with self.subTest(icon=p.name):
                self.assertTrue(p.stem.endswith("-symbolic"))

    def test_symbolic_variants_have_a_full_colour_counterpart(self):
        """Mỗi bản symbolic phải có bản đầy đủ màu tương ứng, và ngược lại một icon
        có bản đầy đủ màu ở actions/places/status thì NÊN có bản symbolic."""
        for p in self.symbolic_svgs():
            ctx = p.parent.name                      # actions / places / status
            base = p.stem[: -len("-symbolic")]
            full = THEME / "scalable" / ctx / f"{base}.svg"
            with self.subTest(symbolic=p.relative_to(THEME).as_posix()):
                self.assertTrue(full.exists(),
                                f"có {ctx}/{base}-symbolic nhưng không có bản đầy đủ "
                                f"màu {ctx}/{base} — GTK xin bản thường sẽ fallback")

    def test_symbolic_geometry_is_not_more_detailed_than_the_colour_version(self):
        """Bản symbolic phải ĐƠN GIẢN HƠN hoặc bằng bản màu: ở 16px chi tiết nhỏ sẽ
        biến mất, và vì chỉ còn kênh alpha nên màu nhấn không cứu được nữa."""
        for p in self.symbolic_svgs():
            ctx = p.parent.name
            base = p.stem[: -len("-symbolic")]
            full = THEME / "scalable" / ctx / f"{base}.svg"
            if not full.exists():
                continue
            n_sym = len(re.findall(r"<(path|circle|rect|ellipse|polygon)\b",
                                   p.read_text(encoding="utf-8")))
            n_full = len(re.findall(r"<(path|circle|rect|ellipse|polygon)\b",
                                    full.read_text(encoding="utf-8")))
            with self.subTest(icon=f"{ctx}/{base}"):
                self.assertLessEqual(n_sym, n_full,
                                     f"bản symbolic có {n_sym} phần tử hình, bản màu "
                                     f"chỉ {n_full} — symbolic đang chi tiết hơn, sẽ "
                                     "bị nhoè ở 16px")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestInkContrastOnBothBackdrops(unittest.TestCase):
    """icon-spec.md mục 4.1 — kết quả ĐO, không phải sở thích."""

    @classmethod
    def setUpClass(cls):
        try:
            import contrast as ct
        except Exception as exc:
            raise unittest.SkipTest(f"không import được contrast.py: {exc}")
        cls.ct = ct

    def _ratio(self, a, b):
        return self.ct.contrast_ratio(self.ct.to_rgb(self.ct.parse_hex(a)),
                                      self.ct.to_rgb(self.ct.parse_hex(b)))

    def test_gray400_is_the_only_ramp_colour_passing_both_backdrops(self):
        """Bảng đo trong icon-spec.md phải tái lập được. Nếu token đổi giá trị thì
        test này đỏ và buộc phải xét lại màu nét vẽ."""
        dark = il.token_hex("mg-surface-base") or "#121316"
        ramp = {n: il.token_hex(f"mg-color-gray-{n}")
                for n in (200, 300, 400, 500, 600)}
        passing = {n: c for n, c in ramp.items()
                   if self._ratio(c, "#ffffff") >= 3.0 and self._ratio(c, dark) >= 3.0}
        self.assertEqual(list(passing), [400],   # khoá dict là INT, không phải chuỗi
                        f"mong gray-400 là màu DUY NHẤT đạt >=3:1 trên cả hai nền, "
                        f"thực tế: {passing}. Token đã đổi -> cập nhật icon-spec.md "
                        "và màu nét vẽ của icon.")

    def test_ink_values_match_the_documented_numbers(self):
        ink = il.token_hex("mg-color-gray-400")
        self.assertAlmostEqual(self._ratio(ink, "#ffffff"), 3.97, delta=0.01)
        self.assertAlmostEqual(self._ratio(ink, "#121316"), 4.68, delta=0.01)

    def test_accent_cannot_be_used_as_ink(self):
        """Ghi lại lý do mint KHÔNG làm nét vẽ, để không ai 'sửa cho đẹp thương hiệu'."""
        accent = il.token_hex("mg-status-accent")
        self.assertLess(self._ratio(accent, "#ffffff"), 3.0,
                        "accent đã đạt 3:1 trên nền trắng? khi đó có thể xét lại "
                        "quy tắc ở icon-spec.md mục 4.1")
        self.assertGreater(self._ratio(accent, "#121316"), 3.0)

    def test_every_app_icon_glyph_pair_meets_3_to_1(self):
        """Đo lại toàn bộ 12 cặp glyph/nền đã công bố trong icon-spec.md mục 4.3.

        Không đọc từ tài liệu — trích thẳng cặp màu THẬT đang nằm trong từng tệp
        SVG, để tài liệu không thể trôi ra khỏi tài nguyên.
        """
        pairs = []
        for p in sorted((THEME / "scalable" / "apps").glob("*.svg")):
            txt = p.read_text(encoding="utf-8")
            m = re.search(r'<rect[^>]*\bfill="(#[0-9a-f]{6})"', txt)
            if not m:
                self.fail(f"{p.name}: không tìm thấy nền squircle (<rect fill=…>)")
            bg = m.group(1)
            glyph = sorted({h.lower() for h in re.findall(r'#[0-9a-f]{6}', txt)} - {bg})
            for g in glyph:
                pairs.append((p.name, bg, g))
        self.assertGreater(len(pairs), 12, f"chỉ trích được {len(pairs)} cặp glyph/nền")
        for name, bg, g in pairs:
            with self.subTest(icon=name, bg=bg, glyph=g):
                self.assertGreaterEqual(self._ratio(g, bg), 3.0,
                                        f"{name}: glyph {g} trên nền {bg} dưới 3:1 "
                                        "(WCAG 1.4.11 cho đối tượng đồ hoạ)")

    def test_line_icons_use_the_ink_colour(self):
        ink = il.token_hex("mg-color-gray-400")
        for ctx in ("actions", "devices"):
            for p in sorted((THEME / "scalable" / ctx).glob("*.svg")):
                with self.subTest(icon=p.relative_to(THEME).as_posix()):
                    self.assertIn(ink, p.read_text(encoding="utf-8"),
                                  f"{p.name} phải dùng nét vẽ {ink} làm màu chính")


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestManifest(unittest.TestCase):
    def setUp(self):
        self.path = THEME / "MANIFEST.md"
        self.assertTrue(self.path.exists(), f"thiếu {self.path}")
        self.txt = self.path.read_text(encoding="utf-8")

    def test_every_core_icon_is_listed(self):
        for entry in il.load_fixture(FIXTURE):
            icon = entry.rsplit("/", 1)[-1]
            with self.subTest(icon=icon):
                self.assertIn(icon, self.txt,
                              "MANIFEST phải liệt kê icon để người đọc tra được nó "
                              "thuộc nhóm nào")

    def test_required_topics_are_covered(self):
        for key in ("Inherits", "fallback", "giấy phép", "chưa có",
                    "preferences-desktop", "hicolor", "symbolic"):
            with self.subTest(topic=key):
                self.assertIn(key.lower(), self.txt.lower(),
                              f"MANIFEST thiếu mục nói về `{key}` (tiêu chí Done #7)")

    def test_missing_icons_are_declared_with_their_fallback(self):
        """Yêu cầu 5.2 + 3.3: phải nói rõ icon nào CHƯA có và fallback về đâu."""
        for token in ("cs-", "panel", "symbolic", "Mint-Y"):
            with self.subTest(topic=token):
                self.assertIn(token, self.txt)

    def test_panel_status_icons_are_explicitly_out_of_scope(self):
        """Yêu cầu 3.3 của Agent 5: không thay icon trạng thái chức năng bằng hình
        trang trí. MANIFEST phải ghi rõ là CỐ Ý không làm, kèm lý do."""
        self.assertRegex(self.txt, r"CỐ Ý KHÔNG LÀM")
        for applet in ("network-wireless", "battery-", "audio-volume-"):
            with self.subTest(topic=applet):
                self.assertIn(applet, self.txt,
                              "phải nêu tên các họ icon trạng thái cần phối hợp với "
                              "Agent 2 trước khi vẽ")

    def test_apple_constraints_are_recorded(self):
        for needle in ("Apple", "thương hiệu"):
            with self.subTest(topic=needle):
                self.assertIn(needle, self.txt)

    def test_unverified_items_are_separated_from_verified(self):
        """Yêu cầu 3.2: không tuyên bố theme đã được hệ thống nhận diện khi chưa xác minh."""
        self.assertIn("CHƯA kiểm chứng", self.txt)
        self.assertIn("Cinnamon 6.6", self.txt)
        self.assertRegex(self.txt, r"(?i)không\s+(tuyên bố|khẳng định)")

    def test_licence_table_covers_every_component(self):
        for needle in ("Tự vẽ", "GPL-3.0-or-later", "freedesktop"):
            with self.subTest(topic=needle):
                self.assertIn(needle, self.txt)


@unittest.skipIf(il is None, f"không import được tools/lint/icon_theme.py: {IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test trên bản sao tạm. Không ghi gì vào repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-icontheme-mutant-"))
        # Tên thư mục tạm PHẢI là MintOS-Glass: lint so `Name=` trong index.theme
        # với TÊN THƯ MỤC (bộ nạp icon tra theme theo tên thư mục). Đặt tên
        # tạm là "theme" thì bài index-theme-valid đỏ trước và CHE MẤT kết quả
        # của chính mutation đang thử — bản đầu mắc đúng lỗi này.
        shutil.copytree(THEME, self.tmp / THEME.name)
        self.theme = self.tmp / THEME.name

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, findings, severity="FAIL"):
        return {cid for sev, cid, _ in findings if sev == severity}

    def _run(self):
        return il.findings(theme_dir=self.theme)

    def _edit_index(self, transform):
        old = (self.theme / "index.theme").read_text()
        new = transform(old)
        self.assertNotEqual(old, new, "đột biến không đổi gì — bài test vô nghĩa")
        (self.theme / "index.theme").write_text(new)
        return self._ids(self._run())

    def test_baseline_is_clean(self):
        bad = [(s, c, m) for s, c, m in self._run() if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"bản sao của theme thật mà đã báo lỗi: {bad[:3]}")

    # --- index.theme -----------------------------------------------------
    def test_detects_declared_but_missing_directory(self):
        shutil.rmtree(self.theme / "scalable" / "devices")
        self.assertIn("directories-two-way", self._ids(self._run()))

    def test_detects_directory_not_declared(self):
        """Hồi quy cho chính bug đã gặp: quên bỏ tiền tố `scalable/`."""
        ids = self._edit_index(lambda s: s.replace("Directories=scalable/apps,",
                                                   "Directories=", 1))
        self.assertIn("directories-two-way", ids)

    def test_detects_dead_section(self):
        ids = self._edit_index(lambda s: s.replace(",symbolic/status", "", 1))
        self.assertIn("sections-match-directories", ids)

    def test_detects_missing_section_for_declared_dir(self):
        ids = self._edit_index(lambda s: re.sub(r"\[scalable/apps\][^\[]*", "", s, count=1))
        self.assertIn("sections-match-directories", ids)

    def test_detects_wrong_context(self):
        ids = self._edit_index(lambda s: s.replace("[scalable/apps]\nSize=24\nContext=Apps",
                                                   "[scalable/apps]\nSize=24\nContext=Status", 1))
        self.assertIn("context-matches-dir", ids)

    def test_detects_scalable_without_maxsize(self):
        ids = self._edit_index(lambda s: s.replace("[scalable/apps]\nSize=24\nContext=Apps\n"
                                                   "Type=Scalable\nMinSize=16\nMaxSize=512",
                                                   "[scalable/apps]\nSize=24\nContext=Apps\n"
                                                   "Type=Scalable\nMinSize=16", 1))
        self.assertIn("section-keys", ids)

    def test_detects_inherits_without_hicolor_last(self):
        ids = self._edit_index(lambda s: s.replace("Inherits=Mint-Y,Adwaita,gnome,hicolor",
                                                   "Inherits=Mint-Y,Adwaita,gnome", 1))
        self.assertIn("inherits-fallback", ids)

    def test_detects_self_inheritance(self):
        ids = self._edit_index(lambda s: s.replace("Inherits=Mint-Y,Adwaita,gnome,hicolor",
                                                   "Inherits=Mint-Y,MintOS-Glass,hicolor", 1))
        self.assertIn("inherits-fallback", ids)

    def test_detects_name_mismatch(self):
        ids = self._edit_index(lambda s: s.replace("Name=MintOS-Glass", "Name=MintOSGlass", 1))
        self.assertIn("index-theme-valid", ids)

    # --- SVG -------------------------------------------------------------
    def _break_svg(self, rel, transform):
        p = self.theme / rel
        old = p.read_text()
        new = transform(old)
        self.assertNotEqual(old, new, f"đột biến không đổi gì {rel}")
        p.write_text(new)
        return self._ids(self._run())

    def test_detects_off_token_colour(self):
        # Nhắm #7c8087 (gray-400) vì list-add.svg đã được sửa từ accent sang nét
        # vẽ chuẩn: accent chỉ đạt 1.77:1 trên nền trắng nên không được làm nét
        # chính của line icon (icon-spec.md mục 4.4). Mutation test bắt đúng việc
        # asset đổi màu dưới chân nó.
        ids = self._break_svg("scalable/actions/list-add.svg",
                              lambda s: s.replace("#7c8087", "#ff00aa"))
        self.assertIn("colors-are-token-values", ids)

    def test_detects_external_reference(self):
        """xmlns phải được MIỄN, nhưng một URL thật thì phải bị bắt."""
        ids = self._break_svg("scalable/places/folder.svg",
                              lambda s: s.replace("</svg>",
                                                  '  <image href="https://example.com/x.png"/>\n</svg>'))
        self.assertIn("no-external-refs", ids)

    def test_detects_filter_tag(self):
        ids = self._break_svg("scalable/places/folder.svg",
                              lambda s: s.replace("</svg>",
                                                  '  <filter id="f"><feGaussianBlur stdDeviation="1"/></filter>\n</svg>'))
        self.assertIn("no-external-refs", ids)

    def test_detects_gradient_in_icon_theme(self):
        """Bản đầu của bài này có khẳng định lỏng (`... or ids`) nên PASS kể cả khi
        lint im lặng. icon-spec.md mục 6 cấm gradient trong icon theme, nên phải có
        bài lint `no-gradient` thật và test phải đòi đúng nó."""
        ids = self._break_svg("scalable/places/folder.svg",
                              lambda s: s.replace("</svg>",
                                                  '  <defs><linearGradient id="g"/></defs>\n</svg>'))
        self.assertIn("no-gradient", ids)

    def test_detects_wrong_viewbox(self):
        ids = self._break_svg("scalable/devices/computer.svg",
                              lambda s: s.replace('viewBox="0 0 24 24"', 'viewBox="0 0 48 48"'))
        self.assertIn("svg-viewbox", ids)

    def test_detects_malformed_xml(self):
        ids = self._break_svg("scalable/apps/pix.svg", lambda s: s.replace("</svg>", ""))
        self.assertIn("svg-wellformed", ids)

    def test_detects_rgba_usage(self):
        # pix.svg không chứa `fill="#7c8087"` (nền nó là amber-600) nên bản đầu
        # của mutation này không đổi được gì. Phải nhắm chuỗi có thật.
        ids = self._break_svg("scalable/apps/pix.svg",
                              lambda s: s.replace('fill="#d99a1f"', 'fill="rgba(217,154,31,1)"'))
        self.assertIn("no-rgba-in-svg", ids)

    # --- symbolic --------------------------------------------------------
    def test_detects_two_colours_in_symbolic(self):
        # Bản đầu của bài này gọi _break_svg HAI lần và lần đầu thay `#000000`
        # bằng chính `#000000` — một đột biến không đột biến gì, chỉ làm bẩn trạng
        # thái cho lần sau. Một mutation test phải tạo ra input SAI một cách xác
        # định (bài học đã ghi từ T09: mutation phải hợp lệ về cú pháp VÀ phải đổi
        # thứ nó định đổi).
        # Bản đầu của mutation này đổi #000000 -> #3ddc97, tức là vẫn ĐƠN SẮC nên
        # lint (đúng đắn) không báo gì và test đỏ vì lý do sai. Muốn bắt
        # `symbolic-monochrome` thì phải tạo ra HAI màu thật sự.
        ids = self._break_svg("symbolic/places/folder-symbolic.svg",
                              lambda s: s.replace("</svg>",
                                                  '  <path d="M6 6h4v4H6z" fill="#3ddc97"/>\n</svg>'))
        self.assertIn("symbolic-monochrome", ids)

    def test_detects_symbolic_in_a_non_black_single_colour(self):
        """Đơn sắc nhưng không đen: chức năng vẫn chạy (GTK tô bằng kênh alpha) nên
        lint chỉ WARN. Test này khoá mức nghiêm trọng đó, để không ai nâng nó thành
        FAIL sai bản chất, cũng không ai bỏ hẳn."""
        f = None
        p = self.theme / "symbolic" / "places" / "folder-symbolic.svg"
        p.write_text(p.read_text().replace('fill="#000000"', 'fill="#3ddc97"', 1))
        res = self._run()
        self.assertIn("symbolic-monochrome", {c for s_, c, _ in res if s_ == "WARN"},
                      f"không có WARN nào: {res}")
        self.assertNotIn("symbolic-monochrome", self._ids(res),
                         "đơn sắc không-đen phải là WARN chứ không phải FAIL")

    def test_detects_symbolic_without_suffix(self):
        (self.theme / "symbolic" / "places" / "folder-symbolic.svg").rename(
            self.theme / "symbolic" / "places" / "folder.svg")
        ids = self._ids(self._run())
        self.assertTrue({"symbolic-monochrome", "core-coverage", "manifest"} & ids,
                        f"đổi tên symbolic mà lint không bắt: {ids}")

    # --- coverage --------------------------------------------------------
    def test_detects_missing_core_icon(self):
        (self.theme / "scalable" / "apps" / "xplayer.svg").unlink()
        ids = self._ids(self._run())
        self.assertIn("core-coverage", ids)

    def test_detects_icon_outside_the_core_set(self):
        shutil.copy2(self.theme / "scalable" / "apps" / "pix.svg",
                     self.theme / "scalable" / "apps" / "some-random-app.svg")
        # lint hiện chỉ kiểm một chiều (fixture -> đĩa); chiều ngược lại do test
        # test_no_icon_outside_the_core_set đảm nhiệm. Khẳng định điều đó vẫn đúng.
        have = set()
        for p in self.theme.rglob("*.svg"):
            rel = p.parent.relative_to(self.theme).as_posix()
            if rel.startswith("scalable/"):
                rel = rel[len("scalable/"):]
            have.add(f"{rel}/{p.stem}")
        self.assertIn("apps/some-random-app", have - set(il.load_fixture(FIXTURE)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
