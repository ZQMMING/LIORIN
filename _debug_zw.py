# -*- coding: utf-8 -*-
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

# 炎上格用例
p = gp('己巳辛未丙午丁酉')
f = l0build(p)
th = build_tian_he(p, f)
wp = build_wuxing_power(p, f, th)

# 手动算关键变量
pw = wp['wuxing_power']
dm_wx = wp['daymaster_element']
print(f'dm_wx: {dm_wx}')

from engines.common.special_pattern import SHENG_ME, SHENG, KE, KE_ME, _BEN_TAGS, _ben_branches, _shi, _fkey, _pat
yin_wx, ss_wx, cai_wx, gs_wx = SHENG_ME[dm_wx], SHENG[dm_wx], KE[dm_wx], KE_ME[dm_wx]
dm, yin = pw[dm_wx], pw.get(yin_wx, {})
ss, cai, gs = pw.get(ss_wx, {}), pw.get(cai_wx, {}), pw.get(gs_wx, {})

dm_ben = int(dm.get('ben_n', 0))
dm_stem = int(dm.get('stem_n', 0))
dm_ju = int(dm.get('ju_n', 0))
yin_ben = int(yin.get('ben_n', 0))
gs_ben = int(gs.get('ben_n', 0))
gs_stem = int(gs.get('stem_n', 0))
gs_ju = int(gs.get('ju_n', 0))
cai_ben = int(cai.get('ben_n', 0))
cai_stem = int(cai.get('stem_n', 0))
cai_ju = int(cai.get('ju_n', 0))

print(f'dm_ben: {dm_ben}, dm_stem: {dm_stem}, dm_ju: {dm_ju}')
print(f'gs_ben(官杀): {gs_ben}, gs_stem: {gs_stem}, gs_ju: {gs_ju}')
print(f'cai_ben(财): {cai_ben}, cai_stem: {cai_stem}, cai_ju: {cai_ju}')

# gate_ok
gs_ben_zw = gs_ben  # 简化
cai_ben_zw = cai_ben
gate_ok = (gs_ben_zw == 0 and gs_stem == 0 and gs_ju == 0) and (cai_ben_zw <= 1 and cai_stem == 0 and cai_ju == 0)
print(f'gate_ok: {gate_ok}')

tougan_row = (dm_stem >= 1)
day_stem = p['day'][0]
day_in_row = (day_stem in ['丙', '丁'] and dm_wx == '火')
print(f'tougan_row: {tougan_row}, day_in_row: {day_in_row}')

confirmed_zw = gate_ok and (dm_ju >= 1) and tougan_row and day_in_row
print(f'confirmed_zw: {confirmed_zw}')

# dm_ben_eff
print(f'dm root_detail: {dm.get("root_detail", {})}')
