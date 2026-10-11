# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"
with open(RAW, encoding='utf-8') as f:
    canon = f.read()

# 王阳明上下文
i = canon.find("王阳明")
print("王阳明 位置:", i)
if i>=0:
    print(repr(canon[i-20:i+200]))

# 全库再扫：所有 "如...：" "某人..." 型具名
import json
CASES = r"D:\顺天系统资料\六部经典独立案例\三命通会\三命通会.jsonl"
with open(CASES, encoding='utf-8') as f:
    cases=[json.loads(l) for l in f if l.strip()]

# 搜潜在人名关键词（明代/历史名人）
suspect = ["阳明","守仁","新建伯","文成","太师","太傅","尚书","侍郎","学士","状元","宰相","丞相","国公","都督","总兵","进士","举人","状元","状元"]
print("\n=== 潜在具名案例 ===")
for c in cases:
    hits=[k for k in ["阳明","守仁","新建伯","翁仲益","张侍郎","明太祖","王陵","谢安","贾复"] if k in c['raw']]
    if hits:
        print(c['case_id'], c['bazi'], hits)
