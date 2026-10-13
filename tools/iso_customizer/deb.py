"""Sinh goi Debian (.deb) bang Python thuan (ar + tar.gz).

Dinh dang .deb la mot ar archive gom: debian-binary, control.tar.gz,
data.tar.gz. Module tu xay ca ba thanh phan bang thu vien chuan, khong can
cong cu dong goi he thong, va khong cai goi len may host.

Goi nay la phuong an dong goi duoc uu tien cho thanh phan giao dien; ISO
Builder van co the staging truc tiep cung mot cay file vao rootfs khi can.
"""

from __future__ import annotations

import io
import tarfile
import time
from pathlib import Path

_AR_MAGIC = b"!<arch>\n"


def _ar_member(name: str, data: bytes, mtime: int) -> bytes:
    header = (
        f"{name:<16}{mtime:<12}{0:<6}{0:<6}{0o100644:<8}{len(data):<10}`\n"
    ).encode("ascii")
    payload = data + (b"\n" if len(data) % 2 else b"")
    return header + payload


def _tar_gz(files: dict[str, bytes], mtime: int) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name in sorted(files):
            data = files[name]
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = mtime
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def build_deb(
    staging_root: Path,
    output_path: Path,
    package: str,
    version: str,
    maintainer: str,
    description: str,
) -> dict:
    """Dong goi toan bo cay staging thanh mot file .deb. Tra ve thong tin goi."""
    staged: dict[str, bytes] = {}
    for item in sorted(staging_root.rglob("*")):
        if item.is_file():
            arcname = "./" + item.relative_to(staging_root).as_posix()
            staged[arcname] = item.read_bytes()
    if not staged:
        raise ValueError("cay staging rong, khong co gi de dong goi")
    mtime = int(time.time())
    control = (
        f"Package: {package}\n"
        f"Version: {version}\n"
        "Section: x11\n"
        "Priority: optional\n"
        "Architecture: all\n"
        f"Maintainer: {maintainer}\n"
        f"Description: {description}\n"
        " Goi giao dien MintOS Glass (theme/icon/wallpaper + mac dinh GSettings).\n"
        " Chi dat gia tri mac dinh; nguoi dung van doi duoc giao dien sau cai dat.\n"
    ).encode("utf-8")
    control_tar = _tar_gz({"./control": control}, mtime)
    data_tar = _tar_gz(staged, mtime)
    archive = (
        _AR_MAGIC
        + _ar_member("debian-binary", b"2.0\n", mtime)
        + _ar_member("control.tar.gz", control_tar, mtime)
        + _ar_member("data.tar.gz", data_tar, mtime)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(archive)
    return {
        "package": package,
        "version": version,
        "file": str(output_path),
        "bytes": len(archive),
        "data_files": len(staged),
        "note": "goi duoc sinh trong workspace; chua duoc cai thu tren may dich",
    }
