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
    NO_EVIDENCE_TOPICS,
    assert_topic_not_concluded,
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


def test_no_xiaoyun_computation():
    """COV-013-2: 引擎不计算小运（COV-006 待裁决前缺省行为）。

    守卫对象是计算路径而非字面提及（登记注释允许提及小运）：
    不存在 xiaoyun 标识符、不存在名字含小运的函数/变量。
    """
    import re
    src = inspect.getsource(ziping_bridge)
    assert not re.search(r"xiaoyun|xiao_yun", src, re.IGNORECASE), (
        "COV-013-2 守卫: bridge 出现小运计算标识符"
    )
    assert not re.search(r"def\s+\w*小运\w*|小运\s*=", src), (
        "COV-013-2 守卫: bridge 出现小运函数/赋值路径"
    )


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
