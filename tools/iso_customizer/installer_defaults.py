"""Installer Defaults: mac dinh cho nguoi dung moi sau khi cai dat.

Co che duoc chon la GSettings schema override o cap he thong (file dat trong
thu muc schemas cua rootfs). Ly do:
- Override chi dat GIA TRI MAC DINH. Nguoi dung doi theme sau khi cai thi
  gia tri cua ho thang mac dinh va khong bi ghi de boi override.
- Khong dung thu muc skel he thong de chep cau hinh ca nhan, khong cham tai khoan
  da ton tai, khong khoa (lock) bat ky khoa nao.

Gioi han kiem chung: danh sach khoa duoc lay tu danh sach khoa dong da doi
chieu voi cinnamon-settings upstream trong repo nay. Chua co may Linux Mint
22.3 that de chung minh override duoc ap dung sau cai dat; ket qua phai
duoc xac minh bang muc Installation validation, khong duoc coi la bang chung.
"""

from __future__ import annotations

from dataclasses import dataclass, field

THEME_NAME = "MintOS-Glass"
OVERRIDE_FILENAME = "90_mintos-glass.gschema.override"

# Khoa da xac minh ton tai trong repo (danh sach dong cua task T12):
# org.cinnamon.theme name; org.cinnamon.desktop.interface gtk-theme,
# icon-theme; org.cinnamon.desktop.wm.preferences theme.
# Khoa wallpaper khong nam trong danh sach da xac minh nen cong cu khong
# dat mac dinh wallpaper bang GSettings (xem live_config ve XML nen).


@dataclass
class ComponentState:
    cinnamon_theme: bool = False
    gtk_theme: bool = False
    icon_theme: bool = False
    wallpapers: bool = False


@dataclass
class DefaultsResult:
    override_relative_path: str = ""
    override_text: str = ""
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def build_defaults(components: ComponentState) -> DefaultsResult:
    result = DefaultsResult()
    sections: list[str] = []
    if components.cinnamon_theme:
        sections.append("[org.cinnamon.theme]\n" f'name="{THEME_NAME}"\n')
        result.applied.append("org.cinnamon.theme name (Cinnamon Dark Glass)")
    else:
        result.skipped.append("org.cinnamon.theme name: theme Cinnamon chua san sang")
    interface_keys: list[str] = []
    if components.gtk_theme:
        interface_keys.append(f'gtk-theme="{THEME_NAME}"')
        result.applied.append("org.cinnamon.desktop.interface gtk-theme")
    else:
        result.skipped.append("gtk-theme: theme GTK chua ton tai nen khong dat mac dinh")
    if components.icon_theme:
        interface_keys.append(f'icon-theme="{THEME_NAME}"')
        result.applied.append("org.cinnamon.desktop.interface icon-theme")
    else:
        result.skipped.append("icon-theme: icon theme chua san sang")
    if interface_keys:
        sections.append("[org.cinnamon.desktop.interface]\n" + "\n".join(interface_keys) + "\n")
    if components.gtk_theme:
        sections.append(
            "[org.cinnamon.desktop.wm.preferences]\n" f'theme="{THEME_NAME}"\n'
        )
        result.applied.append("org.cinnamon.desktop.wm.preferences theme")
    else:
        result.skipped.append("wm.preferences theme: phu thuoc theme GTK nen chua dat")
    header = (
        "# MintOS Glass - gia tri mac dinh cho nguoi dung moi.\n"
        "# Day chi la mac dinh he thong: nguoi dung doi trong Settings thi thang.\n"
        "# File duoc bien dich bang glib-compile-schemas khi build ISO.\n"
    )
    result.override_text = header + "\n" + "\n".join(sections) if sections else header
    result.override_relative_path = (
        "usr/share/glib-2.0/schemas/" + OVERRIDE_FILENAME
    )
    return result
