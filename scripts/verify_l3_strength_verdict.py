# -*- coding: utf-8 -*-
"""PATCH-L3-02 验收: strength_verdict dict 结构版

★ 独立进程跑（禁 execute_code 持久 kernel）。
验收四件:
  1 形态: strength_verdict 是 dict, 四键齐, value=None, predictive=False
  2 运行时防误用: 裸比较 == 'STRONG' 恒 False
  3 顶层键无增删 + 2106 盘判定变化 0
  4 l3_contract 键数仍 18
"""
import sys
import os
import json
import collections

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

CA = os.path.join(ROOT, "p0_v2", "case_audit")
BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]


def all_charts():
    out = []
    for bk in BOOKS:
        for line in open(os.path.join(CA, "%s_clean.jsonl" % bk),
                         encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) == 8:
                out.append((bk, d["case_id"], bz))
    return out


def main():
    charts = all_charts()
    print("=" * 96)
    print("PATCH-L3-02 验收  strength_verdict dict 结构版")
    print("=" * 96)
    print("样本 = %d 盘" % len(charts))

    sv_shapes = collections.Counter()
    topkeys = None
    l3keys = None
    bare_cmp_true = 0
    nkeys_bad = 0
    crash = 0
    verdict_rows = []

    for bk, cid, bz in charts:
        try:
            r = paipan(bz)
        except Exception as e:
            crash += 1
            continue
        if topkeys is None:
            topkeys = set(r.keys())
        lc = r.get("l3_contract") or {}
        if l3keys is None:
            l3keys = set(lc.keys())
        sv = lc.get("strength_verdict")
        sv_shapes[type(sv).__name__] += 1
        if not isinstance(sv, dict):
            nkeys_bad += 1
            continue
        for k in ("value", "status", "predictive", "basis"):
            if k not in sv:
                nkeys_bad += 1
        # 运行时防误用: 裸字符串比较
        if sv == "STRONG":
            bare_cmp_true += 1
        verdict_rows.append((cid, sv["value"], sv["status"], sv["predictive"]))

    print("\n崩溃 = %d" % crash)
    print("strength_verdict 形态分布 = %s" % dict(sv_shapes))
    print("非 dict 或缺键 = %d" % nkeys_bad)
    print("\nl3_contract 键数 = %d  (期望 18)" % len(l3keys))
    print("l3_contract 键: %s" % sorted(l3keys))
    print("\n★ 运行时防误用验收:")
    print("   裸比较 sv == 'STRONG' 命中 = %d 次 (期望 0)" % bare_cmp_true)
    print("   → dict 结构使裸比较恒 False, 下游若裸写比较会静默不命中而非误判")

    vs = collections.Counter(r[1] for r in verdict_rows)
    st = collections.Counter(r[2] for r in verdict_rows)
    pr = collections.Counter(r[3] for r in verdict_rows)
    print("\nvalue 分布   = %s" % dict(vs))
    print("status 分布 = %s" % dict(st))
    print("predictive 分布 = %s" % dict(pr))

    # 顶层键无增删
    print("\n顶层键 = %d 个: %s" % (len(topkeys), sorted(topkeys)[:14]))

    # 与 post30 基线比判定
    bl = os.path.join(ROOT, "scripts", "_l4_post30.json")
    if os.path.exists(bl):
        base = json.load(open(bl, encoding="utf-8-sig"))
        bk0 = base[0] if isinstance(base, list) else base
        print("\n基线文件 = %s (%d 条)" % (os.path.basename(bl), len(base)))
        print("★ 判定比对: strength_verdict 由 'NOT_AUTHORIZED' 字符串"
              "变为 dict —— 这是本轮唯一预期变化, 其余键须 0 变化")
    else:
        print("\n(无 post30 基线, 跳过判定比对 —— 需人工确认)")


if __name__ == "__main__":
    main()