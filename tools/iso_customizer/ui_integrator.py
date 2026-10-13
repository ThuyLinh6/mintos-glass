"""UI Integrator: kiem ke va staging tai nguyen MintOS Glass tu repo.

Nguyen tac:
- Chi tich hop thanh phan thuc su ton tai. Thieu thanh phan thi ghi
  BLOCKED trong ket qua, khong bia file, khong sao chep ngau nhien.
- Moi dich den deu la duong dan TUONG DOI ben duoi rootfs trong workspace
  (vi du usr/share/themes/...). Cong cu khong ghi truc tiep len may host.
- Khong viet lai ma nguon cua agent khac. SCSS chi duoc bien dich bang
  compiler da co tren may build; thieu compiler thi bao loi som.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .errors import IntegrationError
from .installer_defaults import ComponentState

REPO_ROOT = Path(__file__).resolve().parents[2]
THEME_NAME = "MintOS-Glass"


@dataclass
class ComponentInventory:
    cinnamon_theme: bool = False
    cinnamon_assets: int = 0
    icon_theme: bool = False
    icon_files: int = 0
    wallpapers: list[str] = field(default_factory=list)
    gtk_theme: bool = False
    gtk_partials_orphan: list[str] = field(default_factory=list)
    libadwaita_files: bool = False
    compile_available: bool = False
    problems: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    def component_state(self) -> ComponentState:
        return ComponentState(
            cinnamon_theme=self.cinnamon_theme,
            gtk_theme=self.gtk_theme,
            icon_theme=self.icon_theme,
            wallpapers=bool(self.wallpapers),
        )


def _count_svg(folder: Path) -> int:
    return sum(1 for _ in folder.rglob("*.svg")) if folder.is_dir() else 0


def inventory(repo_root: Path = REPO_ROOT) -> ComponentInventory:
    inv = ComponentInventory()
    cinnamon_entry = repo_root / "src" / "cinnamon" / "cinnamon.scss"
    assets_dir = repo_root / "src" / "cinnamon" / "assets"
    inv.cinnamon_assets = _count_svg(assets_dir)
    inv.cinnamon_theme = cinnamon_entry.is_file() and inv.cinnamon_assets > 0
    if not inv.cinnamon_theme:
        inv.problems.append("thieu entry hoac asset cua theme Cinnamon")

    icon_dir = repo_root / "src" / "icons" / THEME_NAME
    inv.icon_files = _count_svg(icon_dir)
    inv.icon_theme = (icon_dir / "index.theme").is_file() and inv.icon_files > 0
    if not inv.icon_theme:
        inv.problems.append("thieu icon theme (index.theme hoac file SVG)")

    wallpaper_dir = repo_root / "src" / "wallpapers"
    if wallpaper_dir.is_dir():
        inv.wallpapers = sorted(p.name for p in wallpaper_dir.glob("*.svg"))
    if not inv.wallpapers:
        inv.problems.append("thieu wallpaper SVG")

    # GTK: chi tinh la san sang khi co entry point that. Partial khong entry
    # la hang ton kho chua noi (QA-09), tuyet doi khong dong goi nhu da xong.
    gtk_entry = repo_root / "src" / "gtk-3.0" / "sass" / "gtk.scss"
    inv.gtk_theme = gtk_entry.is_file()
    if not inv.gtk_theme:
        for partial in ("_apps-nemo.scss", "_apps-mint.scss"):
            candidate = repo_root / "src" / "gtk-3.0" / "sass" / partial
            if candidate.is_file():
                inv.gtk_partials_orphan.append(str(candidate.relative_to(repo_root)))
        inv.blocked.append(
            "GTK theme: chua co src/gtk-3.0/sass/gtk.scss nen khong co gtk.css; "
            "partial Nemo/Mint dang mo coi va khong duoc tich hop"
        )
    libadwaita_required = [
        repo_root / "src" / "libadwaita" / name
        for name in ("base.css", "base-hc.css", "defaults-light.css", "defaults-dark.css")
    ]
    inv.libadwaita_files = all(p.is_file() for p in libadwaita_required)
    if not inv.libadwaita_files:
        inv.blocked.append(
            "GTK4/libadwaita: chua du 4 file bat buoc nen khong tich hop"
        )
    try:
        import sass  # noqa: F401

        inv.compile_available = True
    except ImportError:
        inv.compile_available = bool(shutil.which("pysassc") or shutil.which("sass"))
    if not inv.compile_available:
        inv.problems.append(
            "khong co SCSS compiler (libsass/pysassc/dart-sass) tren may build"
        )
    return inv


def compile_cinnamon_css(repo_root: Path, destination: Path) -> int:
    """Bien dich cinnamon.scss thanh CSS. Tra ve kich thuoc byte."""
    entry = repo_root / "src" / "cinnamon" / "cinnamon.scss"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        import sass

        css = sass.compile(filename=str(entry))
        destination.write_text(css, encoding="utf-8")
        return destination.stat().st_size
    except ImportError:
        pass
    compiler = shutil.which("pysassc") or shutil.which("sass")
    if not compiler:
        raise IntegrationError(
            "khong the bien dich Cinnamon SCSS: thieu libsass/pysassc/dart-sass"
        )
    completed = subprocess.run(
        [compiler, str(entry), str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not destination.is_file():
        raise IntegrationError(
            f"bien dich SCSS that bai ({compiler}): {completed.stderr.strip()[:400]}"
        )
    return destination.stat().st_size


@dataclass
class StageResult:
    staged_files: list[str] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)


def stage_overlay(
    repo_root: Path,
    staging_root: Path,
    inv: ComponentInventory,
) -> StageResult:
    """Chep tai nguyen vao cay staging (duoi workspace). Khong ghi len host."""
    result = StageResult()

    def record(source: Path, relative_target: str) -> None:
        target = staging_root / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        result.staged_files.append(relative_target)

    if inv.cinnamon_theme:
        css_rel = f"usr/share/themes/{THEME_NAME}/cinnamon/cinnamon.css"
        css_size = compile_cinnamon_css(repo_root, staging_root / css_rel)
        result.staged_files.append(css_rel)
        assets_dir = repo_root / "src" / "cinnamon" / "assets"
        for svg in sorted(assets_dir.glob("*.svg")):
            record(svg, f"usr/share/themes/{THEME_NAME}/cinnamon/assets/{svg.name}")
        result.manifest["cinnamon"] = {
            "status": "staged",
            "css_bytes": css_size,
            "assets": inv.cinnamon_assets,
            "variant": "Dark Glass (bien the duy nhat dang emit)",
        }
    if inv.icon_theme:
        icon_src = repo_root / "src" / "icons" / THEME_NAME
        for item in sorted(icon_src.rglob("*")):
            if item.is_file():
                relative = item.relative_to(icon_src).as_posix()
                record(item, f"usr/share/icons/{THEME_NAME}/{relative}")
        result.manifest["icons"] = {
            "status": "staged",
            "files": inv.icon_files,
            "inherits": "Mint-Y,Adwaita,gnome,hicolor (theo index.theme)",
        }
    for wallpaper in inv.wallpapers:
        record(
            repo_root / "src" / "wallpapers" / wallpaper,
            f"usr/share/backgrounds/mintos-glass/{wallpaper}",
        )
    if inv.wallpapers:
        result.manifest["wallpapers"] = {
            "status": "staged",
            "files": list(inv.wallpapers),
        }
    result.manifest["gtk"] = {
        "status": "blocked",
        "reason": list(inv.blocked),
        "orphan_partials": list(inv.gtk_partials_orphan),
    }
    result.manifest["ownership"] = (
        "tat ca file staging nam trong workspace; khi vao rootfs chung thuoc "
        "rootfs he thong (khong ghi len may host trong qua trinh staging)"
    )
    return result
