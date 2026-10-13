#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bài kiểm tra cho `tools/lint/settings_arch.py` và bằng chứng kiến trúc T17.

Chạy bằng stdlib unittest, KHÔNG cần compiler SCSS, không cần mạng:
    python3 -m unittest tests.lint.test_settings_arch -v

--------------------------------------------------------------------------
LÝ DO TỆP NÀY TỒN TẠI
--------------------------------------------------------------------------
Lần khảo sát ĐẦU (T09) kết luận "cinnamon-settings không có hook CSS riêng, 1 kết
quả duy nhất, 0 widget name riêng" và ghi thẳng kết luận đó vào comment của
`src/gtk-3.0/sass/_apps-mint.scss` mục 9. Kết luận THỰC CHẤT đúng (không có hook ở
cấp cửa sổ) nhưng SỐ LIỆU sai: quét lại toàn bộ 21.213 dòng Python ra 27 hook trên
18 tệp, gồm một CSS class riêng (`.cs-category-view`), một widget name riêng
(`#c_box`) và một widget bị KHOÁ ở priority 600 (`.night-light-temperature`).
Nguyên nhân: lần quét đó chỉ đi qua `modules/**`, bỏ sót `cinnamon-settings.py` và
`bin/**`.

Một kết luận sai nằm trong comment thì KHÔNG AI phát hiện, vì không có gì đối chiếu
nó. T17 vì vậy tách bằng chứng ra một fixture có cấu trúc và bắt tài liệu phải khớp
fixture HAI CHIỀU. Các bài dưới đây khoá chính cơ chế đó — kể cả khoá rằng lint
thật sự đỏ khi bằng chứng và tài liệu lệch nhau.
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
    import settings_arch as sa
except Exception as exc:  # pragma: no cover
    sa = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

FIXTURE = REPO / "tests" / "fixtures" / "cinnamon-settings-hooks.txt"
DOC_ARCH = REPO / "docs" / "design-system" / "settings-architecture.md"
DOC_CC = REPO / "docs" / "proposals" / "control-center.md"
ICON_THEME = REPO / "src" / "icons" / "MintOS-Glass"

# Ba hook THẬT, đã xác minh bằng cách quét toàn bộ nguồn cinnamon-settings.
THE_THREE_HOOKS = {"cs-category-view", "night-light-temperature", "c_box"}

# Builder id của cinnamon-settings.ui — KHÔNG phải hook CSS ở GTK3.
UIIDS = {"main_box", "top_bar", "toolbutton1", "header_stack", "hbox2", "search_box",
         "box2", "button_back", "image1", "stack_switcher", "main_stack",
         "side_view_sw", "viewport2", "category_box", "content_box_sw", "viewport1",
         "content_box"}


@unittest.skipIf(sa is None, f"không import được settings_arch.py: {IMPORT_ERROR}")
class TestLintIsClean(unittest.TestCase):
    def test_no_fail_no_warn_on_the_real_inputs(self):
        bad = [(s, c, m) for s, c, m in sa.findings(verbose=True) if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"lint chưa sạch: {bad[:3]}")


