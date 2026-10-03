# -*- coding: utf-8 -*-
"""底层矩阵断链量化诊断 —— 核「多维度是否真的相互影响」

只统计事实, 不下判断。三问:
  Q1 六维是否各自独立算?  月令被冲时 ling_state 有没有跟着变?
  Q2 合冲会刑害破 是否传导到 根/透干? 还是只被记录?
  Q3 三合/三会成局是否进力量统计? 还是只记录不入量?
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
SEASON = {"寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水","子":"水","丑":"土"}
BOOKS = ["DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"]


def main():
    st = collections.Counter()
    ex = collections.defaultdict(list)
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
            try:
                r = paipan(bz)
            except Exception:
                st["崩溃"] += 1
                continue
            rf = r.get("raw_facts") or {}
            cf = rf.get("combination_facts") or {}
            wp = (rf.get("wuxing_power") or {}).get("wuxing_power") or {}
            wm = r.get("wangshuai_matrix") or {}
            # ★ PATCH-L3-03 (2026-10-03) six_dims 已废弃 -> 改读 by_element[日主五行]
            #   工程理由: 本就在算 dwx 并按日主五行取行(row = wp.get(dwx)),
            #             by_element[dwx] 与既有写法一致。
            #   两段显式失败 —— dwx 是脚本自算, 引擎的是 daymaster_element;
            #   若脚本 dwx 恰是另一合法五行, 只判 by_element 缺行【不会】raise,
            #   会静默读错行 -> 必须先比对两者是否相等。
            dm = bz[4]
            dwx = GW[dm]
            _dwx_eng = wm.get("daymaster_element")
            if dwx != _dwx_eng:
                raise KeyError("脚本 dwx=%s != 引擎 daymaster_element=%s" % (dwx, _dwx_eng))
            six = (wm.get("by_element") or {}).get(dwx)
            if six is None:
                raise KeyError("by_element 缺 %s" % dwx)
            zs = [bz[1], bz[3], bz[5], bz[7]]
            mz = zs[1]
            row = wp.get(dwx) or {}

            # Q1a 月令被六冲
            mz_chong = any(mz in pr for pr in
                           [set(p) for p in (cf.get("liuchong") or [])])
            if mz_chong:
                st["Q1 月令被冲"] += 1
                if len(ex["Q1"]) < 6:
                    ex["Q1"].append((d["case_id"], bz, mz, row.get("ling_state")))
            # Q1b 月令入合
            mz_he = any(mz in pr for pr in
                        [set(p) for p in (cf.get("liuhe") or [])])
            if mz_he:
                st["Q1b 月令六合"] += 1
            # Q1c 月令入三会
            sanhui = cf.get("sanhui") or []
            for sh in sanhui:
                try:
                    if mz in sh:
                        st["Q1c 月令三会"] += 1
                        if len(ex["Q1c"]) < 6:
                            ex["Q1c"].append((d["case_id"], bz, mz, row.get("ling_state")))
                except Exception:
                    pass

            # Q2 合冲是否传导到 根
            if (cf.get("liuhe") or cf.get("banhe") or cf.get("liuchong")):
                st["Q2 盘有合/冲"] += 1
                # 引擎有没有把合冲状态写进 l3_contract / six_dims?
                has_field = any(k in (six or {}) for k in ("gen_lost", "root_lost", "chong_deduct"))
                if not has_field:
                    st["Q2★ 合冲未进六维字段"] += 1
                    if len(ex["Q2"]) < 6:
                        ex["Q2"].append((d["case_id"], bz,
                                         list((cf.get("liuhe") or []) + (cf.get("liuchong") or [])),
                                         six.get("root_detail")))
            # 根被冲是否已扣减(对照 dm_ben_eff)
            for z in zs:
                rd = row.get("root_detail") or {}
                if rd.get(z) == "BEN":
                    if any(z in pr for pr in [set(p) for p in (cf.get("liuchong") or [])]):
                        st["Q2b 日主本气根被冲"] += 1
                        if len(ex["Q2b"]) < 8:
                            ex["Q2b"].append((d["case_id"], bz, z,
                                              (r.get("l3_contract") or {}).get("dm_ben_eff"),
                                              six.get("ben_n")))

            # Q3 三合/三会是否进力量
            if (cf.get("sanhe") or sanhui):
                st["Q3 有三合/三会"] += 1
                jn = (six.get("ju_n"))
                if jn is None:
                    st["Q3★ 三合未进六维"] += 1
                else:
                    st["Q3 三合已进 ju_n"] += 1
                    if len(ex["Q3"]) < 6:
                        ex["Q3"].append((d["case_id"], bz, cf.get("sanhe"), sanhui, jn))

            # Q4 天干合是否影响 stem_n
            hg = cf.get("he_pairs") or cf.get("hegan") or []
            if hg:
                st["Q4 天干五合"] += 1
                if len(ex["Q4"]) < 6:
                    ex["Q4"].append((d["case_id"], bz, hg, six.get("stem_n")))

    print("=" * 92)
    print("底层矩阵断链诊断   六本 %d 盘" % n)
    print("=" * 92)
    for k in sorted(st):
        print("  %-22s %5d  (%.1f%%)" % (k, st[k], st[k] / max(1, n) * 100))

    for tag in ("Q1", "Q1c", "Q2", "Q2b", "Q3", "Q4"):
        if ex[tag]:
            print("\n【%s 样本】" % tag)
            for e in ex[tag]:
                print("   %s" % (e,))


if __name__ == "__main__":
    main()