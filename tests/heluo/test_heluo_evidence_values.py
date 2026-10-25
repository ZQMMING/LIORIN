# -*- coding: utf-8 -*-
"""河洛证据层（evidence_producer）与诊断图（diagnosis_rule_graph）的值守恒守卫。

**为什么要有这个守卫**
------------------

2026-10-24 全面审计发现的三处盲区：

1. **`HL_JIEHOU_GUA` 无值断言** —— 它是 `evidence_producer.py:190-211` 产出的
   第 7 条证据（节候卦，含 `main_gua`/`jq_name`/`jq_index`/`moving_line`/
   `result_gua` 五个属性），但：
   * `tests/heluo/test_heluo_p0_guards.py:108-136` 的期望 rule 集合是 **6 条**，
     **不含** `HL_JIEHOU_GUA`；
   * `tests/heluo/test_h2_frozen_state.py:131-138` 用的是 `issubset`
     （**子集**断言）—— 新增或删除任一条证据都不会红。

   后果：`value=sh.get('main_gua', '')` 若取错键、或 attributes 里的
   `jq_index` 取错，诊断层拿到的是**结构正确但内容错误**的事实 ——
   而这层一旦错，下游断言照单全收。

2. **丢弃清单是单向断言** —— `test_audit_batch_20261007.py:389-391` 只保证
   「被丢的都被记录了」，**不保证「没有该被丢的」**。
   `HL_HEXAGRAM_STRUCTURE` 持续被丢（产出即丢弃），守卫永远绿。

3. **五处「静默降级」无留痕** —— 2026-10-24 已在引擎侧补留痕
   （`era_source` / `yuan_qi_error` / 判词层 error 字典 / `_KZ_ERRORS` 清零），
   本守卫把「留痕确实产出」钉住，防止将来被改回静默。

**口径说明**
------------
`HL_HEXAGRAM_STRUCTURE`（卦体结构事实）**当前是「已产出未接入」**：
`evidence_producer` 每盘都产出它，但 `HELUO_RULES` 注册表里没有这一项，
`build_diagnosis_graph` 会把它登记进 `dropped_rule_ids`（**已披露**，非静默）。
这与 `HL_DAYUN` / `HL_YUEGUA` / `HL_RIGUA`（「已注册未产出」）是**镜像**的一侧。
本守卫**不擅自注册**（注册表即授权面，删/加都改变对外契约），
而是把当前状态**显式钉住**：确知它被产出、被记录、且**不在**诊断断言链里。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.evidence_producer import HeLuoEvidenceProducer  # noqa: E402
from heluo_engine.engines.heluo.diagnosis_rule_graph import (  # noqa: E402
    HELUO_RULES, RULE_DOMAIN_MAP, build_diagnosis_graph, dropped_rules,
)

#: 证据产出但**未接入**诊断图的 rule_id（已披露，留档）。
#:
#: ⚠ 2026-10-25：原为 ``{"HL_HEXAGRAM_STRUCTURE"}`` —— 该条（卦体）证据
#:   一直**在产出**，只是注册表里没有 ⇒ 被诊断图当作「未注册」静默丢弃。
#:   现已补注册（起例卷之上 L140 卦体互体伏体定义 / L161 看卦次序），
#:   故本集合**清空**（空集合仍被本守卫钉住：将来若再有「产出但未接入」的
#:   rule_id，本守卫会变红，逼人显式登记而不是让它静默丢）。
KNOWN_PRODUCED_NOT_LINKED: set = set()

#: 已注册但**证据层不产出**的 rule_id（留档）。
#:
#: ⚠ 2026-10-25：原为 ``{"HL_DAYUN", "HL_YUEGUA", "HL_RIGUA"}``（三条
#:   「注册了却从不产出」的空授权）。现证据生产器**已产出**这三条
#:   （见 time_layer_judgment），故本集合清空。
#:   注：``HL_RIGUA``（流日）在**无 target_date** 的直调场景下确实不产出
#:   （引擎不算日卦）—— 但那不是「规则未接入」，故不入本清单。
KNOWN_REGISTERED_NOT_PRODUCED: set = set()


class TestEvidenceValues(unittest.TestCase):
    """证据的**值**必须与河洛结果一致（不只是「有这条证据」）。"""

    @classmethod
    def setUpClass(cls):
        cls.adapter = HeluoAdapter()
        cls.result = cls.adapter.compute((1990, 6, 15, 14), gender="male",
                                         target_date="2026-10-23")
        cls.evidences = HeLuoEvidenceProducer().produce(cls.result)
        cls.by_rule = {e.rule_id: e for e in cls.evidences}

    def test_jiehou_evidence_values_match_result(self):
        """HL_JIEHOU_GUA 的值与属性必须逐项等于 result.seasonal_hexagram。"""
        ev = self.by_rule.get("HL_JIEHOU_GUA")
        self.assertIsNotNone(ev, "应产出 HL_JIEHOU_GUA 证据")
        sh = self.result.seasonal_hexagram
        self.assertTrue(sh, "结果里应有节候卦")
        self.assertEqual(ev.value, sh.get("main_gua", ""),
                         "HL_JIEHOU_GUA.value 应等于 seasonal_hexagram.main_gua")
        for key in ("jq_name", "jq_index", "main_gua", "moving_line", "result_gua"):
            with self.subTest(attr=key):
                self.assertEqual(ev.attributes.get(key), sh.get(key),
                                 f"HL_JIEHOU_GUA.attributes[{key}] 与结果不一致")

    def test_all_seven_evidence_rules_produced(self):
        """证据 rule_id 集合必须**精确相等**（新增/删除一条都会被抓）。

        ⚠ 2026-10-25：新增四条**时间层**证据（大运/流年/流月/流日）。
        原断言名为 "seven"（7 条），现为 11 条 —— 名字保留是为了让历史
        git blame 可追，但期望集合已按实码更新。
        ⚠ 集合**不是**包含关系：新加一条而忘记改本断言 ⇒ 变红（正是本守卫
          的用意：守住「证据集合与断言同步」这件事）。
        """
        expected = {
            "HL_TIAN_DI_SHU", "HL_PRENATAL_HEXAGRAM", "HL_YUANTANG",
            "HL_POSTNATAL_HEXAGRAM", "HL_HEXAGRAM_STRUCTURE", "HL_HUA_GONG",
            "HL_JIEHOU_GUA",
            # 2026-10-25 时间层（详见 time_layer_judgment 模块）
            "HL_DAYUN", "HL_LIUNIAN_GUA", "HL_YUEGUA", "HL_RIGUA",
        }
        self.assertEqual(set(self.by_rule), expected,
                         "证据 rule_id 集合与期望不符（新增/删除一条都会被抓）")

    def test_evidence_values_non_empty(self):
        """每条证据的 value 不得为空（空值=取错键）。"""
        for rid, ev in self.by_rule.items():
            with self.subTest(rule=rid):
                self.assertTrue(str(ev.value).strip(),
                                f"{rid} 的 value 为空（可能取错了键）")


class TestDroppedRulesBidirectional(unittest.TestCase):
    """丢弃清单的**双向**断言。"""

    @classmethod
    def setUpClass(cls):
        cls.adapter = HeluoAdapter()
        cls.result = cls.adapter.compute((1990, 6, 15, 14), gender="male",
                                         target_date="2026-10-23")
        cls.evidences = HeLuoEvidenceProducer().produce(cls.result)

    def test_dropped_set_is_exactly_known(self):
        """被丢弃的 rule_id 集合必须**恰好**是留档清单。

        单向断言（只保证「被丢的都记录了」）挡不住「新证据悄悄被丢」——
        这正是本守卫要补的方向。
        """
        graph = build_diagnosis_graph(self.evidences, [])
        dropped = set(dropped_rules())
        produced = {e.rule_id for e in self.evidences}
        expect = KNOWN_PRODUCED_NOT_LINKED & produced
        self.assertEqual(
            dropped, expect,
            "被丢弃的 rule_id 与留档清单不符：多=%r 少=%r"
            % (sorted(dropped - expect), sorted(expect - dropped)))
        self.assertIsNotNone(graph)

    def test_known_produced_not_linked_is_actually_produced(self):
        """留档的「已产出未接入」必须真的产出了（否则留档本身过时了）。"""
        produced = {e.rule_id for e in self.evidences}
        for rid in KNOWN_PRODUCED_NOT_LINKED:
            with self.subTest(rule=rid):
                self.assertIn(rid, produced,
                              f"{rid} 登记为「已产出未接入」，但本盘没产出 —— 留档过时")

    def test_known_registered_not_produced_stays_registered(self):
        """留档的「已注册未产出」必须仍在注册表里（不得被悄悄删掉）。"""
        for rid in KNOWN_REGISTERED_NOT_PRODUCED:
            with self.subTest(rule=rid):
                self.assertIn(rid, HELUO_RULES)
                self.assertIn(rid, RULE_DOMAIN_MAP)

    def test_registered_rules_have_domain(self):
        """注册表里的每条规则都必须有领域映射（否则落 default，语义错配）。"""
        for rid in HELUO_RULES:
            with self.subTest(rule=rid):
                self.assertIn(rid, RULE_DOMAIN_MAP,
                              f"{rid} 已注册但无领域映射，会落到 default")


class TestSilentDegradationTraced(unittest.TestCase):
    """五处「静默降级」必须留痕（2026-10-24 引擎侧补的）。"""

    @classmethod
    def setUpClass(cls):
        cls.adapter = HeluoAdapter()
        cls.result = cls.adapter.compute((1990, 6, 15, 14), gender="male",
                                         target_date="2026-10-23")

    def test_era_source_present(self):
        """era 的来源必须标记（era 决定寄宫 → 全链判词）。"""
        self.assertIn(self.result.era_source, ("explicit", "derived", "fallback"),
                      "era_source 必须是三种来源标记之一")
        self.assertTrue(self.result.era_source,
                        "era_source 不得为空 —— era 静默回落而无标记 = 缺失被当成正常")

    def test_yuan_qi_error_field_exists(self):
        """元气层异常必须有留痕字段（无异常时为空字符串）。"""
        self.assertIsInstance(self.result.yuan_qi_error, str)
        if self.result.yuan_qi is None:
            self.assertTrue(
                self.result.yuan_qi_error,
                "yuan_qi 为 None 时必须说明是「异常」还是「本无元气」，不得沉默")

    def test_guajie_present_or_error(self):
        """判词层要么正常产出，要么挂 error 字典 —— 不得静默为 None。"""
        gj = self.result.guajie
        self.assertIsNotNone(gj, "判词层不得静默丢失")
        if isinstance(gj, dict) and "error" in gj:
            self.assertTrue(str(gj["error"]).strip(), "error 字典须有内容")

    def test_kuozhan_errors_are_per_run(self):
        """kuozhan_errors() 必须是「最近一次」，不是进程级累积。

        2026-10-24 前：`_KZ_ERRORS` 只 append 从不清空，
        而 docstring 声称「最近一次」—— 第一盘失败过一次后，
        之后每一盘都带着那条陈迹。
        """
        from heluo_engine.engines.heluo import guajie as gj
        before = list(gj.kuozhan_errors())
        # 再跑一盘健康的
        self.adapter.compute((1990, 6, 15, 14), gender="male",
                             target_date="2026-10-23")
        after = list(gj.kuozhan_errors())
        self.assertEqual(len(after), len(before),
                         "健康盘跑完后 kuozhan_errors 不应比上次更多"
                         "（若更多，说明有累积或新失败）")


if __name__ == "__main__":
    unittest.main()
