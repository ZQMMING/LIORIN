# -*- coding: utf-8 -*-
"""PATCH-4c/4d/4e + PATCH-YS-1 落码后: 15 格盘数前后对比 + 被拦盘清单 + 孙岳造反查。
旧 dump: scripts/_sp_audit.json (commit ee739175 时代)
新 dump: scripts/_sp_audit_new.json (本轮落码后)
"""
import json, collections, sys

OLD = json.load(open("scripts/_sp_audit.json", encoding="utf-8"))
NEW = json.load(open("scripts/_sp_audit_new.json", encoding="utf-8"))

def cell(sp):
    """主从格 15 格: 类 x 态。返回 (类, 态) 或 None。"""
    ct, cs = sp.get("cong_type"), sp.get("cong_state")
    if not ct:
        return None
    cls = None
    for k in ("从财格", "从杀格", "从儿格", "从官格", "从势格"):
        if k in ct:
            cls = k; break
    if cls is None:
        cls = ct
    return (cls, cs or "CONFIRMED")

def pats_of(sp):
    return [(p[0], p[2]) for p in sp.get("pats", [])]

# --- 1. 15 格盘数前后 ---
old_cell = collections.Counter()
new_cell = collections.Counter()
for d in OLD.values():
    c = cell(d)
    if c: old_cell[c] += 1
for d in NEW.values():
    c = cell(d)
    if c: new_cell[c] += 1
print("=== 1. 主从格 15 格盘数 旧 -> 新 ===")
for k in sorted(old_cell):
    o, n = old_cell[k], new_cell.get(k, 0)
    flag = "  <- 变动" if o != n else ""
    print("  %s: %d -> %d%s" % (k[0] + "/" + k[1], o, n, flag))
for k in sorted(new_cell):
    if k not in old_cell:
        print("  %s: 0 -> %d  <- 新增" % (k[0] + "/" + k[1], new_cell[k]))

# --- 2. 被拦盘 (ZP-SPECIAL-CONG-BAN) ---
ban = [(cid, [p[1] for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG-BAN"], d.get("label"))
       for cid, d in NEW.items()
       if any(p[0] == "ZP-SPECIAL-CONG-BAN" for p in d.get("pats", []))]
print("\n=== 2. 通判据/类专属被拦盘 (ZP-SPECIAL-CONG-BAN) 共 %d 盘 ===" % len(ban))
for cid, reasons, lab in ban[:60]:
    print("  %s [%s] %s" % (cid, lab, "; ".join(reasons)))
if len(ban) > 60:
    print("  ... 共 %d 盘, 余 %d 略" % (len(ban), len(ban) - 60))

# --- 3. 孙岳造反查 PZ-0067 ---
print("\n=== 3. 孙岳造反查 PZ-0067 (L1034 化气格真) ===")
for cid in ("PZ-0067",):
    o, n = OLD.get(cid, {}), NEW.get(cid, {})
    print("  旧: cong=%s/%s hq=%s pats=%s" % (o.get("cong_type"), o.get("cong_state"), o.get("hq"), pats_of(o)))
    print("  新: cong=%s/%s hq=%s pats=%s" % (n.get("cong_type"), n.get("cong_state"), n.get("hq"), pats_of(n)))

# --- 4. 化气格全量对比 ---
print("\n=== 4. 化气格 (hua_qi) 全量对比 ===")
old_hq = collections.Counter()
new_hq = collections.Counter()
hq_changed = []
for cid in OLD:
    o, n = OLD[cid].get("hq"), NEW.get(cid, {}).get("hq")
    old_hq[o] += 1
    new_hq[n] += 1
    if o != n:
        hq_changed.append((cid, o, n))
print("  旧分布: %s" % dict(old_hq))
print("  新分布: %s" % dict(new_hq))
print("  变化 %d 盘:" % len(hq_changed))
for cid, o, n in hq_changed[:40]:
    print("    %s: hq %s -> %s" % (cid, o, n))

# --- 5. 全部 patterns 态分布对比 ---
print("\n=== 5. patterns 态分布 (全 pattern) 旧 -> 新 ===")
def pat_cnt(d):
    c = collections.Counter()
    for p in d.values():
        for pid, st in pats_of(p):
            c[(pid, st)] += 1
    return c
o_cnt, n_cnt = pat_cnt(OLD), pat_cnt(NEW)
allk = sorted(set(o_cnt) | set(n_cnt))
for k in allk:
    o, n = o_cnt.get(k, 0), n_cnt.get(k, 0)
    if o != n:
        print("  %s: %d -> %d" % (k, o, n))
