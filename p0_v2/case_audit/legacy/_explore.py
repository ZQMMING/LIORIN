# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'

cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
print('=== CASES:', len(cases))

keys = collections.Counter()
for c in cases:
    for k in c.keys():
        keys[k] += 1
print('keys:', dict(keys))

def pillars(b):
    return [p for p in re.split(r'\s+', (b or '').strip()) if p]

bad_pillar = []
no_analysis = []
for c in cases:
    bs = pillars(c['bazi'])
    if len(bs) != 4:
        bad_pillar.append((c['case_id'], c['bazi'], len(bs)))
    a = (c.get('analysis') or '').strip()
    if len(a) < 20:
        no_analysis.append((c['case_id'], c['bazi'], repr(a)))
print('--- bazi not 4 pillars:', len(bad_pillar))
for x in bad_pillar: print(x)
print('--- analysis <20 chars:', len(no_analysis))
for x in no_analysis: print(x)

print('\n--- last 5 ---')
for c in cases[-5:]:
    print(c['case_id'], '|', repr(c['bazi']), '| alen=', c['analysis_chars'], '| rawhead=', (c.get('raw') or '')[:70].replace('\n','\\n'))

# show a few middle cases
print('\n--- middle SF-0050 ~ SF-0055 ---')
for c in cases[49:55]:
    print(c['case_id'], '|', repr(c['bazi']), '| alen=', c['analysis_chars'])
    print('   raw:', (c.get('raw') or '')[:120].replace('\n','\\n'))

raw = open(CAN, encoding='utf-8').read()
print('\n=== CANONICAL len:', len(raw))
print('--- head 600 ---')
print(raw[:600])
print('--- tail 400 ---')
print(raw[-400:])

print('\n楠曰 in canonical:', raw.count('楠曰'))
print('楠曰 in cases raw:', sum((c.get('raw') or '').count('楠曰') for c in cases))
print('病 in canonical:', raw.count('病'))
print('药 in canonical:', raw.count('药'))
print('病药 occurrences:', len(re.findall(r'病药|药\b', raw)))
