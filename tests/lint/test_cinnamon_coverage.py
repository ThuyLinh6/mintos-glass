#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/lint/test_cinnamon_coverage.py — unittest (stdlib, KHÔNG cần pytest).

Ba chốt chặn:

  A. COVERAGE (ràng buộc E6) — mọi selector của theme gốc Cinnamon 6.6 phải có
     mặt trong CSS ta sinh ra. St chỉ nạp CSS của Mint làm `fallback_stylesheet`
     KHÔNG cascade (src/st/st-theme.c, doc của PROP_FALLBACK_STYLESHEET: chỉ áp
     dụng khi stylesheet người dùng không trả về property nào, và phải đặt
     `important`). Thiếu một selector = widget đó MẤT STYLE HOÀN TOÀN.

  B. NO DEAD SELECTORS — mọi selector ta THÊM NGOÀI theme gốc phải nằm trong
     danh sách đóng băng bên dưới, mỗi mục kèm bằng chứng đã grep trong mã
     nguồn Cinnamon 6.6. Selector bịa ra là CSS chết: St bỏ qua trong im lặng,
     không ai phát hiện cho tới khi chạy trên máy thật.

  C. ASSETS — mọi url() HIỆU LỰC (sau cascade, last-wins) phải là một trong 15
     file `assets/*.svg` mà T05 phải cung cấp. Test này KHÔNG fail khi thiếu
     file (T05 chưa chạy) mà fail khi TẬP url() KHÁC với danh sách đã chốt —
     tức là bắt được cả url() bịa lẫn url() tên trần của vendor chưa bị ghi đè.

Chạy: python3 -m unittest discover -s tests -t . -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "tools" / "lint"))

try:  # chạy qua `python3 -m unittest discover -s tests -t .`
    from tests.lint.test_st_properties import compiled_css, findings_for, rules, sp
except ImportError:  # chạy trực tiếp file này
    from test_st_properties import compiled_css, findings_for, rules, sp  # type: ignore

