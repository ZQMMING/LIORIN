# -*- coding: utf-8 -*-
"""废弃残桩的**状态守卫**（2026-10-22 改写）。

背景：这两个模块是历史残留，首行已标 DEPRECATED、import 即发
DeprecationWarning，且实现本身不可用：

  · `dayu.py` —— 干支排盘式旧大运。取代者是 `timeline_yun.compute_dayun_liyao`
    （爻位值运，阳爻 9 年 / 阴爻 6 年），后者才是生产口径（canonical.py 调用）。
    本模块起运年龄硬编码 `qi_yun_age = 3`（TODO 未实现），卦象字段全空。
  · `time_sequence.py` —— 旧版流年/流月/流日干支占位。取代者是 `timeline_yun`
    （流卦链）。本模块流月支 `(target_month+1)%12` 与常规月支（亥/戌）不符，
    基准日也非真甲子日。

原 `tests/test_heluo_dayu.py` / `tests/test_heluo_time_sequence.py`
测的是**废弃残桩的错误算法**（如「流月支 11 月得子」），继续保留等于
把错的东西钉成标准。2026-10-22 改写为**钉死废弃状态**：

  1. import 即 DeprecationWarning（防复活后无人察觉）
  2. 取代者确实在生产链上（防误删真正在用的实现）
  3. 残桩的关键缺陷仍在（防「单方面修复残桩」造成两套口径并存）

覆盖不减：原测试涉及的有效部分（干支表正确性、流卦链的连续性）已由
`tests/heluo/` 下的主链守卫承担；本文件把「废弃」这一事实本身变成可回归的断言。
"""
from __future__ import annotations

import ast
import importlib
import inspect
import sys
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _import_afresh(mod_name: str):
    """强制重新 import，捕获模块级 warnings.warn。

    模块一旦被 sys.modules 缓存，再次 import 不会重跑模块体，
    DeprecationWarning 也就不会再发 —— 直接 import 的守卫会 flaky。
    """
    sys.modules.pop(mod_name, None)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        mod = importlib.import_module(mod_name)
    return mod, w


