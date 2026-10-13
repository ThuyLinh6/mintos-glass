#!/usr/bin/env python3
"""MintOS Glass — design token generator.

Một nguồn sự thật (design/tokens/*.json) -> nhiều định dạng stylesheet.

    python3 tools/tokens/generate.py                 # sinh tất cả output (scheme dark)
    python3 tools/tokens/generate.py --scheme all    # dark + light
    python3 tools/tokens/generate.py --check         # KHÔNG ghi; exit 1 nếu output lệch (CI)
    python3 tools/tokens/generate.py --report        # in báo cáo token + contrast, không ghi

Nguyên tắc (xem docs/plan/03-design-system.md §3):
  1. Deterministic — cùng input cho ra output giống hệt từng byte, không timestamp.
  2. Fail-fast — ref không phân giải được là lỗi, không đoán.
  3. Clamp blur — vượt primitives.blur.MAX_ALLOWED là lỗi (rào cứng theo bằng chứng E11).
  4. Không bịa — token có "unverified": true bị BỎ QUA khi emit và in cảnh báo.
  5. Contrast AA — mọi cặp trong 50-a11y.json phải đạt, nếu không là lỗi.

Chỉ dùng Python stdlib.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOKENS_DIR = ROOT / "design" / "tokens"
sys.path.insert(0, str(ROOT / "tools" / "lint"))

from contrast import (  # noqa: E402  (đường dẫn được thêm ở trên)
    composite,
    contrast_ratio,
    parse_hex,
    ratio_over_backdrop,
    to_rgb,
)

GENERATOR_VERSION = "1.0.0"

TOKEN_FILES = (
    "00-meta.json",
    "10-primitives.json",
    "20-semantic-dark.json",
    "20-semantic-light.json",
    "30-component.json",
    "40-motion.json",
    "50-a11y.json",
)

SCHEMES = ("dark", "light")
SEMANTIC_FILE = {"dark": "20-semantic-dark.json", "light": "20-semantic-light.json"}

# Đơn vị khi emit số. Mặc định là px.
UNITLESS_KEYS = {"blur"}
PX_KEY_OVERRIDE = {
    # leaf key -> unit, dùng khi giá trị là số trần không có ref
    "bar-radius": "px",
    "indicator-size": "px",
}
NS_UNIT = {
    "radius": "px",
    "space": "px",
    "size": "px",
    "border-width": "px",
    "blur": "",
    "duration": "ms",
}

RESERVED_KEYS = {"note", "_note", "_doc", "_blur_note", "_max_surface_note", "evidence", "phase", "unverified", "_applies_to", "_not_applies_to", "_duration_unit", "_scheme"}


class TokenError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Nạp + làm phẳng
# --------------------------------------------------------------------------- #

def load_tokens(tokens_dir: Path | None = None) -> dict[str, Any]:
    tokens_dir = tokens_dir or TOKENS_DIR
    data: dict[str, Any] = {}
    for name in TOKEN_FILES:
        path = tokens_dir / name
        if not path.exists():
            raise TokenError(f"thiếu file token: {path}")
        try:
            data[name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TokenError(f"{name}: JSON không hợp lệ — {exc}") from exc
    return data


def flatten(obj: Any, prefix: str = "", out: dict[str, Any] | None = None) -> dict[str, Any]:
    """{'a': {'b': 1}} -> {'a.b': 1}. Bỏ qua khoá bắt đầu bằng '_' và khoá ghi chú."""
    if out is None:
        out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.startswith("_") or key in RESERVED_KEYS:
                continue
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and _is_leaf_value(value):
                out[path] = value
            elif isinstance(value, dict):
                flatten(value, path, out)
            else:
                out[path] = value
    return out


def _is_leaf_value(d: dict[str, Any]) -> bool:
    """Dict là 'lá' nếu nó là một giá trị token (color/shadow/annotated), không phải nhóm."""
    keys = set(d)
    if {"ref", "alpha"} <= keys or {"value", "alpha"} <= keys:
        return True
    if {"x", "y", "blur", "color"} <= keys:
        return True
    if "value" in keys and ("note" in keys or "unverified" in keys):
        return True
    return False


# --------------------------------------------------------------------------- #
# Phân giải giá trị
# --------------------------------------------------------------------------- #

class Resolver:
    """Phân giải ref -> giá trị cụ thể, theo đúng thứ tự tầng."""

    def __init__(self, prim: dict[str, Any], sem: dict[str, Any], scheme: str) -> None:
        self.prim = prim
        self.sem = sem
        self.scheme = scheme
        self.warnings: list[str] = []
        self._cache: dict[str, Any] = {}

    # -- tra cứu thô -------------------------------------------------------- #
    def _lookup(self, path: str) -> Any:
        if path in self.sem:
            return self.sem[path]
        if path in self.prim:
            return self.prim[path]
        raise TokenError(
            f"[{self.scheme}] ref không phân giải được: '{path}' "
            f"(không có trong semantic lẫn primitives)"
        )

    # -- alpha -------------------------------------------------------------- #
    def alpha(self, value: Any, where: str) -> float:
        if isinstance(value, (int, float)):
            a = float(value)
        elif isinstance(value, str):
            a = self.number(value, where)
        else:
            raise TokenError(f"{where}: alpha phải là số hoặc ref, nhận {value!r}")
        if not 0.0 <= a <= 1.0:
            raise TokenError(f"{where}: alpha {a} ngoài khoảng [0,1]")
        return a

    # -- số ----------------------------------------------------------------- #
    def number(self, path: str, where: str) -> float:
        raw = self._lookup(path)
        if isinstance(raw, dict) and "value" in raw:
            raw = raw["value"]
        if not isinstance(raw, (int, float)):
            raise TokenError(f"{where}: '{path}' không phải số (nhận {raw!r})")
        return float(raw)

    # -- màu ---------------------------------------------------------------- #
    def color(self, node: Any, where: str) -> tuple[int, int, int, float]:
        """Trả về (r, g, b, alpha)."""
        if isinstance(node, str):
            if node.startswith("#"):
                return (*parse_hex(node), 1.0)
            target = self._lookup(node)
            return self.color(target, f"{where} -> {node}")
        if isinstance(node, dict):
            if node.get("unverified"):
                raise UnverifiedToken(where, node.get("note", ""))
            if "ref" in node:
                r, g, b, _ = self.color(node["ref"], f"{where}.ref")
                return (r, g, b, self.alpha(node["alpha"], f"{where}.alpha"))
            if "value" in node:
                base = node["value"]
                if base is None:
                    raise UnverifiedToken(where, node.get("note", ""))
                if isinstance(base, str) and base.startswith("#"):
                    return (*parse_hex(base), self.alpha(node.get("alpha", 1.0), f"{where}.alpha"))
                r, g, b, _ = self.color(base, f"{where}.value")
                return (r, g, b, self.alpha(node.get("alpha", 1.0), f"{where}.alpha"))
            raise TokenError(f"{where}: dict màu không hợp lệ — {sorted(node)}")
        raise TokenError(f"{where}: giá trị màu không hợp lệ — {node!r}")

    # -- kích thước --------------------------------------------------------- #
    def dimension(self, node: Any, where: str, leaf: str) -> tuple[float, str]:
        """Trả về (giá trị, đơn vị)."""
        if isinstance(node, str):
            ns = node.split(".")[0]
            unit = NS_UNIT.get(ns)
            if unit is None:
                raise TokenError(f"{where}: ref kích thước '{node}' không thuộc namespace có đơn vị")
            return (self.number(node, where), unit)
        if isinstance(node, dict):
            if node.get("unverified"):
                raise UnverifiedToken(where, node.get("note", ""))
            if "value" in node:
                return self.dimension(node["value"], where, leaf)
            raise TokenError(f"{where}: dict kích thước không hợp lệ — {sorted(node)}")
        if isinstance(node, (int, float)):
            unit = "" if leaf in UNITLESS_KEYS else PX_KEY_OVERRIDE.get(leaf, "px")
            return (float(node), unit)
        raise TokenError(f"{where}: kích thước không hợp lệ — {node!r}")

    # -- shadow ------------------------------------------------------------- #
    def shadow(self, node: Any, where: str) -> dict[str, Any]:
        if isinstance(node, str):
            return self.shadow(self._lookup(node), f"{where} -> {node}")
        if not isinstance(node, dict) or "x" not in node:
            raise TokenError(f"{where}: shadow phải là object có x/y/blur — nhận {node!r}")
        r, g, b, _ = self.color(node["color"], f"{where}.color")
        a = self.alpha(node.get("alpha", 1.0), f"{where}.alpha")
        return {
            "x": float(node["x"]),
            "y": float(node["y"]),
            "blur": float(node["blur"]),
            "spread": float(node.get("spread", 0.0)),
            "inset": bool(node.get("inset", False)),
            "rgb": (r, g, b),
            "alpha": a,
        }


class UnverifiedToken(TokenError):
    """Token đánh dấu unverified — KHÔNG được emit, chỉ cảnh báo."""

    def __init__(self, where: str, note: str) -> None:
        super().__init__(where)
        self.where = where
        self.note = note


# --------------------------------------------------------------------------- #
# Định dạng output
# --------------------------------------------------------------------------- #

def fmt_rgba(rgba: tuple[int, int, int, float]) -> str:
    r, g, b, a = rgba
    if a >= 1.0:
        return f"#{r:02x}{g:02x}{b:02x}"
    return f"rgba({r}, {g}, {b}, {_num(a)})"


def _num(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


def fmt_dim(value: float, unit: str) -> str:
    return f"{_num(value)}{unit}"


def fmt_shadow(sh: dict[str, Any]) -> str:
    parts = []
    if sh["inset"]:
        parts.append("inset")
    parts += [
        f"{_num(sh['x'])}px",
        f"{_num(sh['y'])}px",
        f"{_num(sh['blur'])}px",
    ]
    if sh["spread"]:
        parts.append(f"{_num(sh['spread'])}px")
    parts.append(fmt_rgba((*sh["rgb"], sh["alpha"])))
    return " ".join(parts)


def sass_name(path: str) -> str:
    return "$mg-" + path.replace(".", "-").replace("_", "-")


def define_color_name(path: str) -> str:
    return "mg_" + path.replace(".", "_").replace("-", "_")


# --------------------------------------------------------------------------- #
# Build model
# --------------------------------------------------------------------------- #

def build_scheme(
    prim_flat: dict[str, Any], sem_flat: dict[str, Any], comp_flat: dict[str, Any], scheme: str
) -> dict[str, dict[str, Any]]:
    """Phân giải toàn bộ token của một scheme thành giá trị CSS-ready."""
    resolver = Resolver(prim_flat, sem_flat, scheme)
    resolved: dict[str, dict[str, Any]] = {}

    def classify_and_resolve(path: str, node: Any, layer: str) -> None:
        leaf = path.rsplit(".", 1)[-1]
        try:
            if leaf == "blur" or (isinstance(node, str) and node.startswith("blur.")):
                value, unit = resolver.dimension(node, path, "blur")
                resolved[path] = {"kind": "dim", "value": value, "unit": unit, "layer": layer}
                return
            if isinstance(node, dict) and "x" in node and "blur" in node and "color" in node:
                resolved[path] = {"kind": "shadow", "value": resolver.shadow(node, path), "layer": layer}
                return
            if isinstance(node, str) and node.startswith("shadow."):
                resolved[path] = {"kind": "shadow", "value": resolver.shadow(node, path), "layer": layer}
                return
            if _is_colorish(node, path, prim_flat, sem_flat):
                rgba = resolver.color(node, path)
                resolved[path] = {"kind": "color", "value": rgba, "layer": layer}
                return
            value, unit = resolver.dimension(node, path, leaf)
            resolved[path] = {"kind": "dim", "value": value, "unit": unit, "layer": layer}
        except UnverifiedToken as exc:
            resolver.warnings.append(f"BỎ QUA (chưa xác minh): {exc.where} — {exc.note}")

    for path, node in prim_flat.items():
        ns = path.split(".")[0]
        if ns == "color":
            try:
                resolved[path] = {"kind": "color", "value": resolver.color(node, path), "layer": "primitive"}
            except UnverifiedToken as exc:
                resolver.warnings.append(f"BỎ QUA (chưa xác minh): {exc.where} — {exc.note}")
        elif ns == "opacity":
            resolved[path] = {"kind": "number", "value": float(node), "layer": "primitive"}
        elif ns == "font" and isinstance(node, dict) and node.get("value") is None:
            resolver.warnings.append(f"BỎ QUA (chưa xác minh): {path} — {node.get('note','')}")
        else:
            classify_and_resolve(path, node, "primitive")

    for path, node in sem_flat.items():
        classify_and_resolve(path, node, "semantic")

    for path, node in comp_flat.items():
        classify_and_resolve(path, node, "component")

    resolved["_warnings"] = {"kind": "warnings", "value": resolver.warnings, "layer": "_"}  # type: ignore[assignment]
    return resolved


def _is_colorish(node: Any, path: str, prim: dict[str, Any], sem: dict[str, Any]) -> bool:
    """Đoán xem node có phải màu không, dựa trên namespace/ref."""
    if isinstance(node, str):
        if node.startswith("#"):
            return True
        target = node.split(".")[0]
        return target in ("color", "surface", "border", "text", "status", "modal-shade")
    if isinstance(node, dict):
        if {"ref", "alpha"} <= set(node) or {"value", "alpha"} <= set(node):
            ref = node.get("ref") or node.get("value")
            if isinstance(ref, str) and ref.startswith("#"):
                return True
            head = str(ref).split(".")[0]
            return head in ("color", "surface", "border", "text", "status", "opacity")
    head = path.split(".")[0]
    return head in ("surface", "border", "text", "status")


# --------------------------------------------------------------------------- #
# Kiểm tra
# --------------------------------------------------------------------------- #

def check_blur_cap(resolved: dict[str, Any], prim_flat: dict[str, Any]) -> list[str]:
    cap = prim_flat.get("blur.MAX_ALLOWED")
    if cap is None:
        return ["primitives: thiếu blur.MAX_ALLOWED — không thể clamp (rào cứng theo E11)"]
    errors = []
    for path, entry in resolved.items():
        if entry.get("kind") != "dim" or entry.get("unit") != "":
            continue
        if not (path.split(".")[-1] == "blur" or path.startswith("blur.")):
            continue
        if path == "blur.MAX_ALLOWED":
            continue
        if entry["value"] > float(cap):
            errors.append(f"blur vượt trần: {path} = {_num(entry['value'])} > MAX_ALLOWED {_num(float(cap))}")
    return errors


def check_scheme_parity(data: dict[str, Any]) -> list[str]:
    """Dark và light phải có CÙNG tập khoá semantic (V9)."""
    dark = set(k for k in flatten(data[SEMANTIC_FILE["dark"]]) if not k.startswith("_"))
    light = set(k for k in flatten(data[SEMANTIC_FILE["light"]]) if not k.startswith("_"))
    errors = []
    for missing in sorted(dark - light):
        errors.append(f"scheme light thiếu khoá semantic: {missing}")
    for extra in sorted(light - dark):
        errors.append(f"scheme light thừa khoá semantic: {extra}")
    return errors


def check_contrast(data: dict[str, Any], schemes: dict[str, dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    a11y = data["50-a11y.json"]
    targets = a11y["contrast_targets"]
    backdrops = a11y["worst_case_backdrop"]
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    for scheme, resolved in schemes.items():
        for pair in a11y["contrast_pairs"].get(scheme, []):
            fg_key = pair.get("text") or pair.get("ui")
            bg_key = pair["on"]
            min_key = pair["min"]
            role = pair.get("role", "text")
            target = float(targets[min_key])
            try:
                fg = resolved[fg_key]["value"]
                bg = resolved[bg_key]["value"]
            except KeyError as exc:
                errors.append(f"[{scheme}] contrast pair thiếu token: {exc}")
                continue
            ratio, surf_eff, text_eff = ratio_over_backdrop(fg, bg, backdrops[scheme])
            ok = ratio >= target
            rows.append({
                "scheme": scheme, "fg": fg_key, "bg": bg_key, "min": min_key,
                "target": target, "ratio": ratio, "ok": ok, "role": role,
            })
            if not ok:
                # WCAG 1.4.11 chỉ BẮT BUỘC 3:1 cho ranh giới cần để nhận diện control.
                # Đường kẻ trang trí (role=decorative) được báo cáo nhưng không chặn build.
                if role == "decorative":
                    print(f"  · [{scheme}] INFO contrast {fg_key} trên {bg_key}: "
                          f"{ratio} < {target} — role=decorative, không chặn")
                else:
                    errors.append(
                        f"[{scheme}] FAIL contrast {fg_key} trên {bg_key}: {ratio} < {target} "
                        f"({min_key}, role={role})"
                    )
    return errors, rows


# --------------------------------------------------------------------------- #
# Emit
# --------------------------------------------------------------------------- #

HEADER = (
    "// GENERATED — TUYỆT ĐỐI KHÔNG SỬA TAY.\n"
    "// Nguồn : design/tokens/*.json\n"
    "// Tool  : tools/tokens/generate.py v{ver}\n"
    "// Scheme: {scheme}\n"
    "// Lock  : {lock}\n"
    "// Chạy `make tokens` sau khi đổi token; `make lint` sẽ phát hiện file này lệch.\n"
)


def emit_scss(resolved: dict[str, Any], scheme: str, lock: str) -> str:
    lines = [HEADER.format(ver=GENERATOR_VERSION, scheme=scheme, lock=lock)]
    warnings = resolved.pop("_warnings", {}).get("value", [])
    for w in warnings:
        lines.append(f"// WARN {w}")
    if warnings:
        lines.append("")

    order = (("primitive", "PRIMITIVES"), ("semantic", "SEMANTIC"), ("component", "COMPONENT"))
    for layer, title in order:
        block = [(p, e) for p, e in resolved.items() if e.get("layer") == layer]
        if not block:
            continue
        lines.append(f"// --- {title} ({layer}) ---")
        for path, entry in block:
            name = sass_name(path)
            kind = entry["kind"]
            if kind == "color":
                lines.append(f"{name}: {fmt_rgba(entry['value'])};")
            elif kind == "shadow":
                lines.append(f"{name}: {fmt_shadow(entry['value'])};")
            elif kind == "dim":
                lines.append(f"{name}: {fmt_dim(entry['value'], entry['unit'])};")
            elif kind == "number":
                lines.append(f"{name}: {_num(entry['value'])};")
        lines.append("")
    return "\n".join(lines)


def emit_define_color(resolved: dict[str, Any], scheme: str, lock: str) -> str:
    lines = [
        "/* GENERATED — TUYỆT ĐỐI KHÔNG SỬA TAY.",
        " * Nguồn : design/tokens/*.json",
        f" * Tool  : tools/tokens/generate.py v{GENERATOR_VERSION}",
        f" * Scheme: {scheme}",
        f" * Lock  : {lock}",
        " *",
        " * Đây là token KHÔNG GIAN TÊN RIÊNG (mg_*). T10 phải map chúng sang tên",
        " * mà libadwaita mong đợi trong defaults-light.css / defaults-dark.css",
        " * (xem docs/plan/01-survey.md E21-E23).",
        " */",
        "",
    ]
    for path, entry in resolved.items():
        if entry.get("layer") not in ("semantic", "component"):
            continue
        name = define_color_name(path)
        kind = entry["kind"]
        if kind == "color":
            lines.append(f"@define-color {name} {fmt_rgba(entry['value'])};")
        elif kind == "shadow":
            lines.append(f"/* shadow {name}: {fmt_shadow(entry['value'])} */")
        elif kind == "dim":
            lines.append(f"/* dim {name}: {fmt_dim(entry['value'], entry['unit'])} */")
    lines.append("")
    return "\n".join(lines)


def emit_markdown(
    resolved: dict[str, Any], scheme: str, lock: str, contrast_rows: list[dict[str, Any]], meta: dict[str, Any]
) -> str:
    out = [
        "# Design tokens — MintOS Glass",
        "",
        "> **GENERATED** từ `design/tokens/*.json` bởi `tools/tokens/generate.py` "
        f"v{GENERATOR_VERSION}. Không sửa tay.",
        "",
        f"- Scheme: `{scheme}`",
        f"- Lock: `{lock}`",
        f"- Accent: `{meta.get('decisions', {}).get('D3_accent', '?')}`",
        f"- Target: {meta.get('target', {}).get('distro', '?')} "
        f"(Cinnamon vendor pin `{meta.get('target', {}).get('cinnamon_vendor_pin', '?')}`)",
        f"- Đã xác minh trên máy thật: **{meta.get('target', {}).get('verified_on_target', False)}**",
        "",
        "## Semantic",
        "",
        "| Token | Giá trị | Mẫu |",
        "|---|---|---|",
    ]
    for path, entry in resolved.items():
        if entry.get("layer") != "semantic":
            continue
        if entry["kind"] == "color":
            css = fmt_rgba(entry["value"])
            swatch = css if css.startswith("#") else css
            out.append(f"| `{sass_name(path)}` | `{css}` | `{swatch}` |")
        elif entry["kind"] == "shadow":
            out.append(f"| `{sass_name(path)}` | `{fmt_shadow(entry['value'])}` | — |")
        elif entry["kind"] == "dim":
            out.append(f"| `{sass_name(path)}` | `{fmt_dim(entry['value'], entry['unit'])}` | — |")
    out += ["", "## Component", "", "| Token | Giá trị |", "|---|---|"]
    for path, entry in resolved.items():
        if entry.get("layer") != "component":
            continue
        if entry["kind"] == "color":
            out.append(f"| `{sass_name(path)}` | `{fmt_rgba(entry['value'])}` |")
        elif entry["kind"] == "shadow":
            out.append(f"| `{sass_name(path)}` | `{fmt_shadow(entry['value'])}` |")
        elif entry["kind"] == "dim":
            out.append(f"| `{sass_name(path)}` | `{fmt_dim(entry['value'], entry['unit'])}` |")
    out += [
        "",
        "## Kiểm tra tương phản WCAG",
        "",
        "Mô hình: composite bề mặt glass lên **backdrop xấu nhất** "
        f"(`{scheme}` → xem `50-a11y.json`), rồi composite chữ lên bề mặt đó.",
        "",
        "| Cặp | Vai trò | Ngưỡng | Đo được | Kết quả |",
        "|---|---|---|---|---|",
    ]
    for row in contrast_rows:
        if row["scheme"] != scheme:
            continue
        if row["ok"]:
            mark = "PASS"
        elif row.get("role") == "decorative":
            mark = "n/a (decorative)"
        else:
            mark = "**FAIL**"
        out.append(
            f"| `{row['fg']}` trên `{row['bg']}` | {row.get('role', 'text')} "
            f"| {row['target']} ({row['min']}) | {row['ratio']} | {mark} |"
        )
    warnings = resolved.get("_warnings", {}).get("value", [])
    if warnings:
        out += ["", "## Token bị bỏ qua (chưa xác minh trên máy thật)", ""]
        out += [f"- {w}" for w in warnings]
        out += ["", "Xem `docs/plan/09-verification-checklist.md` để biết cách xác minh."]
    out.append("")
    return "\n".join(out)


def compute_lock(data: dict[str, Any]) -> str:
    blob = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    blob = f"generator={GENERATOR_VERSION}\n{blob}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def run(
    schemes: tuple[str, ...],
    check: bool,
    report: bool,
    out_root: Path,
    tokens_dir: Path | None = None,
) -> int:
    data = load_tokens(tokens_dir)
    meta = data["00-meta.json"]
    lock = compute_lock(data)

    prim_flat = flatten(data["10-primitives.json"])
    comp_flat = flatten(data["30-component.json"])

    errors: list[str] = []
    errors += check_scheme_parity(data)

    built: dict[str, dict[str, Any]] = {}
    outputs: dict[Path, str] = {}
    contrast_rows: list[dict[str, Any]] = []

    for scheme in schemes:
        sem_flat = flatten(data[SEMANTIC_FILE[scheme]])
        try:
            resolved = build_scheme(prim_flat, sem_flat, comp_flat, scheme)
        except TokenError as exc:
            errors.append(f"[{scheme}] {exc}")
            continue
        errors += check_blur_cap(resolved, prim_flat)
        built[scheme] = resolved

    if built:
        cerr, contrast_rows = check_contrast(data, built)
        errors += cerr

    for scheme, resolved in built.items():
        emit = meta.get("schemes", {}).get(scheme, {}).get("emit", scheme == "dark")
        if not emit:
            print(f"[skip] scheme '{scheme}' có emit=false (Phase 2) — không sinh file")
            continue
        scss = emit_scss(dict(resolved), scheme, lock)
        css = emit_define_color(dict(resolved), scheme, lock)
        md = emit_markdown(dict(resolved), scheme, lock, contrast_rows, meta)
        for rel in meta.get("emitters", {}):
            cfg = meta["emitters"][rel]
            if cfg.get("scheme") != scheme:
                continue
            target = out_root / rel
            if cfg["format"] == "scss":
                outputs[target] = scss
            elif cfg["format"] == "define-color":
                outputs[target] = css
            elif cfg["format"] == "markdown":
                outputs[target] = md
            else:
                errors.append(f"emitter không rõ format: {rel} -> {cfg['format']}")
        # Lock KHÔNG được phụ thuộc vào --scheme trên CLI, nếu không `--scheme dark`
        # và `--scheme all` sẽ liên tục ghi đè nhau và CI báo drift giả.
        emitted_schemes = sorted(
            name for name, cfg in meta.get("schemes", {}).items() if cfg.get("emit")
        )
        outputs[out_root / "design" / "tokens.lock.json"] = json.dumps(
            {"lock": lock, "generator": GENERATOR_VERSION, "emitted_schemes": emitted_schemes},
            indent=2, ensure_ascii=False, sort_keys=True,
        ) + "\n"

    if errors:
        print("TOKEN ERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)

    if report:
        for scheme, resolved in built.items():
            print(f"\n=== scheme {scheme} ===")
            for path, entry in resolved.items():
                if path == "_warnings":
                    continue
                if entry["kind"] == "color":
                    print(f"  {path:52s} {fmt_rgba(entry['value'])}")
                elif entry["kind"] == "shadow":
                    print(f"  {path:52s} {fmt_shadow(entry['value'])}")
                elif entry["kind"] == "dim":
                    print(f"  {path:52s} {fmt_dim(entry['value'], entry['unit'])}")
                else:
                    print(f"  {path:52s} {_num(entry['value'])}")
            for w in resolved.get("_warnings", {}).get("value", []):
                print(f"  ! {w}")
        print("\n=== contrast ===")
        for row in contrast_rows:
            if row["ok"]:
                tag = "PASS"
            elif row.get("role") == "decorative":
                tag = "INFO"
            else:
                tag = "FAIL"
            print(f"  [{tag}] {row['scheme']:5s} {row.get('role','text'):10s} "
                  f"{row['fg']:22s} on {row['bg']:22s} = {row['ratio']:5} (>= {row['target']})")
        return 1 if errors else 0

    if check:
        drift = []
        for target, content in sorted(outputs.items()):
            current = target.read_text(encoding="utf-8") if target.exists() else None
            if current != content:
                drift.append(str(target.relative_to(out_root)))
        if drift:
            print("GENERATED FILES LỆCH (chạy `make tokens`):", file=sys.stderr)
            for d in drift:
                print(f"  ✗ {d}", file=sys.stderr)
            return 1
        print(f"OK — {len(outputs)} file generated khớp token (lock {lock})")
        return 1 if errors else 0

    for target, content in sorted(outputs.items()):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print(f"OK — đã sinh {len(outputs)} file (lock {lock})")
    for target in sorted(outputs):
        print(f"  → {target.relative_to(out_root)}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Sinh stylesheet từ design tokens.")
    ap.add_argument("--scheme", choices=("dark", "light", "all"), default="dark")
    ap.add_argument("--check", action="store_true", help="không ghi; exit 1 nếu output lệch")
    ap.add_argument("--report", action="store_true", help="in báo cáo token + contrast")
    ap.add_argument("--out-root", type=Path, default=ROOT)
    ap.add_argument("--tokens-dir", type=Path, default=None,
                    help="thư mục token thay thế (dùng cho test negative-case)")
    args = ap.parse_args(argv)
    schemes = SCHEMES if args.scheme == "all" else (args.scheme,)
    try:
        return run(schemes, args.check, args.report, args.out_root, args.tokens_dir)
    except TokenError as exc:
        print(f"TOKEN ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
