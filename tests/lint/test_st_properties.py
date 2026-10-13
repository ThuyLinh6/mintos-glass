#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/lint/test_st_properties.py — unittest (stdlib, KHÔNG cần pytest).

Chạy: python3 -m unittest discover -s tests -t . -v
Hoặc: python3 -m unittest tests.lint.test_st_properties -v

NGUYÊN TẮC TRUNG THỰC: nếu môi trường không có trình biên dịch SCSS thì các test
cần CSS sẽ `skipTest(...)` với lý do rõ ràng. KHÔNG bao giờ biến "không chạy
được" thành "pass".
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "tools" / "lint"))

_spec = importlib.util.spec_from_file_location(
    "st_properties", REPO / "tools" / "lint" / "st_properties.py"
)
sp = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(sp)

CSS_CACHE: dict[str, object] = {}


def compiled_css() -> str:
    """Compile src/cinnamon/cinnamon.scss một lần, cache cho cả module."""
    if "css" in CSS_CACHE:
        return CSS_CACHE["css"]  # type: ignore[return-value]
    css, compiler = sp.compile_css()
    if css is None:
        raise unittest.SkipTest(
            "không có trình biên dịch SCSS trong môi trường này "
            "(cần `pip install libsass` hoặc `npm install sass@1.77.8`). "
            "Đây là SKIP có chủ đích, không phải PASS."
        )
    CSS_CACHE["css"] = css
    CSS_CACHE["compiler"] = compiler
    CSS_CACHE["rules"] = sp.parse_rules(css)
    return css


def rules():
    compiled_css()
    return CSS_CACHE["rules"]  # type: ignore[return-value]


def findings_for(check: str):
    out = []
    r = rules()
    css = CSS_CACHE["css"]
    if check == "properties":
        sp.check_properties(r, out)
    elif check == "forbid-blur":
        sp.check_forbid_blur(css, r, out)  # type: ignore[arg-type]
    elif check == "duration-unit":
        sp.check_duration_unit(r, out)
    elif check == "font-weight":
        sp.check_font_weight(r, out)
    elif check == "single-shadow":
        sp.check_single_shadow(r, out)
    elif check == "coverage":
        sp.check_coverage(r, out)
    elif check == "dead-vendor":
        sp.check_dead_vendor(r, out)
    return [f for f in out if f.severity == "ERROR"]


class TestFixturesExist(unittest.TestCase):
    """Fixture phải tồn tại và không rỗng — kiểm tra được KHÔNG cần compiler."""

    def test_allowed_properties_fixture(self):
        p = REPO / "tests" / "fixtures" / "st-allowed-properties.txt"
        self.assertTrue(p.exists(), f"thiếu {p}")
        entries = sp.load_fixture(p)
        self.assertGreater(len(entries), 100, "fixture quá nhỏ — có thể bị truncate")
        # opacity phải BỊ LOẠI (đã chứng minh St không có property này)
        self.assertNotIn("opacity", entries,
                         "`opacity` không phải property của St — không được nằm trong allow-list")
        # -blur phải BỊ LOẠI khỏi allow-list (cấm theo chính sách)
        self.assertNotIn("-blur", entries)
        # các property đã xác minh bằng mã nguồn phải CÓ
        for must in ("background-position", "background-repeat", "background-size",
                     "border-top-color", "border-bottom-color", "max-rows",
                     "-cinnamon-close-overlap", "-barlevel-height", "-slider-height",
                     "transition-duration", "box-shadow", "caret-size",
                     "selection-background-color", "-boxpointer-gap"):
            self.assertIn(must, entries, f"thiếu `{must}` trong allow-list")
        # các property GNOME-Shell-only phải KHÔNG có
        for must_not in ("-barlevel-overdrive-color", "-barlevel-overdrive-separator-width",
                         "-barlevel-border-color", "-barlevel-border-width",
                         "transform", "filter", "backdrop-filter",
                         "transition-timing-function"):
            self.assertNotIn(must_not, entries,
                             f"`{must_not}` không tồn tại trong St — không được allow")

    def test_selector_fixture(self):
        p = REPO / "tests" / "fixtures" / "cinnamon-6.6-selectors.txt"
        self.assertTrue(p.exists(), f"thiếu {p}")
        entries = sp.load_fixture(p)
        self.assertGreater(len(entries), 400, "fixture selector quá nhỏ")
        for must in (".popup-menu-content", ".applet-box", ".grouped-window-list-item-box",
                     ".dialog .dialog-button:default", ".vkeyboard-key.enter-key",
                     "#notification", ".calendar-today", ".switcher-list"):
            self.assertIn(must, entries)

    def test_vendor_is_pristine(self):
        """Vendor phải còn nguyên văn — mọi thay đổi nằm trong overrides/."""
        v = REPO / "src" / "cinnamon" / "vendor" / "cinnamon-6.6-sass"
        self.assertTrue(v.is_dir(), f"thiếu {v}")
        self.assertTrue((v / "VENDOR.md").exists(), "thiếu VENDOR.md ghi nguồn + SHA-256")
        scss = sorted(p for p in v.rglob("*.scss"))
        self.assertEqual(len(scss), 22, f"kỳ vọng 22 file scss pristine, thấy {len(scss)}")
        # VENDOR.md phải ghi commit SHA đầy đủ và tag
        doc = (v / "VENDOR.md").read_text()
        self.assertIn("806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18", doc)
        self.assertIn("6.6.9", doc)
        # mỗi file phải có SHA-256 trong VENDOR.md
        for p in scss:
            self.assertIn(p.name, doc, f"VENDOR.md thiếu mục cho {p.name}")


