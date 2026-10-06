"""核1: 从势-真从 0 的结构性核验。
对全量2106盘重跑 paipan, 统计:
  A. 从势格全部盘及其 dm_ben_eff (CONFIRMED 需要 dm_ben_eff==0)
  B. dm_ben_eff==0 且无主从格/专旺/化气 的盘 (从势CONFIRMED候选) -> 落入什么 pattern
  C. dm_ben_eff==0 盘的 pattern 分布 (验证主从格先吸收)
"""
import json, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
audit = json.load(open("scripts/_sp_audit.json", encoding="utf-8"))
# 从 case_audit 取 bazi
bazi_of = {}
for f in glob.glob("p0_v2/case_audit/*_clean.jsonl"):
    for l in open(f, encoding="utf-8"):
        x = json.loads(l); bazi_of[x["case_id"]] = x.get("bazi")
def run(bazi):
    sys.path.insert(0, "p0_v2")
    from bazi_gate import paipan
    try:
        return paipan(bazi)
    except Exception as e:
        return {"_err": str(e)}
from collections import Counter
dm0 = Counter(); cong_all = []
cand = []
n = 0
for cid, v in audit.items():
    bazi = bazi_of.get(cid)
    if not bazi: continue
    r = run(bazi)
    n += 1
    sp = r.get("special") or {}
    ct = sp.get("cong_type"); cs = sp.get("cong_state")
    zw = sp.get("zhuanwang"); hq = sp.get("hua_qi"); mm = sp.get("mu_mie")
    lq = sp.get("liangqi")
    dmp = r.get("daymaster_power") or {}
    ben = dmp.get("ben_n")
    if ct == "从势格":
        cong_all.append((cid, cs, ben, bazi))
    if ben == 0:
        dm0["%s/%s" % (ct, cs)] += 1
        dm0["zw=%s" % zw] += 1 if zw else 0
        dm0["hq=%s" % hq] += 1 if hq else 0
        dm0["mm=%s" % mm] += 1 if mm else 0
        dm0["lq=%s" % (lq.get("name") if lq else None)] += 1 if lq else 0
        if not ct and not zw and not hq and not mm and not lq:
            cand.append((cid, bazi, mm, lq))
print("== A. 从势格全部盘(日主本气根 ben_n) ==")
for x in cong_all: print("  %s state=%s ben_n=%s %s" % x)
print("== B. ben_n==0 的盘 pattern 分布(主从格吸收验证) ==")
for k, c in dm0.most_common(): print("  %s: %d" % (k, c))
print("== C. ben_n==0 且无任何 pattern 的盘(从势CONFIRMED候选) ==")
print("  总数:", len(cand))
for cid, bazi, mm, lq in cand[:20]:
    print("  %s %s mm=%s lq=%s" % (cid, bazi, mm, (lq.get("name") if lq else None)))
print("== 统计 ==")
print("  跑盘数:", n)
