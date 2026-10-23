"""批次 I/J 守卫：interpretation 接原典六项 + 诊断建议接进管线（2026-10-08）

I. interpretation 层
   `_hexagram_base_score` / `_year_cycle_factor` 于 2026-10-07 因无原典依据被作废、
   恒抛 NotImplementedError → compute() 整个不可用，即 tests/test_h4_interpretation.py
   那 6 条长期失败的根因。本批改为消费 gui_ming_liu_ju 的六项原典判据。

   关键不变量：**不复活任何自拟分数**。
   - base = (吉 − 凶) / 已判项数，且须随输入变化（改元堂爻位就该改结果）
   - 六项全「不判」时 base = 0.0 且明细写明「六项皆不判，不等于中性」
   - 原典未给的流年数值因子**不进公式**，也不换一个自造因子顶上

J. 管线接线
   诊断图与建议两层此前**生产调用方为零**（只被单测手动调过）。
   本批接入 compute_stage，须守住：
   - 必须排在 canonical_signals **之后**（否则方向全落 neutral）
   - 单层失败降级为 None 但留 warning，不静默、不中断主链路
   - PipelineResult 上真的能拿到 heluo_diagnosis / heluo_guidance
"""
from __future__ import annotations

import importlib.util
import inspect
import io
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "heluo_engine" / "engines" / "heluo"

#: 主仓顶层包是否可用（跨仓接线守卫的前提）
#: ⚠ 必须查**具体子模块**，不能只看顶层包 `tongshu`：
#:   残留目录/命名空间包会让 `find_spec("tongshu")` 返回真，
#:   但 `tongshu.pipeline` 并不存在 —— 实测踩过（守卫恒不生效，
#:   跨仓测试在独立包内照样炸红）。这里查的就是本类真正要用的那个模块。
def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        return False


_MAIN_REPO_AVAILABLE = _module_available("tongshu.pipeline")


def _mk(**kw):
    from heluo_engine.engines.heluo.interpretation import HeluoInput
    d = dict(prenatal_hexagram="乾上乾下", yuan_tang="五爻",
             postnatal_hexagram="乾上坤下", day_hexagram="屯上蒙下",
             year_cycle="乙巳", month_cycle="甲申", day_cycle="丙午",
             element_state={"木": 0.6, "火": 0.8, "土": 0.3, "金": 0.5, "水": 0.7},
             line_position={"active_line": 5, "position_type": "尊位",
                            "yinyang": "阳"},
             time_state={"solar_term": "立秋", "hour": 14})
    d.update(kw)
    return HeluoInput(**d)


class TestInterpretationUsesOriginalCriteria(unittest.TestCase):
    def test_compute_no_longer_raises(self):
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        r = RelationalInterpretationEngine(_mk()).compute()
        self.assertTrue(r.current_state)

    def test_base_comes_from_liuju_judgements(self):
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        base, ju = RelationalInterpretationEngine(_mk())._liuju_base()
        self.assertIn("爻位", ju.get("吉", []) + ju.get("凶", []) + ju.get("不判", []),
                      "六项判据一项都没跑 —— base 恐怕不是来自原典")
        self.assertIn("刻度说明", ju)

    def test_base_varies_with_input(self):
        """元堂五爻(二五爻为吉) vs 初爻 → base 必须变。

        只断言「不抛异常」是不够的：把 direction 恒读成 0 也能全绿。
        """
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        good = RelationalInterpretationEngine(_mk(yuan_tang="五爻"))._liuju_base()[0]
        bad = RelationalInterpretationEngine(_mk(yuan_tang="初爻"))._liuju_base()[0]
        self.assertGreater(good, 0, "五爻(二五吉) 应为正")
        self.assertLess(bad, 0, "初爻 非二五，应为负")

    def test_all_undecided_is_zero_and_labelled(self):
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        base, ju = RelationalInterpretationEngine(
            _mk(yuan_tang="?"))._liuju_base()
        self.assertEqual(base, 0.0)
        self.assertIn("不判", ju)
        self.assertEqual(ju["吉"], [])
        self.assertEqual(ju["凶"], [])

    def test_year_cycle_factor_stays_out_of_the_formula(self):
        """作废的流年因子不得以任何形式回到总分公式。

        ⚠ 判据用 **AST 的 Call 节点**，不用文本匹配 ——
          修复说明本身就要引「原 _year_cycle_factor()」来交代为什么移除它，
          文本匹配会被自己写的说明打中。这已是本项目第四次栽在同一个坑
          （E3 注释订正 / 批次 G 伪引 / 批次 H 契约注释 / 此处），
          故这里换成结构化判据：只认 `Name(id='_year_cycle_factor')` 的调用。
        """
        import ast
        src = io.open(_E / "interpretation.py", encoding="utf-8").read()
        tree = ast.parse(src)
        target = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) \
                    and node.name == "_compute_total_score":
                target = node
                break
        self.assertIsNotNone(target, "找不到 _compute_total_score")
        called = set()
        for n in ast.walk(target):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Name):
                called.add(n.func.id)          # _year_cycle_factor()
            elif isinstance(n.func, ast.Attribute):   # self._liuju_base()
                called.add(n.func.attr)
        self.assertNotIn("_year_cycle_factor", called,
                         "作废的流年数值因子又回到总分公式里了")
        self.assertIn("_liuju_base", called,
                      "总分公式没走六项判据")

    def test_void_factors_still_raise(self):
        """两个作废函数须保留为显式拒绝点，防止有人接回去。"""
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        e = RelationalInterpretationEngine(_mk())
        for fn in (e._hexagram_base_score, e._year_cycle_factor):
            with self.assertRaises(NotImplementedError):
                fn()

    def test_liuju_base_is_count_ratio_not_invented_weight(self):
        from heluo_engine.engines.heluo.interpretation import RelationalInterpretationEngine
        base, ju = RelationalInterpretationEngine(_mk())._liuju_base()
        n = len(ju.get("吉", [])) + len(ju.get("凶", []))
        if n:
            self.assertAlmostEqual(base, (len(ju["吉"]) - len(ju["凶"])) / n,
                                   places=4)