# --------------------------------------------------------------------------- #
# B. Selector ta thêm ngoài theme gốc — ĐÓNG BĂNG, kèm bằng chứng.
#    "JS"  = chuỗi style class có thật trong js/ hoặc files/usr/share/cinnamon/
#            của commit 806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18 (tag 6.6.9).
#    "ST"  = pseudo-class do chính St thêm (src/st/st-widget.c, st-button.c).
#    "VENDOR" = selector có trong CSS gốc nhưng ở dạng nhóm khác, ta tách ra.
# --------------------------------------------------------------------------- #
NEW_SELECTORS: dict[str, str] = {
    # --- ô tìm kiếm: theme gốc chỉ có :focus và :insensitive, ta thêm :hover ---
    "#appmenu-search-entry:hover": "VENDOR: gốc có #appmenu-search-entry(:focus,:insensitive)",
    "#menu-search-entry:hover": "VENDOR: gốc có #menu-search-entry(:focus,:insensitive)",
    ".expo-workspaces-name-entry:hover": "VENDOR: gốc có selector này ở dạng nhóm",
    ".prompt-dialog-password-entry:hover": "VENDOR: gốc có selector này ở dạng nhóm",
    ".run-dialog-entry:hover": "VENDOR: gốc có selector này ở dạng nhóm",
    ".search-entry": "JS: menu@cinnamon.org/applet.js dùng style_class 'search-entry'",
    ".search-entry-icon": "JS: menu@cinnamon.org/applet.js dùng 'search-entry-icon'",
    ".search-entry:focus": "JS + ST: st-widget.c:701 thêm pseudo 'focus'",
    ".search-entry:focus .search-entry-icon": "JS + ST",
    ".search-entry:hover": "JS + ST: st-widget.c:1840 thêm pseudo 'hover'",
    ".search-entry:hover .search-entry-icon": "JS + ST",

    # --- applet / panel ---
    ".applet-box:active": "ST: st-button.c:132 thêm pseudo 'active'",
    ".applet-box:focus": "JS 'applet-box' + ST st-widget.c:701 'focus'",
    ".applet-box:hover .applet-icon": "JS 'applet-icon' (applets dùng trong panel)",
    ".applet-box:hover .applet-label": "JS 'applet-label'",
    ".applet-icon": "JS: chuỗi 'applet-icon' có trong applets của Cinnamon",
    ".applet-icon:hover": "JS + ST",
    ".applet-label:hover": "JS + ST",
    ".panel-left .workspace-switcher": "VENDOR: gốc chỉ có .panel-top/.panel-bottom .workspace-switcher",
    ".panel-right .workspace-switcher": "VENDOR: như trên, panel dọc cũng có applet này",
    ".system-status-icon:hover": "VENDOR: gốc có .system-status-icon",

    # --- app menu (appmenu@cinnamon.org, Cinnamon 6.6) ---
    ".appmenu-application-button-selected .appmenu-application-button-description":
        "JS: cả hai class đều do menu@cinnamon.org/applet.js đặt",
    ".appmenu-application-button-selected:focus": "JS + ST",
    ".appmenu-application-button:hover": "JS + ST",
    ".appmenu-category-button-selected:focus": "JS + ST",
    ".appmenu-sidebar-button:focus": "JS: menu@cinnamon.org/applet.js dùng 'appmenu-sidebar-button'",
    ".appmenu-sidebar-button:selected": "JS + ST: st-widget.c:2901 thêm 'selected' theo ATK_STATE_SELECTED",
    ".appmenu-system-button-shutdown:focus": "JS + ST",
    ".appmenu-system-button:focus": "JS + ST",

    # --- menu cũ (menu@cinnamon.org) ---
    ".menu-application-button-selected:focus": "JS + ST",
    ".menu-application-button:hover": "JS + ST",
    ".menu-category-button-selected:focus": "JS + ST",
    ".menu-context-menu": "JS: menu@cinnamon.org/applet.js dùng 'menu-context-menu'",
    ".menu-context-menu .popup-menu-item": "JS + VENDOR",
    ".menu-favorites-button:focus": "JS + ST",

    # --- popup menu ---
    ".popup-combobox-item:focus": "JS + ST",
    ".popup-combobox-item:hover": "JS + ST",
    ".popup-inactive-menu-item": "JS: js/ui/popupMenu.js dùng 'popup-inactive-menu-item'",
    ".popup-inactive-menu-item:insensitive": "JS + ST: st-widget.c:1502 thêm 'insensitive'",
    ".popup-menu-item:active .popup-menu-arrow": "JS + ST",
    ".popup-menu-item:active .popup-menu-icon": "JS + ST",
    ".popup-menu-item:focus": "JS + ST",
    ".popup-separator-menu-item .popup-menu-item": "VENDOR: gốc có .popup-separator-menu-item",

    # --- lịch ---
    ".calendar-day-base:focus": "JS 'calendar-day-base' (calendar@cinnamon.org) + ST",
    ".calendar-event-button:focus": "JS 'calendar-event-button' + ST",
    ".calendar-today:focus": "JS: calendar@cinnamon.org/applet.js dùng 'calendar-today' + ST",

    # --- IBus candidate popup ---
    ".candidate-box:selected .candidate-index": "JS 'candidate-box','candidate-index' + ST",
    ".candidate-page-button:hover": "JS 'candidate-page-button' + ST",

    # --- dialog ---
    ".dialog .dialog-button-box": "JS: js/ui/dialog.js:68 style_class 'dialog-button-box'",
    ".dialog .dialog-button:default:focus": "JS: js/ui/dialog.js:148 'dialog-button' + ST",
    ".dialog .dialog-button:focus:default": "JS + ST",
    ".dialog .dialog-button:focus:destructive-action": "JS: 'destructive-action' + ST",

    # --- notification ---
    "#notification:focus": "VENDOR: gốc có #notification + ST 'focus'",

    # --- dock / window list ---
    ".grouped-window-list-item-box:hover .grouped-window-list-item-label":
        "JS: grouped-window-list@cinnamon.org dùng cả hai class",
    ".grouped-window-list-item-box:outlined":
        "JS: grouped-window-list@cinnamon.org đặt pseudo 'outlined' khi duyệt bằng bàn phím",
    ".window-list-item-box:active": "JS 'window-list-item-box' + ST st-button.c:132 'active'",
    ".switcher-list .item-box:hover": "JS 'switcher-list','item-box' + ST 'hover'",
    ".window-close:active": "VENDOR: gốc có .window-close + ST",
    ".window-close:hover": "VENDOR + ST",

    # --- toggle switch: theme gốc Cinnamon 6.6 chỉ style .toggle-switch,
    #     nhưng js/ui/popupMenu.js VẪN đặt 'toggle-switch-us' / 'toggle-switch-intl'
    #     nên hai class đó có thật và cần style để không rơi về ảnh mặc định. ---
    ".toggle-switch-us": "JS: js/ui/popupMenu.js dùng 'toggle-switch-us'",
    ".toggle-switch-us:checked": "JS + ST: st-button.c:661 thêm 'checked'",
    ".toggle-switch-intl": "JS: js/ui/popupMenu.js dùng 'toggle-switch-intl'",
    ".toggle-switch-intl:checked": "JS + ST",

    # --- bàn phím ảo ---
    ".vkeyboard-key.enter-key:hover": "VENDOR: gốc có .vkeyboard-key.enter-key + ST",
    ".vkeyboard-key.enter-key:active": "VENDOR + ST",
    ".vkeyboard-key.enter-key:focus": "VENDOR + ST",

    # --- scrollbar: St đặt TÊN (name) chứ không phải style class ---
    "StScrollBar": "ST: type selector, GType của src/st/st-scroll-bar.c",
    "StScrollBar StButton#hhandle:active": "ST: src/st/st-scroll-bar.c đặt name 'hhandle'",
    "StScrollBar StButton#vhandle:active": "ST: src/st/st-scroll-bar.c đặt name 'vhandle'",
    "StButton:focus": "ST: type selector + st-widget.c:701 'focus'",
    "StEntry": "ST: type selector, GType của src/st/st-entry.c",
    "StEntry:focus": "ST + st-widget.c:701",
    "StEntry:insensitive": "ST + st-widget.c:1502",
}

