# -*- coding: utf-8 -*-
"""STEP-DBG-14 独立验② —— branch_chong 四柱维度

判据全部独立手写(读 DTS L102/L106/L108/L110/L96/L98, 不读引擎实现):
  冲方 = 能克被冲方者(L106)  丑未/辰戌 = 四库兄弟冲(L102)
  被冲方 adj = _compare_both  冲方 adj = 0  兄弟冲 adj=0 + library_open=True
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

BW = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
SH = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
KE = {"木":"土","火":"金","土":"水","金":"木","水":"火"}
CHONG = {frozenset(x) for x in [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]}
POS = ("year","month","day","hour")


def ling(mw, w):
    if not w: return ""
    if w == mw: return "旺"
    if SH[mw] == w: return "相"
    if SH[w] == mw: return "休"
    if KE[w] == mw: return "囚"
    return "死"


def cmp_both(mw, bc, cf):
    lb, lc = ling(mw, bc), ling(mw, cf)
    if lc in ("囚","死") and lb in ("旺","相"): return +1
    if lc in ("旺","相") and lb in ("囚","死"): return -1
    return 0


def main():
    st = collections.Counter()
    mism = []
    n = 0
    for bk in ["DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            mw = BW[bz[3]]
            zlis = [bz[1], bz[3], bz[5], bz[7]]
            # 独立手算四柱
            mine = {p: {'adj':0,'role':'NO_CHONG','chong_by':None,'library_open':False} for p in POS}
            byz = {}
            for i, p in enumerate(POS):
                if zlis[i] not in byz:
                    byz[zlis[i]] = p
            for pr in CHONG:
                cand = [z for z in zlis if z in pr]
                if len(cand) < 2 or cand[0] == cand[1]:
                    continue    # 同支不构成六冲(两支须不同)
                a, b = cand[0], cand[1]
                wa, wb = BW[a], BW[b]
                pa, pb = byz.get(a), byz.get(b)
                if pa is None or pb is None:
                    continue
                if KE[wa] == wb:
                    cf_p,bc_p,cf_z,bc_z = pa,pb,a,b
                elif KE[wb] == wa:
                    cf_p,bc_p,cf_z,bc_z = pb,pa,b,a
                else:
                    mine[pa].update(role='BROTHER_CHONG',chong_by=b,library_open=True)
                    mine[pb].update(role='BROTHER_CHONG',chong_by=a,library_open=True)
                    continue
                mine[cf_p].update(role='CHONG_ACTIVE',chong_by=bc_z)
                mine[bc_p].update(role='CHONG_PASSIVE',chong_by=cf_z,
                                  adj=cmp_both(mw, BW[bc_z], BW[cf_z]))
            try:
                r = paipan(bz)
            except Exception as e:
                st["崩溃"] += 1
                continue
            bc_eng = ((r.get("wangshuai_matrix") or {}).get("branch_chong")) or {}
            ok_all = True
            for p in POS:
                me = mine[p]
                en = bc_eng.get(p) or {}
                st["role=%s" % me['role']] += 1
                if me['adj'] != 0:
                    st["adj=%+d" % me['adj']] += 1
                if me['library_open']:
                    st["library_open=True"] += 1
                same = (me['adj'] == en.get('adj') and me['role'] == en.get('role')
                        and me['library_open'] == en.get('library_open')
                        and me['chong_by'] == en.get('chong_by'))
                if not same:
                    ok_all = False
                    if len(mism) < 8:
                        mism.append((d["case_id"], bz, p, me, en))
            st["盘全对" if ok_all else "盘有不一致"] += 1
            # N_dup: 重复支(同支出现>=2次) 是否参与真六冲 —— _by_pos 单值映射的真实影响面
            from collections import Counter as _C
            cntz = _C(zlis)
            dup = [z for z, c in cntz.items() if c >= 2]
            if dup:
                st["有重复支的盘"] += 1
                dup_in_chong = False
                for z in dup:
                    for pr in CHONG:
                        other = [o for o in pr if o != z]
                        if other and other[0] in zlis:
                            dup_in_chong = True
                st["重复支★参与真冲(N_dup_chong)" if dup_in_chong
                   else "重复支★不参与真冲(N_dup_nochong)"] += 1

    print("=" * 96)
    print("STEP-DBG-14 branch_chong 独立验   六本 %d 盘" % n)
    print("=" * 96)
    for k in sorted(st):
        print("  %-22s %5d" % (k, st[k]))
    if mism:
        print("\n  不一致样本(最多8):")
        for c, b, p, me, en in mism:
            print("    %-9s %-17s %-6s 我=%s 引擎=%s" % (c, b, p, me, en))


if __name__ == "__main__":
    main()