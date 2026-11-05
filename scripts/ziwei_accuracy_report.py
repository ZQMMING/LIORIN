#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紫微准确率总报告（一条命令跑完所有准确率证据）。

覆盖四条独立来源：
1. 原典锚点（无 node）：起紫微星诀三例 / 命身 / 十四星 / 四化 / 闰月 / 十二神；
2. 原生实现 vs 外部数据集 Golden 80（语义换算后逐字段）；
3. 原生实现 vs 生产适配器（随机抽样，13 字段）；
4. 双后端一致性（引擎 iztro↔native、适配器 iztro↔native）。

用法：
    $env:PYTHONPATH='src;.'; $env:PYTHONUTF8='1'
    python scripts/ziwei_accuracy_report.py            # 默认抽样 120 盘
    python scripts/ziwei_accuracy_report.py 300

说明：需要 node + node_modules/iztro 才会跑 3/4 两项；缺 iztro 时这几项标 SKIP，
并明确提示「只跑了原典锚点 + 原生实现」——不会把 SKIP 当 PASS。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _run(label: str, args: list[str]) -> tuple[str, str]:
    proc = subprocess.run([PY, *args], cwd=str(ROOT), capture_output=True,
                          text=True, encoding="utf-8", timeout=900)
    out = (proc.stdout or "") + (proc.stderr or "")
    status = "PASS" if proc.returncode == 0 else "FAIL"
    return status, out.strip()


def main() -> int:
    n = sys.argv[1] if len(sys.argv) > 1 else "120"
    checks = [
        ("原典锚点（无 node）", ["-m", "pytest", "tests/test_ziwei_natal_anchors.py",
                             "tests/test_ziwei_native_backend.py", "-q"]),
        ("Golden 80 案逐字段", ["scripts/ziwei_golden_accuracy.py"]),
        ("原生 vs 生产适配器（13 字段）", ["scripts/ziwei_natal_verify.py", n]),
        ("引擎双后端一致性", ["scripts/ziwei_backend_parity.py"]),
        ("适配器双后端一致性", ["scripts/ziwei_adapter_parity.py"]),
        ("亮度表外部取证", ["scripts/ziwei_brightness_audit.py"]),
    ]

    rows = []
    details = []
    for label, args in checks:
        status, out = _run(label, args)
        if "node_modules/iztro 缺失" in out or "iztro 不可用" in out:
            status = "SKIP"
        rows.append((label, status))
        details.append((label, out))

    width = max(len(r[0]) for r in rows)
    print("=" * 78)
    print("紫微斗数准确率总报告（原生实现 vs 生产实现 vs 外部数据）")
    print("=" * 78)
    for label, status in rows:
        print(f"  {label:<{width}}  {status}")
    print("-" * 78)
    ok = all(s in ("PASS", "SKIP") for _, s in rows)
    skipped = [l for l, s in rows if s == "SKIP"]
    if skipped:
        print(f"  SKIP（缺 node/iztro，不代表通过）: {', '.join(skipped)}")
    print("  结论：" + ("全部可执行项 PASS" if ok else "存在 FAIL，见下方明细"))
    print("=" * 78)

    for label, out in details:
        tail = "\n".join(out.splitlines()[-12:])
        print(f"\n[{label}]\n{tail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
