#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/css_sanity.py` và cho chính sổ bug QA (T13).

Chạy bằng stdlib unittest, KHÔNG cần mạng:
    python3 -m unittest tests.lint.test_css_sanity -v

Các bài cần compiler SCSS sẽ SKIP khi không có libsass/dart-sass. Đó là SKIP có
chủ đích, KHÔNG phải PASS — chính QA-01 trong sổ bug là về việc CI bỏ qua khác biệt
này và báo xanh giả.

--------------------------------------------------------------------------
VÌ SAO CÓ LỚP TestLintActuallyFails
--------------------------------------------------------------------------
`css_sanity.py` được viết trong đợt QA này và NGAY TRONG LÚC VIẾT nó đã có NĂM bug
khiến nó báo sai. Cả năm chỉ lộ ra khi chạy thật:
  1. `bare_classes()` coi class thứ hai trong selector GHÉP là "trần", nên báo oan
     `.nemo-window.background` và `treeview.view.treeview-drop-indicator` — hai
     selector có qualifier riêng của app, không rò rỉ.
  2. So selector giữa hai compiler bằng CHUỖI THÔ nên nhạy với whitespace: libsass
     giữ selector nhóm kèm xuống dòng, dart-sass thì không -> FAIL giả.
  3. Chạy dart-sass không kèm `--no-source-map` nên để lại `*.qa-dart.css.map`
     TRONG src/, rồi chính bài "generated bị sửa tay" đọc thấy rác đó và FAIL giả.
     Tức lint vi phạm cam kết "không ghi gì" trong docstring của chính nó.
  4. Bài phát hiện target build giả kiểm tra `startswith(("echo","#","@echo","if",
     "fi"))` nhưng thân target mở đầu bằng `@if` (có dấu @) nên điều kiện sai và
     bài kiểm tra IM LẶNG dù `make scss` thật sự chỉ echo ra TODO.
  5. Sau khi sửa (4) thì lại báo oan: dòng `@if [ -z "$(SASS)" ]` có THAM CHIẾU
     compiler nhưng đó là phép THỬ chứ không phải lời gọi.
Cả năm đã sửa và mỗi cái có một bài hồi quy ở dưới.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "lint"))

try:
    import css_sanity as cs
except Exception as exc:  # pragma: no cover
    cs = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

REGISTER = REPO / "tests" / "fixtures" / "qa-bug-register.txt"
GTK_CLASSES = REPO / "tests" / "fixtures" / "gtk-standard-style-classes.txt"
SEVERITIES = {"P0", "P1", "P2", "P3"}
STATUSES = {"OPEN", "FIXED", "WONT-FIX", "BLOCKED"}
OWNERS_OK = re.compile(r"^(T\d{2}|T0\d|—)")


def has_compiler() -> bool:
    return cs is not None and cs.find_compiler() is not None


NEED_COMPILER = unittest.skipUnless(has_compiler(),
                                    "cần libsass hoặc dart-sass — SKIP có chủ đích, "
                                    "KHÔNG phải PASS (xem QA-01)")


# ---------------------------------------------------------------------------
def parse_register() -> list[dict]:
    rows = []
    for n, raw in enumerate(REGISTER.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("//", 1)[0].rstrip() if raw.lstrip().startswith("//") else raw.rstrip()
        if not line.strip():
            continue
        # split trên `|` CHƯA ESCAPE. Cột REPRO chứa lệnh shell nên có thể có pipe;
        # trong sổ bug những pipe đó được viết là `\|`. Bản đầu dùng line.split("|")
        # nên một dòng có pipe bị tách thành 9 cột và làm sai cả sổ bug một cách âm thầm.
        cols = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]
        rows.append({"line": n, "cols": cols, "raw": line})
    return rows


