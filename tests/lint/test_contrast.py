#!/usr/bin/env python3
"""Test Tầng 1 (offline) cho phép đo tương phản WCAG.

Các giá trị chuẩn dùng để kiểm chứng công thức lấy từ WCAG 2.1
(#767676 trên trắng = 4.54:1 là ngưỡng kinh điển của AA body text).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lint"))
sys.path.insert(0, str(ROOT / "tools" / "tokens"))

from contrast import (  # noqa: E402
    composite,
    contrast_ratio,
    parse_hex,
    ratio_over_backdrop,
    to_rgb,
)

TOKENS = ROOT / "design" / "tokens"


class TestContrastMath(unittest.TestCase):
    def test_black_on_white_is_21(self):
        ratio = contrast_ratio(to_rgb(parse_hex("#000000")), to_rgb(parse_hex("#ffffff")))
        self.assertAlmostEqual(ratio, 21.0, delta=0.01)

    def test_known_wcag_threshold_values(self):
        cases = {
            "#767676": 4.54,   # đúng ngưỡng AA
            "#777777": 4.48,   # trượt AA một chút
            "#595959": 7.0,    # ngưỡng AAA
        }
        white = to_rgb(parse_hex("#ffffff"))
        for colour, expected in cases.items():
            with self.subTest(colour=colour):
                got = contrast_ratio(to_rgb(parse_hex(colour)), white)
                self.assertAlmostEqual(got, expected, delta=0.03)

    def test_symmetry(self):
        a = to_rgb(parse_hex("#3ddc97"))
        b = to_rgb(parse_hex("#0b0c0e"))
        self.assertEqual(contrast_ratio(a, b), contrast_ratio(b, a))

    def test_composite_opaque_foreground_ignores_backdrop(self):
        fg = to_rgb(parse_hex("#17181c"), 1.0)
        out = composite(fg, to_rgb(parse_hex("#ffffff"), 1.0))
        self.assertEqual(out[:3], (0x17, 0x18, 0x1C))

    def test_composite_half_alpha_is_midpoint(self):
        out = composite(to_rgb(parse_hex("#ffffff"), 0.5), to_rgb(parse_hex("#000000"), 1.0))
        for channel in out[:3]:
            self.assertAlmostEqual(channel, 128, delta=1)

    def test_glass_over_white_backdrop_lightens_surface(self):
        """Mô hình worst-case: glass tối trên wallpaper trắng phải SÁNG LÊN."""
        surface = to_rgb(parse_hex("#121316"), 0.72)
        ratio, surf_eff, _ = ratio_over_backdrop(
            to_rgb(parse_hex("#ffffff"), 0.92), surface, "#ffffff"
        )
        self.assertGreater(surf_eff[0], 0x12)
        self.assertGreater(ratio, 1.0)

    def test_worst_case_is_worse_than_opaque(self):
        """Đo trên backdrop xấu nhất phải cho tỉ lệ THẤP HƠN đo trên nền opaque."""
        text = to_rgb(parse_hex("#ffffff"), 0.92)
        glass = to_rgb(parse_hex("#121316"), 0.72)
        opaque = to_rgb(parse_hex("#121316"), 1.0)
        worst, _, _ = ratio_over_backdrop(text, glass, "#ffffff")
        best = contrast_ratio(composite(text, opaque), opaque)
        self.assertLess(worst, best)

    def test_parse_hex_rejects_garbage(self):
        for bad in ("17181c", "#12345", "#gggggg", "rgba(0,0,0,1)"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_hex(bad)


class TestTokenContrastBudget(unittest.TestCase):
    """Mọi cặp trong 50-a11y.json phải đạt ngưỡng, trừ role=decorative."""

    @classmethod
    def setUpClass(cls):
        cls.a11y = json.loads((TOKENS / "50-a11y.json").read_text(encoding="utf-8"))
        cls.prim = json.loads((TOKENS / "10-primitives.json").read_text(encoding="utf-8"))
        cls.sem = {
            "dark": json.loads((TOKENS / "20-semantic-dark.json").read_text(encoding="utf-8")),
            "light": json.loads((TOKENS / "20-semantic-light.json").read_text(encoding="utf-8")),
        }

    def _flat(self, obj, prefix=""):
        out = {}
        for key, value in obj.items():
            if key.startswith("_"):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and not ({"ref", "alpha"} <= set(value)):
                out.update(self._flat(value, path))
            else:
                out[path] = value
        return out

    def _rgba(self, node, scheme):
        sem = self._flat(self.sem[scheme])
        prim = self._flat(self.prim)
        if isinstance(node, str) and node.startswith("#"):
            return (*parse_hex(node), 1.0)
        if isinstance(node, str):
            target = sem.get(node) or prim.get(node)
            self.assertIsNotNone(target, f"ref {node} không phân giải được")
            return self._rgba(target, scheme)
        alpha = node["alpha"]
        if isinstance(alpha, str):
            alpha = prim[alpha]
        base = node.get("ref") or node.get("value")
        r, g, b, _ = self._rgba(base, scheme)
        return (r, g, b, float(alpha))

    def test_every_enforced_pair_meets_its_target(self):
        failures = []
        for scheme, pairs in self.a11y["contrast_pairs"].items():
            backdrop = self.a11y["worst_case_backdrop"][scheme]
            sem = self._flat(self.sem[scheme])
            for pair in pairs:
                if pair.get("role") == "decorative":
                    continue
                fg_key = pair.get("text") or pair.get("ui")
                target = self.a11y["contrast_targets"][pair["min"]]
                fg = self._rgba(sem[fg_key], scheme)
                bg = self._rgba(sem[pair["on"]], scheme)
                ratio, _, _ = ratio_over_backdrop(fg, bg, backdrop)
                if ratio < target:
                    failures.append(f"{scheme}: {fg_key} trên {pair['on']} = {ratio} < {target}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_decorative_pairs_are_documented(self):
        for scheme, pairs in self.a11y["contrast_pairs"].items():
            for pair in pairs:
                if pair.get("role") == "decorative":
                    self.assertIn("_note", pair, f"{scheme}: cặp decorative thiếu giải thích")

    def test_on_accent_text_is_not_white_on_mint(self):
        """Trắng trên mint.500 chỉ ~1.9:1 — quyết định thiết kế đã chốt là chữ tối."""
        sem = self._flat(self.sem["dark"])
        fg = self._rgba(sem["text.on-accent"], "dark")
        bg = self._rgba(sem["status.accent"], "dark")
        ratio, _, _ = ratio_over_backdrop(fg, bg, "#ffffff")
        self.assertGreaterEqual(ratio, 4.5)
        self.assertLess(fg[0], 64, "text.on-accent phải là màu tối, không phải trắng")


if __name__ == "__main__":
    unittest.main(verbosity=2)