class TestNoBlur(unittest.TestCase):
    """Ràng buộc cứng: biến thể chuẩn KHÔNG được có -blur."""

    def test_no_blur_property(self):
        self.assertEqual(findings_for("forbid-blur"), [],
                         "tìm thấy -blur hoặc background-bumpmap trong output")

    def test_glass_is_alpha_not_blur(self):
        """Chống tuyên bố sai: 'glass' phải là alpha thật, không phải blur."""
        css = compiled_css()
        self.assertNotRegex(css, r"(?m)^\s*-blur\s*:",
                            "-blur xuất hiện trong CSS — vi phạm quyết định không ship blur")
        # phải thực sự có bề mặt rgba (alpha < 1) thì mới được gọi là trong suốt
        rgba = re.findall(r"rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)", css)
        translucent = [a for a in rgba if 0 < float(a) < 1]
        self.assertGreater(len(translucent), 30,
                           "quá ít bề mặt alpha<1 — không đủ cơ sở gọi theme là 'glass'")


class TestStSyntaxRules(unittest.TestCase):
    """Các ràng buộc cú pháp suy ra từ mã nguồn C của St."""

    def test_transition_duration_is_unitless(self):
        errs = findings_for("duration-unit")
        self.assertEqual([str(e) for e in errs], [],
                         "transition-duration có đơn vị — St sẽ BỎ QUA (cần số trần, ms ngầm định)")

    def test_font_weight_is_unitless_or_keyword(self):
        errs = findings_for("font-weight")
        self.assertEqual([str(e) for e in errs], [],
                         "font-weight sai dạng — font_weight_from_term() cần NUM_GENERIC hoặc keyword")

    def test_single_box_shadow_per_rule(self):
        errs = findings_for("single-shadow")
        self.assertEqual([str(e) for e in errs], [],
                         "box-shadow nhiều lớp — st_theme_node_lookup_shadow() chỉ trả về MỘT StShadow")

    def test_properties_are_known_to_st(self):
        errs = findings_for("properties")
        self.assertEqual([str(e) for e in errs], [],
                         "có property St không parse — sẽ bị bỏ qua trong im lặng")

    def test_no_dead_properties_added(self):
        errs = findings_for("dead-vendor")
        self.assertEqual([str(e) for e in errs], [],
                         "tầng override đã thêm property chết (opacity / border-style)")

    def test_no_css_custom_property_or_calc(self):
        """St không có var()/calc()/@media — blacklist đã ghi trong docs/design-system."""
        css = compiled_css()
        for pat, why in ((r"\bvar\(\s*--", "var(--…) không tồn tại trong St"),
                         (r"\bcalc\(", "calc() không tồn tại trong St"),
                         (r"@media", "@media không tồn tại trong St"),
                         (r"^\s*--[\w-]+\s*:", "custom property --x không tồn tại trong St")):
            self.assertIsNone(re.search(pat, css, re.M), why)


