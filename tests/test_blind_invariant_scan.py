# -*- coding: utf-8 -*-
"""盲派不变式扫描的回归守护（㊻s132）。

两层：
1) 枚举/自洽/应期：随机 12 盘跑 scripts/blind_invariant_scan.py 的检查器，必须 0 问题；
2) 事件域白名单：blind_yingqi.EVENT_DOMAINS 必须与源码实际产出的 domain 字面量一致
   （新增域忘记登记时, 下游按域分派会漏事件）。
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def _load_scan():
    path = ROOT / "scripts" / "blind_invariant_scan.py"
    spec = importlib.util.spec_from_file_location("blind_invariant_scan", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scan():
    return _load_scan()


def test_invariant_scan_random_12(scan):
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.engines.blind_bazi_engine import BlindBaziEngine

    be = BaziEngine()
    bl = BlindBaziEngine(bazi_engine=be)
    issues = []
    cases = [
        (1975, 5, 5, 12), (1980, 6, 22, 10), (1990, 3, 1, 12), (1968, 7, 22, 14),
        (2025, 8, 20, 14), (1890, 2, 12, 4), (1955, 9, 22, 2), (1968, 10, 21, 4),
        (1913, 11, 18, 22), (1930, 12, 1, 8), (1945, 4, 18, 16), (2005, 2, 3, 6),
    ]
    for i, b in enumerate(cases):
        chart = be.compute(b, gender="male" if i % 2 == 0 else "female")
        r = bl.compute_from_chart(chart)
        scan.check_result(issues, i, b, r)
    assert not issues, f"不变式扫描发现问题: {issues[:5]}"


DOMAIN_SOURCE = SRC / "tongshu" / "engines" / "blind_yingqi.py"


def test_event_domains_registered():
    from tongshu.engines.blind_yingqi import EVENT_DOMAINS

    text = DOMAIN_SOURCE.read_text(encoding="utf-8")
    # 源码里的 domain 赋值/回填都会带引号字面量; 逐个核对已登记
    import re
    literals = set(re.findall(r"['\"]([^'\"]*?(?:财富|婚姻|官贵|家宅|学业|灾伤|刑伤|竞争|子女|禄位|口舌)[^'\"]*?)['\"]", text))
    # 「口舌子女」「子女前程」等都匹配; 只核对"看起来是域值"的短串
    candidates = {x for x in literals if len(x) <= 6 and "=" not in x}
    unknown = sorted(c for c in candidates if c not in EVENT_DOMAINS and not c.endswith("事件"))
    assert not unknown, f"blind_yingqi 产出了未登记的事件域: {unknown}"
