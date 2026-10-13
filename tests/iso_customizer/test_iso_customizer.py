"""Unit test cho MintOS Glass ISO Customizer (chi chay offline).

Fixture ISO trong test nay la file tong hop nho, chi de kiem tra trinh
doc cau truc. No khong phai ISO Mint that va khong chung minh ISO boot
hay cai dat duoc.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iso_customizer.iso_fixture import make_fixture_iso  # noqa: E402
from tools.iso_customizer.checksums import sha256_file  # noqa: E402
from tools.iso_customizer.cli import main as cli_main  # noqa: E402
from tools.iso_customizer.deb import build_deb  # noqa: E402
from tools.iso_customizer.errors import UsageError  # noqa: E402
from tools.iso_customizer.installer_defaults import ComponentState, build_defaults  # noqa: E402
from tools.iso_customizer.iso_builder import run_build  # noqa: E402
from tools.iso_customizer.iso_validator import validate_iso  # noqa: E402
from tools.iso_customizer.iso9660 import inspect_iso  # noqa: E402
from tools.iso_customizer.live_config import build_live_config  # noqa: E402
from tools.iso_customizer.source_validator import validate_source  # noqa: E402
from tools.iso_customizer.ui_integrator import inventory  # noqa: E402
from tools.iso_customizer.workspace import clean_workspace, create_workspace  # noqa: E402


class TestIso9660Reader(unittest.TestCase):
    def test_fixture_structure_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            iso = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            info = inspect_iso(iso)
            self.assertTrue(info.has_el_torito)
            self.assertIn("casper/filesystem.squashfs", info.files)
            self.assertIn("22.3", info.volume_id)

    def test_non_iso_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bogus = Path(tmp) / "bogus.iso"
            bogus.write_bytes(b"x" * 40000)
            with self.assertRaises(Exception):
                inspect_iso(bogus)


class TestSourceValidator(unittest.TestCase):
    def test_fixture_detected_as_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            iso = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            before = sha256_file(iso)
            report = validate_source(iso)
            self.assertTrue(report.compatible, report.problems)
            self.assertEqual(report.detected_version, "22.3")
            self.assertEqual(report.detected_arch, "amd64")
            self.assertEqual(sha256_file(iso), before, "validator khong duoc sua ISO goc")

    def test_missing_source_raises(self):
        with self.assertRaises(Exception):
            validate_source(Path("/definitely/not/here.iso"))

    def test_wrong_checksum_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            iso = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            report = None
            try:
                report = validate_source(iso, expected_sha256="0" * 64)
            except Exception:
                report = None
            # Du tra report hay nem loi thi khong bao gio duoc coi la verified.
            if report is not None:
                self.assertFalse(report.checksum_verified_official)


class TestDefaultsAndLiveConfig(unittest.TestCase):
    def test_defaults_skip_gtk_when_gtk_missing(self):
        result = build_defaults(
            ComponentState(cinnamon_theme=True, gtk_theme=False, icon_theme=True)
        )
        self.assertIn('name="MintOS-Glass"', result.override_text)
        self.assertIn('icon-theme="MintOS-Glass"', result.override_text)
        self.assertNotIn('gtk-theme="MintOS-Glass"', result.override_text)
        self.assertTrue(any("gtk-theme" in item for item in result.skipped))

    def test_live_config_ships_wallpaper_listing_only(self):
        live = build_live_config(
            ComponentState(cinnamon_theme=True, icon_theme=True),
            ["mintos-glass-dark.svg"],
        )
        self.assertIn("mintos-glass-dark.svg", live.background_props_text)
        self.assertTrue(
            any("chua xac minh" in note for note in live.notes),
            "live config phai khai bao phan chua xac minh",
        )


class TestInventoryHonesty(unittest.TestCase):
    def test_real_repo_inventory(self):
        inv = inventory(ROOT)
        self.assertTrue(inv.cinnamon_theme)
        self.assertTrue(inv.icon_theme)
        self.assertTrue(inv.wallpapers)
        self.assertFalse(inv.gtk_theme, "GTK entry chua co; khong duoc bao la san sang")
        self.assertTrue(inv.blocked)


class TestDebBuilder(unittest.TestCase):
    def test_deb_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            target = staging / "usr" / "share" / "themes" / "MintOS-Glass" / "cinnamon"
            target.mkdir(parents=True)
            (target / "cinnamon.css").write_text("stage { color: #fff; }", encoding="utf-8")
            output = Path(tmp) / "pkg.deb"
            info = build_deb(staging, output, "mintos-glass-theme", "0.1.0", "Tester", "Desc")
            data = output.read_bytes()
            self.assertTrue(data.startswith(b"!<arch>\n"))
            self.assertIn(b"debian-binary", data)
            self.assertIn(b"control.tar.gz", data)
            self.assertIn(b"data.tar.gz", data)
            self.assertEqual(info["data_files"], 1)


class TestWorkspaceSafety(unittest.TestCase):
    def test_create_and_guarded_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspaces"
            workspace = create_workspace(parent, "test01")
            self.assertTrue((workspace.root / ".mintos-glass-workspace").is_file())
            with self.assertRaises(UsageError):
                clean_workspace(parent, workspace.root, "yes")
            removed = clean_workspace(parent, workspace.root, "DELETE")
            self.assertFalse(removed.exists())

    def test_refuses_to_clean_outside_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "workspaces"
            parent.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (outside / ".mintos-glass-workspace").write_text("fake", encoding="utf-8")
            with self.assertRaises(UsageError):
                clean_workspace(parent, outside, "DELETE")
            self.assertTrue(outside.exists())


class TestValidatorLevels(unittest.TestCase):
    def test_levels_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            iso = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            report = validate_iso(iso)
            by_level = {lv.level: lv for lv in report.levels}
            self.assertEqual(by_level[1].status, "FAIL")  # fixture qua nho
            self.assertEqual(by_level[2].status, "PASS")
            self.assertEqual(by_level[3].status, "FAIL")  # chua co noi dung MintOS tren be mat ISO
            self.assertEqual(by_level[4].status, "NOT TESTED")
            self.assertEqual(by_level[5].status, "NOT TESTED")


class TestCli(unittest.TestCase):
    def test_help_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            cli_main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_inspect_missing_file_nonzero(self):
        self.assertEqual(cli_main(["inspect-source", "/definitely/not/here.iso"]), 4)

    def test_validate_missing_file_nonzero(self):
        self.assertNotEqual(cli_main(["validate", "/definitely/not/here.iso"]), 0)


class TestBuildDryRun(unittest.TestCase):
    def test_dry_run_stages_without_repacking(self):
        inv = inventory(ROOT)
        if not inv.compile_available:
            self.skipTest("can SCSS compiler de staging theme Cinnamon")
        with tempfile.TemporaryDirectory() as tmp:
            source = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            output = Path(tmp) / "mintos-glass.iso"
            manifest = run_build(
                source_iso=source,
                output_iso=output,
                workspace_parent=Path(tmp) / "workspaces",
                repo_root=ROOT,
                dry_run=True,
                build_id="dryrun-test",
            )
            self.assertEqual(manifest["result"], "DRY-RUN")
            self.assertFalse(output.exists(), "dry-run khong duoc tao ISO dau ra")
            staged = set(manifest["staged_files"])
            self.assertIn("usr/share/themes/MintOS-Glass/cinnamon/cinnamon.css", staged)
            self.assertIn("usr/share/icons/MintOS-Glass/index.theme", staged)
            self.assertIn("usr/share/glib-2.0/schemas/90_mintos-glass.gschema.override", staged)
            workspace = Path(manifest["workspace"])
            self.assertTrue((workspace / "manifest.json").is_file())
            self.assertTrue((workspace / "package" / "mintos-glass-theme.deb").is_file())
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(),
                digest,
                "ISO nguon phai nguyen ven sau build",
            )

    def test_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            output = Path(tmp) / "exists.iso"
            output.write_bytes(b"already here")
            with self.assertRaises(UsageError):
                run_build(
                    source_iso=source,
                    output_iso=output,
                    workspace_parent=Path(tmp) / "workspaces",
                    repo_root=ROOT,
                    dry_run=True,
                )
            self.assertEqual(output.read_bytes(), b"already here")

    def test_output_must_not_equal_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = make_fixture_iso(Path(tmp) / "linuxmint-22.3-cinnamon-64bit.iso")
            with self.assertRaises(UsageError):
                run_build(
                    source_iso=source,
                    output_iso=source,
                    workspace_parent=Path(tmp) / "workspaces",
                    repo_root=ROOT,
                    dry_run=True,
                    force=True,
                )


if __name__ == "__main__":
    unittest.main()
