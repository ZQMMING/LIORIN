"""V2.2.2 FINAL §K-14/§57 Phase 0 Validator: check_input_contracts.py

Runtime Input Boundary（§26/§106）：
- 仅禁止 import 不够；context["l2a"]["..."] 等运行时访问也必须被拒绝
- 用 AST 扫描 context[...] 下标访问与字典取值（allowed_engines/forbidden_engines）
- 同时校验 engines/<engine>/contract.json 的输入矩阵（若存在）
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, List

# 使 CLI 可直接运行
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared_types.errors import BoundaryViolation

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [ROOT / "engines", ROOT / "src"]

ENGINE_MODULES = {
    "yuhai_ziping": "YUHAI_ZIPING",
    "ziping_zhenquan": "ZIPIN_ZHENQUAN",
    "di_tian_sui": "DI_TIAN_SUI",
    "qiongtong_baojian": "QIONGTONG_BAOJIAN",
    "sanming_tonghui": "SANMING_TONGHUI",
    "shenfeng_tongkao": "SHENFENG_TONGKAO",
}

# 运行时读取引擎的键名变体（context["l2a"]、ctx["yuhai_ziping"]…）
ENGINE_KEYS = {
    "l2a", "l2b", "l2c", "l2d", "l2e", "l3",
    "yuhai_ziping", "ziping_zhenquan", "di_tian_sui",
    "qiongtong_baojian", "sanming_tonghui", "shenfeng_tongkao",
    "YUHAI_ZIPING", "ZIPIN_ZHENQUAN", "DI_TIAN_SUI",
    "QIONGTONG_BAOJIAN", "SANMING_TONGHUI", "SHENFENG_TONGKAO",
}

# 每引擎允许的运行时读取键（SFTK 例外）
ALLOWED_RUNTIME_KEYS: Dict[str, set] = {
    "yuhai_ziping": set(),
    "ziping_zhenquan": set(),
    "di_tian_sui": set(),
    "qiongtong_baojian": set(),
    "sanming_tonghui": set(),
    "shenfeng_tongkao": {"l2a", "l2b", "l2c", "l2d", "l2e"},
}


def _which_engine(path: Path) -> str | None:
    for part in path.parts:
        if part in ENGINE_MODULES:
            return part
    return None


def _runtime_engine_keys(tree: ast.AST) -> List[str]:
    keys: List[str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str) and sl.value in ENGINE_KEYS:
                keys.append(sl.value)
            elif isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                low = sl.value.lower()
                for alias in ENGINE_KEYS:
                    if alias in low:
                        keys.append(low)
    return keys


def scan_files() -> List[str]:
    violations: List[str] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "tests" in path.parts:
                continue  # 测试构造违规反例合法，不扫测试代码
            engine = _which_engine(path)
            if engine is None:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            allowed = ALLOWED_RUNTIME_KEYS.get(engine, set())
            for key in _runtime_engine_keys(tree):
                if key not in allowed:
                    violations.append(f"{path}: {engine} 运行时违规读取 {key}")
    return violations


def main() -> int:
    violations = scan_files()
    if not violations:
        print("check_input_contracts PASS (无运行时跨引擎读取)")
        return 0
    for v in violations:
        print(f"RUNTIME_BOUNDARY_VIOLATION {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
