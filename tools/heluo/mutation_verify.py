#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""河洛引擎 · 变异验证总入口（2026-10-07）

守卫测试全绿**不等于**规则被锁住了。若断言写错、被测函数恰好返回期望值，
或断言压根没跑到出错的那段代码，绿就是假的。本脚本逐条往源码注入已知错误，
要求对应守卫测试**必须变红**，并确认还原后基线一致。

每条守卫在入库前都必须挂在某一个变异清单下；新增守卫请一并在此登记。

用法（在仓库根目录）::

    python tools/heluo/mutation_verify.py            # 跑全部
    python tools/heluo/mutation_verify.py --only shu_ge

工程约束（都是实际踩过的坑，不是泛泛之谈）：

1. ``PYTHONPYCACHEPREFIX`` 隔离字节码。变异还原时若 mtime 落在同一秒、
   且变异前后**字节数相同**（如 ``(0, 0, 0, 0)`` → ``(9, 9, 9, 9)``），
   Python 会直接复用陈旧 ``.pyc``，让「还原后复跑」假红——
   先天策数那次就栽在这里，误以为源码没还原。
2. 每条变异还原后校验内容哈希，确保真的回到初始字节。
3. 基线先跑一次：未变异就不绿的话，变异验证没有意义。

退出码：0 = 全部变异被抓住；1 = 有变异存活 / 锚点未命中 / 还原失败。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUITES = {
    "xian_tian_ce_shu": ("tools/heluo/mutation_verify_xian_tian_ce_shu.py",),
    "shu_ge": ("tools/heluo/mutation_verify_shu_ge.py",),
    "jiehhou": ("tools/heluo/mutation_verify_jiehhou.py",),
}


def main(argv: list[str]) -> int:
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    if only and only not in SUITES:
        print(f"未知套件：{only}；可选：{', '.join(SUITES)}")
        return 1

    failed = []
    for name, scripts in SUITES.items():
        if only and name != only:
            continue
        print(f"\n{'#' * 70}\n# 变异套件：{name}\n{'#' * 70}")
        for s in scripts:
            print(f"\n--- {s} ---")
            rc = subprocess.call([sys.executable, str(ROOT / s)], cwd=str(ROOT))
            if rc != 0:
                failed.append(s)

    print(f"\n{'=' * 70}")
    if failed:
        print(f"❌ 以下套件存在未被抓住的变异：{', '.join(failed)}")
        return 1
    print("✅ 全部变异套件通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
