"""Doc ISO9660 + El Torito o muc cau truc bang Python thuan.

Module nay khong mount, khong ghi va khong sua ISO. No chi doc:
- Primary Volume Descriptor (sector 16): volume id, kich thuoc, root record.
- Boot Record (sector 17) de phat hien El Torito.
- Cay thu muc ISO9660 du de liet ke file (ten duoc chuan hoa thanh chu thuong,
  bo hau to phien ban ';1'). Rock Ridge / Joliet khong duoc giai ma; viec tim
  kiem noi dung dung ten chuan hoa nen van ap dung duoc cho ISO Mint thong
  thuong, nhung day khong phai trinh phan tich ISO9660 day du.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path

SECTOR = 2048
_MAGIC = b"CD001"


class Iso9660Error(ValueError):
    """File khong phai ISO9660 doc duoc o muc cau truc toi thieu."""


@dataclass
class DirRecord:
    name: str
    extent: int
    size: int
    is_dir: bool


@dataclass
class IsoInfo:
    volume_id: str = ""
    volume_size_bytes: int = 0
    block_size: int = SECTOR
    has_el_torito: bool = False
    boot_catalog_hint: str = ""
    files: list[str] = field(default_factory=list)

    def has_path(self, suffix: str) -> bool:
        wanted = suffix.lower().strip("/")
        return any(name == wanted or name.endswith("/" + wanted) for name in self.files)


def _both16(data: bytes) -> int:
    return struct.unpack("<H", data[:2])[0]


def _both32(data: bytes) -> int:
    return struct.unpack("<I", data[:4])[0]


def _parse_record(raw: bytes, offset: int) -> tuple[DirRecord | None, int]:
    length = raw[offset]
    if length == 0:
        return None, 0
    record = raw[offset : offset + length]
    if len(record) < 34:
        return None, length
    extent = _both32(record[2:10])
    size = _both32(record[10:18])
    flags = record[25]
    name_len = record[32]
    raw_name = record[33 : 33 + name_len]
    if raw_name == b"\x00":
        name = "."
    elif raw_name == b"\x01":
        name = ".."
    else:
        name = raw_name.decode("ascii", errors="replace")
        if ";" in name:
            name = name.split(";", 1)[0]
        name = name.lower()
    return DirRecord(name=name, extent=extent, size=size, is_dir=bool(flags & 0x02)), length


def _read_extent(handle, extent: int, size: int) -> bytes:
    handle.seek(extent * SECTOR)
    return handle.read(size)


def _walk(handle, extent: int, size: int, prefix: str, out: list[str], depth: int) -> None:
    if depth > 32:
        return
    raw = _read_extent(handle, extent, size)
    offset = 0
    while offset < len(raw):
        if raw[offset] == 0:
            # Padding toi het sector; nhay sang sector ke tiep neu con du lieu.
            next_sector = ((offset // SECTOR) + 1) * SECTOR
            if next_sector >= len(raw):
                break
            offset = next_sector
            continue
        record, length = _parse_record(raw, offset)
        if length <= 0:
            break
        offset += length
        if record is None or record.name in (".", ".."):
            continue
        path = f"{prefix}{record.name}"
        if record.is_dir:
            _walk(handle, record.extent, record.size, path + "/", out, depth + 1)
        else:
            out.append(path)


def inspect_iso(path: Path) -> IsoInfo:
    """Doc thong tin cau truc cua ISO. Nem Iso9660Error neu khong hop le."""
    if not path.is_file():
        raise Iso9660Error(f"khong tim thay file ISO: {path}")
    size = path.stat().st_size
    if size < 17 * SECTOR or size % SECTOR != 0:
        raise Iso9660Error(
            f"kich thuoc ISO khong hop le cho ISO9660: {size} byte "
            f"(can >= {17 * SECTOR} va chia het cho {SECTOR})"
        )
    info = IsoInfo()
    with path.open("rb") as handle:
        handle.seek(16 * SECTOR)
        pvd = handle.read(SECTOR)
        if len(pvd) < SECTOR or pvd[1:6] != _MAGIC or pvd[0] != 1:
            raise Iso9660Error("thieu Primary Volume Descriptor (magic CD001 o sector 16)")
        info.volume_id = pvd[40:72].decode("ascii", errors="replace").strip()
        info.block_size = _both16(pvd[128:132]) or SECTOR
        info.volume_size_bytes = _both32(pvd[80:88]) * info.block_size
        root, _ = _parse_record(pvd, 156)
        # Boot record o sector 17 (neu co).
        handle.seek(17 * SECTOR)
        boot = handle.read(SECTOR)
        if len(boot) == SECTOR and boot[1:6] == _MAGIC and boot[0] == 0:
            identifier = boot[7:39]
            if identifier.startswith(b"EL TORITO SPECIFICATION"):
                info.has_el_torito = True
                catalog_block = struct.unpack("<I", boot[71:75])[0]
                info.boot_catalog_hint = f"boot catalog tai block {catalog_block}"
        if root is not None:
            _walk(handle, root.extent, root.size, "", info.files, 0)
    info.files.sort()
    return info
