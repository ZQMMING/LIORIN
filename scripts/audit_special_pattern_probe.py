# -*- coding: utf-8 -*-
"""核2 探针: special_pattern 输出结构 + DTS 依据核（先过探针再跑全量）

探针三项:
  甲 已知应命中: build_special_patterns 返回 10 键（人工读源码 L71-74）
  乙 已知应全空: 极简盘不应有 zhuanwang/hua_qi
  丙 已知全有: 日主极旺盘应命中 zhuanwang
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


def probe():
    print("=" * 100)
    print("【探针】三项（立规 2e: 先过已知答案, 再跑真实数据）")
    print("=" * 100)
    r = paipan("癸酉丁巳己卯甲戌")
    sp = r.get("special") or {}
    keys = sorted(sp.keys())
    print("甲 期望 10 键, 实得 %d 键: %s" % (len(keys), keys))
    EXP = sorted(['patterns', 'cong_type', 'cong_state', 'zhuanwang', 'hua_qi',
                  'mu_mie', 'mu_mie_state', 'liangqi', 'zhuanwang_state',
                  'judgment_status'])
    print("   与源码 L71-74 期望一致 =", keys == EXP)
    if keys != EXP:
        print("   ★ 差异: 缺 %s / 多 %s" % (set(EXP) - set(keys), set(keys) - set(EXP)))

    # 乙 已知应全空
    r2 = paipan("甲寅乙卯丙辰丁巳")
    sp2 = r2.get("special") or {}
    print("\n乙 甲寅乙卯丙辰丁巳（身旺无根）: zhuanwang=%r hua_qi=%r cong_type=%r"
          % (sp2.get("zhuanwang"), sp2.get("hua_qi"), sp2.get("cong_type")))

    # 丙 已知全有: 一行得气盘
    r3 = paipan("戊辰壬辰甲辰戊辰")   # 甲木专旺候选
    sp3 = r3.get("special") or {}
    print("丙 戊辰壬辰甲辰戊辰: zhuanwang=%r state=%r"
          % (sp3.get("zhuanwang"), sp3.get("zhuanwang_state")))
    return keys


def full():
    keys = probe()
    print("\n" + "=" * 100)
    print("【全量】六本 2106 盘 special 字段分布")
    print("=" * 100)
    rows = []
    for bk in BOOKS:
        for line in open(os.path.join(CA, "%s_clean.jsonl" % bk),
                         encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            try:
                sp = (paipan(bz).get("special") or {})
            except Exception:
                continue
            rows.append((d["case_id"], sp))
    print("样本 = %d 盘" % len(rows))

    print("\n%-16s %8s %s" % ("字段", "非空数", "值域分布"))
    print("-" * 100)
    for k in ["cong_type", "cong_state", "zhuanwang", "zhuanwang_state",
              "hua_qi", "mu_mie", "judgment_status"]:
        c = collections.Counter(str(sp.get(k)) for _, sp in rows)
        nz = len(rows) - c.get("None", 0)
        top = ", ".join("%s:%d" % (a, b) for a, b in c.most_common(8))
        print("%-16s %8d  %s" % (k, nz, top))

    # 判定树: 从格类型 × 状态
    print("\n" + "=" * 100)
    print("【判定树 1】从格: cong_type × cong_state")
    print("=" * 100)
    tree = collections.Counter((sp.get("cong_type"), sp.get("cong_state"))
                               for _, sp in rows)
    for (t, s), n in sorted(tree.items(), key=lambda kv: -kv[1]):
        print("   %-12s %-12s %d" % (str(t), str(s), n))

    print("\n" + "=" * 100)
    print("【判定树 2】专旺: zhuanwang × zhuanwang_state")
    print("=" * 100)
    tree2 = collections.Counter((sp.get("zhuanwang"), sp.get("zhuanwang_state"))
                                for _, sp in rows)
    for (t, s), n in sorted(tree2.items(), key=lambda kv: -kv[1]):
        print("   %-12s %-12s %d" % (str(t), str(s), n))

    print("\n" + "=" * 100)
    print("【判定树 3】化气: hua_qi（hua_qi_state 不在 10 键内, 另核）")
    print("=" * 100)
    c = collections.Counter(str(sp.get("hua_qi")) for _, sp in rows)
    for a, n in c.most_common():
        print("   %-14s %d" % (a, n))

    # 互斥核: 乙 —— 专旺与从格是否互斥
    print("\n" + "=" * 100)
    print("【乙】专旺 / 从格 重叠核（核3 发现共用 CONG_GE 段）")
    print("=" * 100)
    both = [cid for cid, sp in rows
            if sp.get("cong_type") and sp.get("zhuanwang")]
    print("   同时命中 cong_type 与 zhuanwang 的盘 = %d" % len(both))
    if both[:8]:
        print("   样例: %s" % ", ".join(both[:8]))
    only_c = sum(1 for _, sp in rows if sp.get("cong_type"))
    only_z = sum(1 for _, sp in rows if sp.get("zhuanwang"))
    print("   只命中从格 = %d / 只命中专旺 = %d" % (only_c, only_z))
    print("   两者独立(互斥) =", len(both) == 0)

    # patterns 列表里的 id
    print("\n" + "=" * 100)
    print("【patterns】规则 id × state")
    print("=" * 100)
    pid = collections.Counter()
    for _, sp in rows:
        for p in (sp.get("patterns") or []):
            pid[(p.get("id"), p.get("state"))] += 1
    for (a, b), n in sorted(pid.items(), key=lambda kv: -kv[1]):
        print("   %-26s %-12s %d" % (str(a), str(b), n))


if __name__ == "__main__":
    full()