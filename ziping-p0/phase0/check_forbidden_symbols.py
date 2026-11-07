"""V2.2.2 FINAL §105/§57 Phase 0 Validator: check_forbidden_symbols.py

Forbidden Symbol Scan 重点检查：
score / confidence / probability / percentage / vote / consensus /
LLM / recalculate / sxtwl / charting dependency

扫描 engines/ 与 src/ 下 Python 源码的标识符与字符串字面量。
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import List, Set

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [ROOT / "engines", ROOT / "src"]

# §105 禁用词表（标识符级）
FORBIDDEN_IDENTIFIERS: Set[str] = {
    "score", "scores", "total_score", "weighted_score", "percentage",
    "probability", "probabilities", "confidence", "vote", "votes",
    "consensus", "llm", "llm_judgment", "recalculate", "rechart",
    "sxtwl", "charting_dependency", "weighted_average", "majority_vote",
}

# 字符串字面量级禁用片段（正则词边界匹配；只保留输出字段级全局禁词。
# sxtwl/llm 等调用类禁词由标识符级（FORBIDDEN_IDENTIFIERS）检测，避免误伤契约定义层如 forbidden_input 列表）
FORBIDDEN_STRING_FRAGMENTS: List[str] = [
    "FINAL_USE_SHEN", "GLOBAL_USE_SHEN", "UNIFIED_USE_SHEN",
    "total_score", "weighted_score", "majority_vote", "consensus",
]

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _iter_identifiers(tree: ast.AST):
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            yield n.id
        elif isinstance(n, ast.Attribute):
            yield n.attr
        elif isinstance(n, ast.arg):
            yield n.arg
        elif isinstance(n, ast.FunctionDef):
            yield n.name
        elif isinstance(n, ast.ClassDef):
            yield n.name


def _iter_strings(tree: ast.AST):
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def scan_files() -> List[str]:
    violations: List[str] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "tests" in path.parts:
                continue  # 测试构造违规反例合法，不扫测试代码
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for ident in _iter_identifiers(tree):
                low = ident.lower()
                if low in FORBIDDEN_IDENTIFIERS:
                    violations.append(f"{path}: 禁用标识符 '{ident}'")
            for s in _iter_strings(tree):
                for frag in FORBIDDEN_STRING_FRAGMENTS:
                    # 词边界匹配：前后不得为字母/数字/下划线，避免误伤禁词表定义（如 llm_judgment）
                    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(frag)}(?![A-Za-z0-9_])", s, re.IGNORECASE):
                        violations.append(f"{path}: 禁用字符串 '{frag}'")
    return violations


def main() -> int:
    violations = scan_files()
    if not violations:
        print("check_forbidden_symbols PASS (无禁用符号)")
        return 0
    for v in violations:
        print(f"FORBIDDEN_SYMBOL {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
