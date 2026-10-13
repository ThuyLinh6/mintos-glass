#!/usr/bin/env python3
"""Test Tầng 1 cho ràng buộc AN TOÀN (nguyên tắc bất biến #1-#3).

Đây là nhóm test quan trọng nhất về mặt rủi ro: dự án chạy trên máy thật của
người dùng, nên mọi đường ghi/cài đặt/leo quyền đều phải bị chặn từ trong mã nguồn.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lint"))

from safety_paths import FORBIDDEN, SCAN_SUFFIXES, scan  # noqa: E402

SAFETY_LINT = ROOT / "tools" / "lint" / "safety_paths.py"


class TestSafetyLintRunsClean(unittest.TestCase):
    def test_repo_is_clean(self):
        self.assertEqual(scan(), [], "có chuỗi cấm trong mã thực thi — xem output")

    def test_lint_script_exits_zero(self):
        res = subprocess.run([sys.executable, str(SAFETY_LINT)], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


class TestForbiddenPatternsActuallyMatch(unittest.TestCase):
    """Lint sạch chỉ có ý nghĩa nếu pattern thực sự bắt được vi phạm."""

    def test_detects_privilege_escalation(self):
        for line in ("sudo cp x /usr/share/themes", "pkexec foo", "  sudo -n true"):
            with self.subTest(line=line):
                self.assertTrue(any(re.search(p, line) for p, _ in FORBIDDEN), line)

    def test_detects_package_install(self):
        for line in ("apt install plank", "apt-get install -y sassc", "dpkg -i x.deb",
                     "snap install foo", "flatpak install org.x"):
            with self.subTest(line=line):
                self.assertTrue(any(re.search(p, line) for p, _ in FORBIDDEN), line)

    def test_detects_system_paths(self):
        for line in ('open("/usr/share/themes/x")', '"/etc/dconf/db"', "p = '/opt/foo'",
                    "cp x /var/tmp"):
            with self.subTest(line=line):
                self.assertTrue(any(re.search(p, line) for p, _ in FORBIDDEN), line)

    def test_detects_dangerous_rm(self):
        for line in ("rm -rf /usr/share", "rm -rf / "):
            with self.subTest(line=line):
                self.assertTrue(any(re.search(p, line) for p, _ in FORBIDDEN), line)

    def test_allows_legitimate_project_paths(self):
        """Đường dẫn user-level của chính dự án KHÔNG được bị bắt nhầm."""
        for line in ('Path.home() / ".local/share/themes/MintOS-Glass"',
                    'state = Path.home() / ".local/state/mintos-glass"',
                    "# READONLY-OK: /usr/share/themes chỉ để giải thích trong tài liệu",
                    'rm -rf /tmp/mg-build'):
            with self.subTest(line=line):
                if "READONLY-OK" in line or "/tmp" in line:
                    continue
                self.assertFalse(any(re.search(p, line) for p, _ in FORBIDDEN), line)

    def test_readonly_marker_is_honoured_by_scanner(self):
        """Scanner phải bỏ qua dòng comment có marker READONLY-OK."""
        src = SAFETY_LINT.read_text(encoding="utf-8")
        self.assertIn("READONLY_MARKER", src)
        self.assertIn("READONLY-OK:", src)


class TestNoSystemFileWritesAnywhereInRepo(unittest.TestCase):
    def test_only_two_write_roots_are_mentioned_in_tooling(self):
        """Mọi tool phải chỉ nói về 2 đường ghi được phép."""
        allowed = (".local/share/themes", ".local/state/mintos-glass")
        offenders = []
        for path in ROOT.rglob("*.py"):
            if any(part in {".git", "__pycache__", "docs", "tests"} for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"""['"](/[a-z][^'"\s]*)['"]""", text):
                target = m.group(1)
                if target.startswith("/tmp") or target.startswith("/dev/null"):
                    continue
                if any(a in target for a in allowed):
                    continue
                offenders.append(f"{path.relative_to(ROOT)}: {target}")
        self.assertEqual(offenders, [], "tooling tham chiếu đường dẫn tuyệt đối ngoài phạm vi cho phép")

    def test_scan_covers_the_file_types_we_will_add(self):
        for suffix in (".py", ".sh", ".yml", ".json"):
            with self.subTest(suffix=suffix):
                self.assertIn(suffix, SCAN_SUFFIXES)


class TestLicenseGateForVendoring(unittest.TestCase):
    """ADR-007: KHÔNG được vendor mã GPL khi repo chưa có LICENSE."""

    def test_vendor_dir_is_empty_while_license_missing(self):
        license_exists = (ROOT / "LICENSE").exists()
        vendor = ROOT / "src" / "cinnamon" / "vendor"
        vendored = sorted(p for p in vendor.rglob("*") if p.is_file()) if vendor.exists() else []
        if not license_exists:
            self.assertEqual(
                vendored, [],
                "src/cinnamon/vendor/ đã có file nhưng repo chưa có LICENSE — vi phạm ADR-007/R7. "
                "Thêm LICENSE (GPL-3.0-or-later) TRƯỚC, rồi mới vendor.",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
