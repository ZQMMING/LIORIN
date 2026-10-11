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
CN = norm(canon)
byid = {c['case_id']:c for c in cases}

print('======== 3 原文存在 ========')
for cid in ['SF-0002','SF-0033','SF-0052']:
    c = byid[cid]
    print('='*60)
    print(cid, c['bazi'])
    print('RAW:', c['raw'][:300])
    nb = norm(re.sub(r'^\s*[\u4e00-\u9fa5]{2,4}\s+[\u4e00-\u9fa5]{2,4}\s+[\u4e00-\u9fa5]{2,4}\s+[\u4e00-\u9fa5]{2,4}\s*','',c['raw']))
    for i in [0, len(nb)//3, 2*len(nb)//3, len(nb)-16]:
        seg = nb[i:i+16]
        print('  seg', repr(seg), '->', seg in CN)

print('\n======== 8 断语归属 ========')
for cid in ['SF-0106','SF-0107','SF-0119','SF-0120','SF-0121','SF-0125','SF-0129','SF-0138']:
    c = byid[cid]
    print('='*60)
    print(cid, c['bazi'])
    print('RAW:', c['raw'][:280].replace('\n','\\n'))
