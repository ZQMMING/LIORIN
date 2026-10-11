# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'
canon = open(CAN, encoding='utf-8').read()
def norm(s): return re.sub(r'\s+','',s or '')
CN = norm(canon)

# distinctive phrases from the 3 cases
tests = [
 '富夫女克制克星格','伤庚丙火气盈余','患瘵死也明矣','夫星得生于巳',
 '尚书妻火少金多格','乙未那堪叠见金','夫星术旺','夫子全美也',
 '临忠所贵命土重木轻格','日主干强七杀轻','暗来破戊己为药','旺助衰木之气',
]
for t in tests:
    print(repr(t), '->', norm(t) in CN)

# also check 鹧鸪天 for SF-0107
print()
print('甲临子位日时全 ->', '甲临子位日时全' in CN)
