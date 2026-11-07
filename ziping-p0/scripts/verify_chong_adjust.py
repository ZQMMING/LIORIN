# -*- coding: utf-8 -*-
"""STEP-DBG-14 独立验 —— chong_adjust 落码效果

不读引擎判定逻辑, 只读输出值 + 独立手算 DTS L108/L110 两方对比。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

GW = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
BW = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
SH = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
CHONG = {frozenset(x) for x in [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]}
LO = {"旺":1,"相":2,"休":3,"囚":4,"死":5}
BOOKS = ["DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"]


def ling(mw, w):
    if w == mw: return "旺"
    if SH[mw] == w: return "相"
    if SH[w] == mw: return "休"
    if KE[w] == mw: return "囚"
    return "死"


def mine(mb, zs):
    """独立手算: 月令 mb 的 chong_adjust (DTS L108/L110)
       返回 (adj, chong_by)"""
    for z in zs:
        if z == mb: continue
        if frozenset((mb, z)) in CHONG:
            mw = BW[mb]; cw = BW[z]
            m = LO[ling(mw, mw)]          # 月令五行对自己的位 = 旺
            c = LO[ling(mw, cw)]          # 冲方五行在月令下的位
            # 月令本身: 旺1相2休3囚4死5
            m2 = LO[ling(mw, mw)]
            adj = 0
            if m2 in (4, 5) and c in (1, 2): adj = -1     # 旺者冲衰衰者拔
            if m2 in (1, 2) and c in (4, 5): adj = +1     # 衰神冲旺旺神发
            return adj, z
    return 0, None


def main():
    st = collections.Counter()
    mism = []
    n = 0
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
            mb = bz[3]                      # 月支
            zs = [bz[1], bz[3], bz[5], bz[7]]
            try:
                r = paipan(bz)
            except Exception as e:
                st["崩溃"] += 1
                continue
            wm = r.get("wangshuai_matrix") or {}
            mc = wm.get("month_chong") or {}
            six = wm.get("six_dims") or {}
            eng_adj = mc.get("chong_adjust")
            eng_by = mc.get("chong_by")
            badj, bby = mine(mb, zs)
            if badj == 0 and bby is None:
                st["月令未被冲"] += 1
                if eng_adj not in (0, None):
                    st["★无冲却有adjust"] += 1
                    if len(mism) < 6: mism.append((d["case_id"], bz, "无冲", eng_adj, eng_by))
            else:
                st["月令被冲"] += 1
                if eng_adj == badj and eng_by == bby:
                    st["被冲★一致"] += 1
                else:
                    st["被冲★不一致"] += 1
                    if len(mism) < 10:
                        mism.append((d["case_id"], bz, "被冲", (bby, badj), (eng_by, eng_adj)))
            # 分布
            st["adj=%s" % eng_adj] += 1
            if six.get("ling_state_eff"):
                st["eff=%s" % six["ling_state_eff"]] += 1

    print("=" * 92)
    print("STEP-DBG-14 chong_adjust 独立验   六本 %d 盘" % n)
    print("=" * 92)
    for k in sorted(st):
        print("  %-20s %5d" % (k, st[k]))
    if mism:
        print("\n  不一致样本:")
        for m in mism:
            print("    %-9s %-17s %s  我=%s 引擎=%s" % m)


if __name__ == "__main__":
    main()