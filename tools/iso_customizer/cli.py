"""CLI cua MintOS Glass ISO Customizer.

Cach chay (tu thu muc goc repository, khong can cai dat):
  python3 -m tools.iso_customizer --help
  python3 -m tools.iso_customizer check-environment
  python3 -m tools.iso_customizer inspect-source /path/to/linuxmint.iso
  python3 -m tools.iso_customizer build --source /path/to/linuxmint.iso \\
      --output /path/to/mintos-glass.iso
  python3 -m tools.iso_customizer validate /path/to/mintos-glass.iso
  python3 -m tools.iso_customizer clean --workspace <dir> --confirm DELETE

Ma thoat: 0 thanh cong; 2 loi dau vao; 3 moi truong chua san sang;
4 ISO nguon khong hop le; 5 tich hop chua san sang; 6 buoc build that bai.
Khong lenh nao tu leo quyen, tu cai goi hay ghi de file da ton tai.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path

from . import __version__
from .env_validator import validate_environment
from .errors import CustomizerError
from .iso_builder import run_build
from .iso_validator import validate_iso
from .source_validator import validate_source
from .workspace import clean_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE_PARENT = Path("build-iso-workspaces")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mintos-glass-iso",
        description="MintOS Glass ISO Customizer: remaster ISO Linux Mint voi giao dien MintOS Glass.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-environment", help="kiem tra may build va cong cu remaster")

    inspect_cmd = sub.add_parser("inspect-source", help="kiem tra ISO nguon (khong sua file goc)")
    inspect_cmd.add_argument("source", type=Path)
    inspect_cmd.add_argument("--expected-sha256", default="", help="checksum doi chieu do ban cung cap")
    inspect_cmd.add_argument("--json", action="store_true", help="in JSON thay vi text")

    build_cmd = sub.add_parser("build", help="build ISO MintOS Glass trong workspace rieng")
    build_cmd.add_argument("--source", type=Path, required=True)
    build_cmd.add_argument("--output", type=Path, required=True)
    build_cmd.add_argument("--workspace-parent", type=Path, default=DEFAULT_WORKSPACE_PARENT)
    build_cmd.add_argument("--build-id", default="", help="dinh danh workspace (mac dinh: thoi gian UTC)")
    build_cmd.add_argument("--force", action="store_true", help="cho phep ghi de file dau ra da ton tai")
    build_cmd.add_argument(
        "--allow-partial",
        action="store_true",
        help="tiep tuc du thieu thanh phan (vd chua co theme GTK); ISO se bi ghi ro la thieu",
    )
    build_cmd.add_argument("--no-deb", action="store_true", help="khong sinh goi Debian trong workspace")
    build_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="chi validate + staging + manifest; chua extract/repack ISO",
    )

    validate_cmd = sub.add_parser("validate", help="kiem tra ISO theo 5 muc (1-3 chay that, 4-5 bao chua test)")
    validate_cmd.add_argument("iso", type=Path)
    validate_cmd.add_argument("--source-iso", action="store_true", help="day la ISO nguon (khong yeu cau noi dung MintOS Glass)")

    clean_cmd = sub.add_parser("clean", help="xoa mot workspace cua cong cu (can --confirm DELETE)")
    clean_cmd.add_argument("--workspace-parent", type=Path, default=DEFAULT_WORKSPACE_PARENT)
    clean_cmd.add_argument("--workspace", type=Path, required=True)
    clean_cmd.add_argument("--confirm", required=True, help="phai dung cau DELETE")
    return parser


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check-environment":
            report = validate_environment(DEFAULT_WORKSPACE_PARENT)
            _print_json(report.to_dict())
            print(
                "ready_for_remaster=" + str(report.ready_for_remaster),
                file=sys.stderr,
            )
            return 0 if report.ready_for_remaster else 3
        if args.command == "inspect-source":
            report = validate_source(args.source, expected_sha256=args.expected_sha256)
            if args.json:
                _print_json(report.to_dict())
            else:
                print(f"source: {report.path}")
                print(f"size: {report.size_bytes} byte")
                print(f"sha256: {report.sha256}")
                print(f"checksum: {report.checksum_role}")
                print(f"iso9660: {report.is_iso9660} volume_id={report.volume_id!r}")
                print(f"el_torito: {report.has_el_torito}")
                print(f"version_detected: {report.detected_version or '(chua xac dinh)'}")
                print(f"arch_detected: {report.detected_arch or '(chua xac dinh)'}")
                print(f"squashfs: {report.squashfs_paths}")
                print(f"compatible: {report.compatible}")
                for problem in report.problems:
                    print(f"PROBLEM: {problem}")
                for warning in report.warnings:
                    print(f"WARNING: {warning}")
            return 0 if report.compatible else 4
        if args.command == "build":
            manifest = run_build(
                source_iso=args.source,
                output_iso=args.output,
                workspace_parent=args.workspace_parent,
                repo_root=REPO_ROOT,
                force=args.force,
                allow_partial=args.allow_partial,
                make_deb=not args.no_deb,
                dry_run=args.dry_run,
                build_id=args.build_id,
            )
            _print_json(manifest)
            return 0
        if args.command == "validate":
            report = validate_iso(args.iso, expected_content=not args.source_iso)
            _print_json(report.to_dict())
            levels = report.to_dict()["levels"]
            failed = any(lv["status"] == "FAIL" for lv in levels[:3])
            return 1 if failed else 0
        if args.command == "clean":
            removed = clean_workspace(args.workspace_parent, args.workspace, args.confirm)
            print(f"da xoa workspace: {removed}")
            return 0
    except CustomizerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        manifest = getattr(exc, "manifest", None)
        if manifest:
            _print_json(manifest)
        return exc.exit_code
    parser.error("lenh khong hop le")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
