# -*- coding: utf-8 -*-
"""Authority Matrix v0.2 单元测试.
测试6元定义完整性、主轨/辅助轨正确性、独立方法体系标注、判定依据原文引用、与引擎轨道设计一致性.
脚本式, 末尾 sys.exit(1 if fails else 0)。"""
import sys
sys.path.insert(0, '.')
from engines.common.authority_matrix import (
    META_DEFINITIONS, CLASSIC_BOOKS,
    get_meta_definition, get_tracks_for_meta,
    get_judgment_criteria, get_independent_method_systems,
    get_authority_matrix_summary,
)

fails = 0
def check(name, cond):
    global fails
    print(('PASS' if cond else 'FAIL'), name)
    if not cond:
        fails += 1

# === 1. 6元定义完整性 ===
print("\n=== 1. 6元定义完整性 ===")
EXPECTED_METAS = ['WANG_SHUAI', 'QIANG_RUO', 'GE_JU', 'DIAO_HOU', 'BING_YAO', 'YONG_SHEN']
for meta_id in EXPECTED_METAS:
    meta = META_DEFINITIONS.get(meta_id)
    check(f'{meta_id} 存在', meta is not None)
    if meta:
        check(f'{meta_id} 有meta_name', bool(meta.get('meta_name')))
        check(f'{meta_id} 有definition', bool(meta.get('definition')))
        check(f'{meta_id} 有primary_track', bool(meta.get('primary_track')))
        check(f'{meta_id} 有secondary_tracks', isinstance(meta.get('secondary_tracks'), list))
        check(f'{meta_id} 有alternate_tracks', isinstance(meta.get('alternate_tracks'), list))
        check(f'{meta_id} 有activation_condition', bool(meta.get('activation_condition')))
        check(f'{meta_id} 有boundary_note', bool(meta.get('boundary_note')))
        check(f'{meta_id} 有judgment_criteria(v0.2)', bool(meta.get('judgment_criteria')))
        check(f'{meta_id} 有independent_method_systems(v0.2)', bool(meta.get('independent_method_systems')))

# === 2. 每元的主轨/辅助轨正确性 ===
print("\n=== 2. 主轨/辅助轨正确性 ===")
EXPECTED_PRIMARY = {
    'WANG_SHUAI': 'PZZQ',
    'QIANG_RUO': 'PZZQ',
    'GE_JU': 'PZZQ',
    'DIAO_HOU': 'QTBJ',
    'BING_YAO': 'SFTK',
    'YONG_SHEN': 'PZZQ',
}
for meta_id, expected_primary in EXPECTED_PRIMARY.items():
    meta = META_DEFINITIONS.get(meta_id, {})
    check(f'{meta_id} 主轨={expected_primary}', meta.get('primary_track') == expected_primary)

# 调候轨主轨必须是QTBJ(穷通宝鉴是唯一有完整调候体系的经典)
check('DIAO_HOU 主轨=QTBJ(唯一完整调候体系)', META_DEFINITIONS['DIAO_HOU']['primary_track'] == 'QTBJ')

# 病药轨主轨必须是SFTK(神峰通考是病药体系的源头)
check('BING_YAO 主轨=SFTK(病药体系源头)', META_DEFINITIONS['BING_YAO']['primary_track'] == 'SFTK')

# === 3. 独立方法体系标注正确性 ===
print("\n=== 3. 独立方法体系标注正确性 ===")
# 旺衰: 三部以上各有独立体系
wangshuai_systems = META_DEFINITIONS['WANG_SHUAI'].get('independent_method_systems', {})
check('WANG_SHUAI PZZQ有独立体系', wangshuai_systems.get('PZZQ', {}).get('has_independent_system') == True)
check('WANG_SHUAI YHZP有独立体系', wangshuai_systems.get('YHZP', {}).get('has_independent_system') == True)
check('WANG_SHUAI DTS有独立体系', wangshuai_systems.get('DTS', {}).get('has_independent_system') == True)

# 格局: 三部以上各有独立体系
geju_systems = META_DEFINITIONS['GE_JU'].get('independent_method_systems', {})
check('GE_JU PZZQ有独立体系', geju_systems.get('PZZQ', {}).get('has_independent_system') == True)

# 调候: 只有QTBJ有完整独立体系
tiaohou_systems = META_DEFINITIONS['DIAO_HOU'].get('independent_method_systems', {})
check('DIAO_HOU QTBJ有独立体系', tiaohou_systems.get('QTBJ', {}).get('has_independent_system') == True)

