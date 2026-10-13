"""Build Environment Validator: kiem tra may build, bao loi som.

Cong cu khong tu cai goi he thong va khong sua cau hinh may phat trien.
Nhung buoc can quyen quan tri (UID 0) duoc liet ke de nguoi van hanh tu
quyet dinh, khong bao gio tu leo quyen.
"""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Cong cu ben ngoai ma quy trinh remaster dung. Khoa la ma bao cao on dinh.
REQUIRED_TOOLS: dict[str, str] = {
    "xorriso": "doc/ghi ISO va giu thong tin boot El Torito khi repack",
    "unsquashfs": "giai nen filesystem.squashfs cua live system",
    "mksquashfs": "nen lai filesystem.squashfs sau khi tich hop",
}
OPTIONAL_TOOLS: dict[str, str] = {
    "glib-compile-schemas": "bien dich GSettings schema override ngay tren may build",
    "qemu-system-x86_64": "thu boot ISO dau ra (muc Boot validation)",
    "7z": "phuong an du phong de liet ke/giai nen ISO khi khong co xorriso",
}
ADMIN_STEPS = [
    "giai nen squashfs voi quyen so huu file he thong (root/UID 0 khuyen nghi)",
    "chroot vao rootfs neu can chay lenh ben trong he thong dich",
    "mount loop ISO/squashfs neu chon duong mount thay vi extract",
]


@dataclass
class ToolStatus:
    name: str
    purpose: str
    found: bool
    path: str = ""


@dataclass
class EnvReport:
    os_name: str = ""
    os_release: str = ""
    machine: str = ""
    python_version: str = ""
    is_linux: bool = False
    euid: int | None = None
    is_root: bool = False
    disk_free_bytes: int = 0
    disk_required_bytes: int = 0
    tools: list[ToolStatus] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    admin_steps: list[str] = field(default_factory=list)
    ready_for_remaster: bool = False
    ready_for_offline_checks: bool = True
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = dict(self.__dict__)
        data["tools"] = [dict(t.__dict__) for t in self.tools]
        return data


def _disk_free(path: Path) -> int:
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    return shutil.disk_usage(probe).free


def validate_environment(
    workspace_parent: Path,
    source_size_bytes: int = 0,
) -> EnvReport:
    report = EnvReport()
    report.os_name = platform.system()
    report.os_release = platform.release()
    report.machine = platform.machine()
    report.python_version = platform.python_version()
    report.is_linux = report.os_name == "Linux"
    if hasattr(os, "geteuid"):
        report.euid = os.geteuid()
        report.is_root = report.euid == 0
    report.admin_steps = list(ADMIN_STEPS)

    for name, purpose in {**REQUIRED_TOOLS, **OPTIONAL_TOOLS}.items():
        found_path = shutil.which(name) or ""
        report.tools.append(ToolStatus(name, purpose, bool(found_path), found_path))
    report.missing_required = [
        t.name for t in report.tools if t.name in REQUIRED_TOOLS and not t.found
    ]
    report.missing_optional = [
        t.name for t in report.tools if t.name in OPTIONAL_TOOLS and not t.found
    ]

    # Can: ISO goc + ban extract + rootfs giai nen + squashfs moi + ISO ra.
    report.disk_required_bytes = max(source_size_bytes * 4, 2 * 1024**3)
    report.disk_free_bytes = _disk_free(workspace_parent)
    if report.disk_free_bytes < report.disk_required_bytes:
        report.problems.append(
            f"khong du dia trong: con {report.disk_free_bytes} byte, "
            f"can toi thieu ~{report.disk_required_bytes} byte"
        )
    if not report.is_linux:
        report.problems.append(
            f"may build khong phai Linux ({report.os_name}); remaster chi ho tro Linux"
        )
    if report.missing_required:
        report.problems.append(
            "thieu cong cu remaster bat buoc: " + ", ".join(report.missing_required)
        )
    if not report.is_root:
        report.warnings.append(
            "dang chay khong phai root: cac buoc squashfs/chroot co the that bai; "
            "cong cu se dung o buoc can quyen thay vi tu leo quyen"
        )
    if report.missing_optional:
        report.warnings.append(
            "thieu cong cu tuy chon: " + ", ".join(report.missing_optional)
        )
    report.ready_for_remaster = not report.problems
    report.ready_for_offline_checks = True
    return report
