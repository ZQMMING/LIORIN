# -*- coding: utf-8 -*-
with open('special_pattern.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if i == 391:
        new_lines.append('    if dm_ben_eff >= 1 and not _yin_wang_not_zw:\n')
        new_lines.append('        if confirmed_zw:\n')
        new_lines.append('            zw = ZHUANWANG_NAME.get(dm_wx)\n')
        new_lines.append("            out['patterns'].append(_pat('ZP-SPECIAL-ZHUANWANG', zw, 'CONFIRMED', dm_wx,\n")
        new_lines.append("                '支局全、透干含本行、日主属该行，官杀财无本气不透，一行得气',\n")
        new_lines.append("                ['combination_facts', 'wuxing_power', 'tian_he']))\n")
        new_lines.append("            out['zhuanwang'] = zw\n")
        new_lines.append("            out['zhuanwang_state'] = 'CONFIRMED'\n")
        new_lines.append('        elif candidate_zw:\n')
        new_lines.append('            zw = ZHUANWANG_NAME.get(dm_wx)\n')
        new_lines.append("            out['patterns'].append(_pat('ZP-SPECIAL-ZHUANWANG', zw, 'CANDIDATE', dm_wx,\n")
        new_lines.append("                '党众成势、透干含本行、日主属该行，官杀/财仅虚透无根；支局未全为候选',\n")
        new_lines.append("                ['wuxing_power', 'tian_he']))\n")
        new_lines.append("            out['zhuanwang'] = zw\n")
        new_lines.append("            out['zhuanwang_state'] = 'CANDIDATE'\n")
        skip = True
        continue
    if skip:
        if i == 422:
            skip = False
            continue
        continue
    new_lines.append(line)

with open('special_pattern.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('done')