# 15 asset mà CSS đã biên dịch tham chiếu. T05 (Agent D) phải tạo đủ.
EXPECTED_ASSETS = {
    "assets/add-workspace.svg",
    "assets/add-workspace-hover.svg",
    "assets/calendar-arrow-left.svg",
    "assets/calendar-arrow-left-hover.svg",
    "assets/calendar-arrow-right.svg",
    "assets/calendar-arrow-right-hover.svg",
    "assets/checkbox.svg",
    "assets/checkbox-off.svg",
    "assets/radio.svg",
    "assets/radio-off.svg",
    "assets/toggle-on.svg",
    "assets/toggle-off.svg",
    "assets/close.svg",
    "assets/trash-icon.svg",
    "assets/corner-ripple.svg",
}

VENDOR_DIR = REPO / "src" / "cinnamon" / "vendor" / "cinnamon-6.6-sass"
VENDOR_COMMIT = "806c1a4e8cd23e528d3446b9e3cf5a3c7a3ddf18"
VENDOR_TAG = "6.6.9"


class TestCoverageOfStockSelectors(unittest.TestCase):
    """A. Theme phải HOÀN CHỈNH (ràng buộc E6)."""

    def test_no_stock_selector_is_missing(self):
        errs = findings_for("coverage")
        self.assertEqual([str(e) for e in errs], [],
                         "thiếu selector của theme gốc — widget tương ứng sẽ MẤT STYLE hoàn toàn")

    def test_fixture_is_not_polluted(self):
        """Chống tái diễn lỗi đã gặp: fixture từng chứa 439 mục dạng '} #Tooltip'.

        Nguyên nhân: sinh fixture bằng regex `^([^@\\s/][^{}]*)\\{{` với re.M, mà
        `[^{}]` KHÔNG loại trừ dấu xuống dòng, nên nó nuốt cả `}}` của rule trước.
        """
        fx = sp.load_fixture(REPO / "tests" / "fixtures" / "cinnamon-6.6-selectors.txt")
        self.assertTrue(fx, "fixture rỗng")
        for bad in ("}", "{", "//"):
            polluted = [s for s in fx if bad in s]
            self.assertEqual(polluted, [], f"fixture còn mục bẩn chứa {bad!r}")
        ids = [s for s in fx if s.startswith("#")]
        self.assertGreaterEqual(len(ids), 5,
                                "fixture mất selector ID — marker comment đang xung đột với `#` của CSS")
        for must in ("#notification", "#Tooltip", "#LookingGlassDialog", "#altTabPopup"):
            self.assertIn(must, fx)

    def test_fixture_marker_is_not_hash(self):
        p = REPO / "tests" / "fixtures" / "cinnamon-6.6-selectors.txt"
        head = p.read_text().splitlines()[:40]
        self.assertTrue(any(l.startswith("//") for l in head),
                        "header fixture phải comment bằng `//`, không phải `#`")


