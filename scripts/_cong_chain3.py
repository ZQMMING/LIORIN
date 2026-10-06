# -*- coding: utf-8 -*-
"""核1 差9盘定性 + 补2 4f影响面探针。"""
import json, collections

OLD = json.load(open("scripts/_sp_audit.json", encoding="utf-8"))
NEW = json.load(open("scripts/_sp_audit_new.json", encoding="utf-8"))

def main_cell(d):
    ct, cs = d.get("cong_type"), d.get("cong_state")
    return (ct, cs) if ct else None

def all_pats(d):
    return [p[1] for p in d.get("pats", [])]

def bans(d):
    return [p[1] for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG-BAN"]

old_main = {cid for cid, d in OLD.items() if main_cell(d)}
ban_ids = [cid for cid, d in NEW.items() if bans(d)]

# 差 9: BAN 186 - (旧主从268 - 新主从91=177)
in_old = [cid for cid in ban_ids if cid in old_main]
not_old = [cid for cid in ban_ids if cid not in old_main]
print("BAN 186: 旧有主从 %d / 旧无主从 %d (差9盘来源)" % (len(in_old), len(not_old)))
for cid in not_old:
    o = OLD.get(cid, {})
    print("   %s 旧pats=%s 新BAN=%s" % (cid, all_pats(o), bans(NEW[cid])))

# 旧追加分支盘在新状态 (追加分支减少 489->192 去向)
old_apps = {cid for cid, d in OLD.items() if [p for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG" and p[2] == "CANDIDATE" and not d.get("cong_type")]}
new_apps = {cid for cid, d in NEW.items() if [p for p in d.get("pats", []) if p[0] == "ZP-SPECIAL-CONG" and p[2] == "CANDIDATE" and not d.get("cong_type")]}
lost_app = old_apps - new_apps
print("\n旧追加分支 %d -> 新 %d; 失去 %d 盘:" % (len(old_apps), len(new_apps), len(lost_app)))
lost_ban = lost_app & set(ban_ids)
print("  失去中转为BAN: %d / 无条件退出(4e-3/4e-4 收紧不输出): %d" % (len(lost_ban), len(lost_app - lost_ban)))
print("  无条件退出里 新cong非None(转主从格): %d" % len([c for c in lost_app - lost_ban if main_cell(NEW.get(c, {}))]))
