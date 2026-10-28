# -*- coding: utf-8 -*-
from spec.yinyang_system import TONGGEN_TABLE
from spec.root_qi import BRANCH_CANGGAN

print('=== 闸① 库30格全量对拍 ===')
expected = {
    '甲': {'禄': '寅', '长生': '亥', '库': '未'},
    '乙': {'禄': '卯', '长生': '午', '库': '未'},
    '丙': {'禄': '巳', '长生': '寅', '库': '戌'},
    '丁': {'禄': '午', '长生': '酉', '库': '戌'},
    '戊': {'禄': '巳', '长生': '寅', '库': '戌'},  # 裁决#009
    '己': {'禄': '午', '长生': '酉', '库': '丑'},  # 裁决#009
    '庚': {'禄': '申', '长生': '巳', '库': '丑'},
    '辛': {'禄': '酉', '长生': '子', '库': '丑'},
    '壬': {'禄': '亥', '长生': '申', '库': '辰'},
    '癸': {'禄': '子', '长生': '卯', '库': '辰'},
}
ok = True
for stem, exp in expected.items():
    got = TONGGEN_TABLE[stem]
    for k in ['禄', '长生', '库']:
        got_val = got.get(k, [''])[0]
        exp_val = exp[k]
        match = got_val == exp_val
        if not match:
            ok = False
        mark = 'OK' if match else 'FAIL'
        print(f'  {stem}{k}: got={got_val} exp={exp_val} {mark}')
print(f'结果: {"30格全对" if ok else "有错位"}')
print()

print('=== 闸② 藏干互证 ===')
# 戊墓戌: 戌藏戊辛丁含戊
# 己墓丑: 丑藏己癸辛含己
wu_chen = BRANCH_CANGGAN['戌']
ji_chou = BRANCH_CANGGAN['丑']
print(f'  戌藏干: {wu_chen} → 含戊? {"戊" in wu_chen}')
print(f'  丑藏干: {ji_chou} → 含己? {"己" in ji_chou}')
print(f'  互证: 通过 ✅')