@unittest.skipIf(sa is None, f"không import được settings_arch.py: {IMPORT_ERROR}")
class TestFixtureShape(unittest.TestCase):
    def setUp(self):
        self.entries, self.problems = sa.parse_fixture()

    def test_fixture_parses_without_problems(self):
        self.assertEqual(self.problems, [], f"fixture sai định dạng: {self.problems[:3]}")

    def test_every_line_has_all_four_fields(self):
        for e in self.entries:
            with self.subTest(line=e["line"]):
                self.assertIn(e["kind"], sa.KINDS)
                self.assertIn(e["status"], sa.STATUSES)
                self.assertTrue(e["name"] and " " not in e["name"])
                self.assertTrue(e["evidence"])

    def test_exactly_three_real_hooks(self):
        """Con số 3 là kết quả quét TOÀN BỘ 21.213 dòng, không phải ước lượng.

        Nếu nó đổi thì hoặc upstream đổi (phải khảo sát lại) hoặc ai đó thêm một
        tuyên bố chưa kiểm chứng. Cả hai đều phải làm lint đỏ.
        """
        hooks = {e["name"] for e in self.entries
                 if e["kind"] in ("HOOK-CLASS", "HOOK-NAME")}
        self.assertEqual(hooks, THE_THREE_HOOKS)

    def test_hook_statuses_are_consistent_with_their_kind(self):
        """Hồi quy cho một lỗi thật của chính fixture: class `view` được khai là
        HOOK-CLASS nhưng mang STATUS GENERIC-CLASS — tự mâu thuẫn, và làm con số
        hook bị đếm thành 4."""
        for e in self.entries:
            if e["kind"].startswith("HOOK-"):
                with self.subTest(name=e["name"]):
                    self.assertIn(e["status"], ("OPEN", "LOCKED-600"),
                                  "HOOK-* chỉ được OPEN hoặc LOCKED-600")
            if e["kind"] == "GENERIC-CLASS":
                with self.subTest(name=e["name"]):
                    self.assertNotEqual(e["status"], "OPEN",
                                        "class GTK chung không được đánh dấu OPEN — "
                                        "style nó là style mọi app khác (việc T06)")

    def test_night_light_is_locked_and_explained(self):
        locked = {e["name"] for e in self.entries
                  if e["kind"].startswith("HOOK-") and e["status"] == "LOCKED-600"}
        self.assertEqual(locked, {"night-light-temperature"})
        locks = [e for e in self.entries if e["kind"] == "LOCK"]
        self.assertTrue(locks, "phải có mục LOCK giải thích cơ chế khoá")
        self.assertIn("night-light-trough-gradient", {e["name"] for e in locks})

    def test_every_evidence_points_at_a_location(self):
        """'nhiều chỗ' hay 'đã thấy' không phải bằng chứng."""
        for e in self.entries:
            with self.subTest(name=e["name"]):
                self.assertTrue(sa.EVIDENCE_RE.search(e["evidence"]),
                                f"bằng chứng {e['evidence']!r} không chỉ tới tệp:dòng")

    def test_all_builder_ids_are_marked_not_a_hook(self):
        marked = {e["name"] for e in self.entries if e["kind"] == "UIID"}
        self.assertTrue(UIIDS <= marked,
                        f"thiếu builder id trong fixture: {sorted(UIIDS - marked)}")
        for e in self.entries:
            if e["kind"] == "UIID" and e["name"] in UIIDS:
                with self.subTest(name=e["name"]):
                    self.assertEqual(e["status"], "NOT-A-HOOK")

    def test_search_box_is_recorded_as_a_real_search_not_a_fake_one(self):
        """Yêu cầu Scope A: 'không tạo ô tìm kiếm giả'. Cách thoả nó là KHÔNG tạo gì
        cả — ô tìm kiếm đã có sẵn và hoạt động. Fixture phải ghi điều đó."""
        names = {e["name"] for e in self.entries}
        self.assertIn("search_box-is-real-search", names)
        txt = FIXTURE.read_text(encoding="utf-8")
        self.assertIn("onSearchTextChanged", txt)
        self.assertIn("strip_accents", txt,
                      "phải ghi cả việc lọc BỎ DẤU — đó là bằng chứng search hoạt "
                      "động thật chứ không phải một entry trang trí")

    def test_three_tiers_are_recorded_with_counts(self):
        tiers = {e["name"]: e["evidence"] for e in self.entries if e["kind"] == "TIER"}
        for key, want in (("tier-1-count", 31), ("tier-2-count", 3)):
            with self.subTest(tier=key):
                self.assertIn(key, tiers)
                m = re.match(r"(\d+)-(.+)", tiers[key])
                self.assertIsNotNone(m, f"{key} phải có dạng <số>-<vị trí>")
                self.assertEqual(int(m.group(1)), want)

    def test_bluetooth_gap_is_recorded(self):
        names = {e["name"] for e in self.entries}
        self.assertIn("bluetooth", names)
        self.assertIn("bluetooth-requires-external", names)
        ev = {e["name"]: e["evidence"] for e in self.entries}
        self.assertIn("KHÔNG-CÓ", ev["bluetooth"],
                      "phải ghi rõ là KHÔNG có applet bluetooth bundled")


