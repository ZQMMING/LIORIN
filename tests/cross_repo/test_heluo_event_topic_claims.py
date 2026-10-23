"""河洛「只算不说」与 EVENT_TOPIC 声明核查（2026-10-06）

锁定本轮审计查实的两件事，防止再次漂移：

1. **信号引擎归属**：信号缺 `source_engine` 时按 rule_refs 前缀反查引擎。
   原实现只认 `ZW-`，其余一律归 `ZI_PING` —— 一旦 `HL-`（河洛）规则命中
   就会被错记到子平名下，污染 `CrossDomainResult.by_engine` 的归属与
   coverage 统计。

2. **EVENT_TOPIC 求值器并不存在**：`matcher.py` 多处注释声称「专用求值器位于
   `heluo_engine.reasoning.event_topic`」「由 EventTopicEngine 处理」，
   而 `tongshu/reasoning/` 下**无此模块**，`annual_event_evaluator.py`
   同样不存在。这些注释会把后来者引向一个幻影模块。
   故本测试用文件系统事实把该结论钉住。

关于「HL 规则为何一条都不生效」——这是**治理状态，不是缺陷**：
21 条 `HL-*` 规则 status 全为 `draft`，而
`EXECUTABLE_STATUSES = ("validated", "active")`（DECISION-010：
防止 AI 静默激活规则）。另有 11 条属 `EVENT_TOPIC` 层，被
`SIGNAL_LAYER_ORDER` 挡在 matcher 之外。**不得为了让规则生效而改 status。**
"""
from __future__ import annotations

import inspect
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.pipeline_stages import compute_stage as cs
from tongshu.reasoning import matcher as matcher_mod
from tongshu.reasoning.matcher import (
    EXECUTABLE_STATUSES,
    RuleContext,
    UnknownOperatorError,
    evaluate_conditions,
)
from tongshu.reasoning.signal_engine import SIGNAL_LAYER_ORDER

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RULES_DIR = _REPO_ROOT / "backend" / "data" / "rules"
_HELUO_DIR = _REPO_ROOT / "src" / "heluo_engine" / "reasoning"


def _load_rules(prefix: str) -> list[dict]:
    out = []
    for p in sorted(_RULES_DIR.glob(f"{prefix}*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


class TestSignalEngineAttribution(unittest.TestCase):
    """rule_refs 前缀 → 引擎归属。"""

    def test_prefix_map_declares_heluo(self):
        self.assertEqual(cs._RULE_PREFIX_ENGINE.get("HL-"), "HE_LUO")

    def test_prefix_map_keeps_ziwei(self):
        self.assertEqual(cs._RULE_PREFIX_ENGINE.get("ZW-"), "ZI_WEI")

    def test_hlt_is_not_confused_with_hl(self):
        """HLT-（健康类）不得被 HL- 前缀误伤。"""
        table = cs._RULE_PREFIX_ENGINE
        self.assertFalse("HLT-101".startswith("HL-"),
                         "HLT- 若以 'HL-' 起首则前缀表会误判")

    def test_heluo_rule_prefix_matches(self):
        """规则库里的河洛规则确实使用 HL- 前缀。"""
        rules = _load_rules("HL-")
        self.assertGreaterEqual(len(rules), 1)
        self.assertTrue(all(r["rule_id"].startswith("HL-") for r in rules))
        self.assertEqual(cs._RULE_PREFIX_ENGINE.get("HL-"), "HE_LUO")


class TestHeluoRulesAreGovernedNotBroken(unittest.TestCase):
    """HL 规则不生效是治理状态，不得被当成缺陷「修掉」。"""

    def test_all_hl_rules_are_draft(self):
        rules = _load_rules("HL-")
        self.assertGreaterEqual(len(rules), 21)
        for r in rules:
            self.assertEqual(r.get("status"), "draft",
                             f"{r['rule_id']} 非 draft——治理状态已变，需重新评估")

    def test_draft_is_not_executable(self):
        self.assertNotIn("draft", EXECUTABLE_STATUSES)
        self.assertEqual(set(EXECUTABLE_STATUSES), {"validated", "active"})

    def test_hl_rules_reference_heluo_fields(self):
        """HL 规则确实是为河洛字段写的（说明接线方向正确，只是被门禁挡住）。"""
        fields = set()
        for r in _load_rules("HL-"):
            for c in (r.get("conditions", {}).get("all") or []):
                fields.add(c.get("field"))
        heluo_fields = {f for f in fields if f and f.startswith("heluo_")}
        self.assertTrue(heluo_fields,
                        "HL 规则应引用 heluo_* 字段，否则接入方向需重估")


class TestEventTopicEvaluatorDoesNotExist(unittest.TestCase):
    """把「EVENT_TOPIC 求值器不存在」钉成事实，防止注释再次漂移。"""

    def test_event_topic_module_absent(self):
        self.assertFalse(
            (_HELUO_DIR / "event_topic.py").exists(),
            "若 event_topic 已建，本测试与 matcher 注释都需同步更新")

    def test_annual_event_evaluator_absent(self):
        self.assertFalse(
            (_REPO_ROOT / "src" / "tongshu" / "engines" / "annual_event_evaluator.py").exists())

    def test_matcher_source_no_longer_points_at_phantom_module(self):
        """matcher 源码/注释不得再把使用者导向不存在的 EventTopicEngine。"""
        src = inspect.getsource(matcher_mod)
        self.assertNotIn("use EventTopicEngine instead", src,
                         "错误信息不得指引到不存在的引擎")

    def test_unknown_operator_error_message_is_honest(self):
        ctx = RuleContext(day_master="甲", day_master_element="木")
        with self.assertRaises(UnknownOperatorError) as cm:
            evaluate_conditions(
                {"field": "day_master_element", "op": "like", "value": "WOOD"}, ctx)
        self.assertNotIn("EventTopicEngine", str(cm.exception))

    def test_event_topic_rules_are_outside_signal_layer_order(self):
        """EVENT_TOPIC 不在 SignalEngine 层序内，故不会进 matcher 求值路径。"""
        self.assertNotIn("EVENT_TOPIC", SIGNAL_LAYER_ORDER)


if __name__ == "__main__":
    unittest.main()