# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B8: 方夺字
裁决#022: 三会>三合, 字归方
裁决#022b: 中神被夺→三合散, 生支被夺→局残
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import get_hehui_summary

PASS = 0
FAIL = 0

print('=== B8 方夺字 ===')
print()

# 盘1: 生支被夺型 亥子丑方+亥卯半局
# 亥归方(生支), 木局剩卯1支 → 局散
print('--- 盘1: 生支被夺(应局散) ---')
branches1 = ['亥', '子', '丑', '卯']
r1 = get_hehui_summary(branches1, ['甲', '乙'])
print(f'  地支: {branches1}')
print(f'  方: {r1["fang_wx"]}')
print(f'  局: {[(h["hua"], h["status"]) for h in r1["hehui"]]}')
# 期望: 水方成✅, 木局散(亥归方, 剩卯1支)
fang_ok = r1['fang_wx'] == '水'
he_ok = any(h['hua'] == '木' and h['status'] == '局散' for h in r1['hehui'])
if fang_ok and he_ok:
    PASS += 1
    print(f'  OK: 生支被夺→局散')
else:
    FAIL += 1
    print(f'  FAIL: 期望方成+局散')

print()
print('--- 盘2: 中神被夺(应局散) ---')
branches2 = ['寅', '卯', '辰', '亥']
r2 = get_hehui_summary(branches2, ['甲', '乙'])
print(f'  地支: {branches2}')
print(f'  方: {r2["fang_wx"]}')
print(f'  局: {[(h["hua"], h["status"]) for h in r2["hehui"]]}')
# 期望: 木方成✅, 木局散(中神卯被夺)
fang_ok2 = r2['fang_wx'] == '木'
he_ok2 = any(h['hua'] == '木' and h['status'] == '局散' for h in r2['hehui'])
if fang_ok2 and he_ok2:
    PASS += 1
    print(f'  OK: 中神被夺→局散')
else:
    FAIL += 1
    print(f'  FAIL: 期望方成+局散')

print()
print(f'B8结果: {PASS} PASS / {FAIL} FAIL')
print(f'备注: 汇总层已实现, 两盘验#022/#022b')
print()
