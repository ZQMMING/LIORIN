# -*- coding: utf-8 -*-
"""special_pattern.py加母灭判定(修正版)"""
f = 'engines/common/special_pattern.py'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

# 1. 加import
old1 = '# -*- coding: utf-8 -*-\nimport re\n"""特殊格局结构识别'
new1 = '# -*- coding: utf-8 -*-\nimport re\nimport sys\nsys.path.insert(0, ".")\nfrom engines.common.mumie_checker import check_mumie\n"""特殊格局结构识别'
c = c.replace(old1, new1)

# 2. 在build_special_patterns函数开头加母灭判定
old2 = '''    dm_ling = dm.get('ling_state') == '旺'

    # ---- 孤根被冲拔(T30):'''
new2 = '''    dm_ling = dm.get('ling_state') == '旺'

    # ---- L2母灭判定(接入L2-3修正版) ----
    branches = [p[1] if len(p) > 1 else '' for p in [pillars.get('year', []), pillars.get('month', []), pillars.get('day', []), pillars.get('hour', [])]]
    stems = [p[0] if p else '' for p in [pillars.get('year', []), pillars.get('month', []), pillars.get('day', []), pillars.get('hour', [])]]
    mumie = check_mumie(branches, stems, day_stem)
    if mumie['status'] == '母灭':
        out['mu_mie'] = mumie['mu_wx'] + '多' + mumie['zi_wx'] + '熄'
        out['mu_mie_state'] = 'CONFIRMED'
        out['judgment_status'] = 'PURE_RULE'
        return out

    # ---- 孤根被冲拔(T30):'''
c = c.replace(old2, new2)

with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
