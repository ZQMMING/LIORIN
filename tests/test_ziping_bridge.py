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
    build_context,
    run_ziping_judgment,
    synthesis_to_dict,
)
from tongshu.reasoning.judgment import JudgmentConclusion  # noqa: E402


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
    assert "土" in s.yongshen.reasoning
    # p0 线明言不判身强, 十神/事件未输出 → 必须 UNKNOWN 且写明原因
    for domain in ("wangshuai", "shishen", "shijian"):
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