class TestNoDeadSelectors(unittest.TestCase):
    """B. Không được thêm selector bịa."""

    def test_new_selectors_are_exactly_the_frozen_allowlist(self):
        compiled_css()
        have = {x for sel, _ in rules() for x in sp.split_selectors(sel)}
        fx = set(sp.load_fixture(REPO / "tests" / "fixtures" / "cinnamon-6.6-selectors.txt"))
        new = have - fx
        allowed = set(NEW_SELECTORS)
        self.assertEqual(new - allowed, set(),
                         "có selector MỚI chưa được biện minh — kiểm tra nó có thật trong "
                         "Cinnamon 6.6 không (grep js/, files/usr/share/cinnamon/, src/st/) "
                         "rồi mới thêm vào NEW_SELECTORS kèm bằng chứng")
        self.assertEqual(allowed - new, set(),
                         "NEW_SELECTORS có mục không còn xuất hiện trong output — "
                         "danh sách đang phình ra, hãy xoá mục thừa")

    def test_known_dead_selectors_are_not_used(self):
        """Các selector đã chứng minh là KHÔNG tồn tại trong Cinnamon 6.6."""
        compiled_css()
        have = {x for sel, _ in rules() for x in sp.split_selectors(sel)}
        dead = {
            ".osd-window": 'grep js/ + applets + desklets của 806c1a4e: "osd-window" = 0 kết quả',
            ".modal-dialog": 'grep như trên: "modal-dialog" = 0 kết quả (lớp thật là .dialog)',
            ".keyboard-key": "Cinnamon 6.6 dùng .vkeyboard-key, không có .keyboard-key",
            ".appmenu-item": "grep toàn bộ js/ + applets: 0 kết quả",
            ".device-box .device-labels .secondary-label":
                "cả họ .device-box/.device-labels/.primary-label đều 0 kết quả trong JS; "
                "Cinnamon 6.6 dùng họ .audio-selection-* (js/ui/audioDeviceSelection.js:111,122)",
            "StLabel:selected": "selection trong St đi qua selection-background-color của StEntry "
                                "(st-entry.c:289), không qua :selected trên StLabel",
            "StBoxLayout:selected": "như trên",
        }
        hits = sorted(s for s in dead if s in have)
        self.assertEqual(hits, [],
                         "CSS chết: " + "; ".join(f"{h} ({dead[h]})" for h in hits))

    def test_every_new_selector_has_evidence(self):
        for sel, why in NEW_SELECTORS.items():
            self.assertTrue(why.strip(), f"{sel} thiếu bằng chứng")
            self.assertRegex(why, r"(JS|ST|VENDOR)",
                             f"{sel}: bằng chứng phải ghi rõ nguồn (JS/ST/VENDOR)")


