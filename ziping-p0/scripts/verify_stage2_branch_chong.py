# -*- coding: utf-8 -*-
"""阶段2b/2c 验收: transit_power 切源 relations 后的 branch_chong 补齐核验

对照 2a 前(post19)与 2b/2c 后(post20)的 branch_chong 全量 diff。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))

POSK = ("year", "month", "day", "hour")
CHONG = {frozenset(x) for x in [("子", "午"), ("丑", "未"), ("寅", "申"),
                                ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]}


def main():
    from p0_v2.bazi_gate import paipan
    st = collections.Counter()
    samples = []
    dup_pans = []          # 有重复支且参与真冲的盘 = 预期会变的盘
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
            zlis = [bz[1], bz[3], bz[5], bz[7]]
            # 是否重复支且参与真冲
            cnt = collections.Counter(zlis)
            inst = []
            for i in range(4):
                for j in range(i + 1, 4):
                    if frozenset((zlis[i], zlis[j])) in CHONG:
                        inst.append((i, j))
            is_dup = bool(inst) and any(cnt[z] >= 2 for z in {zlis[i] for i, _ in inst} |
                                        {zlis[j] for _, j in inst})
            try:
                r = paipan(bz)
            except Exception as e:
                st["崩溃"] += 1
                if st["崩溃"] <= 3:
                    print("  崩溃 %s %s: %s" % (d["case_id"], bz, e))
                continue
            bc = (r.get("wangshuai_matrix") or {}).get("branch_chong") or {}
            for p in POSK:
                role = (bc.get(p) or {}).get("role", "MISSING")
                st["role:%s" % role] += 1
            mc = (bc.get("month") or {})
            st["月令:%s" % mc.get("role")] += 1
            if is_dup:
                dup_pans.append((d["case_id"], bz, bc, inst))

    print("=" * 96)
    print("阶段2b/2c  branch_chong 全量分布   六本 %d 盘  崩溃 %d" % (n, st["崩溃"]))
    print("=" * 96)
    print("  四柱 role 分布 (总 %d):" % (n * 4))
    for k in sorted(st):
        if k.startswith("role:"):
            print("    %-22s %6d" % (k[5:], st[k]))
    print("\n  月令 role 分布 (总 %d):" % n)
    for k in sorted(st):
        if k.startswith("月令:"):
            print("    %-22s %6d" % (k[3:], st[k]))
    print("\n  有重复支且参与真冲的盘 = %d  (旧 _by_pos 单值口径下会丢实例的盘)" % len(dup_pans))
    print("\n  【样例 3 盘 branch_chong 全文】")
    for cid, bz, bc, inst in dup_pans[:3]:
        print("\n  %s  %s  支=%s  理论冲实例=%d" % (cid, bz, "".join([bz[1], bz[3], bz[5], bz[7]]), len(inst)))
        for p in POSK:
            v = bc.get(p) or {}
            print("    %-6s role=%-14s adj=%-3s by=%-5s lib=%s"
                  % (p, v.get("role"), v.get("adj"), v.get("chong_by"), v.get("library_open")))

    # DT-0039 定点
    print("\n" + "=" * 96)
    print("定点: DT-0039 甲寅戊辰丙寅丙申")
    print("=" * 96)
    r = paipan("甲寅戊辰丙寅丙申")
    bc = (r.get("wangshuai_matrix") or {}).get("branch_chong") or {}
    for p in POSK:
        v = bc.get(p) or {}
        mark = "  ← day 寅" if p == "day" else ""
        print("    %-6s role=%-14s adj=%-3s by=%-5s lib=%s%s"
              % (p, v.get("role"), v.get("adj"), v.get("chong_by"), v.get("library_open"), mark))
    day_role = (bc.get("day") or {}).get("role")
    print("\n  ★ day 寅 role = %s   %s" % (day_role,
          "已补齐 ✓" if day_role != "NO_CHONG" else "★仍落空"))
    print("\n  relations CHONG 原始实例:")
    for rel in (r.get("raw_facts") or {}).get("relations") or []:
        if rel.get("type") == "CHONG":
            print("    branches=%s count=%d positions=%s"
                  % (rel["branches"], rel["instance_count"], json.dumps(rel["positions"], ensure_ascii=False)))


if __name__ == "__main__":
    main()