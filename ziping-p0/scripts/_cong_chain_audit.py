# -*- coding: utf-8 -*-
"""核1 从格数字链全量对账: 790 = 主从268 + 追加522(从旺198+并列从杀324) 新旧全链 + BAN 成分。
核 268-91=177 vs BAN 186 差 9 盘去向; 追加分支受 4e-3/4e-4 约束数。"""
import json, collections

OLD = json.load(open("scripts/_sp_audit.json", encoding="utf-8"))
NEW = json.load(open("scripts/_sp_audit_new.json", encoding="utf-8"))

def classify(d):
    """返回 (主从格type,state, 追加分支names, BAN reasons)。"""
    ct, cs = d.get("cong_type"), d.get("cong_state")
    apps, bans = [], []
    for p in d.get("pats", []):
        pid, name, st = p
        if pid == "ZP-SPECIAL-CONG-BAN":
            bans.append(name)
        elif pid == "ZP-SPECIAL-CONG" and ct is None and st == "CANDIDATE":
            apps.append(name)
    return ct, cs, apps, bans

# 旧: 全链
old_cong_all = old_apps = old_zw = old_bs = 0
old_app_names = collections.Counter()
old_main = collections.Counter()
for d in OLD.values():
    ct, cs, apps, _ = classify(d)
    if ct or apps:
        old_cong_all += 1
    if ct:
        old_main[(ct, cs)] += 1
    for a in apps:
        old_app_names[a] += 1

# 新: 全链
new_cong_all = new_apps = 0
new_app_names = collections.Counter()
new_main = collections.Counter()
ban_main, ban_app = 0, 0
ban_reasons = collections.Counter()
ban_by_name = collections.defaultdict(list)
for cid, d in NEW.items():
    ct, cs, apps, bans = classify(d)
    if ct or apps:
        new_cong_all += 1
    if ct:
        new_main[(ct, cs)] += 1
    for a in apps:
        new_app_names[a] += 1
    for b in bans:
        ban_reasons[b] += 1
        ban_by_name[b].append(cid)
        # 该 BAN 盘原本的追加分支 (用 OLD 查它是否曾输出追加分支)
        oa = classify(OLD.get(cid, {}))[2]
        if oa:
            ban_app += 1
        else:
            ban_main += 1

print("=== 旧: CONG 全链 ===")
print("  CONG pattern 全量(主从+追加): %d" % old_cong_all)
print("  主从格: %s (总 %d)" % (dict(old_main), sum(old_main.values())))
print("  追加分支: %s (总 %d)" % (dict(old_app_names), sum(old_app_names.values())))
print("  核对: 主从 %d + 追加 %d = %d (应=790)" % (sum(old_main.values()), sum(old_app_names.values()),
      sum(old_main.values()) + sum(old_app_names.values())))

print("\n=== 新: CONG 全链 ===")
print("  CONG pattern 全量(主从+追加): %d" % new_cong_all)
print("  主从格: %s (总 %d)" % (dict(new_main), sum(new_main.values())))
print("  追加分支: %s (总 %d)" % (dict(new_app_names), sum(new_app_names.values())))

print("\n=== BAN 186 成分 ===")
print("  原主从格盘被拦: %d" % ban_main)
print("  原追加分支盘被拦: %d" % ban_app)
print("  拦因分布: %s" % dict(ban_reasons))

print("\n=== 数字链核对 ===")
old_total = sum(old_main.values()) + sum(old_app_names.values())
new_total = sum(new_main.values()) + sum(new_app_names.values())
print("  旧 790 = 主从 %d + 追加 %d" % (sum(old_main.values()), sum(old_app_names.values())))
print("  新 = 主从 %d + 追加 %d = %d (BAN 186 后余)" % (sum(new_main.values()), sum(new_app_names.values()), new_total))
print("  旧主从 268 - 新主从 %d = %d (应=BAN中主从盘 %d + 转追加/其他?)"
      % (sum(new_main.values()), sum(old_main.values()) - sum(new_main.values()), ban_main))
