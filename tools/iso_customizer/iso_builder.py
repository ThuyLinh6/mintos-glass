"""ISO Builder: dieu phoi toan bo lan build trong mot workspace rieng.

Thu tu bat buoc (dung an toan ngay khi mot buoc bat buoc that bai):
1. Source Validator (khong sua ISO goc; checksum truoc va sau de chung minh).
2. Build Environment Validator (chan som khi thieu cong cu/dia quyen).
3. UI Integrator staging + Live/Installer defaults + goi Debian tuy chon.
4. Extract ISO, giai nen squashfs, chep staging, bien dich schema,
   nen lai squashfs, repack ISO giu boot image.
5. ISO Validator muc 1-3 tren file dau ra va ghi manifest.

Buoc 4 chi chay khi cong cu he thong thuc su ton tai. Thieu cong cu thi
build dung lai sau buoc 3, giu workspace + staging + manifest, tra ma loi
moi truong. Khong bao gio ghi de ISO nguon hay file dau ra da ton tai khi
chua co tuy chon cho phep tuong minh.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import __version__
from .checksums import sha256_file
from .deb import build_deb
from .env_validator import validate_environment
from .errors import BuildStepError, EnvValidationError, IntegrationError, UsageError
from .installer_defaults import ComponentState
from .live_config import build_live_config
from .source_validator import validate_source
from .ui_integrator import inventory, stage_overlay
from .workspace import Workspace, append_log, create_workspace, write_manifest


def _run_step(workspace: Workspace, argv: list[str], label: str) -> None:
    append_log(workspace, f"RUN {label}: {' '.join(argv)}")
    completed = subprocess.run(argv, capture_output=True, text=True, check=False)
    tail = (completed.stdout + completed.stderr).strip()[-800:]
    if tail:
        append_log(workspace, f"OUTPUT {label}: {tail}")
    if completed.returncode != 0:
        raise BuildStepError(
            f"buoc '{label}' that bai (exit {completed.returncode}): {tail[:300]}"
        )


def _git_commit(repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.stdout.strip() if completed.returncode == 0 else ""
    except OSError:
        return ""


def run_build(
    source_iso: Path,
    output_iso: Path,
    workspace_parent: Path,
    repo_root: Path,
    force: bool = False,
    allow_partial: bool = False,
    make_deb: bool = True,
    dry_run: bool = False,
    build_id: str = "",
) -> dict:
    source_iso = source_iso.expanduser().resolve()
    output_iso = output_iso.expanduser().resolve()
    if output_iso == source_iso:
        raise UsageError("file dau ra trung ISO nguon; ISO goc phai duoc giu nguyen")
    if output_iso.exists() and not force:
        raise UsageError(
            f"file dau ra da ton tai: {output_iso} (dung --force neu chac chan muon ghi de)"
        )

    manifest: dict = {
        "tool": "MintOS Glass ISO Customizer",
        "tool_version": __version__,
        "mintos_glass_git_commit": _git_commit(repo_root),
        "source_iso": str(source_iso),
        "output_iso": str(output_iso),
        "dry_run": dry_run,
        "allow_partial": allow_partial,
        "steps": [],
        "warnings": [],
        "reproducibility": (
            "chua cam ket bit-for-bit: timestamp trong goi, metadata squashfs "
            "va thu tu file cua cong cu repack la nguon khong xac dinh"
        ),
    }

    def step(name: str) -> None:
        manifest["steps"].append(name)

    # 1) Source.
    source_report = validate_source(source_iso)
    manifest["source"] = source_report.to_dict()
    checksum_before = source_report.sha256
    step("source-validated")
    if not source_report.compatible:
        manifest["result"] = "FAIL"
        manifest["problems"] = list(source_report.problems)
        raise _attach_manifest(
            BuildStepError("ISO nguon khong tuong thich: " + "; ".join(source_report.problems)),
            manifest,
        )

    # Workspace phai co truoc cac buoc ghi de luu log/manifest ke ca khi chan som.
    workspace = create_workspace(workspace_parent, build_id)
    manifest["workspace"] = str(workspace.root)
    append_log(workspace, f"build bat dau; source sha256={checksum_before}")

    # 2) Environment.
    env_report = validate_environment(workspace_parent, source_report.size_bytes)
    manifest["environment"] = env_report.to_dict()
    step("environment-checked")

    # 3) Integration staging (luon chay de co san pham kiem tra duoc du dung lai sau).
    inv = inventory(repo_root)
    manifest["components"] = {
        "cinnamon_theme": inv.cinnamon_theme,
        "cinnamon_assets": inv.cinnamon_assets,
        "icon_theme": inv.icon_theme,
        "icon_files": inv.icon_files,
        "wallpapers": list(inv.wallpapers),
        "gtk_theme": inv.gtk_theme,
        "libadwaita_complete": inv.libadwaita_files,
        "blocked": list(inv.blocked),
        "problems": list(inv.problems),
    }
    if inv.problems and not allow_partial:
        manifest["result"] = "FAIL"
        write_manifest(workspace, manifest)
        raise _attach_manifest(
            IntegrationError(
                "thanh phan giao dien chua san sang: " + "; ".join(inv.problems)
                + " (chi tiep tuc khi co --allow-partial va chap nhan ISO thieu thanh phan)"
            ),
            manifest,
        )
    staging_root = workspace.path("staging/rootfs")
    staged = stage_overlay(repo_root, staging_root, inv)
    manifest["staging"] = staged.manifest
    manifest["staged_files"] = list(staged.staged_files)

    live = build_live_config(inv.component_state(), list(inv.wallpapers))
    defaults = live.defaults
    if defaults.applied:
        target = staging_root / defaults.override_relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(defaults.override_text, encoding="utf-8")
        manifest["staged_files"].append(defaults.override_relative_path)
    if live.background_props_relative_path:
        target = staging_root / live.background_props_relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(live.background_props_text, encoding="utf-8")
        manifest["staged_files"].append(live.background_props_relative_path)
    manifest["defaults"] = {
        "applied": list(defaults.applied),
        "skipped": list(defaults.skipped),
        "live_notes": list(live.notes),
        "scope": "mac dinh he thong cho nguoi dung moi; nguoi dung doi duoc sau",
    }
    step("ui-staged")

    if make_deb:
        deb_info = build_deb(
            staging_root,
            workspace.path("package/mintos-glass-theme.deb"),
            package="mintos-glass-theme",
            version="0.1.0",
            maintainer="MintOS Glass contributors",
            description="MintOS Glass Dark desktop theme for Linux Mint Cinnamon",
        )
        manifest["deb_package"] = deb_info
        step("deb-built")

    if dry_run:
        manifest["result"] = "DRY-RUN"
        manifest["warnings"].append(
            "dry-run: chua extract/repack ISO; staging va manifest la san pham duy nhat"
        )
        write_manifest(workspace, manifest)
        append_log(workspace, "dry-run ket thuc")
        return manifest

    # 4) Remaster that su. Thieu cong cu thi dung tai day, giu workspace.
    if not env_report.ready_for_remaster:
        manifest["result"] = "BLOCKED"
        manifest["problems"] = list(env_report.problems)
        write_manifest(workspace, manifest)
        append_log(workspace, "BLOCKED: moi truong chua san sang cho remaster")
        raise _attach_manifest(
            EnvValidationError(
                "moi truong build chua san sang: " + "; ".join(env_report.problems)
                + f". Workspace duoc giu lai tai {workspace.root}"
            ),
            manifest,
        )

    _remaster(workspace, source_iso, output_iso, staging_root, manifest, step)

    # 5) Kiem tra dau ra o muc file/cau truc/noi dung co ban.
    from .iso_validator import validate_iso

    validation = validate_iso(output_iso)
    manifest["output_validation"] = validation.to_dict()
    step("output-validated-levels-1-3")

    checksum_after = sha256_file(source_iso)
    manifest["source_unchanged"] = checksum_after == checksum_before
    if not manifest["source_unchanged"]:
        manifest["result"] = "FAIL"
        write_manifest(workspace, manifest)
        raise _attach_manifest(
            BuildStepError("ISO nguon bi thay doi trong qua trinh build; dung ngay"),
            manifest,
        )
    manifest["result"] = "BUILT"
    manifest["warnings"].append(
        "BUILT chi co nghia la da tao file va qua kiem tra muc 1-3; "
        "boot/cai dat (muc 4-5) chua duoc kiem chung"
    )
    write_manifest(workspace, manifest)
    append_log(workspace, f"build thanh cong o muc file; output={output_iso}")
    return manifest


def _remaster(
    workspace: Workspace,
    source_iso: Path,
    output_iso: Path,
    staging_root: Path,
    manifest: dict,
    step,
) -> None:
    iso_extract = workspace.path("extract/iso")
    rootfs = workspace.path("extract/rootfs")
    new_squashfs = workspace.path("output/filesystem.squashfs")
    squashfs_rel = None
    source_info = manifest.get("source", {})
    for candidate in source_info.get("squashfs_paths", []):
        if candidate.startswith("casper/"):
            squashfs_rel = candidate
            break
    if not squashfs_rel:
        raise BuildStepError("khong xac dinh duoc casper/filesystem.squashfs de remaster")

    squashfs_on_iso = iso_extract / squashfs_rel
    _run_step(
        workspace,
        ["xorriso", "-osirrox", "on", "-indev", str(source_iso), "-extract", "/", str(iso_extract)],
        "extract-iso",
    )
    step("iso-extracted")
    if not squashfs_on_iso.is_file():
        raise BuildStepError(f"extract xong nhung khong thay {squashfs_rel}")
    _run_step(workspace, ["unsquashfs", "-f", "-d", str(rootfs), str(squashfs_on_iso)], "unsquashfs")
    step("rootfs-extracted")

    # Chep nguyen cay staging (cung noi dung voi goi Debian) vao rootfs.
    import shutil

    for item in sorted(staging_root.rglob("*")):
        if item.is_file():
            relative = item.relative_to(staging_root)
            target = rootfs / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    step("overlay-copied")

    # Bien dich schema override ngay trong rootfs dich.
    schemas_dir = rootfs / "usr" / "share" / "glib-2.0" / "schemas"
    _run_step(
        workspace,
        ["glib-compile-schemas", str(schemas_dir)],
        "compile-schemas",
    )
    step("schemas-compiled")

    _run_step(
        workspace,
        ["mksquashfs", str(rootfs), str(new_squashfs), "-comp", "xz", "-noappend"],
        "mksquashfs",
    )
    step("squashfs-rebuilt")

    output_iso.parent.mkdir(parents=True, exist_ok=True)
    _run_step(
        workspace,
        [
            "xorriso",
            "-indev",
            str(source_iso),
            "-outdev",
            str(output_iso),
            "-boot_image",
            "isolinux",
            "keep",
            "-boot_image",
            "any",
            "keep",
            "-map",
            str(new_squashfs),
            "/" + squashfs_rel,
            "-map",
            str(workspace.manifest_path),
            "/" + "mintos-glass-manifest.json",
        ],
        "repack-iso",
    )
    step("iso-repacked")


def _attach_manifest(error: Exception, manifest: dict) -> Exception:
    error_manifest = dict(manifest)
    error.manifest = error_manifest  # type: ignore[attr-defined]
    return error
