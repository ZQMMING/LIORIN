# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CASES = r"D:\顺天系统资料\六部经典独立案例\三命通会\三命通会.jsonl"
RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"
valid_ganzhi = set(TIANGAN[i%10]+DIZHI[i%12] for i in range(60))
YANG_GAN = set("甲丙戊庚壬"); YANG_ZHI = set("子寅辰午申戌")

with open(CASES, encoding='utf-8') as f:
    cases = [json.loads(l) for l in f if l.strip()]
with open(RAW, encoding='utf-8') as f:
    canon = f.read()

def norm(s):
    return re.sub(r'[\s、，,。.；;：:（）()\[\]【】""''！？!?]+','',s)

canon_n = norm(canon)

def check_bazi(bz):
    issues=[]
    parts=bz.split()
    if len(parts)!=4: issues.append(f"四柱数={len(parts)}"); return issues
    for p in parts:
        if p not in valid_ganzhi: issues.append(f"非法干支:{p}")
        elif p[0] in YANG_GAN and p[1] not in YANG_ZHI: issues.append(f"阳干配阴支:{p}")
    return issues

results=[]
for c in cases:
    bz=c['bazi']; issues=[]
    # gate1
    g1=check_bazi(bz)
    # gate2: bazi in canon (normalized)
    bz_n=norm(bz)
    g2_bazi = bz_n in canon_n
    # gate2: analysis subset of raw
    an_n=norm(c['analysis']); raw_n=norm(c['raw'])
    g2_an = (an_n in raw_n) if an_n else True
    # gate3: raw starts with bazi
    g3 = raw_n.startswith(bz_n)
    results.append(dict(c=c, g1=g1, g2_bazi=g2_bazi, g2_an=g2_an, g3=g3))

print("=== 关1 八字自洽 ===")
for r in results:
    if r['g1']: print(r['c']['case_id'], r['c']['bazi'], r['g1'])
print("=== 关2 bazi 在 canon ===")
miss=[r for r in results if not r['g2_bazi']]
for r in miss: print(r['c']['case_id'], r['c']['bazi'])
print(f"bazi缺失: {len(miss)}")
print("=== 关2 analysis 是 raw 子集 ===")
miss2=[r for r in results if not r['g2_an']]
for r in miss2: print(r['c']['case_id'], r['c']['bazi'])
print(f"analysis不子集: {len(miss2)}")
print("=== 关3 raw 以 bazi 开头 ===")
miss3=[r for r in results if not r['g3']]
for r in miss3: print(r['c']['case_id'], r['c']['bazi'])
print(f"raw非开头: {len(miss3)}")

# 具名人物检测
print("\n=== 具名人物案例 ===")
named_kw = ["明太祖","翁仲益","张侍郎","王陵","谢安","贾复","尊为天子","为天子","帝","王"]
for r in results:
    raw=r['c']['raw']
    hits=[k for k in ["明太祖","翁仲益","张侍郎","王陵","谢安","贾复","尊为天子"] if k in raw]
    if hits:
        print(r['c']['case_id'], r['c']['bazi'], '->', hits)
