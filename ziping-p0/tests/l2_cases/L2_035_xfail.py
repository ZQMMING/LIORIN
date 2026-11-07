# -*- coding: utf-8 -*-
"""
L2 #035 XFAIL收编: 已知误判盘
③子行无救应: 库根救应判定缺失
当前判熄(错误), 正确是不熄
"""
import sys
sys.path.insert(0, '.')

from engines.common.mumie_checker import check_mumie

print('=== #035 XFAIL收编: 已知误判盘 ===')
print()

# XFAIL盘: 木多+火库根戌
# 当前: 判熄(错误)
# 正确: 不熄(戌中丁火=库根救应)
r = check_mumie(['卯', '寅', '卯', '戌'], ['癸', '甲', '甲', '甲'], '丙')
print(f'盘: 卯寅卯戌 + 癸甲甲甲 (丙日主)')
print(f'当前判定: {r["status"]} ratio={r.get("ratio",0):.1f}')
print(f'正确判定: 不熄(戌中丁火=库根救应)')
print(f'标记: XFAIL #035-③ 子行无救应判定缺失')
print()

# 入库注释: ③实现后此盘转PASS
print('已收编: #035-③ XFAIL盘1个(活捉误判在押)')