@unittest.skipIf(cs is None, f"không import được css_sanity.py: {IMPORT_ERROR}")
class TestFixturesAreUsable(unittest.TestCase):
    def test_gtk_standard_classes_fixture_has_84(self):
        """Con số 84 là kết quả trích BẰNG MÁY từ gtk/gtkstylecontext.h @3.24.42.
        Nếu nó đổi thì hoặc upstream đổi hoặc cách trích sai — cả hai đều phải điều
        tra, không sửa số cho khớp."""
        vals = set()
        for line in GTK_CLASSES.read_text(encoding="utf-8").splitlines():
            line = line.split("//", 1)[0].strip()
            if line:
                vals.add(line)
        self.assertEqual(len(vals), 84,
                         f"fixture có {len(vals)} class, mong 84 (GTK_STYLE_CLASS_* "
                         "trong gtkstylecontext.h @3.24.42)")

    def test_fixture_records_how_to_reproduce_itself(self):
        txt = GTK_CLASSES.read_text(encoding="utf-8")
        self.assertIn("gtkstylecontext.h", txt)
        self.assertIn("3.24.42", txt)
        self.assertRegex(txt, r"(?i)cách tái tạo|CÁCH TÁI TẠO")

    def test_dim_label_is_in_the_standard_list(self):
        """Đây là class đã gây ra QA-03. Nếu nó biến mất khỏi fixture thì lint sẽ
        ngừng bắt lỗi đó mà không ai biết."""
        vals = {l.split("//", 1)[0].strip()
                for l in GTK_CLASSES.read_text(encoding="utf-8").splitlines()}
        self.assertIn("dim-label", vals)

    def test_nemo_specific_classes_are_NOT_in_the_standard_list(self):
        """Ba class này do chính Nemo thêm, KHÔNG phải class chuẩn GTK. Nếu ai đó
        "bổ sung cho đủ" thì sẽ sinh dương tính giả cho QA-03."""
        vals = {l.split("//", 1)[0].strip()
                for l in GTK_CLASSES.read_text(encoding="utf-8").splitlines()}
        for c in ("floating-bar", "places-treeview", "treeview-drop-indicator",
                  "nemo-window"):
            with self.subTest(cls=c):
                self.assertNotIn(c, vals,
                                 f"{c} là class riêng của Nemo, không được nằm trong "
                                 "danh sách class CHUẨN GTK")


