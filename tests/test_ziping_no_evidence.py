# -*- coding: utf-8 -*-
"""COV-013①② NO_EVIDENCE 显式登记 —— 引擎侧 fail-closed 缺省行为守卫。

登记模块: src/tongshu/reasoning/ziping_no_evidence.py
守卫目标:
  1) 登记表完整（COV-013-1/COV-013-2 双主题, verdict=NO_EVIDENCE, 证据+缺省行为齐备）
  2) COV-013-1: current_dayun 在 ziping_bridge 内仅流向事件域 _shijian_from_facts
     —— 不得流入喜忌/旺衰/用神任何重定路径
  3) COV-013-2: bridge 无小运计算路径（源码不含 '小运'）
"""
import inspect
from pathlib import Path

import pytest

from src.tongshu.reasoning import ziping_bridge
from src.tongshu.reasoning.ziping_no_evidence import (
    DECIDED_TOPICS,
    NO_EVIDENCE_TOPICS,
    assert_topic_not_concluded,
)
from src.tongshu.reasoning.ziping_bridge import (
    _current_xiaoyun,
    _xiaoyun_from_chart,
)

_REQUIRED = {
    "COV-013-1", "COV-013-2",
    "COV-014-CONG", "COV-027-FU",
    "COV-029-DELING", "COV-029-JIXIONG", "COV-029-SAME8ZI",
}


def test_registry_completeness():
    assert _REQUIRED <= set(NO_EVIDENCE_TOPICS)
    for tid in _REQUIRED:
        t = NO_EVIDENCE_TOPICS[tid]
        assert t["verdict"] == "NO_EVIDENCE", tid
        assert t["evidence"], tid
        assert "fail-closed" in t["default_behavior"], tid
        assert t["topic"], tid


def test_hook_fail_closed():
    with pytest.raises(NotImplementedError):
        assert_topic_not_concluded("COV-013-1")
    with pytest.raises(NotImplementedError):
        assert_topic_not_concluded("COV-013-2")
    with pytest.raises(NotImplementedError):
        assert_topic_not_concluded("COV-014-CONG")
    with pytest.raises(NotImplementedError):
        assert_topic_not_concluded("COV-027-FU")
    with pytest.raises(NotImplementedError):
        assert_topic_not_concluded("COV-029-JIXIONG")
    with pytest.raises(KeyError):
        assert_topic_not_concluded("COV-999-9")


def _current_dayun_functions():
    """ziping_bridge 中签名含 current_dayun 的函数集合（结构守卫白名单外即违规）。"""
    out = {}
    for name, fn in inspect.getmembers(ziping_bridge, inspect.isfunction):
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        if "current_dayun" in sig.parameters:
            out[name] = fn
    return out


_ALLOWED_DAYUN_FNS = {"_shijian_from_facts", "_engines_p0_synthesis", "run_ziping_judgment"}


def test_dayun_confined_to_event_domain():
    """COV-013-1: 大运只做事件域触发符号，不入喜忌/旺衰/用神重定。"""
    fns = _current_dayun_functions()
    assert set(fns) <= _ALLOWED_DAYUN_FNS, f"current_dayun 泄出到未授权函数: {set(fns) - _ALLOWED_DAYUN_FNS}"
    assert "_shijian_from_facts" in fns, "事件域触发符号链缺失"
    # 综合层内 current_dayun 只出现在签名与转交事件域两处（防新增重定路径）
    body = inspect.getsource(fns["_engines_p0_synthesis"])
    assert body.count("current_dayun") == 2, (
        "COV-013-1 守卫: _engines_p0_synthesis 内 current_dayun 出现次数变更, "
        "疑似新增大运参与喜忌/旺衰的路径"
    )