def _ast_imports(source: str):
    """解析 import 语句，返回 {(模块名, 导入名 or None)}。

    用 AST 而不是字符串匹配：源码里出现在注释/docstring 中的模块名
    （例如「canonical 不得 import dayu」这类说明）不应被当成真实依赖。
    """
    tree = ast.parse(source)
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out.add((node.module, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out.add((alias.name.split(".")[0], None))
    return out


class TestLegacyDeprecatedModules(unittest.TestCase):
    """两个废弃残桩模块的状态守卫。"""

    def test_dayu_import_warns_deprecated(self):
        """dayu.py：import 即 DeprecationWarning（防复活无察觉）。"""
        _, w = _import_afresh("heluo_engine.engines.heluo.dayu")
        self.assertTrue(
            any(issubclass(x.category, DeprecationWarning) for x in w),
            "dayu.py 应在 import 时发 DeprecationWarning",
        )

    def test_time_sequence_import_warns_deprecated(self):
        """time_sequence.py：import 即 DeprecationWarning。"""
        _, w = _import_afresh("heluo_engine.engines.heluo.time_sequence")
        self.assertTrue(
            any(issubclass(x.category, DeprecationWarning) for x in w),
            "time_sequence.py 应在 import 时发 DeprecationWarning",
        )

    def test_replacements_are_the_live_ones(self):
        """取代者（爻位值运 + 四层时间轴）确实在生产链上。"""
        from heluo_engine.engines.heluo import timeline_yun
        from heluo_engine.engines.heluo.canonical import HeluoCanonical

        # 取代者不标 DEPRECATED
        src = inspect.getsource(timeline_yun)
        self.assertNotIn("DEPRECATED", src[:400],
                         "timeline_yun 是取代者，不应标 DEPRECATED")

        # canonical 确实用取代者算大运
        csrc = inspect.getsource(HeluoCanonical)
        self.assertIn("compute_dayun_liyao", csrc,
                      "canonical 应调用取代者 compute_dayun_liyao")

    def test_canonical_does_not_import_legacy_modules(self):
        """canonical 不得 import 两个废弃残桩 / 占位桩（防复活被误当生产口径）。"""
        from heluo_engine.engines.heluo import canonical

        imported = _ast_imports(inspect.getsource(canonical))
        self.assertNotIn(("dayu", None), imported,
                         "canonical 不得 import 废弃的 dayu")
        self.assertNotIn(("time_sequence", None), imported,
                         "canonical 不得 import 废弃的 time_sequence")
        self.assertNotIn(("temporal", "compute_timeline"), imported,
                         "canonical 不得 import 占位桩 compute_timeline")
        self.assertIn(("temporal", "Timeline"), imported,
                      "canonical 应 import Timeline（真实时间轴结构）")

    def test_dayu_stub_defects_still_present(self):
        """残桩的已知缺陷仍在（防「单方面修复残桩」造成两套口径并存）。"""
        from heluo_engine.engines.heluo import dayu

        src = inspect.getsource(dayu)
        self.assertIn("qi_yun_age = 3", src,
                      "dayu 起运年龄仍是硬编码 3（残桩，勿当可用实现）")
        self.assertIn('hexagram=""', src,
                      "dayu 卦象字段仍为空（残桩，勿当可用实现）")

    def test_time_sequence_month_branch_rule_is_legacy(self):
        """time_sequence 的流月支规则是旧口径（与常规月支不符），仅留档。"""
        from heluo_engine.engines.heluo import time_sequence

        src = inspect.getsource(time_sequence)
        self.assertIn("target_month + 1", src,
                      "time_sequence 用 (target_month+1)%12 的旧月支规则（留档）")


class TestRelationshipEngineDeprecated(unittest.TestCase):
    """relationship/engine.py（Phase 5-D 残桩）的废弃状态守卫（2026-10-22）。

    裁定依据：主仓与本包 src 内**零生产 import**；本包唯一引用是
    `test_heluo_base_table_consistency.py` 拿它比对两张五行表；
    主仓 compute_stage 已把河洛结果断链。实现另有死分支与**伪造出处**。
    """

    def test_import_warns_deprecated(self):
        _, w = _import_afresh("heluo_engine.engines.heluo.relationship.engine")
        self.assertTrue(
            any(issubclass(x.category, DeprecationWarning) for x in w),
            "relationship/engine.py 应在 import 时发 DeprecationWarning")

    def test_known_defects_still_present(self):
        """残桩缺陷仍在（防「单方面修复残桩」造成两套口径并存）。"""
        from heluo_engine.engines.heluo.relationship import engine

        src = inspect.getsource(engine)
        self.assertIn("any(y in ELEMENT_GEN for y in [year_a, year_b])", src,
                      "time_sync 的「相生」分支仍恒为假（残桩，勿当可用实现）")
        self.assertIn("'sources': ['河洛理数', '周易', '《易经》']", src,
                      "伪造出处仍写死（残桩，勿当可用实现）")

    def test_no_production_import(self):
        """本包 src/ 内不得有生产代码 import 该残桩。"""
        src_root = Path(__file__).resolve().parent.parent / "src"
        offenders = []
        for py in src_root.rglob("*.py"):
            rel = py.relative_to(src_root)
            if rel.as_posix().endswith("heluo/relationship/engine.py"):
                continue
            try:
                # utf-8-sig：部分 src 文件带 BOM，直接 utf-8 读会让 ast.parse 报
                # SyntaxError（U+FEFF），从而把「扫描」变成「崩溃」。
                text = py.read_text(encoding="utf-8-sig")
            except Exception:
                continue
            for mod, name in _ast_imports(text):
                if name == "engine" and mod and mod.endswith("relationship"):
                    offenders.append(str(rel))
        self.assertEqual(offenders, [],
                         f"生产代码不得 import 废弃残桩 relationship.engine：{offenders}")


if __name__ == "__main__":
    unittest.main()
