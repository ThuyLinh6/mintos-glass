"""Checksum SHA-256 doc theo stream, khong nap ca file vao RAM."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Tra ve SHA-256 hex cua file. File khong doc duoc se nem OSError."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum_file(iso_path: Path, checksum_path: Path) -> str:
    """Ghi file checksum theo dinh dang tuong thich sha256sum: '<hash>  <ten file>'."""
    value = sha256_file(iso_path)
    checksum_path.write_text(f"{value}  {iso_path.name}\n", encoding="utf-8")
    return value
