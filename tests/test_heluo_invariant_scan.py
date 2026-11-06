"""河洛不变式扫描固化测试。

把 ``scripts/heluo_invariant_scan.py`` 的结构不变式检查接进 pytest：
先天六爻 / 元堂爻位与阴阳 / 后天爻变与第一步卦名 / 结构六爻与卦名 /
化工卦 / 流年卦 / 解层键与叶不叶证据。

说明：本测试是"质量护栏"，只验证结构自洽，不产真值；真值见
``cases/truth/heluo_truth_cases.json``。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "scripts" / "heluo_invariant_scan.py"

# 固定盘（覆盖男女、三元、单双数、全阳全阴）
CASES = [
    ([("甲", "子"), ("丙", "寅"), ("戊", "辰"), ("庚", "午")], "male"),
    ([("乙", "丑"), ("丁", "卯"), ("己", "巳"), ("辛", "未")], "female"),
    ([("庚", "申"), ("壬", "戌"), ("甲", "子"), ("丙", "寅")], "male"),
    ([("辛", "酉"), ("癸", "亥"), ("乙", "丑"), ("丁", "卯")], "female"),
    ([("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")], "male"),
    ([("癸", "亥"), ("壬", "戌"), ("乙", "未"), ("壬", "午")], "male"),
    ([("戊", "申"), ("己", "未"), ("庚", "申"), ("辛", "巳")], "male"),
    ([("丁", "未"), ("癸", "卯"), ("庚", "子"), ("丁", "丑")], "female"),
    ([("乙", "巳"), ("甲", "申"), ("辛", "酉"), ("乙", "未")], "male"),
    ([("癸", "丑"), ("乙", "卯"), ("戊", "戌"), ("癸", "亥")], "male"),
    ([("甲", "寅"), ("丙", "子"), ("己", "亥"), ("戊", "辰")], "male"),
    ([("戊", "申"), ("壬", "戌"), ("甲", "子"), ("丙", "寅")], "female"),
    ([("乙", "丑"), ("辛", "巳"), ("丁", "亥"), ("辛", "亥")], "female"),
    ([("乙", "未"), ("乙", "酉"), ("丙", "戌"), ("己", "丑")], "female"),
    ([("庚", "寅"), ("戊", "寅"), ("甲", "子"), ("丙", "寅")], "male"),
    ([("丁", "亥"), ("甲", "辰"), ("戊", "辰"), ("甲", "寅")], "male"),
]


def _load_scan():
    spec = importlib.util.spec_from_file_location("heluo_invariant_scan", SCAN)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scan():
    return _load_scan()


@pytest.mark.parametrize("bazi,gender", CASES)
def test_chart_invariants(scan, bazi, gender):
    issues: list[str] = []
    scan.check_case(issues, "fixed", bazi, gender)
    assert issues == []


def test_scan_script_reports_clean(scan, capsys):
    import sys

    argv = sys.argv
    sys.argv = ["heluo_invariant_scan.py", "12"]
    try:
        code = scan.main()
    finally:
        sys.argv = argv
    assert code == 0
    out = capsys.readouterr().out
    assert "发现问题 0" in out
