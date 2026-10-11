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
valid_ganzhi = set()
for i in range(60):
    valid_ganzhi.add(TIANGAN[i%10] + DIZHI[i%12])
YANG_GAN = set("甲丙戊庚壬")
YANG_ZHI = set("子寅辰午申戌")

with open(CASES, encoding='utf-8') as f:
    cases = [json.loads(l) for l in f if l.strip()]
with open(RAW, encoding='utf-8') as f:
    canon = f.read()

# normalize canon: remove whitespace/newlines for substring matching
canon_nows = re.sub(r'\s+', '', canon)

def check_bazi(bz):
    """return list of issues"""
    issues = []
    parts = bz.split()
    if len(parts) != 4:
        issues.append(f"四柱数!=4 (got {len(parts)})")
        return issues
    for p in parts:
        if p not in valid_ganzhi:
            issues.append(f"非法干支:{p}")
    # 阳干配阳支 check (only flag if 阳干配阴支)
    for p in parts:
        if len(p)==2:
            g,z = p[0], p[1]
            if g in YANG_GAN and z not in YANG_ZHI:
                issues.append(f"阳干配阴支:{p}")
    return issues

print("=== 关1: 八字自洽 ===")
bazi_bad = []
for c in cases:
    iss = check_bazi(c['bazi'])
    if iss:
        bazi_bad.append((c['case_id'], c['bazi'], iss))
        print(c['case_id'], c['bazi'], iss)
print(f"自洽不合格: {len(bazi_bad)} / {len(cases)}")

print("\n=== 关2: 原文存在 (bazi+analysis 在 raw 中) ===")
raw_bad = []
for c in cases:
    # check bazi appears in canon
    bz_nows = c['bazi'].replace(' ','')
    # canon may have the bazi with spaces; strip spaces in canon around
    if bz_nows not in canon_nows:
        raw_bad.append((c['case_id'], c['bazi'], 'bazi not in canon'))
        print("BAZI MISSING:", c['case_id'], c['bazi'])
    # check analysis (strip whitespace) is substring of raw (strip whitespace)
    an_nows = re.sub(r'\s+','', c['analysis'])
    raw_nows = re.sub(r'\s+','', c['raw'])
    if an_nows and an_nows not in raw_nows:
        raw_bad.append((c['case_id'], c['bazi'], 'analysis not subset of raw'))
        print("ANALYSIS NOT SUBSET:", c['case_id'], c['bazi'])
print(f"原文存在问题: {len(raw_bad)}")

print("\n=== 关3: 断语归属 (analysis 是否真配 bazi) ===")
# heuristic: does raw start with bazi? is analysis the text immediately after bazi in raw?
attr_bad = []
for c in cases:
    raw_nows = re.sub(r'\s+','', c['raw'])
    bz_nows = c['bazi'].replace(' ','')
    # raw should start with bazi (these are extracted as "bazi, analysis...")
    if not raw_nows.startswith(bz_nows):
        attr_bad.append((c['case_id'], c['bazi'], 'raw does not start with bazi'))
        print("RAW NOT START:", c['case_id'], c['bazi'], '|', raw_nows[:30])
print(f"断语归属问题: {len(attr_bad)}")

print("\n=== 名人名在 canon 中出现情况 ===")
for name in ["岳飞","武穆","明太祖","太祖","朱元璋","韩琦","富弼","范文正","范仲淹","翁仲益","张侍郎","谢安","贾复","王陵","李吉甫","徐子平"]:
    cnt = canon.count(name)
    print(f"  {name}: {cnt}")
