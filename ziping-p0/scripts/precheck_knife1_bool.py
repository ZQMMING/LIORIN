# -*- coding: utf-8 -*-
"""第1刀前置核: 日主行 ling_state 分布 + 三个布尔候选的实测取值

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan


def main():
    st = collections.Counter()
    pair = collections.Counter()      # de_di_raw vs de_di_eff 的组合
    samples = []
    n = 0
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            r = paipan(bz)
            lc = r.get("l3_contract") or {}
            wm = r.get("wangshuai_matrix") or {}
            dm = wm.get("dm_row") or {}
            ls = lc.get("ling_state")
            st["ling_state=%s" % ls] += 1
            st["de_ling=%s" % (ls == "旺")] += 1
            st["de_di_raw=%s" % (lc.get("root_grade") != "无")] += 1
            st["de_di_eff=%s" % ((lc.get("dm_ben_eff") or 0) >= 1)] += 1
            st["dang_duo=%s" % (lc.get("support_state") == "SHENG_FU_CHENG_SHI")] += 1
            st["dang_少=%s" % (lc.get("support_state") == "KE_XIE_CHENG_SHI")] += 1
            st["dang_平=%s" % (lc.get("support_state") == "PINGHENG")] += 1
            pair["raw=%s eff=%s" % (lc.get("root_grade") != "无",
                                   (lc.get("dm_ben_eff") or 0) >= 1)] += 1
            if lc.get("root_grade") != "无" and (lc.get("dm_ben_eff") or 0) == 0 \
                    and len(samples) < 5:
                samples.append((d["case_id"], bz, lc.get("root_grade"),
                                lc.get("dm_ben_eff"), lc.get("root_grade_raw")))
    print("=" * 92)
    print("第1刀前置核   六本 %d 盘" % n)
    print("=" * 92)
    print("\n【日主行 ling_state 五值分布】")
    for k in sorted(k for k in st if k.startswith("ling_state=")):
        print("    %-22s %6d  (%.1f%%)" % (k[11:], st[k], st[k] * 100.0 / n))
    print("\n【四个布尔候选的实测分布】")
    for k in ["de_ling", "de_di_raw", "de_di_eff", "dang_duo", "dang_少", "dang_平"]:
        kk = "%s=True" % k
        kf = "%s=False" % k
        print("    %-12s True %6d (%.1f%%)   False %6d (%.1f%%)"
              % (k, st.get(kk, 0), st.get(kk, 0) * 100.0 / n,
                 st.get(kf, 0), st.get(kf, 0) * 100.0 / n))
    print("\n【de_di_raw vs de_di_eff 交叉】")
    for k in sorted(pair):
        print("    %-24s %6d (%.1f%%)" % (k, pair[k], pair[k] * 100.0 / n))
    if samples:
        print("\n【de_di_raw=True 但 de_di_eff=False 样本】(原始有根, 有效根为0 —— 根被拔)")
        for s in samples:
            print("    %-9s %-17s root_grade=%s dm_ben_eff=%s raw=%s" % s)


if __name__ == "__main__":
    main()