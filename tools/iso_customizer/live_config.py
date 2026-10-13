"""Live Session Configurator: cau hinh cho phien live.

Chien luoc (co che chung cho ca live va sau cai dat):
- Tai nguyen theme/icon/wallpaper nam o vi tri he thong trong squashfs
  filesystem, nen phien live thay duoc ngay tu dau va trinh cai dat sao chep
  cac file do sang he thong dich (tru thanh phan rieng cua live).
- Mac dinh giao dien dat bang schema override o cap he thong
  (installer_defaults), khong dua vao cau hinh ca nhan cua tai khoan live.

Nhung gi CHUA xac minh (khong duoc coi la bang chung):
- Ten tai khoan live, co che khoi tao live session va cach trinh cai dat
  sao chep filesystem cua dung ban Linux Mint 22.3 chua duoc doi chieu tren
  may dich. Cong cu khong gia dinh ten tai khoan live, khong ghi file vao
  home cua tai khoan live va khong sua truc tiep file he thong nao ngoai
  cay staging nam trong workspace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from .installer_defaults import ComponentState, DefaultsResult, build_defaults

BACKGROUNDS_DIR = "usr/share/backgrounds/mintos-glass"
BACKGROUND_PROPS_RELATIVE = "usr/share/gnome-background-properties/mintos-glass.xml"


@dataclass
class LiveConfigResult:
    defaults: DefaultsResult
    background_props_relative_path: str = ""
    background_props_text: str = ""
    notes: list[str] = field(default_factory=list)


def build_background_properties(wallpaper_filenames: list[str]) -> str:
    """Sinh XML danh sach nen theo dinh dang gnome-background-properties.

    Co che doc XML nay da duoc xac minh la ton tai trong Cinnamon Settings
    (parse_xml_backgrounds_list). Vi tri file dich va viec phien live co
    tu dong liet ke hay khong van can xac minh tren may dich; vi vay day
    chi la tai nguyen di kem, khong phai loi hua wallpaper mac dinh.
    """
    entries = []
    for filename in wallpaper_filenames:
        stem = Path(filename).stem
        target = "/" + BACKGROUNDS_DIR + "/" + escape(filename)
        entries.append(
            "  <wallpaper>\n"
            f"    <name>MintOS Glass {escape(stem)}</name>\n"
            f"    <filename>{target}</filename>\n"
            "    <options>zoom</options>\n"
            "  </wallpaper>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<wallpapers>\n'
        + "\n".join(entries)
        + "\n</wallpapers>\n"
    )


def build_live_config(
    components: ComponentState, wallpaper_filenames: list[str]
) -> LiveConfigResult:
    defaults = build_defaults(components)
    result = LiveConfigResult(defaults=defaults)
    if wallpaper_filenames:
        result.background_props_relative_path = BACKGROUND_PROPS_RELATIVE
        result.background_props_text = build_background_properties(wallpaper_filenames)
    result.notes.append(
        "live session dung chung schema override he thong; khong ghi cau hinh "
        "vao home cua tai khoan live vi ten/co che tai khoan chua xac minh"
    )
    result.notes.append(
        "wallpaper chi duoc liet ke qua XML nen; khoa GSettings nen chua xac minh "
        "nen khong tu dat hinh nen mac dinh"
    )
    return result