class TestAssets(unittest.TestCase):
    """C. url() phải đúng và đủ."""

    def test_effective_url_set_is_exactly_the_15_expected(self):
        compiled_css()
        eff = sp.effective_urls(rules())
        urls = {u for v in eff.values() for u in re.findall(r'url\("([^"]+)"\)', v)}
        self.assertEqual(urls - EXPECTED_ASSETS, set(),
                         "có url() lạ — hoặc là tên bịa, hoặc là url tên trần của vendor "
                         "chưa bị tầng override ghi đè")
        self.assertEqual(EXPECTED_ASSETS - urls, set(),
                         "thiếu url() so với danh sách đã chốt — vendor có asset chưa bị ghi đè")

    def test_no_bare_filename_urls_survive(self):
        """Vendor dùng url tên trần; St phân giải tương đối với THƯ MỤC file CSS
        (_st_theme_resolve_url, src/st/st-theme.c:1087-1123). Nếu một url tên trần
        còn sống sau cascade thì file đó sẽ không tồn tại ở theme root."""
        compiled_css()
        eff = sp.effective_urls(rules())
        bare = sorted({u for v in eff.values() for u in re.findall(r'url\("([^"]+)"\)', v)
                       if "/" not in u})
        self.assertEqual(bare, [],
                         f"url() tên trần vẫn thắng cascade: {bare}. "
                         "Thêm rule ghi đè ở tầng overrides, trỏ về assets/.")

    def test_corner_ripple_is_svg_not_png(self):
        """Ta thay corner-ripple.png bằng SVG để không cần bộ encode PNG."""
        compiled_css()
        eff = sp.effective_urls(rules())
        for (sel, _prop), value in eff.items():
            if sel.startswith(".ripple-box"):
                self.assertIn("assets/corner-ripple.svg", value,
                              f"{sel} vẫn trỏ về PNG: {value}")

    def test_assets_are_pending_t05_not_silently_absent(self):
        """T05 (Agent D) sở hữu src/cinnamon/assets/. Test này KHÔNG fail vì thiếu
        file — nó chỉ xác nhận trạng thái để không ai tưởng asset đã có."""
        existing = sorted(p.name for p in (REPO / "src" / "cinnamon" / "assets").glob("*")
                          ) if (REPO / "src" / "cinnamon" / "assets").is_dir() else []
        missing = sorted(a for a in EXPECTED_ASSETS
                         if not (REPO / "src" / "cinnamon" / a).exists())
        if not missing:
            self.assertEqual(len(existing), len(EXPECTED_ASSETS),
                             "assets/ có file ngoài danh sách — cập nhật EXPECTED_ASSETS "
                             "hoặc xoá file thừa")
            return
        self.assertEqual(len(missing), 15,
                         f"số asset thiếu khác 15 — danh sách url() đã đổi: {missing}")
        raise unittest.SkipTest(
            f"15 asset SVG chưa tồn tại — thuộc T05 (Agent D, src/cinnamon/assets/). "
            f"T04 chỉ chốt url() trong CSS. Đã ghi trong "
            f"docs/testing/cinnamon-selector-coverage.md mục 'Phụ thuộc T05'."
        )


class TestVendorIntegrity(unittest.TestCase):
    """Vendor phải nguyên văn — mọi khác biệt nằm trong overrides/."""

    def test_vendor_files_match_sha256_in_vendor_md(self):
        doc = (VENDOR_DIR / "VENDOR.md")
        self.assertTrue(doc.exists(), "thiếu VENDOR.md")
        text = doc.read_text()
        self.assertIn(VENDOR_COMMIT, text, "VENDOR.md thiếu commit SHA đầy đủ")
        self.assertIn(VENDOR_TAG, text, "VENDOR.md thiếu tag")
        scss = sorted(VENDOR_DIR.rglob("*.scss"))
        self.assertEqual(len(scss), 22, f"kỳ vọng 22 file scss, thấy {len(scss)}")
        checked = 0
        for p in scss:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in text:
                checked += 1
            else:
                self.fail(f"{p.relative_to(REPO)} có SHA-256 {digest} KHÔNG khớp VENDOR.md "
                          f"— vendor đã bị sửa tay, hoặc VENDOR.md chưa cập nhật")
        self.assertEqual(checked, len(scss))

    def test_no_mg_tokens_leaked_into_vendor(self):
        for p in VENDOR_DIR.rglob("*.scss"):
            self.assertNotIn("$mg-", p.read_text(),
                             f"{p.name} bị sửa tay để dùng token — vendor phải pristine")

    def test_vendor_colors_file_is_replaced_not_edited(self):
        """_colors.scss của vendor phải còn nguyên; tầng thay thế là _00-globals.scss."""
        c = VENDOR_DIR / "_colors.scss"
        self.assertTrue(c.exists(), "thiếu _colors.scss pristine")
        self.assertEqual(len(re.findall(r"^\$", c.read_text(), re.M)), 25,
                         "_colors.scss của Cinnamon 6.6 định nghĩa đúng 25 biến; "
                         "con số khác nghĩa là file đã bị sửa")
        g = REPO / "src" / "cinnamon" / "overrides" / "_00-globals.scss"
        self.assertTrue(g.exists(), "thiếu overrides/_00-globals.scss")
        gt = g.read_text()
        self.assertIn('@import "../tokens/tokens"', gt,
                      "_00-globals.scss phải import token đã sinh, không tự định nghĩa token")


if __name__ == "__main__":
    unittest.main(verbosity=2)
