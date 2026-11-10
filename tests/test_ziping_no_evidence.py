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

import pytest

from src.tongshu.reasoning import ziping_bridge
from src.tongshu.reasoning.ziping_no_evidence import (
    NO_EVIDENCE_TOPICS,
    assert_topic_not_concluded,
)

_REQUIRED = {"COV-013-1", "COV-013-2"}


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
