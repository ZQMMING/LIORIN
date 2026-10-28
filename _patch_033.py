# -*- coding: utf-8 -*-
"""加#033半局中神被冲=散"""
f = 'spec/root_qi.py'
with open(f, 'r', encoding='utf-8') as fp:
    c = fp.read()

old = '''            if middle in remaining:
                # 旺墓或生旺半局
                for stem in stems:
                    if STEM_WUXING.get(stem, "") == hua_wx:
                        hehui_result.append({
                            'type': '三合',
                            'hua': hua_wx,
                            'members': remaining,
                            'status': '半局',
                            'lost': lost,
                            'reason': f'方夺{lost}→半局',
                        })
                        break
                else:
                    hehui_result.append({
                        'type': '三合',
                        'hua': hua_wx,
                        'members': remaining,
                        'status': '半局合而不化',
                        'lost': lost,
                    })'''

new = '''            if middle in remaining:
                # 裁决#033: 半局中神被冲=散
                if any(_is_chong(middle, b) for b in all_branches):
                    hehui_result.append({
                        'type': '三合',
                        'hua': hua_wx,
                        'members': remaining,
                        'status': '局散',
                        'lost': lost,
                        'reason': f'半局中神{middle}被冲→散(#033)',
                    })
                else:
                    # 旺墓或生旺半局
                    for stem in stems:
                        if STEM_WUXING.get(stem, "") == hua_wx:
                            hehui_result.append({
                                'type': '三合',
                                'hua': hua_wx,
                                'members': remaining,
                                'status': '半局',
                                'lost': lost,
                                'reason': f'方夺{lost}→半局',
                            })
                            break
                    else:
                        hehui_result.append({
                            'type': '三合',
                            'hua': hua_wx,
                            'members': remaining,
                            'status': '半局合而不化',
                            'lost': lost,
                        })'''

c = c.replace(old, new)
with open(f, 'w', encoding='utf-8') as fp:
    fp.write(c)
print('done')