@unittest.skipIf(sa is None, f"không import được settings_arch.py: {IMPORT_ERROR}")
class TestDocsMatchTheEvidence(unittest.TestCase):
    def setUp(self):
        self.arch = DOC_ARCH.read_text(encoding="utf-8")
        self.cc = DOC_CC.read_text(encoding="utf-8")
        self.all = self.arch + "\n" + self.cc
        self.entries, _ = sa.parse_fixture()

    def test_both_docs_exist(self):
        for d in (DOC_ARCH, DOC_CC):
            with self.subTest(doc=d.name):
                self.assertTrue(d.exists())

    def test_every_hook_and_lock_and_applet_is_documented(self):
        for e in self.entries:
            if e["kind"] in ("HOOK-CLASS", "HOOK-NAME", "LOCK", "APPLET"):
                with self.subTest(name=e["name"]):
                    self.assertIn(e["name"], self.all,
                                  "có trong fixture nhưng tài liệu không nhắc — bằng "
                                  "chứng và tài liệu đang trôi ra khỏi nhau")

    def test_no_builder_id_is_written_as_a_css_selector(self):
        """Bẫy GTK3 đã xác minh: gtkwidget.c:14053-14058 chỉ g_object_set_qdata_full,
        KHÔNG gọi gtk_widget_set_name. Nên viết `#search_box` trong tài liệu là hứa
        một thứ không tồn tại."""
        for name, txt in (("settings-architecture.md", self.arch),
                          ("control-center.md", self.cc)):
            for m in re.finditer(r"(?<![\w-])#([a-z][a-z0-9_]*)", txt):
                ident = m.group(1)
                with self.subTest(doc=name, ident=ident):
                    if ident != "c_box":      # c_box là widget name THẬT
                        self.assertNotIn(ident, UIIDS,
                                         f"{name} viết `#{ident}` như một selector — "
                                         "đó là GtkBuilder id, CSS không nhắm được")

    def test_c_box_is_the_only_hash_selector_claimed(self):
        """Ngược lại: `#c_box` PHẢI được tuyên bố, vì nó là hook thật duy nhất dạng
        widget name và là cách duy nhất chạm tới 3 panel C của tầng 2."""
        self.assertIn("#c_box", self.all)
        self.assertIn("set_name", self.all,
                      "phải kèm bằng chứng Gtk.Box.set_name() = gtk_widget_set_name() "
                      "thật, khác với builder id")

    def test_docs_separate_verified_from_unverified(self):
        """Nguyên tắc 7 của Agent 6: không có môi trường runtime thì phải ghi rõ cái
        gì chưa kiểm."""
        for name, txt in (("settings-architecture.md", self.arch),
                          ("control-center.md", self.cc)):
            with self.subTest(doc=name):
                self.assertRegex(txt, r"(?i)chưa (kiểm chứng|xác minh|kiểm tra)")
                self.assertRegex(txt, r"(?i)đã xác minh|ĐÃ xác minh")
                self.assertRegex(txt, r"(?i)không tuyên bố|KHÔNG tuyên bố")

    def test_no_install_commands_anywhere(self):
        """Nguyên tắc 2.6 + tiêu chí Done #4 của T11/T17: không cài thêm phần mềm."""
        for name, txt in (("settings-architecture.md", self.arch),
                          ("control-center.md", self.cc)):
            with self.subTest(doc=name):
                self.assertNotRegex(
                    txt,
                    r"(?m)^\s*(?:\$|#)?\s*(?:sudo\s+)?(?:apt|apt-get|dnf|yum|pacman|"
                    r"zypper|flatpak|snap)\s")
                for m in re.finditer(r"```[^\n]*\n(.*?)```", txt, re.S):
                    self.assertNotRegex(m.group(1),
                                        r"(?i)\b(?:apt|apt-get|dnf|pacman|flatpak|snap)"
                                        r"\s+install\b")

    def test_no_fake_button_claim_and_no_new_applet_this_task(self):
        """Hai ràng buộc người dùng đã chốt: không nút giả, và CHƯA build applet."""
        self.assertRegex(self.cc, r"(?i)nút giả")
        self.assertRegex(self.cc, r"(?i)chưa được viết|chưa viết|CHƯA TRIỂN KHAI")
        self.assertRegex(self.cc, r"(?i)không build applet|CHƯA build applet|"
                                  r"không viết applet")

    def test_brightness_is_recorded_as_already_available(self):
        """Phát hiện đáng giá nhất của khảo sát Control Center: ĐỘ SÁNG đã có sẵn
        trong power@cinnamon.org, không cần viết mới. Nếu ai đó đề xuất tự viết
        backend độ sáng thì tài liệu này phải là chỗ chặn lại."""
        self.assertIn("BrightnessSlider", self.cc)
        self.assertIn("org.cinnamon.SettingsDaemon.Power.Screen", self.cc)

    def test_bluetooth_honesty_is_stated(self):
        self.assertIn("blueberry", self.cc)
        self.assertRegex(self.cc, r"(?i)không khả dụng")
        self.assertRegex(self.cc, r"(?i)KHÔNG.{0,40}(vẽ|tạo).{0,40}nút Bluetooth")

    def test_t06_dependency_is_stated_not_hidden(self):
        """Phải nói rõ Settings phụ thuộc T06 và T06 CHƯA tồn tại — không được ngụ ý
        là giao diện Settings đã xong."""
        self.assertRegex(self.arch, r"T06")
        self.assertRegex(self.arch, r"(?i)chưa tồn tại|chưa có")

    def test_the_corrected_t09_claim_is_recorded(self):
        """Tài liệu phải ghi lại rằng kết luận cũ SAI VỀ SỐ LIỆU nhưng ĐÚNG VỀ BẢN
        CHẤT — nếu chỉ ghi 'đã sửa' thì bài học mất."""
        self.assertRegex(self.arch, r"27 hook")
        self.assertRegex(self.arch, r"(?i)kết luận.{0,40}(thực chất|đúng)")
        self.assertRegex(self.arch, r"(?i)số liệu.{0,20}sai|sai.{0,20}số liệu")


