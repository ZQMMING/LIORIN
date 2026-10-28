# -*- coding: utf-8 -*-
"""PATCH-099 Report Contract 八段式消费层
铁律: Report只消费State/Relation/Evidence, 不推理不造新态
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def build_report(state_pack):
    """八段报告, 只汇总已有state, 不推理"""
    return {
        "01_原局事实": state_pack.get("l0", {}),
        "02_六核心状态": {
            "格局": state_pack.get("pattern", {}),
            "旺衰": state_pack.get("strength", {}),
            "调候": state_pack.get("climate", {}),
            "病药": state_pack.get("bingyao", {}),
            "通关流通": state_pack.get("tongguan", {}),
            "十神": state_pack.get("ten_god", {})
        },
        "03_关系层": state_pack.get("relations", []),
        "04_时间层": state_pack.get("time", {}),
        "05_六亲层": state_pack.get("relative", {}),
        "06_事件Marker": state_pack.get("event_markers", []),
        "07_Evidence追溯": state_pack.get("trace", []),
        "08_未知未定": state_pack.get("unknowns", ["UNDETERMINED", "ABSTAIN"]),
        "_guard": {
            "禁解释造态": "财多耗身→strength下降 FORBIDDEN",
            "禁跨域合并": "调候喜水+旺衰忌水→自动取舍 FORBIDDEN",
            "禁时间改原局": "流年火旺→原局变强 FORBIDDEN"
        }
    }


if __name__ == '__main__':
    gc001 = {
        "l0": {"日主": "乙", "月令": "戌", "四柱": "癸亥 壬戌 乙未 壬午"},
        "pattern": {"state": "财格", "success": "SUCCESS", "level": "MEDIUM"},
        "strength": {"state": "SLIGHTLY_WEAK"},
        "climate": {"use": "癸(DEGRADED)"},
        "bingyao": {"病": "财多", "药": "印"},
        "tongguan": {"木土→火": ""},
        "ten_god": "印比旺",
        "relations": [{"source": "格局", "target": "调候", "relation": "INDEPENDENT"}],
        "time": {"大运": "戊午", "流年": "甲辰"},
        "relative": {"妻": "财星+日支 ACTIVATED"},
        "event_markers": ["career_marker", "relationship_marker"],
        "trace": ["PZZQ-005-007", "QTBJ-022-001", "SFTK-008-001"]
    }
    r = build_report(gc001)
    print("=== PATCH-099 Report 八段 ===")
    for k, v in r.items():
        print(f"  {k}: {str(v)[:60]}")