# 病药: 只有SFTK有完整独立体系
bingyao_systems = META_DEFINITIONS['BING_YAO'].get('independent_method_systems', {})
check('BING_YAO SFTK有独立体系', bingyao_systems.get('SFTK', {}).get('has_independent_system') == True)

# 用神: 四部以上各有独立体系
yongshen_systems = META_DEFINITIONS['YONG_SHEN'].get('independent_method_systems', {})
check('YONG_SHEN PZZQ有独立体系', yongshen_systems.get('PZZQ', {}).get('has_independent_system') == True)
check('YONG_SHEN QTBJ有独立体系', yongshen_systems.get('QTBJ', {}).get('has_independent_system') == True)
check('YONG_SHEN SFTK有独立体系', yongshen_systems.get('SFTK', {}).get('has_independent_system') == True)
check('YONG_SHEN DTS有独立体系', yongshen_systems.get('DTS', {}).get('has_independent_system') == True)

# === 4. 判定依据原文引用完整性 ===
print("\n=== 4. 判定依据原文引用完整性 ===")
for meta_id in EXPECTED_METAS:
    criteria = META_DEFINITIONS[meta_id].get('judgment_criteria', {})
    check(f'{meta_id} 判定依据非空', bool(criteria))
    primary = META_DEFINITIONS[meta_id]['primary_track']
    check(f'{meta_id} 主轨{primary}有判定依据', bool(criteria.get(primary)))

# === 5. 与引擎轨道设计的一致性 ===
print("\n=== 5. 与引擎轨道设计的一致性 ===")
# 引擎用神四轨: 格局(PZZQ)/调候(QTBJ)/病药(SFTK)/体用(DTS)
# Authority Matrix中这四轨都应该有独立体系
check('引擎格局轨PZZQ在矩阵中有独立体系', geju_systems.get('PZZQ', {}).get('has_independent_system') == True)
check('引擎调候轨QTBJ在矩阵中有独立体系', tiaohou_systems.get('QTBJ', {}).get('has_independent_system') == True)
check('引擎病药轨SFTK在矩阵中有独立体系', bingyao_systems.get('SFTK', {}).get('has_independent_system') == True)

# === 6. 函数接口测试 ===
print("\n=== 6. 函数接口测试 ===")
# get_meta_definition
meta = get_meta_definition('WANG_SHUAI')
check('get_meta_definition(WANG_SHUAI)返回非空', bool(meta))
check('get_meta_definition(WANG_SHUAI)meta_name=旺衰', meta.get('meta_name') == '旺衰')

# get_meta_definition 不存在的元
meta_none = get_meta_definition('NOT_EXIST')
check('get_meta_definition(NOT_EXIST)返回None', meta_none is None)

# get_tracks_for_meta
track = get_tracks_for_meta('DIAO_HOU')
check('get_tracks_for_meta(TIAOHOU)primary=QTBJ', track.get('primary') == 'QTBJ')

# get_judgment_criteria
criteria = get_judgment_criteria('BING_YAO')
check('get_judgment_criteria(BINGYAO)返回非空', bool(criteria))
criteria_sftk = get_judgment_criteria('BING_YAO', 'SFTK')
check('get_judgment_criteria(BINGYAO, SFTK)返回非空', bool(criteria_sftk.get('SFTK')))

# get_independent_method_systems
systems = get_independent_method_systems('YONG_SHEN')
check('get_independent_method_systems(YONGSHEN)返回非空', bool(systems))

# get_authority_matrix_summary
summary = get_authority_matrix_summary()
check('get_authority_matrix_summary()返回6元', len(summary) == 6)
check('summary中WANG_SHUAI有name', bool(summary.get('WANG_SHUAI', {}).get('name')))
check('summary中TIAOHOU有has_judgment_criteria=True', summary.get('DIAO_HOU', {}).get('has_judgment_criteria') == True)
check('summary中YONGSHEN有has_independent_method_systems=True', summary.get('YONG_SHEN', {}).get('has_independent_method_systems') == True)

# === 7. CLASSIC_BOOKS完整性 ===
print("\n=== 7. CLASSIC_BOOKS完整性 ===")
EXPECTED_BOOKS = ['PZZQ', 'YHZP', 'DTS', 'QTBJ', 'SFTK', 'SMTH']
for book in EXPECTED_BOOKS:
    check(f'CLASSIC_BOOKS包含{book}', book in CLASSIC_BOOKS)
check('CLASSIC_BOOKS共6部经典', len(CLASSIC_BOOKS) == 6)

# === 总结 ===
print(f"\n{'='*60}")
print(f"Authority Matrix v0.2 单元测试: TOTAL FAILS {fails}")
print(f"{'='*60}")

sys.exit(1 if fails else 0)
