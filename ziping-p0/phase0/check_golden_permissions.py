"""V2.2.2 FINAL §54-55/§57 Phase 0 Validator: check_golden_permissions.py

Golden 权限（§55/§94）：
- Agent: READ / RUN / REPORT
- Agent: CANNOT CREATE FINAL GOLDEN / CANNOT MODIFY APPROVED GOLDEN / CANNOT DELETE GOLDEN
- Human Architect: CREATE / APPROVE / FREEZE
- CI: REJECT unauthorized Golden modifications

扫描 engines/ 与 src/ 下代码中对 golden 的写操作（write/open('w')/remove/unlink/os.remove）。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [ROOT / "engines", ROOT / "src"]

GOLDEN_DIR_TOKENS = ("golden", "technical_golden", "business_golden")

# 写文件 / 删除 / 重命名等危险调用
WRITE_CALLS = {"open", "write_text", "write_bytes", "unlink", "remove", "rename", "replace", "os.remove", "os.unlink", "os.rename", "shutil.move"}
WITH_WRITE_MODE = ("w", "wb", "a", "ab", "w+", "a+")


def _is_golden_path(node: ast.AST) -> bool:
    """粗略判断表达式是否指向 golden 目录/文件名。"""
    parts: List[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            parts.append(n.value.lower())
    return any(tok in " ".join(parts) for tok in GOLDEN_DIR_TOKENS)


def scan_files() -> List[str]:
    violations: List[str] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "tests" in path.parts:
                continue  # 测试构造反例合法，不扫测试代码
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    fn = n.func
                    name = None
                    if isinstance(fn, ast.Name):
                        name = fn.id
                    elif isinstance(fn, ast.Attribute):
                        name = fn.attr
                    if name is None:
                        continue
                    if name in WRITE_CALLS and _is_golden_path(n):
                        violations.append(f"{path}: 疑似 Golden 写操作 {name}")
                    if name == "open" and n.args:
                        first = n.args[0]
                        if _is_golden_path(first):
                            mode = "r"
                            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                                mode = str(n.args[1].value)
                            elif any(isinstance(k, ast.keyword) and k.arg == "mode" and isinstance(k.value, ast.Constant) for k in n.keywords):
                                mode = next(k.value.value for k in n.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant))
                            if any(m.startswith(t) for t in WITH_WRITE_MODE):
                                violations.append(f"{path}: Golden 目录文件以写模式 open")
    return violations


def main() -> int:
    violations = scan_files()
    if not violations:
        print("check_golden_permissions PASS (无 Golden 写操作)")
        return 0
    for v in violations:
        print(f"GOLDEN_PERMISSION_VIOLATION {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
