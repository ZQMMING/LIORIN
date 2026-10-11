# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
byid = {c['case_id']:c for c in cases}
for cid in ['SF-0148','SF-0155']:
    c = byid[cid]
    print('='*60)
    print(cid, c['bazi'])
    print(c['raw'])
    print()