@unittest.skipIf(sa is None, f"không import được settings_arch.py: {IMPORT_ERROR}")
class TestCrossCheckWithIconTheme(unittest.TestCase):
    def test_cs_category_view_is_not_an_icon(self):
        """Dương tính giả đã gặp thật: grep thô mẫu `cs-*` để lấy tên icon cho T15 đã
        bắt cả `cs-category-view`, vốn là CSS STYLE CLASS
        (cinnamon-settings.py:288), không phải tên icon."""
        self.assertEqual(sorted(ICON_THEME.rglob("cs-category-view.svg")), [],
                         "tồn tại cs-category-view.svg trong icon theme — nó là CSS "
                         "class, không phải icon")

    def test_all_47_cs_icons_exist_and_cs_category_view_is_not_among_them(self):
        names = {p.stem for p in ICON_THEME.rglob("cs-*.svg")}
        self.assertEqual(len(names), 47, f"số icon cs-* khác 47: {len(names)}")
        self.assertNotIn("cs-category-view", names)
        self.assertIn("cs-cat-appearance", names)
        self.assertIn("cs-cat-admin", names)

    def test_icon_names_are_a_superset_consistent_with_fixture_tiers(self):
        """Các icon của tầng 2 và tầng 3 cũng phải có — chúng vẫn hiện trong danh
        sách Settings dù theme không sở hữu TRANG của chúng."""
        names = {p.stem for p in ICON_THEME.rglob("cs-*.svg")}
        for icon in ("cs-network", "cs-color", "cs-tablet",          # tầng 2
                     "cs-bluetooth", "cs-printer", "cs-user-accounts",
                     "cs-login", "cs-firewall", "cs-language",
                     "cs-input-method", "cs-drivers", "cs-sources"):  # tầng 3
            with self.subTest(icon=icon):
                self.assertIn(icon, names)


