"""ZIPING 辨层接线测试 — BaziEngine → ZipingBridge → JudgmentFactory

验证:
1. build_context 将 BaziChart 正确转换为 judgment context
2. run_ziping_judgment 端到端产出五大域判断
3. 判断可追溯 (rule_refs/evidence_refs)
4. Fail Closed: 空chart不崩溃
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tongshu.engines.bazi_engine import BaziEngine  # noqa: E402
from tongshu.reasoning.ziping_bridge import (  # noqa: E402
    _engines_p0_synthesis,
    build_context,
    run_ziping_judgment,
    synthesis_to_dict,
)
from tongshu.reasoning.judgment import (  # noqa: E402
    DomainJudgment,
    JudgmentConclusion,
    JudgmentDomain,
    JudgmentSynthesis,
)
import pytest



def _make_chart(solar_date=(1990, 3, 1, 12), gender="male"):
    engine = BaziEngine()
    return engine.compute(solar_date=solar_date, gender=gender)


def test_build_context_structure():
    """build_context 必须输出 {natal: {pillars: [4], day_master}}。"""
    chart = _make_chart()
    ctx = build_context(chart)
    assert "natal" in ctx
    assert len(ctx["natal"]["pillars"]) == 4
    assert ctx["natal"]["day_master"]
    positions = [p["position"] for p in ctx["natal"]["pillars"]]
    assert positions == ["YEAR", "MONTH", "DAY", "HOUR"]
    # 每柱有干支
    for p in ctx["natal"]["pillars"]:
        assert p["heavenly_stem"]
        assert p["earthly_branch"]


def test_run_ziping_judgment_core_domains():
    """端到端: engines(p0) 生产入口 → 五域 (格局成/用药方向, 其余域 fail-closed)。"""
    chart = _make_chart()
    s = run_ziping_judgment(chart)
    assert s is not None
    # 1990-03-01 12:00 男 → 建禄月劫格成, 用药方向=土 (engines 线实测)
    assert s.geju is not None and s.geju.conclusion == JudgmentConclusion.ESTABLISHED
    assert "建禄月劫格" in s.geju.reasoning
    assert s.yongshen is not None and s.yongshen.conclusion == JudgmentConclusion.PRIMARY
    assert "金" in s.yongshen.reasoning
    # 旺衰: 原典三才合参(得令/得地/得势)独立判定, 不再固定 UNKNOWN
    assert s.wangshuai is not None
    assert s.wangshuai.conclusion != JudgmentConclusion.UNKNOWN
    assert "得令" in s.wangshuai.reasoning or "失令" in s.wangshuai.reasoning
    assert any(r.startswith("STATE.WANG_SHUAI") for r in s.wangshuai.rule_refs)
    # 事件域仍 fail-closed (p0 未指定分析年), 十神无病药锚时不硬断
    for domain in ("shishen", "shijian"):
        item = getattr(s, domain)
        assert item is not None and item.conclusion == JudgmentConclusion.UNKNOWN
        assert item.reasoning


def test_judgment_traceable():
    """判断可追溯: 格局/用神带 rule_refs + 可解析的 p0 切片证据锚。"""
    chart = _make_chart()
    s = run_ziping_judgment(chart)
    assert s.geju is not None
    assert any(r.startswith("PZZQ") for r in s.geju.rule_refs)
    assert s.geju.evidence_refs, "格局结论必须带 p0 切片证据锚"
    assert s.yongshen is not None and "ZIPING_ENGINES_P0" in s.yongshen.rule_refs
    assert s.yongshen.evidence_refs, "用神结论必须带 p0 切片证据锚"


def test_deterministic():
    """确定性: 相同 chart → 相同结论 (忽略 created_at 时间戳)。"""
    chart1 = _make_chart()
    chart2 = _make_chart()
    s1 = run_ziping_judgment(chart1).to_dict()
    s2 = run_ziping_judgment(chart2).to_dict()
    for domain in ("wangshuai", "geju", "yongshen", "shishen", "shijian"):
        for d in (s1[domain], s2[domain]):
            if d:
                d.pop("created_at", None)
        assert s1[domain] == s2[domain]


def test_fail_closed_empty_chart():
    """Fail Closed: 空对象不崩溃，五域全 UNKNOWN 且带原因。"""
    class Empty:
        pass
    s = run_ziping_judgment(Empty())
    assert s is not None
    for domain in ("wangshuai", "geju", "yongshen", "shishen", "shijian"):
        item = getattr(s, domain)
        assert item is not None and item.conclusion == JudgmentConclusion.UNKNOWN
        assert item.reasoning


def test_synthesis_to_dict():
    """序列化: 输出可被解层消费的 dict。"""
    chart = _make_chart()
    s = run_ziping_judgment(chart)
    d = synthesis_to_dict(s)
    assert "wangshuai" in d
    assert "has_core_judgment" in d
    assert isinstance(d, dict)


def _unknown_for_test(domain):
    return DomainJudgment(
        domain=domain, conclusion=JudgmentConclusion.UNKNOWN,
        reasoning="测试构造: 未评估", evidence_refs=[], rule_refs=["ZIPING_ENGINES_P0"],
    )


def test_deterministic():
    """确定性: 相同 chart → 相同结论 (忽略 created_at 时间戳)。"""
    chart1 = _make_chart()
    chart2 = _make_chart()
    s1 = run_ziping_judgment(chart1).to_dict()
    s2 = run_ziping_judgment(chart2).to_dict()
    for domain in ("wangshuai", "geju", "yongshen", "shishen", "shijian"):
        for d in (s1[domain], s2[domain]):
            if d:
                d.pop("created_at", None)
        assert s1[domain] == s2[domain]


def test_fail_closed_empty_chart():
    """Fail Closed: 空对象不崩溃，五域全 UNKNOWN 且带原因。"""
    class Empty:
        pass
    s = run_ziping_judgment(Empty())
    assert s is not None
    for domain in ("wangshuai", "geju", "yongshen", "shishen", "shijian"):
        item = getattr(s, domain)
        assert item is not None and item.conclusion == JudgmentConclusion.UNKNOWN
        assert item.reasoning


def test_synthesis_to_dict():
    """序列化: 输出可被解层消费的 dict。"""
    chart = _make_chart()
    s = run_ziping_judgment(chart)
    d = synthesis_to_dict(s)
    assert "wangshuai" in d
    assert "has_core_judgment" in d
    assert isinstance(d, dict)

# ---------------------------------------------------------------------------
# 桥接 fail-closed 回归（重建于 2026-11-10）
# 背景: 此前工作树中 GPT 写的 7 个桥接 fail-closed 测试因文件重建操作丢失。
# 本段按已提交的 V7.185 fail-closed 主链重写等价场景, 防止回归:
#   1. 未知 yongyao state 不得升 PRIMARY
#   2. 未知五行不得升 PRIMARY
#   3. 无证据锚(未核验候选)不得升 PRIMARY, 也不伪造证据
#   4. SOURCE_VERSION_CONFLICT 候选不得升 PRIMARY
#   5. 格局 NOT_EVALUABLE 时 GE_FALLBACK 不得复用格局证据
#   6. GE_FALLBACK 非「源2:格体喜神」来源不得复用格局证据
#   7. 正向对照: 源2 格体喜神 / 无病格用神 在格局已核验时可复用格局证据
# ---------------------------------------------------------------------------


def _fake_p0_result(gc=None, yy=None):
    return {
        "engine_result": {
            "ge_cheng": gc if gc is not None else {},
            "pillars": {"day": ["乙", "丑"]},
            "daymaster_element": "木",
            "wuxing_power": {
                "wuxing_power": {
                    "火": {"ben_n": 1, "zhong_n": 0, "yu_n": 0, "stem_n": 1,
                           "ju_n": 0, "banhe_n": 0, "ling_state": "休", "root_detail": {}},
                    "水": {"ben_n": 1, "zhong_n": 0, "yu_n": 0, "stem_n": 0,
                           "ju_n": 0, "banhe_n": 0, "ling_state": "旺", "root_detail": {"子": "BEN"}},
                }
            },
            "ten_god_members": [],
        },
        "zhenglun": {"yongyao": yy or {}, "zhuangui": {}},
    }


_GE_OK = {
    "ge": "印格",
    "cheng_bai": "CHENG",
    "ge_evidence": {
        "rule_text": "PZZQ255: 印格成格判据",
        "zhun": ["STRUCTURE.GE_JU.CHENG_BAI.007"],
    },
}


def _pillars(*p):
    return {pos: [gz[0], gz[1]] for pos, gz in zip(("year", "month", "day", "hour"), p)}


def test_unknown_yongyao_state_cannot_become_primary():
    res = _fake_p0_result(_GE_OK, {"state": "NO_BING",
                                   "primary_medicine": {"wuxing": "火", "kind": "调候用神"}})
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN
    assert s.yongshen.reasoning


def test_unrecognized_element_cannot_become_primary():
    res = _fake_p0_result(_GE_OK, {"state": "YONGYAO_RESOLVED",
                                   "primary_medicine": {"wuxing": "光", "kind": "调候用神"}})
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN


def test_unverified_candidate_without_evidence_cannot_become_primary():
    res = _fake_p0_result(_GE_OK, {"state": "YONGYAO_RESOLVED",
                                   "primary_medicine": {"wuxing": "火", "kind": "调候用神"}})
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN
    assert s.yongshen.evidence_refs == []


def test_source_version_conflict_cannot_become_primary():
    res = _fake_p0_result(_GE_OK, {
        "state": "YONGYAO_RESOLVED",
        "primary_medicine": {"wuxing": "火", "kind": "调候用神",
                             "candidate_source_verification": "SOURCE_VERSION_CONFLICT"},
        "evidence_refs": ["PATHOLOGY.QI_HOU.008"],
    })
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN


def test_ge_fallback_not_source2_cannot_reuse_ge_evidence():
    res = _fake_p0_result(_GE_OK, {
        "state": "GE_FALLBACK",
        "ge_fallback_source": "源4:救应候选",
        "primary_medicine": {"wuxing": "水", "kind": "救应神"},
    })
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN
    assert "STRUCTURE.GE_JU.CHENG_BAI.007" not in (s.yongshen.evidence_refs or [])


def test_geju_not_evaluable_blocks_ge_fallback_reuse():
    gc = {"ge": "印格", "cheng_bai": "NOT_EVALUABLE",
          "ge_evidence": {"rule_text": "PZZQ255: 印格成格判据",
                          "zhun": ["STRUCTURE.GE_JU.CHENG_BAI.007"]}}
    res = _fake_p0_result(gc, {
        "state": "GE_FALLBACK",
        "ge_fallback_source": "源2:格体喜神",
        "primary_medicine": {"wuxing": "水", "kind": "格局用神"},
    })
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.UNKNOWN


def test_ge_fallback_source2_reuses_ge_evidence_when_verified():
    res = _fake_p0_result(_GE_OK, {
        "state": "GE_FALLBACK",
        "ge_fallback_source": "源2:格体喜神",
        "primary_medicine": {"wuxing": "水", "kind": "格局用神(喜神为辅)"},
    })
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.PRIMARY
    assert "STRUCTURE.GE_JU.CHENG_BAI.007" in s.yongshen.evidence_refs


def test_no_bing_ge_yong_reuses_ge_evidence_when_verified():
    res = _fake_p0_result(_GE_OK, {
        "state": "NO_BING",
        "primary_medicine": {"wuxing": "水", "kind": "格局用神"},
    })
    s = _engines_p0_synthesis(res, _pillars("庚午", "戊寅", "乙丑", "壬午"))
    assert s.yongshen.conclusion == JudgmentConclusion.PRIMARY
    assert "STRUCTURE.GE_JU.CHENG_BAI.007" in s.yongshen.evidence_refs