def test_xiaoyun_zuixingzi_algorithm():
    """COV-006 已裁决(醉醒子法): 时柱次位起, 阳年顺/阴年逆, 一位一年(虚岁)。

    COV-013② 守卫升级: 小运计算路径存在, 但 xiaoyun 标识符仅限事实层两函数,
    综合层/事件域/入口不消费（较量框架立项前禁止）。
    """
    import re
    allowed = {"_xiaoyun_from_chart", "_current_xiaoyun"}
    hits = set()
    for name, fn in inspect.getmembers(ziping_bridge, inspect.isfunction):
        if re.search(r"xiaoyun", inspect.getsource(fn), re.IGNORECASE):
            hits.add(name)
    assert hits <= allowed, f"COV-013② 守卫: xiaoyun 标识符泄出到 {hits - allowed}"
    assert hits == allowed, f"事实层函数缺失: {allowed - hits}"
    # 综合层/事件域/入口不得消费小运
    for fn_name in ("_engines_p0_synthesis", "_shijian_from_facts", "run_ziping_judgment"):
        fn = getattr(ziping_bridge, fn_name)
        assert not re.search(r"xiaoyun", inspect.getsource(fn), re.IGNORECASE), (
            f"COV-013② 守卫: {fn_name} 消费小运（较量框架立项前禁止）"
        )
    # 原文样例: 阳命阳年 甲子时生 堕地(虚岁1)乙丑 2岁丙寅
    assert _current_xiaoyun("甲子", True, 1984, 1984) == "乙丑"
    assert _current_xiaoyun("甲子", True, 1984, 1985) == "丙寅"
    assert _current_xiaoyun("甲子", True, 1984, 1986) == "丁卯"
    # 阴年逆行: 1岁乙丑 2岁甲子 3岁癸亥
    assert _current_xiaoyun("甲子", False, 1985, 1985) == "乙丑"
    assert _current_xiaoyun("甲子", False, 1985, 1986) == "甲子"
    assert _current_xiaoyun("甲子", False, 1985, 1987) == "癸亥"
    # 周而复始: 壬戌时(58) 阳年 1岁癸亥 2岁甲子
    assert _current_xiaoyun("壬戌", True, 1984, 1984) == "癸亥"
    assert _current_xiaoyun("壬戌", True, 1984, 1985) == "甲子"
    # 年阴阳定方向: 甲阳顺/乙阴逆
    assert _xiaoyun_from_chart(_FakeChart("甲子", "甲子")) == ("甲子", True)
    assert _xiaoyun_from_chart(_FakeChart("甲子", "乙丑")) == ("甲子", False)
    # 不猜: 缺参数/坏干支 → None
    assert _current_xiaoyun(None, True, 1984, 1984) is None
    assert _current_xiaoyun("甲子", None, 1984, 1984) is None
    assert _current_xiaoyun("甲子", True, None, 1984) is None
    assert _current_xiaoyun("甲子", True, 1984, None) is None
    assert _current_xiaoyun("甲子", True, 1984, 1980) is None  # 未出生
    assert _current_xiaoyun("坏支", True, 1984, 1984) is None
    assert _xiaoyun_from_chart(_FakeChart("", "甲子")) == (None, None)


class _FakeChart:
    def __init__(self, hour, year):
        self._p = {"hour": hour, "year": year}

    def get_pillars_chinese(self):
        return self._p


def test_cov006_decision_recorded():
    """COV-006 裁决存档: 醉醒子法 + 双锚 + 拒绝理由。"""
    d = DECIDED_TOPICS["COV-006"]
    assert "醉醒子" in d["decision"]
    assert "SUI_YUN.RE_EVALUATION.YUN_XIAN.002" in d["anchors"]
    assert "SUI_YUN.RE_EVALUATION.YUN_XIAN.006" in d["anchors"]
    assert d["rejected"], "裁决须记录落选方案及理由"
    assert "较量" in d["consumption_boundary"]


_ZIPING_LINE_DIRS = [
    Path(__file__).resolve().parent.parent / "src" / "tongshu" / "reasoning",
    Path(__file__).resolve().parent.parent / "engines" / "common",
]


def _ziping_line_sources():
    """ziping 判定线源码；排除登记模块自身（登记条目自引用不算占用）。"""
    out = {}
    for d in _ZIPING_LINE_DIRS:
        for p in sorted(d.glob("*.py")):
            if p.name == "ziping_no_evidence.py":
                continue
            out[p.name] = p.read_text(encoding="utf-8", errors="replace")
    return out


def test_no_fu_zhuan_anchors():
    """COV-027: 太微赋/病药赋/取用神赋 三名目在 ziping 判定线零锚点占用。"""
    for name, src in _ziping_line_sources().items():
        for fu in ("太微赋", "病药赋", "取用神赋"):
            assert fu not in src, f"COV-027 守卫: {name} 出现 {fu} 锚点"


def test_shouyao_disclaimer_only():
    """COV-029②③: 寿夭仅允许出现在 yongyao_resolve 免责声明，无寿夭判定域。"""
    hits = []
    for name, src in _ziping_line_sources().items():
        for i, line in enumerate(src.splitlines(), 1):
            if "寿夭" in line:
                hits.append((name, i, line.strip()))
    assert len(hits) == 1, f"COV-029 守卫: 寿夭出现 {len(hits)} 处, 期望仅 yongyao 免责声明 1 处"
    name, _, line = hits[0]
    assert name == "yongyao_resolve.py" and "不判吉凶寿夭" in line, hits


def test_no_xiangqi_deshi_branch():
    """COV-029①: judge_strength 按 DE_LING.005 口径, 不得实现「相气算得时」。"""
    src = _ziping_line_sources()["ziping_classic_check.py"]
    assert "相气" not in src, "COV-029① 守卫: classic_check 出现相气得时口径"