@unittest.skipUnless(
    _MAIN_REPO_AVAILABLE,
    "跨仓接线守卫：主仓顶层包 `tongshu` 不在河洛独立包内 —— "
    "本类测的是「主仓有没有把河洛诊断/建议接进 pipeline」，"
    "须在主仓仓库中运行")
class TestPipelineWiring(unittest.TestCase):
    """J：诊断与建议必须真的在管线里跑。"""

    def test_compute_result_has_fields(self):
        from tongshu.types import ComputeResult
        f = ComputeResult.__dataclass_fields__
        self.assertIn("heluo_diagnosis", f)
        self.assertIn("heluo_guidance", f)

    def test_pipeline_result_has_fields(self):
        from tongshu.pipeline import PipelineResult
        f = PipelineResult.__dataclass_fields__
        self.assertIn("heluo_diagnosis", f)
        self.assertIn("heluo_guidance", f)

    def test_compute_stage_wires_them(self):
        src = io.open(_ROOT / "src" / "tongshu" /
                      "pipeline_stages" / "compute_stage.py",
                      encoding="utf-8").read()
        self.assertIn("def _compute_heluo_diagnosis", src)
        self.assertIn("build_diagnosis_graph", src)
        self.assertIn("generate_guidance", src)

    def test_diagnosis_called_after_signals(self):
        """排在 canonical_signals 之前 → 方向全落 neutral，且没人会发现。"""
        src = io.open(_ROOT / "src" / "tongshu" /
                      "pipeline_stages" / "compute_stage.py",
                      encoding="utf-8").read()
        self.assertIn("canonical_signals = build_result.get",
                      src)
        self.assertLess(
            src.index("canonical_signals = build_result.get"),
            src.index("self._compute_heluo_diagnosis("),
            "诊断调用排在了 canonical_signals 产出之前")

    def test_degradation_is_logged_not_silent(self):
        """降级必须留 warning。用 AST 判「确实有 log.warning 调用」。

        ⚠ 不能用 `assertIn("诊断降级", src)` —— 该词在 compute_stage.py 里
        出现 **2 次**，替换掉其中一处后另一处仍在，断言照样绿。
        这与「注释引用旧串」是同一类假绿，只是方向反过来：从「有」变成「还在有」。
        """
        import ast
        src = io.open(_ROOT / "src" / "tongshu" /
                      "pipeline_stages" / "compute_stage.py",
                      encoding="utf-8").read()
        tree = ast.parse(src)
        warns = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                if n.func.attr == "warning" and n.args:
                    a0 = n.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        warns.append(a0.value)
        self.assertTrue(any("H12" in w and "诊断" in w for w in warns),
                        "诊断降级不再留 warning（静默失败）—— Ast 实测无对应 log.warning")
        self.assertTrue(any("H12" in w and "建议" in w for w in warns),
                        "建议降级不再留 warning（静默失败）")

    def test_end_to_end_produces_diagnosis_and_guidance(self):
        """端到端：真实排盘后 PipelineResult 上能直接拿到两层，不必手工调。"""
        import os
        from datetime import date
        os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
        os.environ.setdefault(
            "TONGSHU_AUTHORITY_CREDENTIALS",
            "architecture-governance:schema-v1-arch-gov-2026;"
            "admission_registry:test-cred-hash")
        from tongshu.pipeline import TONGSHUPipeline
        p = TONGSHUPipeline.for_demo(_ROOT)
        r = p.run(analysis_date=date(2026, 10, 8),
                  birth_date=(1983, 11, 3, 12), gender="male",
                  theme="WORK", compute_only=True,
                  heluo_target_date=date(2026, 8, 17))
        self.assertIsNotNone(r.heluo_diagnosis, "管线跑完却没产出诊断图")
        self.assertIsNotNone(r.heluo_guidance, "管线跑完却没产出行动建议")
        self.assertTrue(r.heluo_diagnosis.assertions)
        self.assertTrue(r.heluo_guidance.action_items)


if __name__ == "__main__":
    unittest.main()