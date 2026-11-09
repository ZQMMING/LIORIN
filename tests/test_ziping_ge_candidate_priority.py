import pytest

from engines.common.yongyao_resolve import resolve_yongyao


@pytest.mark.parametrize('candidates', [['火', '土'], ['土', '火']])
def test_multiple_pattern_candidates_expose_missing_priority(candidates):
    facts = {'day_stem': '甲', 'ge_cheng': {
        'ge': '正官格', 'xi_wx': candidates, 'cheng_bai': 'CHENG',
        'po_ge_hits': [], 'po_ge_evaluation_complete': True}}
    result = resolve_yongyao(facts, {})
    assert result['primary_selection_status'] == 'NOT_EVALUABLE'
    assert set(result['primary_selection_candidates']) == {'火', '土'}
    assert result['primary_medicine'] is None


def test_repeated_identical_pattern_candidate_is_not_ambiguous():
    facts = {'day_stem': '甲', 'ge_cheng': {
        'ge': '正官格', 'xi_wx': ['火', '火'], 'cheng_bai': 'CHENG',
        'po_ge_hits': [], 'po_ge_evaluation_complete': True}}
    result = resolve_yongyao(facts, {})
    assert result['primary_selection_status'] == 'SINGLE_CANDIDATE'
    assert result['primary_selection_candidates'] == ['火']


@pytest.mark.parametrize('candidates', [['火', '土'], ['土', '火']])
def test_ge_yong_decides_not_unranked_candidates(candidates):
    # 无四柱实体的合成 facts 不派生格用神(V7.182 门控); 多喜神仍不按列表首项升格。
    facts = {'day_stem': '甲', 'daymaster_element': '木', 'ge_cheng': {
        'ge': '正官格', 'xi_wx': candidates, 'cheng_bai': 'CHENG',
        'po_ge_hits': [], 'po_ge_evaluation_complete': True,
        'po_ge': [{'type': '组合', 'match': 'ANY', 'required': ['正财']}]}}
    result = resolve_yongyao(facts, {})
    assert result['primary_selection_status'] == 'NOT_EVALUABLE'
    assert result['primary_medicine'] is None
    assert set(result['primary_selection_candidates']) == set(candidates)


@pytest.mark.parametrize('field', ['xi_wx', 'zhi_wx', 'hua_wx'])
@pytest.mark.parametrize('value', ['火土', ['火', '未知'], [['火']], {'火': True}])
def test_malformed_pattern_elements_do_not_become_medicine(field, value):
    facts = {'day_stem': '甲', 'ge_cheng': {
        'ge': '正官格', 'cheng_bai': 'CHENG', 'po_ge_hits': [],
        'po_ge_evaluation_complete': True, field: value}}
    result = resolve_yongyao(facts, {})
    assert result['state'] == 'PATTERN_ELEMENTS_NOT_EVALUABLE'
    assert result['primary_medicine'] is None
    assert result['invalid_pattern_element_fields'] == [field]
    assert not result['xiji_xian']['xi_wx']


@pytest.mark.parametrize('date,expected_wuxing', [
    # 1980-07-15: 建禄月劫「同财格」(透财而逢食伤, PZZQ L1142) → 格用神=财(水)
    ((1980, 7, 15, 12), '水'),
    # 1981-03-15: 伤官格佩印(印透+官杀藏), 按 PZZQ 伤官佩印取印(金), 非喜神列表首项
    ((1981, 3, 15, 12), '金'),
])
def test_production_bridge_does_not_promote_unranked_candidates(date, expected_wuxing):
    """未排序候选不得升格; 仅原典明文定格的形态(建禄月劫/阳刃)可按格用神裁定。"""
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.reasoning.judgment import JudgmentConclusion
    from tongshu.reasoning.ziping_bridge import _engines_p0_synthesis

    chart = BaziEngine().compute(date, gender='male')
    pillars = {pos: list(gz) for pos, gz in chart.get_pillars_chinese().items()}
    result = production_entry(FrozenCanonicalBaziChart(pillars))
    medicine = result['zhenglun']['yongyao']
    assert medicine['primary_selection_status'] == 'SINGLE_CANDIDATE'
    assert len(medicine['primary_selection_candidates']) > 1
    assert medicine['primary_medicine']['wuxing'] == expected_wuxing
    assert '格局用神' in medicine['primary_medicine']['function']
    assert _engines_p0_synthesis(result).yongshen.conclusion == JudgmentConclusion.PRIMARY