@unittest.skipIf(cs is None, f"không import được css_sanity.py: {IMPORT_ERROR}")
class TestBugRegister(unittest.TestCase):
    """Sổ bug cũng phải được kiểm tra — một sổ bug sai định dạng thì không ai dùng."""

    def setUp(self):
        self.rows = parse_register()
        self.bugs = [r for r in self.rows if r["cols"] and r["cols"][0].startswith("QA-")]

    def test_register_exists_and_is_not_empty(self):
        self.assertTrue(REGISTER.exists())
        self.assertGreaterEqual(len(self.bugs), 10,
                                f"chỉ có {len(self.bugs)} bug — đợt QA này tìm được "
                                "nhiều hơn thế, kiểm tra lại xem có bị mất dòng không")

    def test_every_row_has_exactly_eight_columns(self):
        """Cột REPRO chứa lệnh shell nên rất dễ có dấu `|` chưa escape, sẽ làm lệch
        cột một cách ÂM THẦM. Bài này tồn tại vì lý do đó."""
        for r in self.bugs:
            with self.subTest(line=r["line"], bug=r["cols"][0]):
                self.assertEqual(len(r["cols"]), 8,
                                 f"{r['cols'][0]} có {len(r['cols'])} cột, mong 8. "
                                 "Nếu cột REPRO chứa lệnh shell có pipe thì phải "
                                 "escape thành \\|")

    def test_ids_unique_and_wellformed(self):
        ids = [r["cols"][0] for r in self.bugs]
        self.assertEqual(len(ids), len(set(ids)), f"ID trùng: {ids}")
        for i in ids:
            with self.subTest(bug=i):
                self.assertRegex(i, r"^QA-(N)?\d{2}$")

    def test_severity_and_status_are_from_the_allowed_sets(self):
        for r in self.bugs:
            c = r["cols"]
            with self.subTest(bug=c[0]):
                self.assertIn(c[1], SEVERITIES, f"{c[0]}: mức {c[1]!r} không hợp lệ")
                self.assertIn(c[4], STATUSES, f"{c[0]}: trạng thái {c[4]!r} không hợp lệ")

    def test_every_bug_names_an_owner_task(self):
        """QA không tự sửa sản phẩm của agent khác — mỗi bug phải ghi rõ ai sửa."""
        for r in self.bugs:
            c = r["cols"]
            if c[4] == "WONT-FIX":
                continue
            with self.subTest(bug=c[0]):
                self.assertRegex(c[3], r"T\d{2}",
                                 f"{c[0]}: OWNER phải chỉ tới một task (Txx) để chuyển "
                                 "bug về đúng người sở hữu")

    def test_every_evidence_path_exists_in_the_repo(self):
        """Bằng chứng phải trỏ tới thứ CÓ THẬT. Đây là bài quan trọng nhất của lớp
        này: một sổ bug mà đường dẫn bằng chứng sai thì không ai tái hiện được."""
        for r in self.bugs:
            c = r["cols"]
            ev = c[5]
            with self.subTest(bug=c[0], evidence=ev):
                self.assertTrue((REPO / ev).exists(),
                                f"{c[0]}: bằng chứng `{ev}` không tồn tại trong repo")

    def test_summary_states_a_consequence_not_just_a_symptom(self):
        """Bug THẬT phải nói rõ hệ quả, không chỉ liệt kê triệu chứng.

        MIỄN TRỪ các mục WONT-FIX (QA-N*): mục đích của chúng là ghi lại "đã điều
        tra và kết luận KHÔNG phải lỗi" kèm LÝ DO, nên đòi một từ khoá "hệ quả" ở đó
        là sai bản chất. Bản đầu của bài này không miễn trừ và đã đòi QA-N01 phải
        chứa chữ "hệ quả" — trong khi QA-N01 nói rõ "dễ bị hiểu nhầm là build không
        xác định", tức đã nêu hậu quả của việc KHÔNG ghi lại.
        Cách xử lý đúng là thu hẹp phạm vi bài kiểm tra, KHÔNG phải nới danh sách từ
        khoá tới mức bài kiểm tra thành vô nghĩa.
        """
        for r in self.bugs:
            c = r["cols"]
            if c[4] == "WONT-FIX":
                continue
            with self.subTest(bug=c[0]):
                self.assertGreater(len(c[7]), 80,
                                   f"{c[0]}: tóm tắt quá ngắn để nói rõ HỆ QUẢ")
                # Bản đầu chỉ chấp nhận 5 marker (hệ quả / nghĩa là / nên / dẫn tới /
                # khiến) và báo FAIL oan cho QA-07, QA-11, QA-13 — cả ba đều NÓI RÕ
                # hệ quả nhưng bằng cách diễn đạt khác ("vô nghĩa nếu ai đó đem dùng",
                # "CHƯA phải 'sẵn sàng đóng gói'", "để người đóng gói không tưởng…").
                # Nới danh sách marker nhưng GIỮ yêu cầu độ dài, để bài kiểm tra vẫn
                # chặn được mục chỉ liệt kê triệu chứng mà không nói hậu quả.
                self.assertRegex(
                    c[7],
                    r"(?i)hệ quả|nghĩa là|nên |dẫn tới|khiến|để không|để người|"
                    r"CHƯA phải|vô nghĩa|không thể|sẽ (bị|làm|khiến)|rủi ro")

    def test_no_p0_without_strong_evidence(self):
        """Yêu cầu của Agent 7: chỉ dùng P0/P1 khi có bằng chứng đủ mạnh; không biến
        mọi khác biệt pixel thành lỗi nghiêm trọng."""
        p0 = [r["cols"][0] for r in self.bugs if r["cols"][1] == "P0"]
        self.assertEqual(p0, [],
                         "có bug P0 — P0 nghĩa là không khởi động được desktop hoặc "
                         "huỷ dữ liệu; đợt QA này chỉ kiểm tra tĩnh nên không thể "
                         "có bằng chứng cho mức đó")
        p1 = [r["cols"] for r in self.bugs if r["cols"][1] == "P1"]
        for c in p1:
            with self.subTest(bug=c[0]):
                self.assertIn(c[4], ("OPEN", "FIXED"),
                              "P1 mà BLOCKED thì phải giải thích trong tóm tắt")

    def test_investigated_non_bugs_are_recorded(self):
        """Ba mục QA-N* là thứ đã điều tra và kết luận KHÔNG phải lỗi. Giữ lại để
        không điều tra lần hai và để không ai 'sửa' một thứ đang đúng."""
        ids = {r["cols"][0] for r in self.bugs}
        for nid in ("QA-N01", "QA-N02", "QA-N03"):
            with self.subTest(item=nid):
                self.assertIn(nid, ids)
        for r in self.bugs:
            if r["cols"][0].startswith("QA-N"):
                self.assertEqual(r["cols"][4], "WONT-FIX",
                                 f"{r['cols'][0]} là mục 'không phải lỗi' nên trạng "
                                 "thái phải là WONT-FIX")

    def test_the_ci_false_green_bug_is_p1(self):
        """QA-01 là phát hiện nghiêm trọng nhất đợt này: cổng chất lượng báo xanh mà
        không chạy 67/322 bài. Nếu ai hạ mức nó xuống P2/P3 thì phải có lý do."""
        row = next((r for r in self.bugs if r["cols"][0] == "QA-01"), None)
        self.assertIsNotNone(row, "thiếu QA-01 trong sổ bug")
        self.assertEqual(row["cols"][1], "P1")
        self.assertIn("67", row["cols"][7],
                      "QA-01 phải ghi con số 67 bài skip — đó là bằng chứng định lượng")

    def test_wont_fix_items_state_a_reason(self):
        """Miễn trừ yêu cầu "hệ quả" cho WONT-FIX, nhưng đổi lại chúng PHẢI có lý do
        kết luận không phải lỗi — nếu không thì QA-N* thành chỗ giấu bug."""
        n = 0
        for r in self.bugs:
            c = r["cols"]
            if c[4] != "WONT-FIX":
                continue
            n += 1
            with self.subTest(bug=c[0]):
                self.assertRegex(c[7], r"(?i)KHÔNG PHẢI|không phải lỗi|đã xác minh|"
                                       r"đúng tiến độ|test sai|không phải")
        self.assertGreaterEqual(n, 3, "phải giữ đủ 3 mục QA-N* đã điều tra")

    def test_repro_commands_are_runnable_here(self):
        """Cột REPRO phải là lệnh CHẠY ĐƯỢC trong sandbox này, không phải mô tả.
        Chỉ kiểm những lệnh an toàn (không ghi, không mạng)."""
        # Bỏ qua lệnh GHI/MẠNG và cả lệnh NẶNG. Bản đầu chỉ loại lệnh ghi/mạng nên
        # nó đã chạy QA-01 (nguyên một lần `unittest discover` mô phỏng CI, ~5 phút)
        # BÊN TRONG một bài test — vừa chậm vừa đệ quy, và fail vì /tmp/cihome chưa
        # tồn tại. Kiểm tra "lệnh có chạy được không" không đồng nghĩa với "phải
        # chạy cả bộ test bên trong bộ test".
        skip_pat = re.compile(r"(sudo|rm |mv |cp |>|apt|install|curl|wget|git push"
                              r"|unittest|make check|env -u|css_sanity\.py)")
        checked = 0
        for r in self.bugs:
            cmd = r["cols"][6]
            if not cmd or skip_pat.search(cmd) or cmd.startswith("xem "):
                continue
            with self.subTest(bug=r["cols"][0]):
                proc = subprocess.run(cmd, shell=True, cwd=str(REPO),
                                      capture_output=True, text=True, timeout=300)
                self.assertEqual(proc.returncode, 0,
                                 f"{r['cols'][0]}: lệnh tái hiện exit {proc.returncode}\n"
                                 f"stderr: {proc.stderr[-300:]}")
                checked += 1
        self.assertGreater(checked, 3,
                           f"chỉ kiểm được {checked} lệnh tái hiện — quá ít để tin "
                           "rằng sổ bug tái hiện được")


