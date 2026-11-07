# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目C6: 效力对打分歧盘
裁决#033: 半局中神被冲=散, 非中神被冲=伤
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_chong, get_hehui_summary

PASS = 0
FAIL = 0

print('=== C6 效力对打分歧盘 ===')
print()

# 盘: 午戌半火局 + 子 → 子午冲中神
# 裁决#033: 半局中神被冲=散
print('--- 午戌半局+子冲午(应散) ---')
branches = ['午', '戌', '子']
r = get_hehui_summary(branches, ['丙'])
print(f'  地支: {branches}')
print(f'  子午冲: {_is_chong("午", "子")}')
he = [h for h in r['hehui'] if h['hua'] == '火']
print(f'  火局状态: {he[0]["status"] if he else "无"}')
# 期望: 冲成立+半局散
if _is_chong('午', '子') and he and he[0]['status'] == '局散':
    PASS += 1
    print(f'  OK: 半局中神被冲=散(#033)')
else:
    FAIL += 1
    print(f'  FAIL: 期望冲+散')

print()
print(f'C6结果: {PASS} PASS / {FAIL} FAIL')
print(f'裁决#033: 半局中神被冲=散, 非中神被冲=伤')
print()
