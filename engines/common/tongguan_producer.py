# -*- coding: utf-8 -*-
"""DTS 流通+通关 Producer (PATCH-071)
铁律: DTS_SCOPE_ONLY; 禁YHZP引化=通关/QTBJ寒暖=通关/SFTK病药=通关
原文: DTS-019-002 通天论通关论
  木土而得火/火金而得土/土水而得金/金木而得水
"""
import io, sys
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME

# 相克对 -> 通关五行(贪生忘克)
TONGGUAN = {
    frozenset(["木", "土"]): "火",  # 木克土, 火通
    frozenset(["火", "金"]): "土",  # 火克金, 土通
    frozenset(["土", "水"]): "金",  # 土克水, 金通
    frozenset(["金", "木"]): "水",  # 金克木, 水通
    frozenset(["水", "火"]): "木",  # 水克火, 木通
}


def tongguan_producer(conflict_pair):
    """
    conflict_pair: 两相克五行, 如("木","土")
    return: 通关用神, namespace=DTS.tongguan
    """
    k = frozenset(conflict_pair)
    if k not in TONGGUAN:
        return {"state": "tongguan_state", "namespace": "DTS.tongguan",
                "status": "NOT_CONFLICT", "note": "非相克对或无需通关",
                "evidence": "DTS-019-002"}
    guan = TONGGUAN[k]
    return {
        "state": "tongguan_state",
        "namespace": "DTS.tongguan",
        "status": "RESOLVED",
        "conflict": sorted(conflict_pair),
        "tongguan_element": guan,
        "evidence_chain": ["DTS-019-002"],
        "note": f"{conflict_pair[0]}克{conflict_pair[1]}, 取{guan}通关(贪生忘克)"
    }


def liutong_check(cycle):
    """流通检查: 五行依次相生即流通"""
    SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    flow = all(SHENG.get(cycle[i]) == cycle[i + 1] for i in range(len(cycle) - 1))
    return {"state": "liutong_state", "namespace": "DTS.qi_flow",
            "flow": cycle, "is_liutong": flow,
            "evidence": "DTS-044-002 一气流通"}


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== DTS通关/流通 ===")
    for pair in [("木", "土"), ("水", "火"), ("金", "木")]:
        r = tongguan_producer(pair)
        print(f"{pair}: 通关={r.get('tongguan_element', '-')} | {r['note']}")
    print("流通:", liutong_check(["木", "火", "土", "金", "水"]))
