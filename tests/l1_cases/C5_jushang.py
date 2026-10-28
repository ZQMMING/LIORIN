# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目C5: 局伤不局破
裁决#017: 中神被冲=局伤(占位记录)
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _is_chong, get_hehui_summary

PASS = 0
FAIL = 0

print('=== C5 局伤不局破 ===')
print()

# 验1: 三合中神被冲(寅午戌+子)
print('--- 三合中神被冲(寅午戌+子) ---')
branches1 = ['寅', '午', '戌', '子']
# 午被子冲?
chong1 = _is_chong('午', '子')
print(f'  午子冲: {chong1}')
# 三合局还成立?
r1 = get_hehui_summary(branches1, ['丙'])
he1 = [h for h in r1['hehui'] if h['hua'] == '火']
print(f'  火局状态: {he1[0]["status"] if he1 else "无"}')
# 期望: 冲成立+局成立(局伤占位)
if chong1 == True and he1 and he1[0]['status'] == '全':
    PASS += 1
    print(f'  OK: 局成立+中神被冲(局伤占位)')
else:
    FAIL += 1
    print(f'  FAIL: 期望局成立+冲成立')

# 验2: 三会中神被冲(寅卯辰+酉)
print()
print('--- 三会中神被冲(寅卯辰+酉) ---')
branches2 = ['寅', '卯', '辰', '酉']
# 卯被酉冲?
chong2 = _is_chong('卯', '酉')
print(f'  卯酉冲: {chong2}')
# 方还成立?
r2 = get_hehui_summary(branches2, ['甲'])
print(f'  木方: {r2["fang_wx"]}')
# 期望: 冲成立+方成
if chong2 == True and r2['fang_wx'] == '木':
    PASS += 1
    print(f'  OK: 方成+中神被冲(方伤占位)')
else:
    FAIL += 1
    print(f'  FAIL: 期望方成+冲成立')

print()
print(f'C5结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 局伤标记待L2旺衰层补, 当前只验局/方成立')
print()
