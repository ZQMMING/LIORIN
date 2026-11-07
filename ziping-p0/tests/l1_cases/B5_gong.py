# -*- coding: utf-8 -*-
"""
L1定向用例库 - 类目B5: 拱局三档
裁决#016: 拱局三档
  ① 透干补中神 → 成局
  ② 禄代中神 → 会合之意(弱成局)
  ③ 纯拱无补 → 不成局(B4已验)
"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import _get_hehua_branch

PASS = 0
FAIL = 0

print('=== B5 拱局三档 ===')
print()

# 档1: 透干补中神(寅戌+丙丁透干)
print('--- 档1: 透干补中神(应成局) ---')
GONG_TOUGAN = [
    (('寅','戌'), '火', ['丙','甲'], '火'),  # 寅戌拱午, 丙透干补中神
    (('申','辰'), '水', ['壬','甲'], '水'),  # 申辰拱子, 壬透干补中神
    (('亥','未'), '木', ['甲','丙'], '木'),  # 亥未拱卯, 甲透干补中神
    (('巳','丑'), '金', ['庚','丙'], '金'),  # 巳丑拱酉, 庚透干补中神
]
for members, hua, stems, expected in GONG_TOUGAN:
    all_branches = list(members)
    result = _get_hehua_branch(members[0], all_branches, stems)
    ok = result == expected
    if ok: PASS += 1
    else:
        FAIL += 1
        print(f'  FAIL {"".join(members)}透{hua}: got={result} exp={expected}')
    print(f'  OK {"".join(members)}透{hua}: {result}')

print()
print('--- 档2: 禄代中神(应弱成局, 引擎未实现→SKIP) ---')
# 寅戌+巳(巳为火之禄)→ 会合之意
# 引擎暂无"禄代中神"逻辑, 挂待验
GONG_LU = [
    (('寅','戌','巳'), '火'),
    (('申','辰','亥'), '水'),
]
SKIP = 0
for members, hua in GONG_LU:
    SKIP += 1
    print(f'  SKIP {"".join(members)}代{hua}: 待实现(禄代中神分支)')

print()
print(f'B5结果: {PASS} PASS / {FAIL} FAIL / {SKIP} SKIP')
print(f'备注: 禄代中神分支待实现, 纯拱无补档B4已验(4盘全绿)')
print()
