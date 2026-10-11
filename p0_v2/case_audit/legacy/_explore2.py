# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'
cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
raw = open(CAN, encoding='utf-8').read()

# cases without 楠曰
print('=== cases WITHOUT 楠曰 ===')
no_nan = [c for c in cases if '楠曰' not in (c.get('raw') or '')]
print('count:', len(no_nan))
for c in no_nan:
    print(c['case_id'], '|', c['bazi'], '| alen=', c['analysis_chars'])
    print('   raw:', (c.get('raw') or '')[:160].replace('\n','\\n'))
    print()

print('\n=== "药" contexts in canonical ===')
for m in re.finditer(r'.{0,18}药.{0,18}', raw):
    print(repr(m.group(0)))
