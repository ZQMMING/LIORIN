# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CASES = r"D:\顺天系统资料\六部经典独立案例\三命通会\三命通会.jsonl"
RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"

# 六十甲子 valid ganzhi combos
TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"
# valid 60 jiazi
valid_ganzhi = set()
for i in range(60):
    valid_ganzhi.add(TIANGAN[i%10] + DIZHI[i%12])

# 阳干阳支 check
YANG_GAN = set("甲丙戊庚壬")
YANG_ZHI = set("子寅辰午申戌")

cases = []
with open(CASES, encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        cases.append(json.loads(line))

print("总案例数:", len(cases))

# 读取 canonical raw
with open(RAW, encoding='utf-8') as f:
    canon = f.read()
print("canon长度:", len(canon))

# 检测名人关键词
celebrity_kw = ["岳飞","武穆","明太祖","太祖","朱元璋","韩琦","富弼","范文正","范仲淹","司马温公","司马光",
                "苏东坡","苏轼","欧阳修","王安石","秦桧","张浚","魏公","潞公","程伊川","程颐","朱熹",
                "陆宣公","陆贽","李卫公","李靖","诸葛","孔子","孟子","周公","汉高祖","武帝","唐太宗",
                "玄宗"]
celebrity_kw = list(dict.fromkeys(celebrity_kw))

# 也检测 "某人" "先生" "丞相" 等
# 先看每个案例 raw 前80字
print("\n=== 全部案例 bazi + raw前60字 ===")
for c in cases:
    bz = c['bazi']
    raw_head = c['raw'][:70].replace('\n',' ')
    has_name = any(k in c['raw'] for k in celebrity_kw)
    flag = "【名人?】" if has_name else ""
    print(f"{c['case_id']} | {bz} | {flag}{raw_head}")
