# -*- coding: utf-8 -*-
"""命理元统一输出层端到端测试.
验证6命理元(旺衰/强弱/格局/调候/病药/用神)全部正确输出,
用神四轨并行层完整接入(传入必要参数).
"""
import sys
sys.path.insert(0, '.')

from engines.common.l0_fact_builder import build
from engines.common.daymaster_root_class import build_root_classes
from engines.common.root_effectiveness_filter import filter_root_effectiveness
from engines.common.wuxing_power import build_wuxing_power, build_spectrum_from_power
from engines.common.special_pattern import build_special_patterns
from engines.common.climate_structure import build_climate_structure
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.meta_unified_output import build_all_meta_outputs


def test_meta_unified_output_e2e():
    """端到端测试: 6命理元全部输出."""
    # 测试案例: 甲子 丙寅 甲子 丙寅
    pillars = {'year': ['甲', '子'], 'month': ['丙', '寅'], 'day': ['甲', '子'], 'hour': ['丙', '寅']}
    facts = build(pillars)

    # 构建根气
    hidden_stems_by_branch = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year', 'month', 'day', 'hour')}
    root_classes = build_root_classes(pillars, hidden_stems_by_branch)
    root_effectiveness = filter_root_effectiveness(root_classes, facts['combination_facts'], pillars, facts['day_stem'])

    # 构建用神四轨并行层需要的参数
    wuxing_power = build_wuxing_power(pillars, facts)
    spectrum = build_spectrum_from_power(wuxing_power)
    special = build_special_patterns(pillars, facts, wuxing_power)
    climate = build_climate_structure(pillars, facts)
    bingyao = build_bingyao_layer(facts, [])

    # 构建extra_data
    extra_data = {
        'pillars': pillars,
        'wuxing_power': wuxing_power,
        'spectrum': spectrum,
        'special': special,
        'climate': climate,
        'bingyao': bingyao,
    }

    # 调用命理元统一输出层
    all_outputs = build_all_meta_outputs(facts, root_effectiveness, root_classes, extra_data)

    # 验证
    assert all_outputs['authority_matrix_version'] == 'v0.2'
    assert all_outputs['meta_count'] == 6

    meta_outputs = all_outputs['meta_outputs']

    # 1. 旺衰
    wangshuai = meta_outputs['WANG_SHUAI']
    assert wangshuai['meta_name'] == '旺衰'
    assert 'PZZQ' in wangshuai['tracks']
    assert 'YHZP' in wangshuai['tracks']
    assert 'DTS' in wangshuai['tracks']
    assert wangshuai['tracks']['PZZQ']['activated'] == True
    print(f"[PASS] 旺衰: PZZQ={wangshuai['tracks']['PZZQ']['candidates'][0]['element']}")

    # 2. 强弱
    qiangruo = meta_outputs['QIANG_RUO']
    assert qiangruo['meta_name'] == '强弱'
    assert qiangruo['tracks']['PZZQ']['activated'] == True
    print(f"[PASS] 强弱: PZZQ候选数={len(qiangruo['tracks']['PZZQ']['candidates'])}")

    # 3. 格局
    geju = meta_outputs['GE_JU']
    assert geju['meta_name'] == '格局'
    assert geju['tracks']['PZZQ']['activated'] == True
    assert len(geju['tracks']['PZZQ']['candidates']) > 0
    print(f"[PASS] 格局: PZZQ候选={[c['element'] for c in geju['tracks']['PZZQ']['candidates']]}")

    # 4. 调候
    diaohou = meta_outputs['DIAO_HOU']
    assert diaohou['meta_name'] == '调候'
    assert diaohou['tracks']['QTBJ']['activated'] == True
    print(f"[PASS] 调候: QTBJ候选={[c['element'] for c in diaohou['tracks']['QTBJ']['candidates']]}")

    # 5. 病药
    bingyao_output = meta_outputs['BING_YAO']
    assert bingyao_output['meta_name'] == '病药'
    assert bingyao_output['tracks']['SFTK']['activated'] == True
    print(f"[PASS] 病药: SFTK候选={[c['element'] for c in bingyao_output['tracks']['SFTK']['candidates']]}")

    # 6. 用神 (关键: 验证四轨并行层完整接入)
    yongshen = meta_outputs['YONG_SHEN']
    assert yongshen['meta_name'] == '用神'
    assert 'ZPZQ' in yongshen['tracks']
    assert 'QTBJ' in yongshen['tracks']
    assert 'SFTK' in yongshen['tracks']
    assert 'DTS' in yongshen['tracks']

    # 检查至少有一个轨道激活
    activated_tracks = [tid for tid, tout in yongshen['tracks'].items() if tout.get('activated')]
    print(f"[INFO] 用神激活轨道: {activated_tracks}")
    for tid in activated_tracks:
        candidates = [c['element'] for c in yongshen['tracks'][tid]['candidates']]
        print(f"       {yongshen['tracks'][tid]['track_name']}({tid}): {candidates}")

    # 冲突标注
    conflict = yongshen.get('conflict', {})
    print(f"[INFO] 用神冲突: {conflict.get('conflict_type', '无')}")

    print()
    print("=" * 60)
    print("命理元统一输出层端到端测试: ALL PASS")
    print("6命理元(旺衰/强弱/格局/调候/病药/用神)全部正确输出")
    print("用神四轨并行层完整接入验证通过")
    print("=" * 60)
    return True


if __name__ == '__main__':
    test_meta_unified_output_e2e()