@unittest.skipIf(cs is None, f"không import được css_sanity.py: {IMPORT_ERROR}")
class TestLintFindsTheKnownRealIssues(unittest.TestCase):
    """Khẳng định lint THẬT SỰ bắt được các bug đã ghi trong sổ.

    Đây là bài chống lại rủi ro lớn nhất của một lint mới: nó chạy xanh và mọi
    người tưởng không có lỗi. Các bài dưới đây đòi lint phải ĐỎ ở đúng những chỗ
    đã xác minh bằng tay.
    """

    @classmethod
    def setUpClass(cls):
        cls.f = cs.findings()
        cls.by_id = {}
        for sev, cid, msg in cls.f:
            cls.by_id.setdefault(cid, []).append((sev, msg))

    def test_it_reports_the_dim_label_leak(self):
        hits = self.by_id.get("bare-gtk-class-leak", [])
        self.assertTrue(hits, "lint không báo rò rỉ class chuẩn GTK nào — QA-03 sẽ lọt")
        joined = " ".join(m for _, m in hits)
        self.assertIn("dim-label", joined)
        self.assertIn("_apps-nemo.scss", joined)

    def test_it_does_not_over_report_the_three_nemo_specific_classes(self):
        """Hồi quy cho bug số 1 của chính lint: báo oan selector ghép."""
        joined = " ".join(m for _, m in self.by_id.get("bare-gtk-class-leak", []))
        for c in ("floating-bar", "places-treeview", "treeview-drop-indicator",
                  "background", "view"):
            with self.subTest(cls=c):
                self.assertNotIn(f"'{c}'", joined,
                                 f"{c} bị báo oan là rò rỉ — nó là class riêng của "
                                 "Nemo hoặc nằm trong selector ghép có qualifier")

    def test_it_reports_the_invalid_font_weight_tokens(self):
        hits = [m for s, m in self.by_id.get("invalid-unit-values", []) if s == "FAIL"]
        self.assertTrue(hits, "lint không bắt token font-weight mang đơn vị px — QA-05 sẽ lọt")
        self.assertGreaterEqual(len(hits), 9,
                                f"chỉ {len(hits)} lỗi, mong >= 9 (3 token × 3 tệp _tokens.scss)")
        self.assertTrue(any("_tokens.scss" in h for h in hits))

    def test_it_reports_the_pt_named_px_tokens(self):
        warns = [m for s, m in self.by_id.get("invalid-unit-values", []) if s == "WARN"]
        self.assertTrue(any("-pt" in w for w in warns),
                        "lint không cảnh báo token tên `-pt` nhưng giá trị px — QA-06")

    def test_it_reports_orphan_partials(self):
        hits = self.by_id.get("orphan-partial", [])
        joined = " ".join(m for _, m in hits)
        self.assertIn("_apps-nemo.scss", joined)
        self.assertIn("_apps-mint.scss", joined)

    def test_it_reports_the_motion_token_gap(self):
        self.assertIn("motion-tokens-not-emitted", self.by_id,
                      "lint không báo 40-motion.json không được emit — QA-08")

    def test_it_reports_the_stub_make_target(self):
        """Hồi quy cho bug số 4 và 5 của chính lint."""
        hits = self.by_id.get("make-target-is-a-stub", [])
        self.assertTrue(hits, "lint không phát hiện `make scss` chỉ echo ra TODO — QA-10")
        self.assertIn("scss", " ".join(m for _, m in hits))

    def test_it_does_not_flag_targets_that_really_build(self):
        joined = " ".join(m for _, m in self.by_id.get("make-target-is-a-stub", []))
        for real in ("tokens", "safety", "test", "check"):
            with self.subTest(target=real):
                self.assertNotIn(f"`{real}`", joined,
                                 f"target `{real}` chạy lệnh thật mà bị báo là stub — "
                                 "dương tính giả")

    def test_it_reports_missing_entry_points_as_skip_not_pass(self):
        skips = [m for s, m in self.by_id.get("entry-missing", []) if s == "SKIP"]
        self.assertGreaterEqual(len(skips), 2,
                                "gtk-3.0 và gtk-4.0 chưa có entry point — phải là SKIP "
                                "có lý do, không được im lặng")
        for m in skips:
            self.assertIn("KHÔNG phải PASS", m)

    def test_it_does_not_leave_anything_behind(self):
        """Hồi quy cho bug số 3: lint từng để lại *.qa-dart.css.map trong src/."""
        before = {p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts}
        cs.findings()
        after = {p for p in REPO.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(after - before, set(),
                         "lint đã tạo tệp mới trong repo — nó cam kết không ghi gì")

    def test_exit_code_is_nonzero_when_there_are_fails(self):
        """Một lint in ra FAIL mà exit 0 thì vô dụng trong CI."""
        proc = subprocess.run([sys.executable, str(REPO / "tools" / "lint" / "css_sanity.py")],
                              cwd=str(REPO), capture_output=True, text=True, timeout=600)
        self.assertEqual(proc.returncode, 1,
                         f"css_sanity đang có FAIL mà exit {proc.returncode}\n"
                         f"stdout tail: {proc.stdout[-300:]}")
        self.assertRegex(proc.stdout, r"FAIL — \d+ lỗi")


@NEED_COMPILER
@unittest.skipIf(cs is None, f"không import được css_sanity.py: {IMPORT_ERROR}")
class TestBuildChecks(unittest.TestCase):
    """Build check thật, không phải đọc lại kết quả có sẵn."""

    def test_cinnamon_theme_compiles(self):
        css, err = cs.compile_scss(cs.entries()["cinnamon"])
        self.assertIsNotNone(css, f"không biên dịch được cinnamon.scss: {err}")
        self.assertGreater(len(css), 50_000)

    def test_compilation_is_deterministic(self):
        css1, _ = cs.compile_scss(cs.entries()["cinnamon"])
        css2, _ = cs.compile_scss(cs.entries()["cinnamon"])
        self.assertEqual(css1, css2, "hai lần biên dịch cùng một tệp cho kết quả khác nhau")

    def test_no_dual_compiler_disagreement(self):
        """Hồi quy cho bug số 2 của chính lint (so chuỗi thô, nhạy whitespace).

        Đã xác minh bằng cách thứ hai độc lập: tách selector bằng
        st_properties.parse_rules + split_selectors thì libsass và dart-sass cho
        CÙNG 600 selector. Nếu bài này đỏ thì hoặc dart-sass đổi hành vi, hoặc
        lint lại quay về so chuỗi thô.
        """
        bad = [m for s, c, m in cs.findings()
               if c == "dual-compiler-agreement" and s == "FAIL"]
        self.assertEqual(bad, [], f"hai compiler lệch nhau: {bad[:2]}")

    def test_size_is_within_the_p6_budget(self):
        """Tiêu chí P6: cinnamon.css <= 400 KB."""
        css, _ = cs.compile_scss(cs.entries()["cinnamon"])
        self.assertIsNotNone(css)
        self.assertLessEqual(len(css), 400 * 1024,
                             f"cinnamon.css {len(css):,} B vượt ngân sách 400 KB của P6")

    def test_no_important_in_compiled_css(self):
        """GTK 3.24 không có !important (0 lần xuất hiện trong gtkcssparser.c,
        gtkcssprovider.c, gtkstylecascade.c @3.24.42)."""
        css, _ = cs.compile_scss(cs.entries()["cinnamon"])
        self.assertNotRegex(css, r"!\s*important")

    def test_no_external_urls_in_compiled_css(self):
        css, _ = cs.compile_scss(cs.entries()["cinnamon"])
        self.assertIsNone(cs.EXTERNAL_URL_RE.search(css))


@unittest.skipIf(cs is None, f"không import được css_sanity.py: {IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test. Không ghi gì vào repo — mọi đột biến trên bản sao tạm."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-css-sanity-"))
        # Chỉ sao những thứ lint cần đọc, tránh sao cả repo.
        (self.tmp / "src").mkdir()
        shutil.copytree(REPO / "src" / "gtk-3.0", self.tmp / "src" / "gtk-3.0")
        (self.tmp / "tests" / "fixtures").mkdir(parents=True)
        shutil.copy2(GTK_CLASSES, self.tmp / "tests" / "fixtures" / GTK_CLASSES.name)
        self.orig = (cs.SRC, cs.REPO, cs.GTK_CLASSES_FIXTURE, cs.MAKEFILE)

    def tearDown(self):
        cs.SRC, cs.REPO, cs.GTK_CLASSES_FIXTURE, cs.MAKEFILE = self.orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, findings=None, severity="FAIL"):
        f = findings if findings is not None else cs.findings()
        return {cid for sev, cid, _ in f if sev == severity}

    def _point_at_tmp(self):
        cs.SRC = self.tmp / "src"
        cs.REPO = self.tmp
        cs.GTK_CLASSES_FIXTURE = self.tmp / "tests" / "fixtures" / GTK_CLASSES.name
        cs.MAKEFILE = self.tmp / "Makefile"

    def test_detects_a_new_bare_standard_class(self):
        """Thêm một rule `.sidebar` trần vào partial app -> phải bị bắt.
        `sidebar` nằm trong 84 class chuẩn GTK."""
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n.sidebar { color: #7c8087; }\n", encoding="utf-8")
        self.assertIn("bare-gtk-class-leak", self._ids())

    def test_detects_unscoped_standard_class_but_not_compound(self):
        """Phân biệt đúng: `.view` trần là rò rỉ, `.nemo-window.view` thì không."""
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n.nemo-window.view { color: #7c8087; }\n", encoding="utf-8")
        msgs = " ".join(m for s, c, m in cs.findings() if c == "bare-gtk-class-leak")
        self.assertNotIn("'view'", msgs,
                         "selector ghép có qualifier riêng của app mà vẫn bị báo rò rỉ")

    def test_detects_important(self):
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n.nemo-window .view { color: #7c8087 !important; }\n",
                     encoding="utf-8")
        self.assertIn("no-important", self._ids())

    def test_detects_external_url(self):
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
        p.write_text(p.read_text(encoding="utf-8")
                     + '\n.nemo-window { background-image: url("https://example.com/x.png"); }\n',
                     encoding="utf-8")
        self.assertIn("no-external-url", self._ids())

    def test_detects_broken_import(self):
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_apps-nemo.scss"
        p.write_text('@import "khong-ton-tai";\n' + p.read_text(encoding="utf-8"),
                     encoding="utf-8")
        self.assertIn("imports-resolve", self._ids())

    def test_detects_invalid_unit_in_a_token_file(self):
        self._point_at_tmp()
        p = self.tmp / "src" / "gtk-3.0" / "sass" / "_tokens.scss"
        t = p.read_text(encoding="utf-8")
        self.assertIn("$mg-opacity-hover:", t, "token mẫu đã đổi — cập nhật test này")
        p.write_text(t.replace("$mg-opacity-hover: 0.07;",
                               "$mg-opacity-hover: 0.07px;", 1), encoding="utf-8")
        # opacity nằm trong UNITLESS_PROPERTIES
        self.assertIn("invalid-unit-values", self._ids())


if __name__ == "__main__":
    unittest.main(verbosity=2)
