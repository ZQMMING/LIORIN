# -*- coding: utf-8 -*-
import traceback
from engines.common.l0_fact_builder import build as l0build
from engines.common.wuxing_power import build_wuxing_power, build_spectrum_topology, build_spectrum_from_power
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.special_pattern import build_special_patterns
from engines.common.climate_structure import build_climate_structure
from engines.common.yongshen_engine import build_yongshen_engine

K = ('year', 'month', 'day', 'hour')
def gp(s):
    return {K[i//2]: [s[i], s[i+1]] for i in range(0, 8, 2)}

p = gp('甲子 丙寅 庚午 丙子'.replace(' ', ''))
f = l0build(p)
th = build_tian_he(p, f)
wp = build_wuxing_power(p, f, th)
sp = build_spectrum_topology({}, wp)
_spd = build_spectrum_from_power(wp, p)
sp['wang_shuai'] = _spd.get('wang_shuai')
sp['qiang_ruo'] = _spd.get('qiang_ruo')
cls = build_climate_structure(p, f, th)
spp = build_special_patterns(p, f, wp, th, cls)

try:
    ye = build_yongshen_engine(p, f, wp, sp, spp, None)
    print('OK')
except Exception as e:
    traceback.print_exc()
