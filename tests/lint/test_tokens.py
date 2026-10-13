#!/usr/bin/env python3
"""Test Tầng 1 (offline) cho design tokens.

Chạy: python3 -m unittest discover -s tests -v
Chỉ dùng stdlib (unittest) — KHÔNG cần pytest, vì sandbox và máy người dùng
đều có sẵn python3 nhưng không chắc có pytest.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS_DIR = ROOT / "design" / "tokens"
GENERATOR = ROOT / "tools" / "tokens" / "generate.py"
PY = sys.executable

TOKEN_FILES = (
    "00-meta.json", "10-primitives.json", "20-semantic-dark.json",
    "20-semantic-light.json", "30-component.json", "40-motion.json", "50-a11y.json",
)


def run_generator(*args: str, tokens_dir: Path | None = None, out_root: Path | None = None):
    cmd = [PY, str(GENERATOR), *args]
    if tokens_dir:
        cmd += ["--tokens-dir", str(tokens_dir)]
    if out_root:
        cmd += ["--out-root", str(out_root)]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


class TestTokenFiles(unittest.TestCase):
    def test_all_token_files_exist_and_are_valid_json(self):
        for name in TOKEN_FILES:
            with self.subTest(token_file=name):
                path = TOKENS_DIR / name
                self.assertTrue(path.exists(), f"thiếu {path}")
                json.loads(path.read_text(encoding="utf-8"))

    def test_schema_file_is_valid(self):
        json.loads((TOKENS_DIR / "token-schema.json").read_text(encoding="utf-8"))

    def test_primitives_own_all_hex_values(self):
        """Chỉ tầng primitive được chứa hex. Semantic/component không được hard-code màu."""
        prim = (TOKENS_DIR / "10-primitives.json").read_text(encoding="utf-8")
        self.assertRegex(prim, r"#[0-9a-fA-F]{6}", "primitives phải định nghĩa màu hex")
        for name in ("20-semantic-dark.json", "20-semantic-light.json", "30-component.json"):
            data = json.loads((TOKENS_DIR / name).read_text(encoding="utf-8"))
            offenders = []
            stack = [((), data)]
            while stack:
                path, node = stack.pop()
                if isinstance(node, dict):
                    for k, v in node.items():
                        stack.append((path + (k,), v))
                elif isinstance(node, str) and node.startswith("#") and len(node) == 7:
                    # ngoại lệ có chủ đích: màu chữ icon desktop Nemo (giữ nguyên giá trị gốc
                    # của nemo-style-application.css để không giảm độ đọc — ràng buộc F10)
                    if "desktop-label" not in ".".join(path):
                        offenders.append(".".join(path) + " = " + node)
            self.assertEqual(
                offenders, [],
                f"{name} hard-code hex ngoài tầng primitive: {offenders}"
            )


class TestGenerator(unittest.TestCase):
    def test_generator_exits_zero(self):
        res = run_generator("--scheme", "dark")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_generated_files_are_up_to_date(self):
        res = run_generator("--scheme", "dark", "--check")
        self.assertEqual(
            res.returncode, 0,
            "file generated lệch token — chạy `make tokens`\n" + res.stdout + res.stderr,
        )

    def test_deterministic_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a"; b = Path(tmp) / "b"
            for out in (a, b):
                res = run_generator("--scheme", "dark", out_root=out)
                self.assertEqual(res.returncode, 0, res.stderr)
            files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
            self.assertTrue(files, "không sinh ra file nào")
            for rel in files:
                with self.subTest(file=str(rel)):
                    self.assertEqual(
                        (a / rel).read_bytes(), (b / rel).read_bytes(),
                        "output không deterministic",
                    )

    def test_light_scheme_is_not_emitted_in_phase_one(self):
        """D-2 = dark trước. Light được ĐỊNH NGHĨA nhưng chưa emit."""
        meta = json.loads((TOKENS_DIR / "00-meta.json").read_text(encoding="utf-8"))
        self.assertTrue(meta["schemes"]["dark"]["emit"])
        self.assertFalse(meta["schemes"]["light"]["emit"])
        res = run_generator("--scheme", "all")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("emit=false", res.stdout)

    def test_scheme_parity_dark_light(self):
        """Dark và light phải cùng tập khoá semantic, nếu không V9 không thể đạt."""
        res = run_generator("--scheme", "all", "--report")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_unverified_tokens_are_not_emitted(self):
        scss = (ROOT / "src" / "cinnamon" / "tokens" / "_tokens.scss").read_text(encoding="utf-8")
        self.assertNotIn("$mg-font-family:", scss, "font.family chưa xác minh, không được emit")
        self.assertNotIn("$mg-size-titlebar-height:", scss, "chưa đo trên máy thật")
        self.assertIn("WARN", scss, "phải in cảnh báo cho token bị bỏ qua")

    def test_no_blur_in_emitted_tokens_by_default(self):
        """A6: mặc định tắt blur. Token blur tồn tại nhưng mọi component phải <= trần."""
        for rel in ("src/cinnamon/tokens/_tokens.scss", "src/libadwaita/tokens.css"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            for line in text.splitlines():
                if line.strip().startswith("//") or line.strip().startswith("*"):
                    continue
                if "panel" in line and "blur" in line:
                    self.assertNotRegex(line, r"blur[^;]*:\s*[1-9]", "panel không được bật blur (E11)")


class TestBlurCapIsEnforced(unittest.TestCase):
    """Rào cứng theo E11: generator phải TỪ CHỐI blur vượt trần."""

    def _mutated_tokens(self, mutate) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="mg-tokens-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for name in TOKEN_FILES + ("token-schema.json",):
            src = TOKENS_DIR / name
            if src.exists():
                shutil.copy2(src, tmp / name)
        mutate(tmp)
        return tmp

    def test_rejects_blur_above_max_allowed(self):
        def bump(tmp: Path):
            p = tmp / "10-primitives.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["blur"]["lg"] = data["blur"]["MAX_ALLOWED"] + 5
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        res = run_generator("--scheme", "dark", "--report", tokens_dir=self._mutated_tokens(bump))
        self.assertNotEqual(res.returncode, 0, "phải fail khi blur vượt trần")
        self.assertIn("blur vượt trần", res.stderr)

    def test_rejects_unresolvable_ref(self):
        def break_ref(tmp: Path):
            p = tmp / "20-semantic-dark.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["surface"]["base"] = {"ref": "color.khong-ton-tai.999", "alpha": 1.0}
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        res = run_generator("--scheme", "dark", "--report", tokens_dir=self._mutated_tokens(break_ref))
        self.assertNotEqual(res.returncode, 0, "phải fail khi ref không phân giải được")
        self.assertIn("không phân giải được", res.stderr)

    def test_rejects_alpha_out_of_range(self):
        def bad_alpha(tmp: Path):
            p = tmp / "20-semantic-dark.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            data["surface"]["base"] = {"ref": "color.gray.900", "alpha": 1.7}
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        res = run_generator("--scheme", "dark", "--report", tokens_dir=self._mutated_tokens(bad_alpha))
        self.assertNotEqual(res.returncode, 0, "phải fail khi alpha ngoài [0,1]")
        self.assertIn("ngoài khoảng", res.stderr)

    def test_rejects_scheme_parity_break(self):
        def drop_key(tmp: Path):
            p = tmp / "20-semantic-light.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            del data["surface"]["base"]
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        res = run_generator("--scheme", "all", "--report", tokens_dir=self._mutated_tokens(drop_key))
        self.assertNotEqual(res.returncode, 0, "phải fail khi dark/light lệch khoá")
        self.assertIn("thiếu khoá semantic", res.stderr)


class TestDecisionsAreRecorded(unittest.TestCase):
    def test_meta_records_the_four_decisions(self):
        meta = json.loads((TOKENS_DIR / "00-meta.json").read_text(encoding="utf-8"))
        d = meta["decisions"]
        self.assertIn("grouped-window-list", d["D1_dock"])
        self.assertEqual(d["D3_accent"], "mint-green")
        self.assertIn("Dark trước", d["D2_variants"])
        self.assertIn(".local/share/themes", d["D4_install_path"])

    def test_target_is_marked_unverified(self):
        """Không được nhận vơ là đã xác minh trên máy người dùng."""
        meta = json.loads((TOKENS_DIR / "00-meta.json").read_text(encoding="utf-8"))
        self.assertIs(meta["target"]["verified_on_target"], False)

    def test_accent_really_is_mint(self):
        prim = json.loads((TOKENS_DIR / "10-primitives.json").read_text(encoding="utf-8"))
        self.assertEqual(prim["color"]["mint"]["500"], "#3ddc97")
        sem = json.loads((TOKENS_DIR / "20-semantic-dark.json").read_text(encoding="utf-8"))
        self.assertEqual(sem["status"]["accent"]["ref"], "color.mint.500")


if __name__ == "__main__":
    unittest.main(verbosity=2)
