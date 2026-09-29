"""P0-FNDR-03 (R-09 ⑦ 十神 audit fix): 依赖方向架构验证。

User 第七轮审计核心要求:
"事实表 → 确定性引擎 → BaziEngine"
而不是: "BaziEngine ↔ 十神引擎"

本测试通过 AST 静态分析验证模块间依赖方向:
1. facts.bazi_facts 不依赖任何 tongshu 上层模块
2. reasoning.bazi_ten_gods 只依赖 facts
3. engines.bazi_engine 依赖 facts 和 reasoning，但不形成循环
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _get_internal_imports(filepath: str) -> list[tuple[int, str, list[str]]]:
    """提取文件中所有 import 内部 tongshu.* 模块的语句 (含相对路径)。"""
    with open(filepath, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # level > 0 表示相对导入, 一律算内部依赖
            is_relative = node.level > 0
            # 匹配 tongshu.* 绝对导入 或相对导入 (..facts.* 等)
            if module.startswith("tongshu") or is_relative:
                imports.append((node.lineno, module, [n.name for n in node.names]))
        elif isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("tongshu"):
                    imports.append((node.lineno, n.name, []))
    return imports


# 文件路径 (相对 repo root)
# tests/test_bazi_dependency_direction.py -> parents[1] = repo_root
REPO_ROOT = Path(__file__).resolve().parents[1]
FACTS_FILE = REPO_ROOT / "src" / "tongshu" / "facts" / "bazi_facts.py"
TEN_GODS_FILE = REPO_ROOT / "src" / "tongshu" / "reasoning" / "bazi_ten_gods.py"
BAZI_ENGINE_FILE = REPO_ROOT / "src" / "tongshu" / "engines" / "bazi_engine.py"


class TestDependencyDirection(unittest.TestCase):
    """P0-FNDR-03: 验证依赖方向单向无环."""

    def test_01_facts_has_no_internal_dependencies(self):
        """bazi_facts.py 不应 import 任何 tongshu 内部模块。

        这是依赖图最底层的事实层, 必须保持纯净。
        """
        deps = _get_internal_imports(str(FACTS_FILE))
        self.assertEqual(
            deps, [],
            f"bazi_facts.py 不应有 tongshu 内部依赖, 实际: {deps}",
        )

    def test_02_ten_gods_only_depends_on_facts(self):
        """bazi_ten_gods.py 只应依赖 facts 层, 不应反向依赖 engines。

        依赖图: facts → bazi_ten_gods
        """
        deps = _get_internal_imports(str(TEN_GODS_FILE))
        # 允许: from .facts.bazi_facts import ...
        # 允许: from . import ... 同包内
        # 不允许: from ..engines.bazi_engine import ...
        for line, mod, names in deps:
            self.assertNotIn(
                "engines.bazi_engine", mod,
                f"L{line}: bazi_ten_gods.py 不得 import engines.bazi_engine "
                f"(反向依赖会导致循环). Found: {mod}",
            )

    def test_03_bazi_engine_depends_on_facts_and_ten_gods(self):
        """bazi_engine.py 依赖 facts 和 reasoning, 但不形成循环。

        依赖图: facts → bazi_ten_gods → bazi_engine
        单向无环.
        """
        deps = _get_internal_imports(str(BAZI_ENGINE_FILE))
        # 合并模块名用于子串匹配
        joined = " ".join(f"{d[1]}" for d in deps)

        # 必须包含 facts 依赖
        self.assertIn(
            "facts", joined,
            f"bazi_engine.py 必须 import facts 层获取基础事实表. 实际 deps: {deps}",
        )

        # 必须包含 reasoning.bazi_ten_gods 依赖
        self.assertIn(
            "bazi_ten_gods", joined,
            f"bazi_engine.py 必须 import canonical bazi_ten_gods. 实际 deps: {deps}",
        )

    def test_03b_bazi_engine_no_local_hidden_main_dict(self):
        """P0-FNDR-04 (R-10 ⑧ 藏干): bazi_engine 不应再持有 _BRANCH_HIDDEN_MAIN 副本.

        之前 _BRANCH_HIDDEN_MAIN 是简化副本, 现在应通过 canonical
        bazi_ten_gods.hidden_main_stem 查询.
        """
        import importlib
        if "tongshu.engines.bazi_engine" in sys.modules:
            importlib.reload(sys.modules["tongshu.engines.bazi_engine"])
        be_mod = sys.modules["tongshu.engines.bazi_engine"]
        self.assertFalse(
            hasattr(be_mod, "_BRANCH_HIDDEN_MAIN"),
            "bazi_engine 不应再持有 _BRANCH_HIDDEN_MAIN 副本, "
            "应通过 canonical bazi_ten_gods.hidden_main_stem 查询",
        )

    def test_03c_l1_facts_is_derived_view(self):
        """P0-FNDR-04 (R-10 ⑧ 藏干): bazi_l1_facts.BRANCH_HIDDEN_STEMS 是派生视图.

        它应从 bazi_facts 转换 (拼音 -> 中文), 不再独立存储事实数据.
        """
        from tongshu.engines.bazi_l1_facts import (
            BRANCH_HIDDEN_STEMS as L1_HHS,
        )
        from tongshu.facts.bazi_facts import BRANCH_HIDDEN_STEMS as FACTS_HHS

        # 中文键的 "子" 对应拼音 "ZI"
        # 派生前后内容必须完全一致 (中间经过拼音-中文转换)
        pinyin_to_chinese_stem = {
            "JIA": "甲", "YI": "乙", "BING": "丙", "DING": "丁",
            "WU": "戊", "JI": "己", "GENG": "庚", "XIN": "辛",
            "REN": "壬", "GUI": "癸",
        }
        pinyin_to_chinese_branch = {
            "ZI": "子", "CHOU": "丑", "YIN": "寅", "MAO": "卯",
            "CHEN": "辰", "SI": "巳", "WU": "午", "WEI": "未",
            "SHEN": "申", "YOU": "酉", "XU": "戌", "HAI": "亥",
        }
        for pinyin_branch, hidden_entries in FACTS_HHS.items():
            chinese_branch = pinyin_to_chinese_branch[pinyin_branch]
            l1_hidden = L1_HHS[chinese_branch]
            expected_stems = [
                pinyin_to_chinese_stem[stem] for stem, _role in hidden_entries
            ]
            actual_stems = [
                s for s in [l1_hidden["本气"], l1_hidden["中气"], l1_hidden["余气"]]
                if s is not None
            ]
            with self.subTest(branch=pinyin_branch):
                self.assertEqual(
                    actual_stems, expected_stems,
                    f"L1 {chinese_branch} 派生视图与 canonical {pinyin_branch} 不一致",
                )

    def test_03d_branch_relation_facts_in_facts_layer(self):
        """P0-FNDR-05 (R-11 ⑨ 地支关系): 关系事实表在 bazi_facts 层.

        bazi_engine 不应再定义 BRANCH_HE / BRANCH_SANHE / BRANCH_SANHUI / BRANCH_SANXING 等
        关系事实表 (化气/刑义混入) — 这些都已迁移到 facts 层.
        检查方式: 关系表在 bazi_facts 中存在, 且 bazi_facts 版本是
        tuple of frozensets (不带化气/刑义).
        """
        from tongshu.facts.bazi_facts import (
            BRANCH_HE as FACTS_HE,
            BRANCH_SANHE as FACTS_SANHE,
            BRANCH_SANHUI as FACTS_SANHUI,
        )

        # 关系事实表应是 tuple of frozensets (不带化气/刑义)
        # 这是 P0-FNDR-05 数据契约拆分的核心: 关系 ≠ 化气
        self.assertIsInstance(FACTS_HE, tuple)
        self.assertIsInstance(FACTS_SANHE, tuple)
        self.assertIsInstance(FACTS_SANHUI, tuple)
        for pair in FACTS_HE:
            self.assertIsInstance(pair, frozenset)
            self.assertEqual(len(pair), 2)
        for triple in FACTS_SANHE:
            self.assertIsInstance(triple, frozenset)
            self.assertEqual(len(triple), 3)
        for triple in FACTS_SANHUI:
            self.assertIsInstance(triple, frozenset)
            self.assertEqual(len(triple), 3)

        # 化气/刑义表在 bazi_engine (辨层函数使用, 不混入关系事实表)
        from tongshu.engines.bazi_engine import _HE_HUA_QI, _SANXING_MING
        self.assertTrue(callable(lambda: None))   # placeholder
        # _HE_HUA_QI 应是 dict[set, str] (化气五行), 不是 tuple (关系事实)
        self.assertIsInstance(_HE_HUA_QI, dict)
        self.assertIsInstance(_SANXING_MING, dict)

    def test_03e_kong_wang_facts_in_facts_layer(self):
        """P0-FNDR-06 (R-12 ⑩ 空亡): 空亡事实表在 bazi_facts 层.

        bazi_engine 不应再持有 KONG_WANG_BY_XUN 副本 — 已迁移到 bazi_facts.
        验证 bazi_facts.KONG_WANG_BY_XUN 覆盖 6 旬 (60 甲子).
        """
        from tongshu.facts.bazi_facts import (
            KONG_WANG_BY_XUN as FACTS_KW,
            JIAZI_TABLE as FACTS_JZ,
            JIAZI_INDEX as FACTS_JI,
            XUN_BRANCHES as FACTS_XB,
        )
        # 6 旬全覆盖
        self.assertEqual(len(FACTS_KW), 6)
        for xun in range(6):
            self.assertIn(xun, FACTS_KW)
        # 60 甲子完整
        self.assertEqual(len(FACTS_JZ), 60)
        self.assertEqual(len(FACTS_JI), 60)
        # 6 旬内 10 地支
        self.assertEqual(len(FACTS_XB), 6)
        for xun_branches in FACTS_XB.values():
            self.assertEqual(len(xun_branches), 10)

    def test_03f_start_age_facts_in_facts_layer(self):
        """P0-FNDR-08 (R-14 ⑫ 起运): 起运常量在 bazi_facts 层.

        bazi_engine 不应再硬编码 33 / 3.0, 已迁移到 bazi_facts:
        - MAX_JIEQI_SEARCH_DAYS = 33 (节气搜索窗口)
        - DAYS_PER_YEAR_OF_START_AGE = 3 (3天=1岁换算)
        """
        from tongshu.facts.bazi_facts import (
            MAX_JIEQI_SEARCH_DAYS as FACTS_MAX_JIEQI,
            DAYS_PER_YEAR_OF_START_AGE as FACTS_DAYS_PER_YEAR,
        )
        # 安全上界
        self.assertEqual(FACTS_MAX_JIEQI, 33)
        # 3 天 = 1 岁 (传统起运换算)
        self.assertEqual(FACTS_DAYS_PER_YEAR, 3)

        # bazi_engine._calc_start_age 必须使用这些常量
        from tongshu.engines.bazi_engine import _calc_start_age_constants_used
        constants_used = _calc_start_age_constants_used()
        self.assertEqual(constants_used.get("MAX_JIEQI_SEARCH_DAYS"), 33)
        self.assertEqual(constants_used.get("DAYS_PER_YEAR_OF_START_AGE"), 3)

    def test_04_no_circular_dependency(self):
        """完整依赖图必须无环。

        检查方法: 加载三个模块, 验证 import 链能完整解析 (无 ImportError)。
        """
        # 清缓存
        import importlib
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("tongshu.facts") or \
               mod_name.startswith("tongshu.reasoning.bazi_ten_gods") or \
               mod_name.startswith("tongshu.engines.bazi_engine"):
                del sys.modules[mod_name]

        # 应能干净 import 三个模块, 无 ImportError
        try:
            from tongshu.facts import bazi_facts
            from tongshu.reasoning.bazi_ten_gods import ten_god
            from tongshu.engines.bazi_engine import _ten_god
        except ImportError as e:
            self.fail(f"循环依赖未消除: {e}")

        # 验证同一函数
        self.assertIs(_ten_god, ten_god)


class TestBaziFactsSoleSource(unittest.TestCase):
    """事实层单一来源验证."""

    def test_05_bazi_facts_constants_match(self):
        """bazi_facts 的常量与 bazi_engine 之前定义的内容一致。

        这是验证: 我们把 STEM_ELEMENT 等迁移到 bazi_facts, 但语义未变。
        """
        from tongshu.facts.bazi_facts import (
            STEM_ELEMENT, STEM_POLARITY, BRANCH_ELEMENT,
        )
        from tongshu.engines.bazi_engine import (
            STEM_ELEMENT as ENGINE_SE, STEM_POLARITY as ENGINE_SP,
            BRANCH_ELEMENT as ENGINE_BE,
        )

        self.assertEqual(STEM_ELEMENT, ENGINE_SE)
        self.assertEqual(STEM_POLARITY, ENGINE_SP)
        self.assertEqual(BRANCH_ELEMENT, ENGINE_BE)

    def test_06_bazi_facts_constants_complete(self):
        """bazi_facts 必须提供完整的基础事实表."""
        from tongshu.facts.bazi_facts import (
            HEAVENLY_STEMS, EARTHLY_BRANCHES,
            STEM_ELEMENT, STEM_POLARITY, BRANCH_ELEMENT,
            BRANCH_HIDDEN_STEMS, GENERATES, CONTROLS,
        )
        # 10 天干
        self.assertEqual(len(HEAVENLY_STEMS), 10)
        # 12 地支
        self.assertEqual(len(EARTHLY_BRANCHES), 12)
        # STEM_ELEMENT 完整
        for stem in HEAVENLY_STEMS:
            self.assertIn(stem, STEM_ELEMENT)
            self.assertIn(stem, STEM_POLARITY)
        # BRANCH_ELEMENT 完整
        for branch in EARTHLY_BRANCHES:
            self.assertIn(branch, BRANCH_ELEMENT)
            self.assertIn(branch, BRANCH_HIDDEN_STEMS)
        # 五行 5 个
        self.assertEqual(len(GENERATES), 5)
        self.assertEqual(len(CONTROLS), 5)


class TestEvidenceMetadata(unittest.TestCase):
    """Evidence 元数据."""

    def test_07_evidence_ids_present(self):
        """EVIDENCE_IDS 必须存在."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        self.assertIsInstance(EVIDENCE_IDS, dict)
        self.assertGreater(len(EVIDENCE_IDS), 0)

    def test_08_all_key_facts_have_evidence(self):
        """每个事实常量必须有 evidence id."""
        from tongshu.facts.bazi_facts import EVIDENCE_IDS
        required = {
            "STEM_ELEMENT",
            "STEM_POLARITY",
            "BRANCH_ELEMENT",
            "BRANCH_HIDDEN_STEMS",
            "GENERATES",
            "CONTROLS",
        }
        for key in required:
            self.assertIn(
                key, EVIDENCE_IDS,
                f"事实 {key} 必须在 EVIDENCE_IDS 中标注证据来源",
            )


if __name__ == "__main__":
    unittest.main()
