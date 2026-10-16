# -*- coding: utf-8 -*-
"""Z34: 夹宫双侧判定回归测试

背景：Z29 夹宫实现为"任一相邻宫有羊/陀即触发"，导致单侧陀罗（案例4：
陀罗在父母巳、擎羊在田宅未，命宫辰仅单侧相邻有陀罗）误报"羊陀夹命"，
与盲派断语"亿万富翁"矛盾。Z34 修正为：羊陀须分居命宫/身宫两侧（前宫
有羊或陀 且 后宫有羊或陀）才算夹。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.interpretation import NihaiAssertionResolver


def _resolve(lunar, hour, gender):
    eng = ZiweiEngine()
    chart = eng.full_chart(lunar, hour, gender)
    entries = NihaiAssertionResolver().resolve(chart)
    jia = [e for e in entries if e.category == "夹宫断言"]
    return chart, jia


def test_z34_case4_no_false_yangtuo_jia():
    """案例4（丁亥 1947-12-25 酉时 男）：陀罗在父母巳、擎羊在田宅未，
    均非命宫辰两侧相邻（卯/巳中仅巳有陀罗单侧）→ 不得误报羊陀夹命。
    该案例盲派断语为'亿万富翁'（墓库冲开制杀取财），若误报'贫贱夭折'为硬伤。
    """
    chart, jia = _resolve((1947, 12, 25), 18, "male")
    assert chart.soul_earthly_branch == "辰"
    assert all("羊陀夹" not in e.text for e in jia), f"案例4 不应有羊陀夹命断言: {jia}"


def test_z34_true_yangtuo_jia_hit():
    """真夹命案例（癸酉年 1993-12-18 丑时 女）：羊陀分居命宫两侧 → 触发羊陀夹命。"""
    chart, jia = _resolve((1993, 12, 18), 2, "female")
    assert any("羊陀夹命" in e.text for e in jia), f"应触发羊陀夹命: {jia}"


def test_z34_true_yangtuo_jia_hit2():
    """真夹命案例2（壬辰年 1952-01-03 卯时 男）：命宫亥被羊陀夹 → 触发。"""
    chart, jia = _resolve((1952, 1, 3), 6, "male")
    assert any("羊陀夹命" in e.text for e in jia), f"应触发羊陀夹命: {jia}"


def test_z34_1983_still_zero():
    """1983-11-03 午时男（七杀坐命辰）此前 0 条夹宫断言，修复后仍应为 0。"""
    chart, jia = _resolve((1983, 9, 29), 11, "male")
    assert len(jia) == 0, f"1983 案例不应有夹宫断言: {jia}"
