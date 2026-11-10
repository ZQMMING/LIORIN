"""事件域: 分析年流年冲 → 事件触发符号（原典·岁运）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.tongshu.reasoning.ziping_bridge import _SHIJIAN_ANCHORS, run_ziping_judgment


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

def test_shijian_taisui_chong_yun():
    """V7.192: 太岁冲运(流年支冲当前大运支)是事件触发符号。

    1984 甲子 丙子 乙亥 甲申 男(起运约9.69岁, 第1运丁丑):
    2003 癸未 → 未丑冲大运, 且未不冲命局(子子亥申) → 仅运冲触发。
    """
    from tongshu.engines.bazi_engine import BaziEngine

    chart = BaziEngine().compute((1984, 12, 7, 16), gender="male")
    synth = run_ziping_judgment(chart, target_year=2003)
    assert synth.shijian.conclusion.value == "EVENT_EXIST"
    assert "流年冲大运" in synth.shijian.reasoning
    assert "未丑" in synth.shijian.reasoning
    assert "未核验" in synth.shijian.reasoning
    assert synth.shijian.rule_refs == ["ZIPING_ENGINES_P0"] + list(_SHIJIAN_ANCHORS)
    assert synth.shijian.evidence_refs == list(_SHIJIAN_ANCHORS)


def test_shijian_absent_mentions_dayun(chart):
    """无冲时 EVENT_ABSENT 的口径覆盖「命局及当前大运」。"""
    synth = run_ziping_judgment(chart, target_year=2001)
    assert synth.shijian.conclusion.value == "EVENT_ABSENT"
    assert "当前大运" in synth.shijian.reasoning
