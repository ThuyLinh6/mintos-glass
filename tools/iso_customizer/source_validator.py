"""Source Validator: kiem tra ISO Linux Mint nguon ma khong sua file goc.

Gioi han trung thuc: checksum tu tinh chi dung de nhan dien file va phat hien
thay doi giua cac lan build. Neu khong co file checksum chinh thuc do nguoi
dung cung cap de doi chieu, cong cu KHONG chung minh duoc ISO la ban phat
hanh chinh thuc cua Linux Mint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .checksums import sha256_file
from .errors import SourceIsoError
from .iso9660 import Iso9660Error, IsoInfo, inspect_iso

# Nhan biet phien ban chi la suy doan tu ten file / volume id / .disk/info.
# Khong co bang chung tren may dich thi ket qua van la "chua xac minh".
_MINT_NAME_RE = re.compile(r"linuxmint[-_ ]?(?P<version>\d+\.\d+)?", re.IGNORECASE)
SUPPORTED_MAJOR_MINOR = "22.3"


@dataclass
class SourceReport:
    path: str
    exists: bool = False
    size_bytes: int = 0
    readable: bool = False
    sha256: str = ""
    checksum_role: str = "chi nhan dien / phat hien thay doi (khong doi chieu chinh thuc)"
    checksum_verified_official: bool = False
    is_iso9660: bool = False
    volume_id: str = ""
    has_el_torito: bool = False
    detected_version: str = ""
    detected_arch: str = ""
    detection_basis: list[str] = field(default_factory=list)
    has_casper_squashfs: bool = False
    squashfs_paths: list[str] = field(default_factory=list)
    compatible: bool = False
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    iso: IsoInfo | None = None

    def to_dict(self) -> dict:
        data = {k: v for k, v in self.__dict__.items() if k != "iso"}
        return data


def _arch_from_name(name: str) -> str:
    lowered = name.lower()
    for token, arch in (("amd64", "amd64"), ("x86_64", "amd64"), ("64bit", "amd64"), ("i386", "i386"), ("32bit", "i386")):
        if token in lowered:
            return arch
    return ""


def validate_source(
    path: Path,
    expected_sha256: str = "",
    require_mint_22_3: bool = True,
) -> SourceReport:
    report = SourceReport(path=str(path))
    if not path.exists():
        report.problems.append(f"ISO nguon khong ton tai: {path}")
        raise SourceIsoError("; ".join(report.problems))
    if not path.is_file():
        report.problems.append(f"duong dan ISO khong phai file thuong: {path}")
        raise SourceIsoError("; ".join(report.problems))
    report.exists = True
    report.size_bytes = path.stat().st_size
    if report.size_bytes == 0:
        report.problems.append("ISO nguon rong (0 byte)")
        raise SourceIsoError("; ".join(report.problems))
    try:
        with path.open("rb") as handle:
            handle.read(1)
        report.readable = True
    except OSError as exc:
        report.problems.append(f"khong doc duoc ISO nguon: {exc}")
        raise SourceIsoError("; ".join(report.problems)) from exc

    report.sha256 = sha256_file(path)
    if expected_sha256:
        report.checksum_role = "da doi chieu voi checksum nguoi dung cung cap"
        if expected_sha256.lower() != report.sha256.lower():
            report.problems.append("checksum khong khop gia tri nguoi dung cung cap")
        else:
            report.checksum_verified_official = True
    else:
        report.warnings.append(
            "chua doi chieu checksum chinh thuc: checksum tren chi de nhan dien file"
        )

    try:
        info = inspect_iso(path)
    except Iso9660Error as exc:
        report.problems.append(str(exc))
        raise SourceIsoError("; ".join(report.problems)) from exc
    report.iso = info
    report.is_iso9660 = True
    report.volume_id = info.volume_id
    report.has_el_torito = info.has_el_torito
    report.squashfs_paths = [
        name for name in info.files if name.endswith("filesystem.squashfs")
    ]
    report.has_casper_squashfs = any(
        name.startswith("casper/") for name in report.squashfs_paths
    )
    if not report.has_el_torito:
        report.problems.append("khong phat hien El Torito boot record (sector 17)")
    if not report.has_casper_squashfs:
        report.problems.append(
            "khong tim thay casper/filesystem.squashfs trong cay ISO9660 "
            "(khong dung cau truc live ISO Linux Mint pho bien; can xac minh lai nguon)"
        )

    name_match = _MINT_NAME_RE.search(path.name)
    if name_match and name_match.group("version"):
        report.detected_version = name_match.group("version")
        report.detection_basis.append("ten file ISO")
    arch = _arch_from_name(path.name) or _arch_from_name(info.volume_id)
    if arch:
        report.detected_arch = arch
        report.detection_basis.append("ten file / volume id")
    disk_info = [n for n in info.files if n.endswith(".disk/info")]
    if disk_info:
        report.detection_basis.append(".disk/info ton tai (chua doc noi dung bang cong cu nay)")
    if not report.detected_version:
        report.warnings.append(
            "khong suy ra duoc phien ban Mint tu ten file/volume; can doi chieu thu cong"
        )
    if require_mint_22_3 and report.detected_version and report.detected_version != SUPPORTED_MAJOR_MINOR:
        report.problems.append(
            f"phien ban phat hien duoc ({report.detected_version}) khac muc tieu {SUPPORTED_MAJOR_MINOR}"
        )
    if require_mint_22_3 and not report.detected_version:
        report.warnings.append(
            f"chua chung minh duoc ISO la Linux Mint {SUPPORTED_MAJOR_MINOR}; "
            "build se bi chan neu khong tat yeu cau nay mot cach co y thuc"
        )
    report.compatible = not report.problems
    return report
