"""ISO Validator: kiem tra theo 5 muc, bao cao rieng tung muc.

- Muc 1 File: ton tai, kich thuoc, checksum.
- Muc 2 Structure: ISO9660 + El Torito bang trinh doc thuan.
- Muc 3 Content: tim tai nguyen MintOS Glass trong cay file ISO.
- Muc 4 Boot: chi danh dau trang thai; can moi truong ao hoa phu hop.
- Muc 5 Installation: chi danh dau trang thai; can cai thu tren may/VM dich.

Qua muc 1-3 khong co nghia la qua muc 4-5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .checksums import sha256_file
from .iso9660 import Iso9660Error, inspect_iso

MIN_PLAUSIBLE_ISO_BYTES = 100 * 1024 * 1024


@dataclass
class LevelResult:
    level: int
    name: str
    status: str  # PASS | FAIL | NOT TESTED | BLOCKED
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    path: str
    levels: list[LevelResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "levels": [
                {"level": lv.level, "name": lv.name, "status": lv.status, "details": lv.details}
                for lv in self.levels
            ],
            "overall": (
                "PASS (chi muc 1-3)"
                if all(lv.status == "PASS" for lv in self.levels[:3])
                else "KHONG DAT hoac CHUA KIEM TRA DU"
            ),
        }


def validate_iso(path: Path, expected_content: bool = True) -> ValidationReport:
    report = ValidationReport(path=str(path))
    level1 = LevelResult(1, "File validation", "FAIL")
    if not path.is_file():
        level1.details.append(f"file khong ton tai: {path}")
        report.levels.append(level1)
        report.levels.append(LevelResult(2, "Structure validation", "BLOCKED", ["khong co file de kiem tra"]))
        report.levels.append(LevelResult(3, "Content validation", "BLOCKED", ["khong co file de kiem tra"]))
    else:
        size = path.stat().st_size
        level1.details.append(f"size={size} byte")
        level1.details.append(f"sha256={sha256_file(path)}")
        if size >= MIN_PLAUSIBLE_ISO_BYTES:
            level1.status = "PASS"
        else:
            level1.details.append(
                f"nho hon nguong hop ly cua ISO Mint ({MIN_PLAUSIBLE_ISO_BYTES} byte); "
                "fixture test nho se FAIL muc nay mot cach co chu dich"
            )
        report.levels.append(level1)

        level2 = LevelResult(2, "Structure validation", "FAIL")
        level3 = LevelResult(3, "Content validation", "FAIL")
        try:
            info = inspect_iso(path)
            level2.details.append(f"volume_id={info.volume_id!r}")
            level2.details.append(f"files_listed={len(info.files)}")
            level2.details.append(f"el_torito={info.has_el_torito} ({info.boot_catalog_hint})")
            level2.details.append(f"casper_squashfs={info.has_path('casper/filesystem.squashfs')}")
            if info.has_el_torito and info.has_path("casper/filesystem.squashfs"):
                level2.status = "PASS"
            lowered = [name.lower() for name in info.files]
            checks = {
                "cinnamon theme (cinnamon.css)": any(
                    "mintos-glass" in n and n.endswith("cinnamon.css") for n in lowered
                ),
                "icon theme (index.theme)": any(
                    "mintos-glass" in n and n.endswith("index.theme") for n in lowered
                ),
                "wallpaper": any(
                    "mintos-glass" in n and n.endswith(".svg") and "background" in n
                    for n in lowered
                ),
            }
            for label, ok in checks.items():
                level3.details.append(f"{label}: {'co' if ok else 'THIEU'}")
            if not expected_content:
                level3.status = "PASS"
                level3.details.append("khong yeu cau noi dung MintOS Glass (ISO nguon)")
            elif all(checks.values()):
                level3.status = "PASS"
            else:
                level3.details.append(
                    "noi dung tren la liet ke tu cay ISO9660; tai nguyen ben trong "
                    "squashfs can giai nen moi xac minh duoc (xem manifest build)"
                )
        except Iso9660Error as exc:
            level2.details.append(str(exc))
            level3.status = "BLOCKED"
            level3.details.append("cau truc khong doc duoc nen khong kiem tra noi dung")
        report.levels.append(level2)
        report.levels.append(level3)

    report.levels.append(
        LevelResult(
            4,
            "Boot validation",
            "NOT TESTED",
            ["can qemu/VM va ISO that; kiem tra cau truc khong thay the duoc boot thu"],
        )
    )
    report.levels.append(
        LevelResult(
            5,
            "Installation validation",
            "NOT TESTED",
            ["can cai thu tren VM/may dich va kiem tra giao dien sau cai dat"],
        )
    )
    return report
