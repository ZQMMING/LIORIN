"""V2.2.2 FINAL §K-13/§57 Phase 0 Validator: check_import_boundaries.py

Static Import Boundary（§25/§106）：
- 禁止 L2B import L2A、L2C import L2B、L2D import L2C、L2E import L2D 及任何横向 Engine import
- SFTK 是唯一允许读取 L2A-L2E public contract 的引擎（读取 ≠ import 实现）
- 用 AST 分析 engines/ 与 src/tongshu/ 下 Python 源码的 import 语句
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

# 引擎模块名 -> EngineID
ENGINE_MODULES = {
    "yuhai_ziping": "YUHAI_ZIPING",
    "ziping_zhenquan": "ZIPING_ZHENQUAN",
    "di_tian_sui": "DITIANSUI",
    "qiongtong_baojian": "QIONGTONG_BAOJIAN",
    "sanming_tonghui": "SANMING_TONGHUI",
    "shenfeng_tongkao": "SHENFENG_TONGKAO",
}

# V2.2.2 §K-1~K-6：各引擎允许 import 的引擎模块（空=禁止任何引擎 import）
ALLOWED_IMPORTS: Dict[str, List[str]] = {
    "yuhai_ziping": [],
    "ziping_zhenquan": [],
    "di_tian_sui": [],
    "qiongtong_baojian": [],
    "sanming_tonghui": [],
    "shenfeng_tongkao": ["yuhai_ziping", "ziping_zhenquan", "di_tian_sui", "qiongtong_baojian", "sanming_tonghui"],
}


def _which_engine(path: Path) -> str | None:
    """判断文件属于哪个引擎（按路径中的引擎目录名）。"""
    for part in path.parts:
        if part in ENGINE_MODULES:
            return part
    return None


def _imported_engines(node: ast.AST) -> List[str]:
    found: List[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                top = alias.name.split(".")[0]
                if top in ENGINE_MODULES and top not in found:
                    found.append(top)
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                top = n.module.split(".")[0]
                if top in ENGINE_MODULES and top not in found:
                    found.append(top)
    return found


def scan_files() -> List[str]:
    """返回违规文件列表；每项为 '路径: 违规import'。"""
    violations: List[str] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "tests" in path.parts:
                continue  # 测试构造违规 import 反例合法，不扫测试代码
            engine = _which_engine(path)
            if engine is None:
                continue  # 共享/非引擎代码不扫描（Phase 0 只查引擎隔离）
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue  # 语法错误由测试/CI 处理，不是本项职责
            imported = _imported_engines(tree)
            allowed = ALLOWED_IMPORTS.get(engine, [])
            for mod in imported:
                if mod not in allowed:
                    violations.append(f"{path}: {engine} 违规 import {mod}")
    return violations


def main() -> int:
    violations = scan_files()
    if not violations:
        print("check_import_boundaries PASS (无横向 Engine import)")
        return 0
    for v in violations:
        print(f"BOUNDARY_VIOLATION {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
