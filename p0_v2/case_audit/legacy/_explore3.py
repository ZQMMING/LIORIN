# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
for idx in [0, 1, 50, 53, 54, 55]:
    c = cases[idx]
    print('='*70)
    print(c['case_id'], c['bazi'])
    print(c.get('raw',''))
    print()