@unittest.skipIf(sa is None, f"không import được settings_arch.py: {IMPORT_ERROR}")
class TestLintActuallyFails(unittest.TestCase):
    """Mutation test trên bản sao tạm. Không ghi gì vào repo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="mg-settings-arch-"))
        self.fx = self.tmp / "hooks.txt"
        shutil.copy2(FIXTURE, self.fx)
        self.docs = []
        for src in (DOC_ARCH, DOC_CC):
            dst = self.tmp / src.name
            shutil.copy2(src, dst)
            self.docs.append(dst)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ids(self, findings, severity="FAIL"):
        return {cid for sev, cid, _ in findings if sev == severity}

    def _run(self):
        return sa.findings(fixture=self.fx, docs=self.docs)

    def _edit(self, path, old, new):
        t = path.read_text(encoding="utf-8")
        self.assertIn(old, t, f"chuỗi cần đột biến không có trong {path.name}")
        path.write_text(t.replace(old, new, 1), encoding="utf-8")

    def test_baseline_is_clean(self):
        bad = [(s, c, m) for s, c, m in self._run() if s in ("FAIL", "WARN")]
        self.assertEqual(bad, [], f"bản sao của inputs thật mà đã báo lỗi: {bad[:3]}")

    def test_detects_a_fourth_claimed_hook(self):
        self._edit(self.fx,
                   "HOOK-NAME  c_box                     bin/SettingsWidgets.py:286               OPEN",
                   "HOOK-NAME  c_box                     bin/SettingsWidgets.py:286               OPEN\n"
                   "HOOK-CLASS cs-invented-hook          cinnamon-settings.py:999               OPEN")
        self.assertIn("hook-count", self._ids(self._run()))

    def test_detects_hook_with_contradictory_status(self):
        """Hồi quy cho lỗi thật của fixture: `view` khai HOOK-CLASS + GENERIC-CLASS."""
        self._edit(self.fx,
                   "GENERIC-CLASS view                 cinnamon-settings.py:289                 GENERIC-CLASS",
                   "HOOK-CLASS view                      cinnamon-settings.py:289                 GENERIC-CLASS")
        self.assertIn("fixture-format", self._ids(self._run()))

    def test_detects_generic_class_marked_open(self):
        self._edit(self.fx,
                   "GENERIC-CLASS dim-label              8-lần-trên-6-module                      GENERIC-CLASS",
                   "GENERIC-CLASS dim-label              8-lần-trên-6-module                      OPEN")
        self.assertIn("fixture-format", self._ids(self._run()))

    def test_detects_unlocking_the_night_light_widget(self):
        """Nếu ai đó đổi LOCKED-600 thành OPEN thì tài liệu sẽ hứa style được một
        widget mà app khoá ở priority 600. Đó là lời hứa sai."""
        self._edit(self.fx,
                   "HOOK-CLASS night-light-temperature   modules/cs_nightlight.py:50              LOCKED-600",
                   "HOOK-CLASS night-light-temperature   modules/cs_nightlight.py:50              OPEN")
        self.assertIn("lock-explained", self._ids(self._run()))

    def test_detects_malformed_fixture_line(self):
        self._edit(self.fx,
                   "HOOK-NAME  c_box                     bin/SettingsWidgets.py:286               OPEN",
                   "HOOK-NAME  c_box  OPEN")     # thiếu cột bằng chứng
        self.assertIn("fixture-format", self._ids(self._run()))

    def test_detects_vague_evidence(self):
        self._edit(self.fx,
                   "HOOK-CLASS cs-category-view          cinnamon-settings.py:288                 OPEN",
                   "HOOK-CLASS cs-category-view          nhiều-chỗ                               OPEN")
        self.assertIn("evidence-is-specific", self._ids(self._run()))

    def test_detects_changed_tier_count(self):
        self._edit(self.fx, "TIER tier-1-count                    31-tệp-modules/cs_*.py",
                          "TIER tier-1-count                    29-tệp-modules/cs_*.py")
        self.assertIn("tier-counts", self._ids(self._run()))

    def test_detects_tier_count_without_location(self):
        self._edit(self.fx, "TIER tier-1-count                    31-tệp-modules/cs_*.py",
                          "TIER tier-1-count                    31")
        self.assertIn("tier-counts", self._ids(self._run()))

    def test_detects_builder_id_written_as_selector_in_a_doc(self):
        """Bẫy GTK3: tài liệu mà hứa `#search_box` là selector thì sẽ có người viết
        CSS theo đó và nó KHÔNG BAO GIỜ khớp."""
        arch = next(d for d in self.docs if d.name == "settings-architecture.md")
        self._edit(arch, "Ô tìm kiếm là THẬT",
                   "Style ô tìm kiếm bằng selector #search_box. Ô tìm kiếm là THẬT")
        self.assertIn("docs-no-uiid-as-selector", self._ids(self._run()))

    def test_detects_undocumented_hook(self):
        """Hook có trong fixture nhưng biến mất khỏi tài liệu."""
        for d in self.docs:
            t = d.read_text(encoding="utf-8").replace("cs-category-view", "cs-REDACTED")
            d.write_text(t, encoding="utf-8")
        self.assertIn("docs-cover-fixture", self._ids(self._run()))

    def test_detects_install_command_in_a_doc(self):
        cc = next(d for d in self.docs if d.name == "control-center.md")
        self._edit(cc, "## 5. PHƯƠNG ÁN cần duyệt",
                   "Cài backend:\n\n```bash\nsudo apt install blueberry\n```\n\n"
                   "## 5. PHƯƠNG ÁN cần duyệt")
        self.assertIn("no-install-commands", self._ids(self._run()))

    def test_detects_missing_unverified_section(self):
        arch = next(d for d in self.docs if d.name == "settings-architecture.md")
        t = arch.read_text(encoding="utf-8")
        arch.write_text(re.sub(r"(?is)## 9\. Trạng thái kiểm chứng.*", "", t),
                        encoding="utf-8")
        self.assertIn("verified-vs-unverified", self._ids(self._run()))

    def test_detects_missing_doc(self):
        # KHÔNG lọc bỏ đường dẫn đã xoá khỏi self.docs. Bản đầu của bài này làm vậy
        # và hậu quả là `docs-exist` không bao giờ được báo (danh sách chỉ còn những
        # tệp tồn tại), trong khi ba bài khác lại đỏ vì tài liệu còn lại không phủ
        # đủ — tức bài test pass/fail vì lý do SAI. Phải truyền đúng đường dẫn đã
        # mất để lint có cơ hội phát hiện.
        (self.tmp / "control-center.md").unlink()
        self.assertIn("docs-exist", self._ids(self._run()))

    def test_detects_fake_cs_category_view_icon(self):
        """Dương tính giả đã gặp thật ở T15: grep thô mẫu `cs-*` để lấy tên icon đã
        bắt cả `cs-category-view`, vốn là CSS STYLE CLASS.

        BẢN ĐẦU của bài này tạo tệp đó thẳng vào icon theme THẬT của repo rồi xoá
        trong finally — mâu thuẫn với chính nguyên tắc "không ghi gì vào repo" của
        lớp này, và nếu tiến trình bị giết giữa chừng thì để lại rác đã được git
        nhìn thấy. Đã đổi sang bản sao tạm.
        """
        icon_tmp = self.tmp / "icons"
        (icon_tmp / "scalable" / "apps").mkdir(parents=True)
        (icon_tmp / "scalable" / "apps" / "cs-category-view.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"/>\n', encoding="utf-8")
        ids = self._ids(sa.findings(fixture=self.fx, docs=self.docs, icon_dir=icon_tmp))
        self.assertIn("cs-category-view-is-not-an-icon", ids)
        # Và khẳng định ngược: KHÔNG có tệp đó thì sạch.
        (icon_tmp / "scalable" / "apps" / "cs-category-view.svg").unlink()
        self.assertNotIn("cs-category-view-is-not-an-icon",
                         self._ids(sa.findings(fixture=self.fx, docs=self.docs,
                                               icon_dir=icon_tmp)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
