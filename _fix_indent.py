# -*- coding: utf-8 -*-
"""修正#033补丁的缩进"""
f = 'spec/root_qi.py'
with open(f, 'r', encoding='utf-8') as fp:
    lines = fp.readlines()

# 找第204行(# 旺墓或生旺半局), 把它和后面的for循环加4空格
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    # 找"else:"行(第203行附近)
    if i >= 200 and i <= 210 and line.strip() == 'else:':
        new_lines.append(line)
        # 下一行是注释, 加4空格
        if i+1 < len(lines):
            new_lines.append('    ' + lines[i+1])
            skip_next = True
        # 再下一行是for循环, 加4空格
        if i+2 < len(lines):
            new_lines.append('    ' + lines[i+2])
        continue
    # for stem in stems: 后面的if也要加4空格
    if i >= 200 and i <= 220 and 'if STEM_WUXING' in line:
        new_lines.append('    ' + line)
        continue
    if i >= 200 and i <= 220 and "hehui_result.append({" in line and '三合' in lines[i-1] if i>0 else False:
        new_lines.append('    ' + line)
        continue
    new_lines.append(line)

with open(f, 'w', encoding='utf-8') as fp:
    fp.writelines(new_lines)
print('done')
