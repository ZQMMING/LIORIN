# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"
with open(RAW, encoding='utf-8') as f:
    canon = f.read()

# 1) 查 "与此同义" (SM-0001 raw 中段)
for kw in ["与此同义","皆父母之气","尊为天子","明太祖","五湖水聚掌群黎","翁仲益","张侍郎"]:
    i = canon.find(kw)
    print(f"--- 关键词 [{kw}] 位置={i}")
    if i>=0:
        print(repr(canon[i-60:i+80]))
    print()

# 2) 直接搜 SM-0001 的八字
for kw in ["己未庚辰戊辰丁丑","己未 庚辰 戊辰 丁丑","己未\u3000庚辰"]:
    print(f"搜 [{kw}]:", canon.find(kw))

# 3) 看 canon 开头200字
print("=== canon 开头 ===")
print(repr(canon[:300]))
print("=== canon 末尾 ===")
print(repr(canon[-300:]))