@pytest.mark.parametrize('ambiguous_side', ['base', 'step'])
def test_transit_diff_does_not_compare_unranked_medicine(ambiguous_side):
    from engines.common.suiyun_validate import diff_chain

    def chain(element):
        return {'debate': {'selection_verification': 'ENGINE_DEFINED',
                           'primary_bing': {'bing_id': 'x'}},
                'bingyao': {'bing_list': []},
                'yongyao': {'state': 'GE_FALLBACK',
                            'primary_medicine': {'wuxing': element, 'blocked': {'state': '合绊'}}}}

    base, step = chain('火'), chain('土')
    (base if ambiguous_side == 'base' else step)['yongyao']['primary_selection_status'] = 'NOT_EVALUABLE'
    difference = diff_chain(base, step)
    assert difference[f'{ambiguous_side}_medicine_wx'] is None
    assert difference['primary_medicine_changed'] is None
    assert difference['new_block'] is None
    assert difference['block_released'] is None


def test_transit_diff_preserves_invalid_pattern_elements_as_unknown():
    from engines.common.suiyun_validate import diff_chain

    base = {'debate': {'selection_verification': 'ENGINE_DEFINED'},
            'bingyao': {'bing_list': []},
            'yongyao': {'state': 'PATTERN_ELEMENTS_NOT_EVALUABLE', 'primary_medicine': None}}
    step = {'debate': {'selection_verification': 'ENGINE_DEFINED'},
            'bingyao': {'bing_list': []},
            'yongyao': {'state': 'GE_FALLBACK', 'primary_medicine': {'wuxing': '火'}}}
    difference = diff_chain(base, step)
    assert difference['primary_medicine_changed'] is None
    assert difference['new_block'] is None
    assert difference['block_released'] is None


@pytest.mark.parametrize('verification', [None, '', 'UNKNOWN', 'FUTURE_STATE'])
def test_transit_rejects_missing_or_unrecognized_primary_disease_status(verification):
    from engines.common.suiyun_validate import diff_chain

    def chain(status):
        return {'debate': {'selection_verification': status,
                           'primary_bing': {'bing_id': 'candidate', 'bing_wx': '火'}},
                'bingyao': {'bing_list': []}, 'yongyao': {'state': 'YONGYAO_RESOLVED',
                'primary_medicine': {'wuxing': '水'}}}

    diff = diff_chain(chain(verification), chain('ENGINE_DEFINED'))
    assert diff['base_primary'] is None
    assert diff['primary_bing_changed'] is None
    assert diff['base_medicine_wx'] is None
    assert diff['primary_medicine_changed'] is None


def test_transit_verdict_does_not_use_unknown_primary_disease_status():
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry
    from engines.common.suiyun_validate import validate_suiyun

    pillars = {'year': ['辛', '未'], 'month': ['庚', '寅'],
               'day': ['壬', '午'], 'hour': ['庚', '戌']}
    natal = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    natal['zhenglun']['debate']['selection_verification'] = 'FUTURE_STATE'
    step = validate_suiyun(pillars, natal, ['甲辰'])['dayun_steps'][0]
    assert step['diff']['base_primary'] is None
    assert step['verdict']['status'] == 'NOT_EVALUABLE'
    assert not any('主病' in item for item in step['verdict']['good'])


@pytest.mark.parametrize(('base_medicine', 'step_medicine'), [
    ({'wuxing': '水', 'blocked': {'state': '合绊'}}, {'wuxing': '火'}),
    ({'wuxing': '火'}, {'wuxing': '水', 'blocked': {'state': '合绊'}}),
    ({'wuxing': '火', 'candidate_stem': '丙', 'blocked': {'state': '合绊'}},
     {'wuxing': '火', 'candidate_stem': '丁'}),
])
def test_medicine_replacement_does_not_imply_block_change(base_medicine, step_medicine):
    from engines.common.suiyun_validate import diff_chain

    def chain(medicine):
        return {'debate': {'selection_verification': 'ENGINE_DEFINED'},
                'bingyao': {'bing_list': []},
                'yongyao': {'state': 'YONGYAO_RESOLVED', 'primary_medicine': medicine}}

    difference = diff_chain(chain(base_medicine), chain(step_medicine))
    assert difference['block_released'] is None
    assert difference['new_block'] is None


def test_same_medicine_can_show_release_of_block():
    from engines.common.suiyun_validate import diff_chain

    def chain(blocked):
        return {'debate': {'selection_verification': 'ENGINE_DEFINED'},
                'bingyao': {'bing_list': []}, 'yongyao': {'state': 'YONGYAO_RESOLVED',
                'primary_medicine': {'wuxing': '火', 'blocked': blocked}}}

    difference = diff_chain(chain({'state': '合绊'}), chain(None))
    assert difference['block_released'] is True
    assert difference['new_block'] is False


