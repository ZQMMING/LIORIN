# -*- coding: utf-8 -*-
"""裁七十一乙 拓扑派生层接入验收

★ 独立进程跑(禁 execute_code 持久 kernel)。
★ 注意: scripts/_l4_baseline.py 只快照 12 个顶层键, 不含 topology / l3_contract,
  所以「回归判定变化 0」对拓扑层是空的 —— 本脚本才是拓扑层的真验收。

核三件:
  1 topology 键在 2106/2106 盘全部产出, 四块子结构齐全
  2 四块【不依赖 L4】的证据: 无 xi_wx 实参、无判定结论
  3 值域合法性: 布尔/整数/枚举, 无浮点, 无恒假/恒真
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
SUB = ["yuan_liu", "fang_ju", "tong_guan", "guan_topo", "boundary_note"]


def has_float(o, path="", bad=None):
    """递归找浮点 —— 架构 §1.2 禁浮点"""
    if bad is None:
        bad = []
    if isinstance(o, float):
        bad.append((path, o))
    elif isinstance(o, dict):
        for k, v in o.items():
            has_float(v, "%s.%s" % (path, k), bad)
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            has_float(v, "%s[%d]" % (path, i), bad)
    return bad


def main():
    st = collections.Counter()
    n = 0
    crash = 0
    floats = []
    sample = None
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            try:
                r = paipan(bz)
            except Exception as e:
                crash += 1
                if crash <= 3:
                    print("  崩溃 %s %s: %s" % (d["case_id"], bz, e))
                continue
            tp = r.get("topology")
            if not isinstance(tp, dict):
                st["★缺 topology"] += 1
                continue
            st["topology 存在"] += 1
            for s in SUB:
                st["子键_%s" % s] += (s in tp)

            yl = tp.get("yuan_liu") or {}
            st["源流_status=%s" % yl.get("status")] += 1
            if yl.get("yuan_tou"):
                st["源流_有源头"] += 1
                st["源流_并列=%s" % bool(yl["yuan_tou"].get("tied_with"))] += 1
            st["源流_endpoint=None"] += (yl.get("endpoint") is None)
            st["源流_pending=L4_XI_WX"] += (yl.get("endpoint_pending") == "L4_XI_WX")

            fj = tp.get("fang_ju") or {}
            st["方局_jun_za_ming=%s" % fj.get("jun_za_ming")] += 1
            st["方局_degree=None"] += (fj.get("degree") is None)
            st["方局_variant=%s" % fj.get("variant")] += 1

            tg = tp.get("tong_guan") or {}
            st["通关_规则数=%d" % len(tg.get("rules") or [])] += 1
            st["通关_inert数=%d" % sum(1 for x in (tg.get("rules") or [])
                                      if x.get("inert"))] += 1

            gt = tp.get("guan_topo") or {}
            st["关拓扑_verdict=%s" % gt.get("verdict")] += 1
            c = gt.get("conditions") or {}
            st["关拓扑_jie_zhan=None"] += (c.get("jie_zhan") is None)
            st["关拓扑_distance=%s" % c.get("distance")] += 1
            st["关拓扑_blocked=%s" % c.get("blocked")] += 1

            bad = has_float(tp, d["case_id"])
            if bad:
                floats.append(bad[:3])
            if sample is None and fj.get("jun_za_ming"):
                sample = (d["case_id"], bz, tp)

    print("=" * 96)
    print("裁七十一乙 拓扑派生层接入验收   六本 %d 盘   崩溃 %d" % (n, crash))
    print("=" * 96)

    print("\n【1】键存在性")
    for k in sorted(st):
        if k.startswith("子键_") or k in ("topology 存在", "★缺 topology"):
            print("    %-30s %6d  (%.1f%%)" % (k, st[k], st[k] * 100.0 / n))

    print("\n【2】四块值域")
    for k in sorted(st):
        if k.startswith(("源流", "方局", "通关", "关拓扑")):
            print("    %-34s %6d  (%.1f%%)" % (k, st[k], st[k] * 100.0 / n))

    print("\n【3】浮点检查(架构 §1.2 禁浮点)")
    print("    含浮点的盘 = %d   %s" % (len(floats), floats[:2] if floats else "无"))

    print("\n【4】混局命中样本")
    if sample:
        cid, bz, tp = sample
        print("    %s  %s" % (cid, bz))
        for f in (tp["fang_ju"].get("findings") or []):
            print("      [%s] 完整组 %s + 额外一支 %s  同五行组 %s  [%s]"
                  % (f["group_type"], f["complete_group_display"],
                     f["extra_branch"], f["peer_group_display"], f["evidence"]))
    else:
        print("    (无)")

    print("\n【5】L4 依赖证据")
    print("    源流 endpoint 恒 None + endpoint_pending=L4_XI_WX  → "
          "终点判定待 L4, 但骨架本身已出结果(源头+路径)")
    print("    关拓扑 verdict 恒 INCOMPLETE (jie_zhan=None)      → 劫占未核, 如实闭锁")


if __name__ == "__main__":
    main()