"""Sinh ISO9660 toi thieu lam fixture test.

Day CHI la file mau phuc vu test muc File/Structure, khong phai ISO
Linux Mint that, khong boot duoc va khong duoc dung de tuyen bo build
thanh cong. Cau truc sector khop voi trinh doc trong
tools/iso_customizer/iso9660.py: PVD sector 16, El Torito sector 17,
terminator sector 18, root dir sector 20, casper dir sector 21.
"""

from __future__ import annotations

import struct
from pathlib import Path

SECTOR = 2048


def _both16(value: int) -> bytes:
    return struct.pack("<H", value) + struct.pack(">H", value)


def _both32(value: int) -> bytes:
    return struct.pack("<I", value) + struct.pack(">I", value)


def _record(extent: int, size: int, is_dir: bool, name: bytes) -> bytes:
    name_len = len(name)
    length = 33 + name_len + (0 if name_len % 2 == 1 else 1)
    record = bytearray(length)
    record[0] = length
    record[2:10] = _both32(extent)
    record[10:18] = _both32(size)
    record[18:25] = bytes([124, 1, 1, 0, 0, 0, 0])
    record[25] = 0x02 if is_dir else 0x00
    record[28:32] = _both16(1)
    record[32] = name_len
    record[33 : 33 + name_len] = name
    return bytes(record)


def _dir_sector(entries: list[bytes]) -> bytes:
    sector = bytearray(SECTOR)
    offset = 0
    for entry in entries:
        sector[offset : offset + len(entry)] = entry
        offset += len(entry)
    return bytes(sector)


def make_fixture_iso(path: Path, volume_id: str = "Linux Mint 22.3 Cinnamon 64-bit") -> Path:
    total_sectors = 24
    image = bytearray(total_sectors * SECTOR)

    def place(sector: int, data: bytes) -> None:
        image[sector * SECTOR : sector * SECTOR + len(data)] = data

    squash_content = b"FAKE-SQUASHFS-FOR-STRUCTURE-TESTS-ONLY"
    root_entries = [
        _record(20, SECTOR, True, b"\x00"),
        _record(20, SECTOR, True, b"\x01"),
        _record(21, SECTOR, True, b"CASPER"),
    ]
    root_sector = _dir_sector(root_entries)
    casper_sector = _dir_sector(
        [
            _record(21, SECTOR, True, b"\x00"),
            _record(20, SECTOR, True, b"\x01"),
            _record(22, len(squash_content), False, b"FILESYSTEM.SQUASHFS;1"),
        ]
    )

    pvd = bytearray(SECTOR)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[6] = 1
    pvd[8:40] = b"PYTHON FIXTURE".ljust(32, b" ")
    pvd[40:72] = volume_id.encode("ascii")[:32].ljust(32, b" ")
    pvd[80:88] = _both32(total_sectors)
    pvd[120:124] = _both16(1)
    pvd[124:128] = _both16(1)
    pvd[128:132] = _both16(SECTOR)
    pvd[132:140] = _both32(10)
    root_record = _record(20, SECTOR, True, b"\x00")
    pvd[156 : 156 + len(root_record)] = root_record
    place(16, bytes(pvd))

    boot = bytearray(SECTOR)
    boot[0] = 0
    boot[1:6] = b"CD001"
    boot[6] = 1
    boot[7:39] = b"EL TORITO SPECIFICATION".ljust(32, b"\x00")
    boot[71:75] = struct.pack("<I", 19)
    place(17, bytes(boot))

    terminator = bytearray(SECTOR)
    terminator[0] = 255
    terminator[1:6] = b"CD001"
    terminator[6] = 1
    place(18, bytes(terminator))

    place(20, root_sector)
    place(21, casper_sector)
    place(22, squash_content)
    path.write_bytes(bytes(image))
    return path