@pytest.mark.parametrize(('base_medicine', 'step_medicine', 'changed'), [
    ({'wuxing': '火', 'candidate_stem': '丙'}, {'wuxing': '火', 'candidate_stem': '丁'}, True),
    ({'wuxing': '火', 'candidate_stem': '丙'}, {'wuxing': '火', 'candidate_stem': '丙'}, False),
    ({'wuxing': '火', 'candidate_stem': '丙'}, {'wuxing': '火'}, None),
    ({'wuxing': '火'}, {'wuxing': '水', 'candidate_stem': '癸'}, True),
])
def test_medicine_change_respects_element_and_candidate_stem(base_medicine, step_medicine, changed):
    from engines.common.suiyun_validate import diff_chain

    def chain(medicine):
        return {'debate': {'selection_verification': 'ENGINE_DEFINED'},
                'bingyao': {'bing_list': []},
                'yongyao': {'state': 'YONGYAO_RESOLVED', 'primary_medicine': medicine}}

    assert diff_chain(chain(base_medicine), chain(step_medicine))['primary_medicine_changed'] is changed


def test_actual_independent_pattern_medicine_is_available_without_primary_disease():
    from engines.common.suiyun_validate import base_chain_from_result, diff_chain
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry
    from tongshu.engines.bazi_engine import BaziEngine

    chart = BaziEngine().compute((1980, 4, 15, 12), gender='male')
    pillars = {pos: list(gz) for pos, gz in chart.get_pillars_chinese().items()}
    result = production_entry(FrozenCanonicalBaziChart(pillars))
    base = base_chain_from_result(result)
    assert base['debate']['selection_verification'] == 'NOT_APPLICABLE'
    assert base['yongyao']['primary_selection_status'] == 'SINGLE_CANDIDATE'
    difference = diff_chain(base, base)
    assert difference['base_medicine_wx'] == base['yongyao']['primary_medicine']['wuxing']
    assert difference['primary_medicine_changed'] is False
    assert difference['primary_bing_changed'] is None


@pytest.mark.parametrize('medicine', [None, {}, {'wuxing': '未知'},
    {'wuxing': '火', 'stem_equivalence_status': 'NOT_EVALUABLE'},
    {'wuxing': '火', 'candidate_source_verification': 'SOURCE_VERSION_CONFLICT'}])
def test_transit_does_not_compare_absent_or_unverified_medicine(medicine):
    from engines.common.suiyun_validate import diff_chain

    def chain(value):
        return {'debate': {'selection_verification': 'ENGINE_DEFINED'},
                'bingyao': {'bing_list': []},
                'yongyao': {'state': 'YONGYAO_RESOLVED', 'primary_medicine': value}}

    difference = diff_chain(chain(medicine), chain({'wuxing': '水'}))
    assert difference['base_medicine_wx'] is None
    assert difference['primary_medicine_changed'] is None
    assert difference['new_block'] is None
    assert difference['block_released'] is None


def test_transit_verdict_does_not_treat_unranked_candidate_as_medicine_root():
    from engines.common.suiyun_validate import (base_chain_from_result, element_power_tier,
                                                run_chain_on, verdict_step)
    from engines.production_entry import FrozenCanonicalBaziChart, production_entry

    pillars = {'year': ['辛', '未'], 'month': ['庚', '寅'],
               'day': ['壬', '午'], 'hour': ['庚', '戌']}
    natal = production_entry(FrozenCanonicalBaziChart(pillars=pillars))
    base = base_chain_from_result(natal)
    base['debate']['selection_verification'] = 'ENGINE_DEFINED'
    base['yongyao'] = {'state': 'GE_FALLBACK', 'primary_selection_status': 'NOT_EVALUABLE',
                       'primary_medicine': {'wuxing': '土'}}
    step = run_chain_on(pillars, natal['engine_result'], [['甲', '辰']], natal['l1_result']['queries'])
    tier = element_power_tier(natal['engine_result']['wuxing_power'], '水')
    verdict = verdict_step(pillars, base, step, [['甲', '辰']], tier)
    assert verdict['status'] == 'NOT_EVALUABLE'
    assert not any('冲拔主药根' in item for item in verdict['bad'])
    assert any(item['type'] == '用药状态未核验' for item in verdict['structural_candidates'])
