# -*- coding: utf-8 -*-
"""更新special_pattern.py母灭状态输出"""
f = 'engines/common/special_pattern.py'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

old = """    mumie = check_mumie(branches, stems, day_stem)
    if mumie['status'] == '母灭':
        out['mu_mie'] = mumie['mu_wx'] + '多' + mumie['zi_wx'] + '熄'
        out['mu_mie_state'] = 'CONFIRMED'
        out['judgment_status'] = 'PURE_RULE'
        return out"""

new = """    mumie = check_mumie(branches, stems, day_stem)
    if mumie['status'] == '母灭':
        out['mu_mie'] = mumie['mu_wx'] + '多' + mumie['zi_wx'] + '熄'
        out['mu_mie_state'] = mumie['state']
        out['judgment_status'] = 'PURE_RULE'
        return out"""

c = c.replace(old, new)
with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
