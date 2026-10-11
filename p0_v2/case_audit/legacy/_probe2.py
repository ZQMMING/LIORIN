# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
RAW = r"D:\shuntian\data\classics\canonical\SMTH_三命通会.txt"
with open(RAW, encoding='utf-8') as f:
    canon = f.read()

# SM-0016 乙巳 辛巳 庚午 辛巳
# SM-0047 己未 壬申 乙未 甲申
for bz in ["乙巳辛巳庚午辛巳","己未壬申乙未甲申"]:
    print(f"=== 搜 {bz} ===")
    i = canon.find(bz)
    print("直接找:", i)
    # try variants with 、
    i2 = canon.find(bz[0:2]+"、"+bz[2:4])
    print("含、找开头:", i2)
    if i2>=0:
        print(repr(canon[i2-40:i2+60]))

# 看 SM-0016 raw 开头特征
print("\n=== SM-0016 raw 特征：'庚坐午，入火乡官贵之地' ===")
i = canon.find("庚坐午，入火乡官贵之地")
print(i)
if i>=0: print(repr(canon[i-80:i+40]))

print("\n=== SM-0047 raw 特征：'乙以庚为夫，庚禄到申' ===")
i = canon.find("乙以庚为夫，庚禄到申")
print(i)
if i>=0: print(repr(canon[i-80:i+40]))
