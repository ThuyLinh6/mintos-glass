"""ISO Workspace Manager: workspace rieng cho tung lan build.

An toan:
- Chi ghi ben trong workspace do module nay tao (co file marker).
- Khong bao gio xoa file nguon hoac thu muc ngoai workspace.
- Don dep chi xay ra qua clean_workspace voi cau xac nhan tuong minh va
  kiem tra marker + duong dan nam trong parent da chi dinh.
- Build that bai thi giu nguyen workspace de chan doan.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from . import WORKSPACE_MARKER
from .errors import UsageError

WORKSPACE_DIRS = [
    "source",
    "extract/iso",
    "extract/rootfs",
    "overlay",
    "staging",
    "package",
    "output",
    "logs",
]


@dataclass
class Workspace:
    root: Path
    build_id: str

    def path(self, relative: str) -> Path:
        return self.root / relative

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def log_path(self) -> Path:
        return self.root / "logs" / "build.log"


def create_workspace(parent: Path, build_id: str = "") -> Workspace:
    parent = parent.expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    stamp = build_id or time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    root = parent / f"mintos-glass-build-{stamp}"
    if root.exists():
        raise UsageError(f"workspace da ton tai, chon build id khac: {root}")
    for relative in WORKSPACE_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / WORKSPACE_MARKER).write_text(
        "MintOS Glass ISO Customizer workspace. Chi don dep bang CLI cua cong cu.\n",
        encoding="utf-8",
    )
    return Workspace(root=root, build_id=stamp)


def append_log(workspace: Workspace, message: str) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with workspace.log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def write_manifest(workspace: Workspace, manifest: dict) -> Path:
    workspace.manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return workspace.manifest_path


def clean_workspace(
    parent: Path,
    workspace_root: Path,
    confirmation: str,
) -> Path:
    """Xoa mot workspace. Bat buoc confirmation == 'DELETE' va co marker."""
    if confirmation != "DELETE":
        raise UsageError("don dep yeu cau --confirm DELETE (go hoa thuong dung cau)")
    parent_resolved = parent.expanduser().resolve()
    target = workspace_root.expanduser().resolve()
    if target == parent_resolved or parent_resolved not in target.parents:
        raise UsageError(
            f"tu choi xoa: {target} khong nam trong workspace parent {parent_resolved}"
        )
    if not (target / WORKSPACE_MARKER).is_file():
        raise UsageError(
            f"tu choi xoa: {target} khong co marker {WORKSPACE_MARKER} "
            "(khong chung minh duoc day la workspace cua cong cu)"
        )
    shutil.rmtree(target)
    return target
