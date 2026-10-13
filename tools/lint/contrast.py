#!/usr/bin/env python3
"""MintOS Glass — WCAG 2.1 contrast utilities.

Mô hình đo cho bề mặt BÁN TRONG SUỐT ("glass"):

    Bề mặt glass = màu nền có alpha, nằm trên một wallpaper KHÔNG biết trước.
    Để không tự lừa mình, ta composite bề mặt lên BACKDROP XẤU NHẤT:
      - dark scheme  -> backdrop trắng (#ffffff): glass tối bị sáng lên,
                        chữ sáng mất tương phản. Đây là trường hợp tệ nhất.
      - light scheme -> backdrop đen (#000000).

    Chữ cũng có alpha (ví dụ text.primary = trắng @0.92) nên được composite
    lên bề mặt đã composite, rồi mới đo tỉ lệ tương phản.

Chỉ dùng Python stdlib. Không dependency.
"""

from __future__ import annotations

import math

__all__ = [
    "parse_hex",
    "to_rgb",
    "composite",
    "relative_luminance",
    "contrast_ratio",
    "meets",
]


def parse_hex(value: str) -> tuple[int, int, int]:
    """'#1c1e22' -> (28, 30, 34). Chấp nhận '#rgb' shorthand."""
    s = value.strip()
    if not s.startswith("#"):
        raise ValueError(f"not a hex colour: {value!r}")
    s = s[1:]
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"bad hex length: {value!r}")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def to_rgb(rgb: tuple[int, int, int], alpha: float = 1.0) -> tuple[int, int, int, float]:
    return (rgb[0], rgb[1], rgb[2], alpha)


def composite(
    fg: tuple[int, int, int, float], bg: tuple[int, int, int, float]
) -> tuple[int, int, int, float]:
    """Source-over. Trả về RGB opaque (alpha đã được flatten vào màu)."""
    fa = fg[3]
    ba = bg[3]
    out_a = fa + ba * (1.0 - fa)
    if out_a <= 0.0:
        return (0, 0, 0, 0.0)
    channels = []
    for i in range(3):
        v = (fg[i] * fa + bg[i] * ba * (1.0 - fa)) / out_a
        channels.append(int(round(min(255.0, max(0.0, v)))))
    return (channels[0], channels[1], channels[2], 1.0)


def _linearise(channel8: int) -> float:
    c = channel8 / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int, float]) -> float:
    r, g, b = (_linearise(rgb[0]), _linearise(rgb[1]), _linearise(rgb[2]))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[int, int, int, float], b: tuple[int, int, int, float]) -> float:
    """WCAG contrast ratio của hai màu ĐÃ opaque. Làm tròn 2 chữ số để so sánh ổn định."""
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def meets(ratio: float, target: float, tolerance: float = 0.0) -> bool:
    return ratio >= (target - tolerance)


def ratio_over_backdrop(
    text: tuple[int, int, int, float],
    surface: tuple[int, int, int, float],
    backdrop_hex: str,
) -> tuple[float, tuple[int, int, int, float], tuple[int, int, int, float]]:
    """Composite surface lên backdrop, rồi text lên kết quả, rồi đo.

    Trả về (ratio, surface_effective, text_effective).
    """
    bd = to_rgb(parse_hex(backdrop_hex), 1.0)
    surf = composite(surface, bd)
    txt = composite(text, surf)
    return contrast_ratio(txt, surf), surf, txt


def _selftest() -> int:
    """Kiểm tra nhanh các giá trị chuẩn của WCAG để chắc hàm đúng."""
    checks = [
        ("#000000", "#ffffff", 21.0),
        ("#777777", "#ffffff", 4.48),
        ("#767676", "#ffffff", 4.54),
    ]
    failures = []
    for a, b, expected in checks:
        got = contrast_ratio(to_rgb(parse_hex(a), 1.0), to_rgb(parse_hex(b), 1.0))
        if math.isclose(got, expected, abs_tol=0.02):
            continue
        failures.append(f"{a} on {b}: got {got}, expected ~{expected}")
    if failures:
        print("contrast self-test FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("contrast self-test OK (3/3 giá trị chuẩn WCAG khớp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
