# -*- coding: utf-8 -*-
"""暴露③缺失"""
import sys
sys.path.insert(0, '.')

from engines.common.mumie_checker import check_mumie
from engines.common.dangzhong_counter import calc_dangzhong

# 木=7.0, 火=1.8, ratio=3.9→应判出
# 但火有库根戌→应不判出(③缺失暴露)
dz = calc_dangzhong(['卯', '寅', '卯', '戌'], ['癸', '甲', '甲', '甲'])
mu, zi = dz['木'], dz['火']
ratio = mu / zi if zi > 0 else 999
print(f'木={mu:.1f}, 火={zi:.1f}, ratio={ratio:.1f}')
r = check_mumie(['卯', '寅', '卯', '戌'], ['癸', '甲', '甲', '甲'], '丙')
print(f'判定: {r["status"]} (应无, 因为火有戌库根=救应)')
