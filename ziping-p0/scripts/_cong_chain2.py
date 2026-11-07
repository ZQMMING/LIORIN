# -*- coding: utf-8 -*-
"""核1 深挖: ①旧主从268与新主从91+BAN186的9盘差 ②从财65->21拆分 ③追加489 vs 522来源核。"""
import json, collections

OLD = json.load(open("scripts/_sp_audit.json", encoding="utf-8"))
NEW = json.load(open("scripts/_sp_audit_new.json", encoding="utf-8"))

def main_cell(d):
    ct, cs = d.get("cong_type"), d.get("cong_state")
    return (ct, cs) if ct else None

def apps(d):
    return [p[1] for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG" and p[2] == "CANDIDATE" and not d.get("cong_type")]

def bans(d):
    return [p[1] for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG-BAN"]

# ① 旧主从268盘的新状态
old_main_ids = [cid for cid, d in OLD.items() if main_cell(d)]
new_main_ids = [cid for cid, d in NEW.items() if main_cell(d)]
ban_ids = [cid for cid, d in NEW.items() if bans(d)]
old_set, new_set, ban_set = set(old_main_ids), set(new_main_ids), set(ban_ids)
print("旧主从 %d / 新主从 %d / BAN %d" % (len(old_set), len(new_set), len(ban_set)))
lost = old_set - new_set
print("旧有主从、新无主从: %d" % len(lost))
in_ban = lost & ban_set
print("  其中被BAN: %d / 未被BAN(无主从且无BAN): %d" % (len(in_ban), len(lost - in_ban)))
for cid in sorted(lost - in_ban):
    o = main_cell(OLD[cid]); n = NEW.get(cid, {})
    print("    %s 旧%s -> 新 cong=%s pats=%s" % (cid, o, n.get("cong_type"), n.get("pats")))

# ② 从财 65 -> 21 拆分
old_cai = {cid for cid, d in OLD.items() if main_cell(d) and main_cell(d)[0] == "从财格"}
new_cai = {cid for cid, d in NEW.items() if main_cell(d) and main_cell(d)[0] == "从财格"}
print("\n从财 旧 %d -> 新 %d; 变动 %d 盘:" % (len(old_cai), len(new_cai), len(old_cai ^ new_cai)))
for cid in sorted(old_cai - new_cai):
    o = OLD[cid]; n = NEW.get(cid, {})
    why = "; ".join(bans(n)) if bans(n) else ("无BAN, cong=%s" % n.get("cong_type"))
    print("  失去 %s: %s [%s]" % (cid, why, o.get("label")))
for cid in sorted(new_cai - old_cai):
    print("  新增 %s [%s]" % (cid, NEW[cid].get("label")))

# ③ 追加分支: 旧 pattern 计数 vs 盘数 (多 pattern 盘重叠)
old_app_pattern = collections.Counter()
old_app_disc = set()
for cid, d in OLD.items():
    a = apps(d)
    if a:
        old_app_disc.add(cid)
    for x in a:
        old_app_pattern[x] += 1
print("\n追加分支: 盘 %d / pattern 计数 %s (总 %d)" % (len(old_app_disc), dict(old_app_pattern), sum(old_app_pattern.values())))
