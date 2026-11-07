# -*- coding: utf-8 -*-
"""FAN_JU 双向验 —— 正样本必触发 + 污染样本必不触发"""
import sys, os, json
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

# 13 正样本(已剔除 DT-0370理论段 / PZ-0183马参政 / DT-0009反证)
POS = {
    'JUN_LAI_CHEN_SHENG': ['DT-0363', 'DT-0365', 'PZ-0146', 'PZ-0184'],
    'MU_CI_MIE_ZI': ['DT-0372', 'PZ-0194'],
    'ER_NENG_JIU_MU': ['DT-0368', 'DT-0369', 'PZ-0179'],
    'FU_JIAN_PA_QI': ['DT-0375', 'DT-0376', 'DT-0377', 'DT-0378'],
}
# 污染/否定: 泛论列举或术语另指, 不得触发
NEG = ['YH-0116', 'YH-0117', 'SM-0040', 'YH-0170', 'DT-0370', 'PZ-0183', 'DT-0009']


def _yys_643_youqi(r, wx):
    """yongshen_engine.py:643 口径: to_root_grade(ben)in[禄刃,长生,库] OR stem>=1"""
    wf = (r.get("raw_facts") or {}).get("wuxing_power", {}).get("wuxing_power", {}) or {}
    row = wf.get(wx) or {}
    ben = int(row.get("ben_n", 0) or 0); stem = int(row.get("stem_n", 0) or 0)
    return stem >= 1 or ben >= 1   # 近似: ben>=1 即禄刃/长生/库三档


GW = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
KEW = {"木":"土","火":"金","土":"水","金":"木","水":"火"}


def main():
    rows = {}
    for bk in ("DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"):
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if line.strip():
                d = json.loads(line)
                rows[d["case_id"]] = (d.get("bazi") or "").replace(" ", "")

    print("=" * 96)
    print("FAN_JU 双向验 —— 正样本(必触发) / 污染样本(必不触发)")
    print("=" * 96)
    ok = bad = 0
    for jl, ids in POS.items():
        print("\n【正样本 %s】" % jl)
        for cid in ids:
            bz = rows.get(cid, "")
            if not bz:
                print("  %-9s ★不在案集" % cid); continue
            r = paipan(bz)
            fj = (r.get("l3_contract") or {}).get("fan_ju") or {}
            ts = fj.get("types") or []
            hit = jl in ts
            print("  %s %-9s %-17s 引擎=%-24s flag=%s"
                  % ("✓" if hit else "✗", cid, bz, ",".join(ts),
                     json.dumps(fj.get("flag_map", {}), ensure_ascii=False)))
            ok += 1 if hit else 0
            bad += 0 if hit else 1
    print("\n【污染样本 —— 任一反局都不该触发】")
    for cid in NEG:
        bz = rows.get(cid, "")
        if not bz:
            print("  %-9s ★不在案集" % cid); continue
        r = paipan(bz)
        fj = (r.get("l3_contract") or {}).get("fan_ju") or {}
        ts = fj.get("types") or []
        clean = not ts
        print("  %s %-9s %-17s 引擎=%-24s flag=%s"
              % ("✓" if clean else "✗", cid, bz, ",".join(ts) or "(无)",
                 json.dumps(fj.get("flag_map", {}), ensure_ascii=False)))
        ok += 1 if clean else 0
        bad += 0 if clean else 1
    print("\n双向验: 通过 %d / 失败 %d" % (ok, bad))

    # ⑧ 验收: FAN_JU 财有气 vs yongshen_engine:643 口径 并排打印, 找相反结论
    print("\n" + "=" * 96)
    print("⑧ 并排: FAN_JU._you_qi(财)  vs  yongshen_engine:643 口径   (找相反结论)")
    print("=" * 96)
    import glob, json as _j
    n = clash = 0
    samples = []
    for bk in ("DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"):
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = _j.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            w = GW[bz[4]]
            cai = KEW[w]
            r = paipan(bz)
            fj = (r.get("l3_contract") or {}).get("fan_ju") or {}
            fm = fj.get("flag_map") or {}
            fq = fm.get("cai_youqi")
            yq = _yys_643_youqi(r, cai)
            if fq is None:
                continue
            if bool(fq) != bool(yq):
                clash += 1
                if len(samples) < 10:
                    samples.append((d["case_id"], bz, cai, fq, yq))
    print("  全量 %d 盘, FAN_JU 与 643 口径相反 %d 盘" % (n, clash))
    for c, b, cx, fq, yq in samples:
        print("    %-9s %-17s 财=%s  FAN_JU有气=%-5s  引擎643有气=%s" % (c, b, cx, fq, yq))


if __name__ == "__main__":
    main()