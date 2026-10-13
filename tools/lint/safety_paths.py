#!/usr/bin/env python3
"""Safety-path lint (ràng buộc an toàn #1-#3 của dự án).

Quét toàn bộ mã NGUỒN của repo và fail nếu thấy bằng chứng tooling có thể
chạm vào hệ thống của người dùng:

  * đường dẫn hệ thống tuyệt đối: /usr, /etc, /opt, /var, /bin, /sbin, /boot
  * leo quyền / cài gói:        sudo, pkexec, apt, apt-get, dpkg, snap, flatpak install
  * xoá đệ quy không giới hạn:   rm -rf /

NGOẠI LỆ có chủ đích (không phải hành vi ghi, chỉ là tài liệu/tham chiếu):
  * *.md            — tài liệu được phép nói về /usr/share/themes (để giải thích)
  * docs/, tests/   — tài liệu và fixture
  * chuỗi nằm trong comment bắt đầu bằng READONLY-OK:

Exit 0 nếu sạch, 1 nếu phát hiện vi phạm.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = [
    (r"\bsudo\b", "leo quyền root"),
    (r"\bpkexec\b", "leo quyền root"),
    (r"\bapt-get\b", "cài gói"),
    (r"\bapt\b\s+(install|remove|purge|update|upgrade)", "cài/gỡ gói"),
    (r"\bdpkg\b", "cài/gỡ gói"),
    (r"\bsnap\s+install\b", "cài gói"),
    (r"\bflatpak\s+install\b", "cài gói"),
    (r"rm\s+-rf\s+/(?!tmp)", "xoá đệ quy ngoài /tmp"),
    (r"""['"\s(]/usr/""", "đường dẫn hệ thống /usr"),
    (r"""['"\s(]/etc/""", "đường dẫn hệ thống /etc"),
    (r"""['"\s(]/opt/""", "đường dẫn hệ thống /opt"),
    (r"""['"\s(]/var/""", "đường dẫn hệ thống /var"),
]

SCAN_SUFFIXES = {".py", ".sh", ".bash", ".zsh", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", "docs", "tests", "design", ".github"}
ALLOWLIST_FILES = {
    # file NÀY mô tả chính các chuỗi cấm -> phải được miễn, nếu không nó tự báo lỗi
    "tools/lint/safety_paths.py",
}
READONLY_MARKER = "READONLY-OK:"


def scan() -> list[str]:
    violations: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWLIST_FILES:
            continue
        if path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts[:-1]):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") and READONLY_MARKER in stripped:
                continue
            if stripped.startswith(("//", "*", "/*")) and READONLY_MARKER in stripped:
                continue
            for pattern, why in FORBIDDEN:
                if re.search(pattern, line):
                    violations.append(f"{rel}:{lineno}: {why}  →  {stripped[:110]}")
    return violations


def main() -> int:
    violations = scan()
    if violations:
        print("SAFETY VIOLATIONS — tooling không được chạm hệ thống người dùng:", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        print(
            "\nNếu đây là tham chiếu tài liệu thực sự cần thiết, thêm marker "
            f"'{READONLY_MARKER}' vào comment cùng dòng.",
            file=sys.stderr,
        )
        return 1
    print("OK safety-paths: không có chuỗi cấm trong mã thực thi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
