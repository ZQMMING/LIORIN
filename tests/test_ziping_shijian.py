"""事件域: 分析年流年冲 → 事件触发符号（原典·岁运）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.tongshu.reasoning.ziping_bridge import run_ziping_judgment


@pytest.fixture(scope="module")
def chart():
    from tongshu.engines.bazi_engine import BaziEngine

    return BaziEngine().compute((1990, 3, 1, 12), gender="male")


def test_no_target_year_is_unknown(chart):
    s = run_ziping_judgment(chart)
    assert s.shijian.conclusion.value == "UNKNOWN"
    assert "未指定分析年" in s.shijian.reasoning


def test_clash_year_marks_event_exist(chart):
    s = run_ziping_judgment(chart, target_year=2027)  # 丁未: 未冲日支丑
    assert s.shijian.conclusion.value == "EVENT_EXIST"
    assert "丑未冲" in s.shijian.reasoning
    assert "SUI_YUN.RE_EVALUATION.LIU_NIAN.005" in s.shijian.evidence_refs
    assert "未核验" in s.shijian.reasoning  # 不断言作用成立


def test_plain_year_marks_event_absent(chart):
    s = run_ziping_judgment(chart, target_year=2024)  # 甲辰
    assert s.shijian.conclusion.value == "EVENT_ABSENT"
    assert "无冲" in s.shijian.reasoning


def test_composer_keeps_shijian_fail_closed(chart):
    """S4 治理门: SHIJIAN 域 claim 仍被 fail-closed 拦截(15.14 method audit)。

    事件域现在有方法与证据锚, 但放行 claim 需治理裁决; 本测试锁定现状,
    防止无意中放开伪事件判定。
    """
    from src.tongshu.governance.judgment_claim_composer import JudgmentClaimComposer

    synth = run_ziping_judgment(chart, target_year=2027)
    assert synth.shijian.conclusion.value == "EVENT_EXIST"
    ids = [c.get("claim_id") for c in JudgmentClaimComposer(provenance_resolver=None).compose(synth)]
    assert not any("shijian" in (i or "") for i in ids)
