# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from engines.common.daymaster_wang_xiang import classify_wang_xiang, WANG, XIANG, XIU, QIU, SI

# 春木令: 木旺 火相 水休 金囚 土死
CASES = [
    ('甲', '木', WANG, '春木旺'),
    ('乙', '木', WANG, '春木旺(阴)'),
    ('丙', '木', XIANG, '木生火 火相'),
    ('丁', '木', XIANG, '火相(阴)'),
    ('壬', '木', XIU, '水生木 水休'),
    ('癸', '木', XIU, '水休(阴)'),
    ('庚', '木', QIU, '金克木 金囚'),
    ('辛', '木', QIU, '金囚(阴)'),
    ('戊', '木', SI, '木克土 土死'),
    ('己', '木', SI, '土死(阴)'),
    # 秋金令交叉验证: 金旺 水相 土休 火囚 木死
    ('庚', '金', WANG, '秋金旺'),
    ('壬', '金', XIANG, '金生水 水相'),
    ('戊', '金', XIU, '土生金 土休'),
    ('丙', '金', QIU, '火克金 火囚'),
    ('甲', '金', SI, '金克木 木死'),
]

fails = 0
for dg, m, expect, desc in CASES:
    r = classify_wang_xiang(dg, m)
    ok = r['state'] == expect
    if not ok:
        fails += 1
    print(('PASS' if ok else 'FAIL'), desc, dg + '/令' + m, '->',
          r['state_cn'], '' if ok else '(期望' + expect + ')')

# 边界: 判定字段无强弱/score
import json
blob = json.dumps(classify_wang_xiang('甲', '木'), ensure_ascii=False)
for bad in ['STRONG', 'WEAK', 'score', 'weight']:
    ok = bad not in blob
    if not ok:
        fails += 1
    print(('PASS' if ok else 'FAIL'), '禁用词缺席:', bad)

print()
print('FAILS', fails)
sys.exit(1 if fails else 0)
