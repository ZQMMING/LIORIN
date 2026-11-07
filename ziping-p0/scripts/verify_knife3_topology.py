# -*- coding: utf-8 -*-
"""第3刀验收: 源流骨架(步骤1-2) + 通关映射

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。
"""
import sys, os, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))
from engines.common.topology_paths import (
    WX, WX_SHENG, WX_KE, TONG_GUAN_MAP, GUAN_DISTANCE_MAP,
    GUAN_TOPO_CONDITIONS, find_yuan_tou, gen_liu_cheng,
    build_yuan_liu_skeleton, find_tong_guan, list_chong_xing_in_chart,
)


def main():
    print("=" * 96)
    print("第3刀验收   源流骨架 + 通关映射")
    print("=" * 96)

    # ── ① 通关映射: 前三组 verify=True, 第四组 inert ──
    print("\n【① 通关四组映射 DTS L250】")
    for m in TONG_GUAN_MAP:
        g = "%s%s" % m["guan"]
        print("    %s→%s  trigger=%-3s verify=%-5s inert=%-5s  [%s]"
              % (g, m["tong"], m["trigger"], m.get("verify"), m.get("inert", False), m["line"]))
    v_ok = sum(1 for m in TONG_GUAN_MAP if m.get("verify") is True)
    inert = sum(1 for m in TONG_GUAN_MAP if m.get("inert"))
    print("    → verify 通过 %d 组 / inert %d 组 (预期 3 / 1)" % (v_ok, inert))
    # 第四组必须 inert
    m4 = TONG_GUAN_MAP[3]
    print("    → 第四组 金水→水: verify=%s inert=%s  (金克%s 非水 -> 构造不通)"
          % (m4.get("verify"), m4.get("inert"), WX_KE.get("金")))
    print("    → conflict_note: %s" % m4["conflict_note"][:70])
    print("    → emendation_candidate: %s" % m4["emendation_candidate"][:70])

    # ── ② find_tong_guan ──
    print("\n【② find_tong_guan 查询】")
    for pair in [("木", "土"), ("土", "木"), ("火", "金"), ("土", "水"), ("金", "水"), ("水", "金")]:
        m = find_tong_guan(*pair)
        print("    %s%s → %s" % (pair[0], pair[1],
                                  ("%s (inert=%s)" % (m["tong"], m.get("inert", False))) if m else "None"))

    # ── ③ 关的 distance 映射 ──
    print("\n【③ 关的 distance 档位映射 L250】")
    for m in GUAN_DISTANCE_MAP:
        print("    %-10s ← %s" % (m["distance"], " + ".join(m["dts_words"])))
        print("               mapping=%s" % m["mapping"])

    # ── ④ 拓扑条件 ──
    print("\n【④ 关的拓扑断点条件】")
    for c in GUAN_TOPO_CONDITIONS:
        print("    %-12s 「%s」 source=%-9s status=%s" % (c["key"], c["dts"], c["source"], c["status"]))

    # ── ⑤ 源流 步骤1 ──
    print("\n【⑤ 源流 步骤1 找源头】")
    cases = [
        ({"木": 5, "火": 1, "土": 0, "金": 2, "水": 0}, "木独旺"),
        ({"木": 3, "火": 3, "土": 1, "金": 0, "水": 0}, "木火并列"),
        ({"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}, "全零"),
        ({}, "空"),
    ]
    for mass, lbl in cases:
        r = find_yuan_tou(mass)
        print("    %-10s → %s" % (lbl, ("%s (mass=%d tied=%s)" % (r["yuan_wx"], r["mass"], r["tied_with"]))
                                    if r else "None"))
    r0 = find_yuan_tou(cases[0][0]) or {}
    print("    → upstream_pending = %s" % r0.get("upstream_pending"))
    print("    → zong_zu_note    = %s" % str(r0.get("zong_zu_note"))[:74])

    # ── ⑥ 源流 步骤2 路径 ──
    print("\n【⑥ 源流 步骤2 沿 WX_SHENG 生成路径】")
    for start in WX:
        p = gen_liu_cheng(start)
        print("    %s → %s" % (start, " → ".join(p)))
    print("    ★ 只生成, 不判终点(终点依赖 L4 xi_wx)")

    # ── ⑦ 骨架整体 ──
    print("\n【⑦ build_yuan_liu_skeleton 整体】")
    sk = build_yuan_liu_skeleton({"木": 5, "火": 1, "土": 0, "金": 2, "水": 0})
    print("    status       = %s" % sk["status"])
    print("    yuan_tou     = %s" % (sk.get("yuan_tou") or {}).get("yuan_wx"))
    print("    path         = %s" % " → ".join(sk["path"]))
    print("    endpoint     = %s  (pending: %s)" % (sk["endpoint"], sk["endpoint_pending"]))
    print("    pending_steps= %s" % sk["pending_steps"])
    sk0 = build_yuan_liu_skeleton({})
    print("    空 mass → status=%s  endpoint_pending=%s"
          % (sk0["status"], sk0.get("endpoint_pending")))

    # ── ⑧ 铁律核: 无显式图数据结构 ──
    print("\n【⑧ 落法铁律: 路径只用 WX_SHENG/WX_KE, 无显式图】")
    src = open(os.path.join(ROOT, "engines", "common", "topology_paths.py"), encoding="utf-8").read()
    for bad in ["adjacency", "AdjacencyMatrix", "graph", "Graph", "Node(", "neighbors",
                "adj_list", "edge", "Edge"]:
        print("    %-16s 出现 %d 次" % (bad, src.count(bad)))
    print("    WX_SHENG 引用 %d 次 / WX_KE 引用 %d 次"
          % (src.count("WX_SHENG"), src.count("WX_KE")))
    print("\n  ★ 六本底本核证: DTS 有四组映射; PZZQ 36 处通关但零映射表; 其余四本零")
    print("    → 「金水而要水」是底本原样, 非 OCR 错")


    # ── ⑨ list_chong_xing_in_chart 盘级列举 ──
    print("\n【⑨ list_chong_xing_in_chart 盘级列举(裁二十一丙)】")
    fake_rel = [
        {'type': 'CHONG', 'instances': [{'a_pos': 'year', 'b_pos': 'hour'}]},
        {'type': 'XING', 'instances': [{'a_pos': 'month', 'b_pos': 'day'}]},
        {'type': 'SELF', 'instances': [{'positions': ['day', 'hour']}]},   # 不成对, 应跳过
        {'type': 'HE', 'instances': [{'a_pos': 'year', 'b_pos': 'month'}]},
    ]
    r = list_chong_xing_in_chart(fake_rel)
    print("    输入 4 类关系(CHONG/XING/SELF/HE) → 列出 %d 条 (应=2, SELF 与 HE 跳过)"
          % r["count"])
    for it in r["items"]:
        print("      %s %s %s" % (it["key"], it["type"], it["positions"]))
    print("    scope              = %s" % r["scope"])
    print("    two_branch_verdict = %r  (显式 None = 未实现)" % r["two_branch_verdict"])
    print("    pending            = %s" % r["pending"])
    print("    ★ 无 a_zhi/b_zhi 参数 —— 两支判定未实现, 已在 docstring 与契约 §4.5 记 TODO")

    # ── ⑩ 边界: 负数 / None / 空 ──
    print("\n【⑩ find_yuan_tou 边界(裁二十 None 保护)】")
    for mass, lbl in [
        ({'木': -1, '火': -2, '土': -3, '金': -4, '水': -5}, "全负"),
        ({'木': None, '火': 0, '土': 0, '金': 0, '水': 0}, "含 None"),
        ({'木': 0, '火': 0, '土': 3, '金': None, '水': 0}, "土3 金None"),
        ({'木': 2, '火': 2, '土': 1, '金': 2, '水': 1}, "三值并列 2"),
    ]:
        rr = find_yuan_tou(mass) or {}
        print("    %-14s → %-4s mass=%-5s tied=%s"
              % (lbl, rr.get("yuan_wx"), rr.get("mass"), rr.get("tied_with")))


if __name__ == "__main__":
    main()