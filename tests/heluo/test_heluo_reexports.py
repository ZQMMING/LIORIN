# -*- coding: utf-8 -*-
"""守卫：有意重导出必须**始终存在且是同一个对象**（2026-10-25 新增）。

背景
----
本仓有若干「**有意的重导出**」：模块 A 把模块 B 的单例表/常量 import 进来，
让下游可以 ``from A import X``，且 **A.X is B.X**（同一对象，不复制）。

这保证「全局只有一份」：
  · 六十四卦表（``yi.core.SIXTY_FOUR_MAP``）
  · 错卦对宫表（``hexagram_state.QIANXI_DUKONG``）
  · 纳音/五行相关表等

⚠ 2026-10-25 实测踩坑（重要）：
   「清理未用 import」的工具（**Ruff F401**）会把这些 import 当成**未用**
   而删掉 —— 因为该模块自己并不使用它们。
   ⇒ 一旦删掉：``from A import X`` 直接 ImportError；更糟的是
     「同一对象」类守卫**当场变红**，而批量清理工具自身的验证
     （它同时改了测试文件）**不可靠** ⇒ 静默破坏。
   ⇒ 处置：
     ① 所有有意重导出**必须**写 ``# noqa: F401``（工具就不会动它）；
     ② 本守卫**显式列出**全部有意重导出并校验「存在 + 同一对象」；
        将来新增/删除重导出都要同步本文件（⇒ 破坏性变更显式发生）。
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))


#: 有意重导出清单：(宿主模块, 宿主里的名字, 源头模块, 源头里的名字)
#:
#: ⚠ 改动规则：新增重导出 → 在此追加；删除重导出 → 从此删除并同步源码。
DELIBERATE_REEXPORTS = [
    # 错卦对宫表（六爻全变）—— 全库单一来源 hexagram_state
    ("heluo_engine.engines.heluo.guajie",
     "QIANXI_DUKONG", "heluo_engine.engines.heluo.hexagram_state",
     "QIANXI_DUKONG"),
    ("heluo_engine.engines.heluo.yuan_qi",
     "QIANXI_DUKONG", "heluo_engine.engines.heluo.hexagram_state",
     "QIANXI_DUKONG"),
    ("heluo_engine.engines.heluo.hua_gong",
     "QIANXI_DUKONG", "heluo_engine.engines.heluo.hexagram_state",
     "QIANXI_DUKONG"),
    # 六十四卦表 —— 全库单一来源 yi.core
    ("heluo_engine.engines.heluo.hexagram",
     "_SIXTY_FOUR_MAP", "heluo_engine.engines.yi.core", "SIXTY_FOUR_MAP"),
    # 纳音/五行相关
    ("heluo_engine.engines.heluo.yuanqi_tables",
     "DUI_GUA", "heluo_engine.engines.heluo.hexagram_state", "QIANXI_DUKONG"),
]


class TestDeliberateReexports(unittest.TestCase):
    """有意重导出：存在 + 同一对象。"""

    def test_reexports_exist(self):
        for host, name, _src, _src_name in DELIBERATE_REEXPORTS:
            with self.subTest(host=host, name=name):
                mod = importlib.import_module(host)
                self.assertTrue(hasattr(mod, name),
                                "%s 缺有意重导出 %r（被「清理未用 import」"
                                "误删了？）" % (host, name))

    def test_reexports_are_the_same_object(self):
        for host, name, src, src_name in DELIBERATE_REEXPORTS:
            with self.subTest(host=host, name=name):
                h = getattr(importlib.import_module(host), name)
                s = getattr(importlib.import_module(src), src_name)
                self.assertIs(h, s,
                              "%s.%s 与 %s.%s 不是**同一个对象** ⇒ "
                              "「全局只有一份」被破坏" % (host, name, src, src_name))

    def test_reexport_lines_have_noqa_f401(self):
        """有意重导出的 import 行**必须**带 ``noqa: F401``。

        ⚠ 没有它 ⇒ 任何「清理未用 import」的工具（Ruff F401 / IDE 的
          "remove unused imports"）都会把它删掉 ⇒ 静默破坏。
          本守卫把这条**约定**也钉住。
        """
        src_root = _REPO / "src" / "heluo_engine"
        for host, name, _src, _src_name in DELIBERATE_REEXPORTS:
            with self.subTest(host=host, name=name):
                rel = host.replace("heluo_engine.", "").replace(".", "/")
                cand = list(src_root.rglob(rel + ".py"))
                self.assertTrue(cand, "找不到源文件：%s" % rel)
                text = cand[0].read_text(encoding="utf-8")
                lines = text.splitlines()
                hit = False
                for i, line in enumerate(lines):
                    # 多行 import 的**名字行**本身不含 "import"，
                    # 所以不能拿 "import" in line 当条件 —— 改为：
                    # 该名字出现在 import 语句块内（向上找最近的 import 行）。
                    if name not in line or line.lstrip().startswith("#"):
                        continue
                    # 向上找最近的 import 语句起点
                    start = i
                    while start > 0 and "import" not in lines[start]:
                        start -= 1
                    if "import" not in lines[start]:
                        continue
                    block = "\n".join(lines[start:i + 1])
                    if "noqa" in block and "F401" in block:
                        hit = True
                        break
                self.assertTrue(hit,
                                "%s 里 %r 的 import 缺 ``# noqa: F401`` ⇒ "
                                "会被未用 import 清理工具删掉" % (host, name))


if __name__ == "__main__":
    unittest.main()
