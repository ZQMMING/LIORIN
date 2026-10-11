# LEGACY: 旧案例审计链（2026-09-30 归档）。保留作证据链 —— 记录了"案例允许任注/徐注增补"的判定现场
#      不参与当前 MD 切片链路。当前链路脚本见 p0_v2/ 根目录 + ../README.md
# 保留理由: v1.6 §1.3.1「物理删除与静默否决均不采用，保证证据链可追溯与可回归」
# -*- coding: utf-8 -*-
import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
JL = r'D:\顺天系统资料\六部经典独立案例\神峰通考\神峰通考.jsonl'
CAN = r'D:\shuntian\data\classics\canonical\SFTK_神峰通考.txt'
cases = [json.loads(l) for l in open(JL, encoding='utf-8') if l.strip()]
canon = open(CAN, encoding='utf-8').read()
def norm(s): return re.sub(r'\s+','',s or '')
cn = norm(canon)

c = cases[0]
print('raw repr:')
print(repr(c['raw'][:200]))
print()
# test segments
tests = ['宜黄县刘景八公','壬生丑日水源深','壬水生临丑月','陶朱之富异乎人','盖得巳时']
for t in tests:
    print(repr(t), '->', norm(t) in cn)

# check SF-0050
c50 = cases[49]
print('\nSF-0050 raw:')
print(c50['raw'][:300])
print()
for t in ['丙火生提向二阳','盖云南一省富命','丙丁身旺见金']:
    print(repr(t), '->', norm(t) in cn)
