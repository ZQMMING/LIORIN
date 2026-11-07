# -*- coding: utf-8 -*-
"""Float compliance scanner."""
import sys, os, re
sys.path.insert(0, 'D:/shuntian-ziping-p0')

modules = [
    'engines/common/l0_fact_builder.py',
    'engines/common/wuxing_power.py',
    'engines/common/daymaster_root_class.py',
    'engines/common/daymaster_power_structure.py',
    'engines/common/bingyao_layer.py',
    'engines/common/bing_debate.py',
    'engines/common/ge_jie_layer.py',
    'engines/common/yongyao_resolve.py',
    'engines/common/special_pattern.py',
    'engines/common/strength_rules_full.py',
    'engines/common/strength_producer.py',
    'engines/common/strength_pipeline.py',
    'engines/common/dayun_summary.py',
    'engines/common/liunian_summary.py',
    'engines/common/qiyun.py',
    'engines/common/dayun.py',
    'p0_v2/bazi_gate.py',
    'p0_v2/pzzq_align.py',
    'p0_v2/jiu_ying.py',
    'p0_v2/domain_extract.py',
    'p0_v2/gaodi.py',
    'p0_v2/cheng_bai_criteria.py',
    'p0_v2/cheng_bai.py',
]

float_violations = []
for mod in modules:
    if not os.path.exists(mod):
        continue
    with open(mod, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        if re.search(r'\*\* 0\.\d|/\s*\d+\.\d|\*\*\s*0\.\d', stripped):
            float_violations.append((mod, i, stripped[:100]))
        elif re.search(r'random\.', stripped):
            float_violations.append((mod, i, stripped[:100]))

print(f'Float violations found: {len(float_violations)}')
for m, ln, code in float_violations:
    print(f'{m}:{ln} {code}')
