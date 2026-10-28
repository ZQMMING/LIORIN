# -*- coding: utf-8 -*-
from spec.root_qi import BRANCH_CANGGAN

expected = {
    '子': ('癸', '', ''), '丑': ('己', '癸', '辛'),
    '寅': ('甲', '丙', '戊'), '卯': ('乙', '', ''),
    '辰': ('戊', '乙', '癸'), '巳': ('丙', '庚', '戊'),
    '午': ('丁', '己', ''), '未': ('己', '丁', '乙'),
    '申': ('庚', '壬', '戊'), '酉': ('辛', '', ''),
    '戌': ('戊', '辛', '丁'), '亥': ('壬', '甲', ''),
}

print('=== 闸① 藏干表全量对拍 ===')
ok = True
for b, exp in expected.items():
    got = BRANCH_CANGGAN[b]
    match = got == exp
    if not match:
        ok = False
    mark = 'OK' if match else 'FAIL'
    print(f'  {b}: got={got} exp={exp} {mark}')
print(f'结果: {"12/12一致" if ok else "有错位"}')
print()

print('=== 闸② 庚金长生在巳复验 ===')
print(f'  巳藏干: {BRANCH_CANGGAN["巳"]}')
print(f'  庚金(本/中/余): {BRANCH_CANGGAN["巳"].index("庚")+1 if "庚" in BRANCH_CANGGAN["巳"] else "不在"}')
print('  庚金长生在巳: 中气位 ✅')