class TestHardcodedColors(unittest.TestCase):
    """Tầng override phải đi qua token, không hard-code màu."""

    def test_no_literal_colors_in_overrides(self):
        out = []
        sp.check_hardcoded(out)
        errs = [f for f in out if f.severity == "ERROR"]
        self.assertEqual([str(e) for e in errs], [],
                         "tìm thấy màu hard-code hoặc primitive $mg-color-* rò rỉ ngoài _00-globals")

    def test_no_broken_tokens_referenced(self):
        """Các token đã biết là SINH SAI phải không được dùng.

        Bằng chứng: tools/tokens/generate.py:215 gắn đơn vị "px" cho mọi leaf
        không nằm trong UNITLESS_KEYS (={"blur"}), và NS_UNIT không có nhánh
        "font". Kết quả trong src/cinnamon/tokens/_tokens.scss:
            $mg-font-weight-regular: 400px;  (St cần 400 — 400px bị bỏ qua)
            $mg-font-weight-medium:  500px;
            $mg-font-weight-bold:    700px;
            $mg-font-size-sm-pt:     9px;    (token tên -pt nhưng emit px)
            $mg-font-size-lg-pt:     12px;
            $mg-blur-sm:             2px;    (blur phải là số trần)
        Đã báo cho Agent design-system; tầng override dùng hằng tạm trong
        _00-globals.scss và test này khoá không cho ai dùng lại token hỏng.
        """
        broken = ("$mg-font-weight-regular", "$mg-font-weight-medium", "$mg-font-weight-bold",
                  "$mg-font-size-sm-pt", "$mg-font-size-lg-pt",
                  "$mg-blur-sm", "$mg-blur-md", "$mg-blur-lg")
        for f in sorted((REPO / "src" / "cinnamon" / "overrides").glob("_*.scss")):
            if f.name == "_00-globals.scss":
                continue
            text = re.sub(r"//.*", "", f.read_text())
            for b in broken:
                self.assertNotIn(b, text,
                                 f"{f.name} dùng token đã biết là sinh sai đơn vị: {b}")

    def test_duration_tokens_are_not_emitted(self):
        """Ghi nhận bằng chứng: 40-motion.json không bao giờ được emit.

        tools/tokens/generate.py:605-616 chỉ flatten 10-primitives.json,
        30-component.json và 20-semantic-<scheme>.json. 40-motion.json có trong
        TOKEN_FILES (dòng 50, tức tham gia tính lock) nhưng không vào pipeline
        phân giải -> duration.* và cinnamon_transition.* biến mất khỏi MỌI
        stylesheet sinh ra, trong khi `make tokens-check` vẫn báo OK.
        Test này KHOÁ thực trạng đó: nếu một ngày generator được sửa và bắt đầu
        emit $mg-duration-*, test sẽ fail và nhắc xoá hằng tạm trong
        _00-globals.scss để chuyển sang token thật.
        """
        tokens = (REPO / "src" / "cinnamon" / "tokens" / "_tokens.scss")
        if not tokens.exists():
            self.skipTest("chưa sinh src/cinnamon/tokens/_tokens.scss (chạy `make tokens`)")
        text = tokens.read_text()
        self.assertNotRegex(text, r"(?m)^\$mg-duration-",
                            "generator ĐÃ bắt đầu emit duration.* — hãy xoá hằng tạm "
                            "$mg-duration-* trong overrides/_00-globals.scss và dùng token")
        self.assertNotRegex(text, r"(?m)^\$mg-cinnamon-transition-",
                            "generator đã emit cinnamon_transition.* — dùng token thay hằng tạm")


