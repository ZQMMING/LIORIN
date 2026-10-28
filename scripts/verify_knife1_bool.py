# -*- coding: utf-8 -*-
"""第1刀验收: 三个布尔 de_ling / de_di / dang_duo

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

B3 = ["de_ling", "de_di", "dang_duo"]


def main():
    st = collections.Counter()
    bad = []
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
            lc = paipan(bz).get("l3_contract") or {}
            # 值域检查: 必须是 bool (不能是 0/1 或 None)
            for k in B3:
                v = lc.get(k, "__MISSING__")
                if v == "__MISSING__":
                    st["★%s 缺键" % k] += 1
                elif not isinstance(v, bool):
                    st["★%s 非布尔(%r)" % (k, v)] += 1
                else:
                    st["值域 %s=%s" % (k, v)] += 1
                    if v:
                        st["%s=True" % k] += 1
            # 与来源字段的一致性
            if lc.get("de_ling") == (lc.get("ling_state") == "旺"):
                st["de_ling == (ling_state=='旺')"] += 1
            else:
                st["★de_ling 不一致"] += 1
            if lc.get("de_di") == ((lc.get("dm_ben_eff") or 0) >= 1):
                st["de_di == (dm_ben_eff>=1)"] += 1
            else:
                st["★de_di 不一致"] += 1
                if len(bad) < 4:
                    bad.append((d["case_id"], bz, lc.get("dm_ben_eff"), lc.get("de_di")))
            if lc.get("dang_duo") == (lc.get("support_state") == "SHENG_FU_CHENG_SHI"):
                st["dang_duo == (同党成势)"] += 1
            else:
                st["★dang_duo 不一致"] += 1
            # de_di 与 root_grade 的恒等(契约 §1.5)
            if lc.get("de_di") == (lc.get("root_grade") != "无"):
                st["de_di == (root_grade!='无') 恒等"] += 1
            else:
                st["★de_di 与 root_grade 非恒等"] += 1
    print("=" * 92)
    print("第1刀验收   六本 %d 盘" % n)
    print("=" * 92)
    print("\n【值域 + 分布】")
    for k in B3:
        print("    %-10s True %6d (%.1f%%)   False %6d (%.1f%%)   ★缺键 %d   ★非布尔 %d"
              % (k, st["%s=True" % k], st["%s=True" % k] * 100.0 / n,
                 st["值域 %s=False" % k], st["值域 %s=False" % k] * 100.0 / n,
                 st["★%s 缺键" % k], st.get("★%s 非布尔(%r)" % (k, ""), 0)))
    print("\n【与来源字段一致性】")
    for k, lbl in [("de_ling == (ling_state=='旺')", "de_ling"),
                   ("de_di == (dm_ben_eff>=1)", "de_di"),
                   ("dang_duo == (同党成势)", "dang_duo"),
                   ("de_di == (root_grade!='无') 恒等", "de_di↔root_grade")]:
        print("    %-32s 一致 %5d   ★不一致 %4d" % (k, st[k], n - st[k]))
    for b in bad:
        print("   ", b)


if __name__ == "__main__":
    main()