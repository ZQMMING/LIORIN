# -*- coding: utf-8 -*-
"""post30 -> post31 回归比对（只比判定字段，不比 strength_verdict 形态）

★ 判定口径: ge_cheng / ge / ti_wx / xi_wx / po_ge / bing 数
  strength_verdict 本轮由 'NOT_AUTHORIZED' 字符串变 dict —— 这是预期变化, 单独核。
"""
import io
import json
import os

ROOT = r"D:/shuntian-ziping-p0"
SC = os.path.join(ROOT, "scripts")
A = json.load(io.open(os.path.join(SC, "_l4_post30.json"), encoding="utf-8-sig"))
B = json.load(io.open(os.path.join(SC, "_l4_post31.json"), encoding="utf-8-sig"))


def rows(d):
    return d if isinstance(d, list) else list(d.values())


print("=" * 96)
print("post30 -> post31 判定回归比对")
print("=" * 96)
ra, rb = rows(A), rows(B)
print("post30 = %d 条 / post31 = %d 条" % (len(ra), len(rb)))

if isinstance(ra[0], dict) and "case_id" in ra[0]:
    ma = {r["case_id"]: r for r in ra}
    mb = {r["case_id"]: r for r in rb}
    keys = [k for k in ra[0] if k != "case_id"]
else:
    ma = {i: r for i, r in enumerate(ra)}
    mb = {i: r for i, r in enumerate(rb)}
    keys = list(ra[0].keys()) if isinstance(ra[0], dict) else []

common = set(ma) & set(mb)
print("共同 case = %d" % len(common))
diff = {}
for k in keys:
    n = 0
    sample = []
    for c in common:
        if ma[c].get(k) != mb[c].get(k):
            n += 1
            if len(sample) < 3:
                sample.append((c, ma[c].get(k), mb[c].get(k)))
    diff[k] = (n, sample)

print("\n%-16s %8s" % ("字段", "变化数"))
print("-" * 96)
total = 0
for k in keys:
    n, s = diff[k]
    total += n
    flag = "  ★★ 预期变化" if k == "strength_verdict" else ""
    print("%-16s %8d%s" % (k, n, flag))
    if n and k == "strength_verdict":
        for c, x, y in s:
            print("        %s: %r -> %r" % (c, x, y))

print("\n判定字段总变化(排除 strength_verdict) = %d"
      % (total - diff.get("strength_verdict", (0, []))[0]))
print("★ strength_verdict 变化 = %d (预期 2106, 字符串→dict)"
      % diff.get("strength_verdict", (0, []))[0])