class TestCliBehaviour(unittest.TestCase):
    """CLI phải phân biệt được PASS / FAIL / SKIP."""

    def test_exit_2_when_no_compiler_and_no_css(self):
        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ)
            env["PATH"] = td  # không có sass/sassc trên PATH
            # chặn cả import sass bằng cách chạy trong subprocess với sys.path sạch
            code = (
                "import sys, pathlib;"
                "sys.modules['sass']=None;"
                f"sys.argv=['x'];"
                f"sys.path.insert(0,{str(REPO / 'tools' / 'lint')!r});"
                "import importlib.util;"
                f"s=importlib.util.spec_from_file_location('sp',{str(REPO / 'tools' / 'lint' / 'st_properties.py')!r});"
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m);"
                "m.find_compiler=lambda: None;"
                "sys.exit(m.main([]))"
            )
            proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 2,
                             f"phải trả exit code 2 (skip) khi không có compiler; stderr={proc.stderr[:400]}")

    def test_hardcoded_check_runs_without_compiler(self):
        """check_hardcoded chỉ đọc SCSS nguồn nên luôn chạy được, kể cả không có sass."""
        out = []
        sp.check_hardcoded(out)
        self.assertIsInstance(out, list)


class TestDualCompilerAgreement(unittest.TestCase):
    """ADR-004: Mint build bằng libsass (pysassc). dart-sass phải cho cùng tập selector."""

    @classmethod
    def setUpClass(cls):
        # dart-sass nằm ở toolchain NGOÀI cây repo (xem st_properties.TOOLCHAIN):
        # một node_modules trong repo sẽ bị tools/lint/safety_paths.py quét.
        cls.dart = None
        env = os.environ.get("MINTOS_SASS_BIN")
        cands = [pathlib.Path(env)] if env else []
        cands += [sp.TOOLCHAIN / "node_modules" / ".bin" / "sass",
                  REPO / "node_modules" / ".bin" / "sass"]
        for cand in cands:
            if cand.exists():
                cls.dart = str(cand)
                break
        if cls.dart is None and shutil.which("sass"):
            cls.dart = shutil.which("sass")

    def test_both_compilers_produce_same_selector_set(self):
        lib = compiled_css()
        if self.dart is None:
            self.skipTest("không có dart-sass (`npm install sass@1.77.8`) — chỉ so được libsass")
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td) / "o.css"
            proc = subprocess.run(
                [self.dart, "--no-source-map", "--style=expanded",
                 str(REPO / "src" / "cinnamon" / "cinnamon.scss"), str(out)],
                cwd=str(REPO), capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"dart-sass fail:\n{proc.stderr[:2000]}")
            dart = out.read_text()
        a = {s for sel, _ in sp.parse_rules(lib) for s in sp.split_selectors(sel)}
        b = {s for sel, _ in sp.parse_rules(dart) for s in sp.split_selectors(sel)}
        self.assertEqual(a - b, set(), "dart-sass thiếu selector so với libsass")
        self.assertEqual(b - a, set(), "dart-sass thừa selector so với libsass")

    def test_vendor_slash_division_is_dart_deprecation_evidence(self):
        """Ghi lại bằng chứng cho ADR-004: vendor dùng `/` để chia.

        Dart Sass 1.77.8 phát DEPRECATION WARNING cho `to-em()` (dòng 4) và
        `fontsize()` (dòng 12) của vendor/_drawing.scss; Dart Sass 2.0 sẽ bỏ.
        libsass thì không cảnh báo. Vì Mint build bằng libsass nên theme vẫn
        chạy, nhưng đây là lý do PHẢI khoá phiên bản dart-sass và không được
        nâng cấp mù quáng.
        """
        src = (REPO / "src" / "cinnamon" / "vendor" / "cinnamon-6.6-sass" / "_drawing.scss").read_text()
        self.assertIn("$input / $base", src,
                      "vendor _drawing.scss không còn dùng `/` để chia — cập nhật lại ghi chú ADR-004")


if __name__ == "__main__":
    unittest.main(verbosity=2)
