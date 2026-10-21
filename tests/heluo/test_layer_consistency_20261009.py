"""批次 M 守卫：诊断层与解卦层对同一份数据不得给出不同结论（2026-10-09）

跑真实案例 1983-11-03 12:00 男 时暴露的三处问题，其中两处属实：

① **真缺陷**：`heluo_own_direction` 给 `judge_shu_xiong` 硬传 `birth_month=None`，
   而数格判据含阳月/阴月加减。实测该盘：
     解卦层(birth_month=11) → shu_xiong=True, pattern=以弱敌强
     诊断层(birth_month=None) → 落「不凶」→ 不判方向
   **同一份数据，两层给了不同结论**。这类不一致比缺失更坏 ——
   缺失至少是诚实的「不知道」。

② **我上一条报告说错了**：`judgment.domain` 一直是 `"MULTI_DOMAIN"`，
   是我的探针把字符串当枚举取 `.value` 才显示 None。已在此钉住。

③ **真缺陷**：`HL_HUA_GONG` 本来就有两条断言（证据环 + 冻结态补），
   source_ref 按列表拼会得到同一 id 出现两次。
"""
from __future__ import annotations

import os
import unittest
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"
BIRTH = (1983, 11, 3, 12)


def _run():
    os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
    os.environ.setdefault(
        "TONGSHU_AUTHORITY_CREDENTIALS",
        "architecture-governance:schema-v1-arch-gov-2026;"
        "admission_registry:test-cred-hash")
    from tongshu.pipeline import TONGSHUPipeline
    return TONGSHUPipeline.for_demo(_ROOT).run(
        analysis_date=date(2026, 10, 8), birth_date=BIRTH, gender="male",
        theme="WORK", compute_only=True,
        heluo_target_date=date(2026, 8, 17))


class TestShuGeConsistentAcrossLayers(unittest.TestCase):
    """① 同一份数据，诊断层与解卦层必须一致。"""

    def test_same_verdict_as_guajie_layer(self):
        from tongshu.engines.heluo.frozen_state import build_frozen_state
        from tongshu.engines.heluo.guajie import judge_shu_xiong
        from tongshu.engines.heluo import diagnosis_rule_graph as dg
        r = _run()
        H = r.heluo_result
        fs = build_frozen_state(H)
        # 解卦层：带真实生月
        bm = int(fs.birth_date[5:7])
        sx = judge_shu_xiong(H.numbers.tian_shu, H.numbers.di_shu, bm,
                             fs.gender)
        d, note = dg.heluo_own_direction("HL_TIAN_DI_SHU", fs)
        if sx.shu_xiong:
            self.assertIsNotNone(d,
                                 "解卦层判数凶，诊断层却说不判 —— 两层不一致")
            self.assertEqual(d.value, "caution")
            self.assertIn(sx.pattern or "", note)
        else:
            self.assertIsNone(d, "解卦层不判凶，诊断层却报了方向")

    def test_birth_month_is_derived_not_none(self):
        """诊断层不得硬传 birth_month=None。"""
        from tongshu.engines.heluo.frozen_state import build_frozen_state
        from tongshu.engines.heluo import diagnosis_rule_graph as dg
        r = _run()
        fs = build_frozen_state(r.heluo_result)
        seen = {}
        import tongshu.engines.heluo.guajie as G
        orig = G.judge_shu_xiong

        def spy(t, d, m, g=""):
            seen["bm"] = m
            return orig(t, d, m, g)

        G.judge_shu_xiong = spy
        try:
            dg.heluo_own_direction("HL_TIAN_DI_SHU", fs)
        finally:
            G.judge_shu_xiong = orig
        self.assertIsNotNone(seen.get("bm"),
                             "诊断层给 judge_shu_xiong 传的 birth_month 是 None")
        self.assertEqual(seen["bm"], 11)

    def test_uses_raw_tian_di_not_reduced(self):
        """必须用原始 tian_shu/di_shu（数格档位是原始和的量纲）。"""
        from tongshu.engines.heluo.frozen_state import build_frozen_state
        from tongshu.engines.heluo import diagnosis_rule_graph as dg
        import tongshu.engines.heluo.guajie as G
        r = _run()
        fs = build_frozen_state(r.heluo_result)
        seen = {}
        orig = G.judge_shu_xiong

        def spy(t, d, m, g=""):
            seen["t"] = t
            seen["d"] = d
            return orig(t, d, m, g)

        G.judge_shu_xiong = spy
        try:
            dg.heluo_own_direction("HL_TIAN_DI_SHU", fs)
        finally:
            G.judge_shu_xiong = orig
        self.assertEqual(seen["t"], r.heluo_result.numbers.tian_shu)
        self.assertEqual(seen["d"], r.heluo_result.numbers.di_shu)


class TestJudgmentDomainIsPresent(unittest.TestCase):
    """② 上一条报告误报 domain=None —— 这次钉住它真的有值。"""

    def test_domain_is_multidomain(self):
        r = _run()
        jd = r.heluo_diagnosis.judgment
        self.assertIsNotNone(jd, "判决为 None")
        self.assertEqual(jd.domain, "MULTI_DOMAIN",
                         "判决没有 domain 字段值（或不是 MULTI_DOMAIN）")

    def test_domain_is_readable_as_plain_value(self):
        """domain 是**字符串**不是枚举 —— 取值时别当枚举用（上一条报告就栽在这）。"""
        r = _run()
        jd = r.heluo_diagnosis.judgment
        self.assertIsInstance(jd.domain, str)
        self.assertTrue(jd.domain)


class TestGuidanceSourceRefHasNoDuplicates(unittest.TestCase):
    """③ source_ref 里同一规则 id 不得出现两次。"""

    def test_no_duplicate_rule_ids(self):
        r = _run()
        for a in r.heluo_guidance.action_items:
            ref = a.source_ref or ""
            if "HELUO_RULES::" not in ref:
                continue
            ids = ref.split("::", 1)[1].split(",")
            dup = sorted({x for x in ids if ids.count(x) > 1})
            self.assertEqual(dup, [],
                             "%s 的 source_ref 有重复规则 id：%s" % (a.title, dup))

    def test_count_uses_assertion_count_not_unique_rule_count(self):
        """去重后 confidence 仍须按**断言条数**算，二者口径不同不可混用。

        HL_HUA_GONG 有两条断言，去重后规则只剩 1 个；
        若把 confidence 也按去重后的规则数算，置信度会莫名变低。
        """
        r = _run()
        sup = [a for a in r.heluo_diagnosis.assertions
               if a.direction.value == "supportive"]
        item = [i for i in r.heluo_guidance.action_items
                if i.title == "把握当前趋势"]
        self.assertTrue(sup)
        self.assertTrue(item)
        want = round(0.7 * min(len(sup), 3) / 3, 2)
        self.assertAlmostEqual(item[0].confidence, want, places=2)


if __name__ == "__main__":
    unittest.main()