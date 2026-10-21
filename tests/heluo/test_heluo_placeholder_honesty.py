"""河洛三处「名实不符 / 伪计算」修正回归（2026-10-06）

本文件锁三处**同一形态**的缺陷——声明与实际不符，把「还没做」说成「做了」：

1. ``interpretation._compute_evidence_closure`` 原 ``return 0.85``
   （注释「简化版」）。它被 ``_compute_confidence`` 以 0.6 权重采信，
   等于**任何命盘的置信度都被这一个常数锚定**。
   现按输入里真实存在的证据字典（line_position / time_state /
   element_state）逐字段统计填充率。

2. ``hexagram_state.get_base_factors`` 原注释「TODO: 从
   hexagram_state_definitions 表读取」，但**该表在本仓不存在**。
   与 EVENT_TOPIC 求值器同属「指向幻影资源」的表述。

3. ``Timeline`` 三处占位字段名实不符：``daily_hexagram`` 注释写「今日卦」
   却存**先天卦**，其 ``date`` 塞的是 ``str(birth_year)``（如 "1990"）；
   ``monthly_hexagrams`` 恒 ``[]``、``hourly_hexagram`` 恒 ``None``。
   三者全仓零消费方，真实流月/流日/流时卦在四层时间轴内。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

_REPO_ROOT = Path(__file__).resolve().parents[2]

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.interpretation import HeluoInput as HL4Input

_BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]


def _timeline():
    return HeluoCanonical().calculate(
        bazi=_BAZI, gender="male", birth_hour="午",
        era="zhong", birth_year=1724,
    ).timeline


class TestEvidenceClosureIsReal(unittest.TestCase):
    """证据闭合度必须是算出来的，不是常数。"""

    @staticmethod
    def _engine(line_pos, time_state, element_state):
        from tongshu.engines.heluo.interpretation import RelationalInterpretationEngine
        inp = HL4Input(
            prenatal_hexagram="乾上乾下", yuan_tang="五爻",
            postnatal_hexagram="乾上坤下",
            day_hexagram="乾为天", year_cycle="乙巳", month_cycle="甲申",
            day_cycle="丙午",
            element_state=element_state, line_position=line_pos,
            time_state=time_state,
        )
        return RelationalInterpretationEngine(inp)

    def test_full_evidence_gives_full_closure(self):
        e = self._engine(
            {"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
            {"solar_term": "立秋", "hour": 14, "true_solar_time": True},
            {"木": 0.6, "火": 0.8, "土": 0.5, "金": 0.4, "水": 0.3},
        )
        self.assertEqual(e._compute_evidence_closure(), 1.0)

    def test_empty_evidence_gives_zero(self):
        e = self._engine({}, {}, {})
        self.assertEqual(e._compute_evidence_closure(), 0.0)

    def test_closure_varies_with_input(self):
        """核心区分点：证据不同 → 闭合度不同。旧硬编码恒为 0.85。"""
        full = self._engine(
            {"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
            {"solar_term": "立秋", "hour": 14, "true_solar_time": True},
            {"木": 0.6, "火": 0.8, "土": 0.5, "金": 0.4, "水": 0.3},
        )._compute_evidence_closure()
        half = self._engine(
            {"active_line": 5}, {"hour": 14}, {},
        )._compute_evidence_closure()
        self.assertNotEqual(full, half)

    def test_degenerate_values_count_as_unfilled(self):
        """空串 / None / 全 0 的五行证据视为未填充。"""
        e = self._engine(
            {"active_line": 5, "position_type": "", "yinyang": None},
            {"solar_term": "   ", "hour": None, "true_solar_time": False},
            {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0},
        )
        # 五行全 0 → 5 个都算未填充；line_position 仅 active_line 有效；
        # true_solar_time=False 属已填充（bool 是合法取值，不按 falsy 数字剔除）
        self.assertEqual(e._compute_evidence_closure(), round(2 / 11, 4))

    def test_confidence_no_longer_pinned_to_constant(self):
        """置信度不再被常数锚定：两组输入应给出不同置信度。"""
        a = self._engine(
            {"active_line": 5, "position_type": "尊位", "yinyang": "阳"},
            {"solar_term": "立秋", "hour": 14, "true_solar_time": True},
            {"木": 0.6, "火": 0.8, "土": 0.5, "金": 0.4, "水": 0.3},
        )._compute_confidence()
        b = self._engine({}, {}, {})._compute_confidence()
        self.assertNotEqual(a, b)


class TestHexagramStateClaims(unittest.TestCase):
    """不得再指向不存在的 definitions 表。"""

    def test_definitions_table_really_absent(self):
        """该 definitions 表确实不存在——注释若再说「从表读取」就是误导。

        2026-10-07 更新：原典**确有**判据（L630–L648 六项），
        只是不在名为 ``hexagram_state_definitions`` 的表里，
        而在起例卷之中正文。已落成 ``gui_ming_liu_ju.py``。
        故本断言仅守「不要再去找那张不存在的表」。
        """
        hits = [p for base in (_REPO_ROOT / "backend" / "data", _REPO_ROOT / "data")
                if base.exists()
                for p in base.rglob("*hexagram_state*")]
        hits += [p for base in (_REPO_ROOT / "backend" / "data", _REPO_ROOT / "data")
                 if base.exists() for p in base.rglob("*state_definition*")]
        self.assertEqual(hits, [], "若表已建，注释与本断言都需同步更新")

    def test_real_judgement_module_exists_and_is_used_by_docs(self):
        """作废的假分数必须有**有据替代**指向，否则只是删功能。"""
        from pathlib import Path as _P

        import tongshu.engines.heluo.hexagram_state as hs
        mod = _P(hs.__file__).parent / "gui_ming_liu_ju.py"
        self.assertTrue(mod.exists(), "缺少有原典依据的替代实现 gui_ming_liu_ju.py")
        import inspect
        src = inspect.getsource(hs.get_base_factors)
        self.assertIn("gui_ming_liu_ju", src,
                      "作废提示必须指向有据替代实现")

    def test_docstring_does_not_promise_table_read(self):
        import inspect

        from tongshu.engines.heluo.hexagram_state import get_base_factors
        src = inspect.getsource(get_base_factors)
        self.assertNotIn("从 hexagram_state_definitions 表读取", src)

    def test_base_factors_now_refuses_invented_scores(self):
        """2026-10-07 起：无原典依据的自拟分数一律**拒绝提供**。

        本断言原为 ``test_base_factors_still_deterministic``，
        守的是「修正只动注释、取值行为不变」——那是当时为避免越界而设的约束。
        2026-10-07 经用户 P0 批准，``get_base_factors`` 的静/动/变/互 因子
        被查证为**全书中无出处的凭空捏造**（且 ``hexagram`` 参数从未被使用，
        不同卦返回同一组分数），故整项作废并改为恒抛出。

        本断言的**意图未变**：占位层不得再输出看似可信的假数。
        形式由「锁定捏造的数值」改为「锁定拒绝提供」。
        """
        from tongshu.engines.heluo.hexagram_state import get_base_factors
        for gua, state in (("乾为天", "静"), ("乾为天", "动"), ("坤为地", "变")):
            with self.assertRaises(NotImplementedError,
                                   msg=f"{gua}/{state} 仍在返回自拟分数"):
                get_base_factors(gua, state)

    def test_legacy_scores_are_marked_as_archaeology(self):
        """旧数值若被保留，只能以「已作废、仅供考古」的形式存在。"""
        import inspect

        from tongshu.engines.heluo.hexagram_state import get_base_factors_legacy
        src = inspect.getsource(get_base_factors_legacy)
        self.assertIn("已作废", src)
        self.assertIn("没有原典出处", src)
        # 旧函数确实还留着那组数——但用途被文档钉死为考古
        self.assertEqual(get_base_factors_legacy(), (0.5, 0.3))


class TestTimelinePlaceholdersAreHonest(unittest.TestCase):
    """三处占位字段不得再挂名实不符的内容。"""

    @classmethod
    def setUpClass(cls):
        cls.timeline = _timeline()

    def test_daily_hexagram_is_empty(self):
        """原存先天卦 + str(birth_year)，既非今日卦也非合法日期。"""
        self.assertEqual(self.timeline.daily_hexagram, {})

    def test_monthly_and_hourly_stay_empty(self):
        self.assertEqual(self.timeline.monthly_hexagrams, [])
        self.assertIsNone(self.timeline.hourly_hexagram)

    def test_real_day_hexagrams_live_in_the_four_layer_axis(self):
        """真实流月/流日仍在四层时间轴内——置空的是重复副本，不是能力。"""
        y = self.timeline.yearly_hexagrams[0]
        self.assertEqual(len(y["months"]), 12)
        for m in y["months"]:
            self.assertEqual(len(m["days"]), 6)

    def test_no_birth_year_string_leaks_into_timeline(self):
        """'1990'/'1724' 这类裸年份串不得再作为 date 出现在时间轴。"""
        self.assertNotEqual(str(self.timeline.daily_hexagram.get("date", "")), "1724")


if __name__ == "__main__":
    unittest.main()