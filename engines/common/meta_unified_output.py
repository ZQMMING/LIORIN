# -*- coding: utf-8 -*-
"""命理元统一输出层 v0.1.
按 Authority Matrix v0.1 轨道归属, 统一输出各命理元的多轨结果.
命理元: 旺衰/强弱/格局/调候/病药/用神
每个命理元按 Primary/Secondary/Alternate 分轨输出, 冲突保留不裁决.
不输出单一的最终答案, 不做综合裁决.
"""
from typing import Dict, List, Any, Optional
from engines.common.authority_matrix import (
    META_DEFINITIONS, get_meta_definition, get_tracks_for_meta,
    AUTHORITY_MATRIX_VERSION, AUTHORITY_MATRIX_BOUNDARY_NOTE,
)
from engines.common.multi_track_conflict import (
    detect_conflict, build_multi_track_output, hit_at_k,
)
from engines.common.wangshuai_structure import build_wangshuai_structure


def build_meta_output(
    meta_id: str,
    facts: Dict[str, Any],
    root_effectiveness: Dict[str, Any] = None,
    root_classes: Dict[str, Any] = None,
    extra_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """构建单个命理元的多轨输出.
    输入: meta_id, facts, 其他必要数据
    输出: 多轨输出+冲突标注
    """
    meta = get_meta_definition(meta_id)
    if not meta:
        return {'error': f'未知命理元: {meta_id}'}

    tracks = {}

    # 根据命理元类型, 调用对应的轨道构建函数
    if meta_id == 'WANG_SHUAI':
        tracks = _build_wangshuai_tracks(facts, root_effectiveness, root_classes)
    elif meta_id == 'QIANG_RUO':
        tracks = _build_qiangruo_tracks(facts, root_effectiveness, root_classes)
    elif meta_id == 'GE_JU':
        tracks = _build_geju_tracks(facts, extra_data)
    elif meta_id == 'DIAO_HOU':
        tracks = _build_diaohou_tracks(facts, extra_data)
    elif meta_id == 'BING_YAO':
        tracks = _build_bingyao_tracks(facts, extra_data)
    elif meta_id == 'YONG_SHEN':
        tracks = _build_yongshen_tracks(facts, extra_data)

    # 构建多轨输出(含冲突标注)
    output = build_multi_track_output(meta_id, tracks)
    output['meta_name'] = meta['meta_name']
    output['definition'] = meta['definition']
    output['boundary_note'] = meta['boundary_note']
    return output


def _track_output(track_id, track_name, activated, candidates=None, evidence_grade='CANDIDATE', note=''):
    """统一轨道输出结构."""
    return {
        'track_id': track_id,
        'track_name': track_name,
        'activated': activated,
        'candidates': candidates or [],
        'evidence_grade': evidence_grade,
        'note': note,
    }


def _candidate(element, priority, evidence='', boundary=''):
    """统一候选结构."""
    return {
        'element': element,
        'priority': priority,
        'evidence': evidence,
        'boundary': boundary,
    }


# ============================================================
# 旺衰轨道 (Primary=PZZQ, Secondary=YHZP, Alternate=DTS)
# ============================================================
def _build_wangshuai_tracks(facts, root_effectiveness, root_classes):
    """构建旺衰多轨输出.
    旺衰 = 得令/失令(月令维度), 不回答身强/身弱.
    """
    tracks = {}

    # PZZQ轨: 子平真诠 - 得时不旺失时不弱, 活看月令
    month_supports = facts.get('month_supports_daymaster', False)
    month_qi_ten_god = facts.get('month_qi_ten_god', '')
    in_season = month_supports or month_qi_ten_god in ('比肩', '劫财', '正印', '偏印')
    pzzq_state = '得令' if in_season else ('失令' if month_qi_ten_god else '未知')
    tracks['PZZQ'] = _track_output(
        'PZZQ', '子平真诠轨', True,
        candidates=[_candidate(pzzq_state, 1, 'PZZQ-论十干得时不旺失时不弱', '旺衰只回答得令/失令, 不回答身强/身弱')],
        note='得时不旺失时不弱, 活看月令',
    )

    # YHZP轨: 渊海子平 - 得令即旺的朴素体系
    yhzp_state = '得令' if in_season else '失令'
    tracks['YHZP'] = _track_output(
        'YHZP', '渊海子平轨', True,
        candidates=[_candidate(yhzp_state, 1, 'YHZP-论旺衰', '朴素得令即旺体系')],
        note='得令即旺的朴素体系',
    )

    # DTS轨: 滴天髓 - 旺衰篇, 五行流通配合
    tracks['DTS'] = _track_output(
        'DTS', '滴天髓轨', True,
        candidates=[_candidate(pzzq_state, 1, 'DTS-旺衰篇', '旺衰不在于日主身强身弱, 而在于五行流通配合')],
        note='五行流通配合视角',
    )

    return tracks


# ============================================================
# 强弱轨道 (Primary=PZZQ, Secondary=YHZP, Alternate=DTS)
# ============================================================
def _build_qiangruo_tracks(facts, root_effectiveness, root_classes):
    """构建强弱多轨输出.
    强弱 = 党众/助寡(力量结构维度), 输出多维结构事实, 不输出综合裁决.
    """
    tracks = {}

    # 使用旺衰/强弱结构层获取多维结构事实
    structure = build_wangshuai_structure(facts, root_effectiveness or {}, root_classes)

    # PZZQ轨: 子平真诠 - 党众为强助寡为弱, 重根/轻根分类
    root_power = structure['root_dimension']['power']
    support_state = structure['support_dimension']['state']
    tracks['PZZQ'] = _track_output(
        'PZZQ', '子平真诠轨', True,
        candidates=[
            _candidate(f'根气={root_power}', 1, 'PZZQ-长生禄旺根之重者', '根气分类'),
            _candidate(f'帮扶={support_state}', 2, 'PZZQ-党众为强助寡为弱', '帮扶状态'),
        ],
        note='党众为强助寡为弱, 重根/轻根分类. 不输出综合强弱裁决.',
    )

    # YHZP轨: 渊海子平 - 身强身弱的朴素判断(得令+得地+得势)
    tracks['YHZP'] = _track_output(
        'YHZP', '渊海子平轨', True,
        candidates=[
            _candidate(f'根气={root_power}', 1, 'YHZP-论身强身弱', '得地维度'),
            _candidate(f'帮扶={support_state}', 2, 'YHZP-论身强身弱', '得势维度'),
        ],
        note='得令+得地+得势的朴素判断. 不输出综合强弱裁决.',
    )

    # DTS轨: 滴天髓 - 体用扶抑, 气势流通
    tracks['DTS'] = _track_output(
        'DTS', '滴天髓轨', True,
        candidates=[
            _candidate(f'根气={root_power}', 1, 'DTS-体用篇', '体用关系'),
            _candidate(f'帮扶={support_state}', 2, 'DTS-气势篇', '气势流通'),
        ],
        note='体用扶抑, 气势流通视角. 不输出综合强弱裁决.',
    )

    return tracks


# ============================================================
# 格局轨道 (Primary=PZZQ, Secondary=YHZP, Alternate=SMTH)
# ============================================================
def _build_geju_tracks(facts, extra_data):
    """构建格局多轨输出.
    格局 = 月令定格, 只输出格神候选和结构识别, 不输出格局成立/格局高低.
    接入 pzzq_producer_v1 (格局候选生产者).
    """
    tracks = {}
    extra = extra_data or {}

    # PZZQ轨: 子平真诠 - 八格体系, 格局成败救应
    pzzq_candidates = []
    try:
        from engines.common.pzzq_producer_v1 import produce_pattern_candidates
        pattern_result = produce_pattern_candidates(facts)
        if isinstance(pattern_result, dict):
            for i, pc in enumerate(pattern_result.get('pattern_candidates', [])[:10]):
                pzzq_candidates.append(_candidate(
                    pc.get('pattern_type', ''),
                    i + 1,
                    f'PZZQ-{pc.get("basis", "")}',
                    '月令定格候选, 不等于格局成立/格局高低',
                ))
    except Exception:
        pass

    # 如果extra_data中提供了格局候选, 也加入
    for pc in extra.get('pzzq_candidates', [])[:3]:
        pzzq_candidates.append(_candidate(pc, len(pzzq_candidates) + 1, 'PZZQ-extra', '格局候选'))

    tracks['PZZQ'] = _track_output(
        'PZZQ', '子平真诠轨',
        bool(pzzq_candidates),
        candidates=pzzq_candidates,
        note='八格体系, 格局成败救应. 格清/配合保持PLACEHOLDER. 只输出格神候选, 不判成格/高低.',
    )

    # YHZP轨: 渊海子平 - 格局基础分类(复用PZZQ候选, 不同视角)
    tracks['YHZP'] = _track_output(
        'YHZP', '渊海子平轨',
        bool(pzzq_candidates),
        candidates=pzzq_candidates[:3],
        note='格局基础分类, 月令取格朴素体系',
    )

    # SMTH轨: 三命通会 - 月令取格, 六格大纲
    tracks['SMTH'] = _track_output(
        'SMTH', '三命通会轨',
        bool(pzzq_candidates),
        candidates=pzzq_candidates[:3],
        note='月令取格, 六格大纲',
    )

    return tracks


# ============================================================
# 调候轨道 (Primary=QTBJ, Secondary=SMTH)
# ============================================================
def _build_diaohou_tracks(facts, extra_data):
    """构建调候多轨输出.
    调候 = 月令气候寒暖燥湿与日干所需调候, 只输出调候候选, 不输出用神最终裁决.
    接入 qtbj_climate_candidates (穷通宝鉴调候候选表).
    """
    tracks = {}
    extra = extra_data or {}

    # QTBJ轨: 穷通宝鉴 - 四时调候, 气候用神
    qtbj_candidate_list = []
    try:
        from engines.common.qtbj_climate_candidates import build_climate_candidates
        climate_result = build_climate_candidates(facts)
        if isinstance(climate_result, dict):
            # 尝试从不同字段提取候选
            for key in ['candidates', 'climate_candidates', 'use_candidates', 'primary_candidates']:
                if key in climate_result:
                    for i, c in enumerate(climate_result[key][:5]):
                        elem = c if isinstance(c, str) else c.get('element', c.get('stem', ''))
                        if elem:
                            qtbj_candidate_list.append(_candidate(
                                elem, i + 1,
                                f'QTBJ-{key}',
                                '调候候选, 不等于用神最终裁决',
                            ))
                    break
    except Exception:
        pass

    # 如果extra_data中提供了调候候选, 也加入
    for i, c in enumerate(extra.get('qtbj_candidates', [])[:3]):
        elem = c if isinstance(c, str) else c.get('element', '')
        if elem:
            qtbj_candidate_list.append(_candidate(elem, len(qtbj_candidate_list) + 1, 'QTBJ-extra', '调候候选'))

    tracks['QTBJ'] = _track_output(
        'QTBJ', '穷通宝鉴轨',
        bool(qtbj_candidate_list),
        candidates=qtbj_candidate_list,
        note='四时调候, 气候用神. D5/T16月令效力修正已接入. 只输出调候候选, 不输出用神最终裁决.',
    )

    # SMTH轨: 三命通会 - 调候基础
    tracks['SMTH'] = _track_output(
        'SMTH', '三命通会轨',
        bool(qtbj_candidate_list),
        candidates=qtbj_candidate_list[:3],
        note='调候基础, 月令气候',
    )

    return tracks


# ============================================================
# 病药轨道 (Primary=SFTK, Secondary=DTS)
# ============================================================
def _build_bingyao_tracks(facts, extra_data):
    """构建病药多轨输出.
    病药 = 命局病机和药神候选, 只输出病机和药神候选, 不输出用神最终裁决.
    接入 bingyao_layer (病药/作用子层).
    """
    tracks = {}
    extra = extra_data or {}

    # SFTK轨: 神峰通考 - 病药体系, 张楠核心思想
    sftk_candidates = []
    try:
        from engines.common.bingyao_layer import build_bingyao_layer
        bingyao_result = build_bingyao_layer(facts, [])
        if isinstance(bingyao_result, dict):
            # 病
            for i, b in enumerate(bingyao_result.get('bing_list', [])[:3]):
                bing_name = b.get('name', b.get('bing_id', ''))
                if bing_name:
                    sftk_candidates.append(_candidate(
                        f'病={bing_name}', i + 1,
                        f'SFTK-{b.get("classic", "病药说")}',
                        '病机诊断, 不等于用神最终裁决',
                    ))
            # 药
            for i, y in enumerate(bingyao_result.get('yao_list', [])[:3]):
                yao_name = y.get('name', y.get('yao_id', ''))
                if yao_name:
                    sftk_candidates.append(_candidate(
                        f'药={yao_name}', len(sftk_candidates) + 1,
                        f'SFTK-{y.get("classic", "病药说")}',
                        '药神候选, 不等于用神最终裁决',
                    ))
    except Exception:
        pass

    # 如果extra_data中提供了病药, 也加入
    bingyao_extra = extra.get('bingyao', {})
    if bingyao_extra.get('bing'):
        sftk_candidates.append(_candidate(f'病={bingyao_extra["bing"]}', len(sftk_candidates) + 1, 'SFTK-extra', '病机'))
    if bingyao_extra.get('yao'):
        sftk_candidates.append(_candidate(f'药={bingyao_extra["yao"]}', len(sftk_candidates) + 1, 'SFTK-extra', '药神'))

    tracks['SFTK'] = _track_output(
        'SFTK', '神峰通考轨',
        bool(sftk_candidates),
        candidates=sftk_candidates,
        note='有病方为贵, 无伤不是奇. bingyao_layer已实现. 只输出病机和药神候选, 不输出用神最终裁决.',
    )

    # DTS轨: 滴天髓 - 病药相关论述
    tracks['DTS'] = _track_output(
        'DTS', '滴天髓轨',
        bool(sftk_candidates),
        candidates=sftk_candidates[:3],
        note='病药相关论述, 体用扶抑视角',
    )

    return tracks


# ============================================================
# 用神轨道 (Primary=PZZQ, Secondary=QTBJ, Alternate=SFTK/DTS)
# ============================================================
def _build_yongshen_tracks(facts, extra_data):
    """构建用神多轨输出.
    用神 = 多轨并行, 冲突保留不裁决. 不输出单一的最终用神.
    接入 yongshen_multi_track (用神四轨并行层).
    """
    tracks = {}
    extra = extra_data or {}

    # 直接使用用神四轨并行层的输出(如果已提供)
    yongshen_tracks = extra.get('yongshen_tracks', {})
    if yongshen_tracks:
        return yongshen_tracks

    # 如果提供了必要参数, 调用用神四轨并行层
    pillars = extra.get('pillars')
    wuxing_power = extra.get('wuxing_power')
    spectrum = extra.get('spectrum')
    special = extra.get('special')
    climate = extra.get('climate')
    bingyao = extra.get('bingyao')

    if pillars and wuxing_power is not None and spectrum is not None and special is not None and climate is not None:
        try:
            from engines.common.yongshen_multi_track import build_yongshen_multi_track
            result = build_yongshen_multi_track(pillars, facts, wuxing_power, spectrum, special, climate, bingyao)
            # 从结果中提取tracks
            if isinstance(result, dict) and 'tracks' in result:
                return result['tracks']
            elif isinstance(result, dict):
                # 可能直接就是tracks字典
                return result
        except Exception as e:
            # 用神四轨并行层调用失败, 构建占位轨道
            pass

    # 否则构建占位轨道
    tracks['ZPZQ'] = _track_output('ZPZQ', '格局轨', False, note='待接入yongshen_multi_track')
    tracks['QTBJ'] = _track_output('QTBJ', '调候轨', False, note='待接入yongshen_multi_track')
    tracks['SFTK'] = _track_output('SFTK', '病药轨', False, note='待接入yongshen_multi_track')
    tracks['DTS'] = _track_output('DTS', '体用轨', False, note='待接入yongshen_multi_track')

    return tracks


def build_all_meta_outputs(
    facts: Dict[str, Any],
    root_effectiveness: Dict[str, Any] = None,
    root_classes: Dict[str, Any] = None,
    extra_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """构建所有命理元的多轨输出.
    输出: 6个命理元的多轨输出汇总
    """
    all_outputs = {}
    for meta_id in META_DEFINITIONS.keys():
        all_outputs[meta_id] = build_meta_output(
            meta_id, facts, root_effectiveness, root_classes, extra_data,
        )

    return {
        'authority_matrix_version': AUTHORITY_MATRIX_VERSION,
        'boundary_note': AUTHORITY_MATRIX_BOUNDARY_NOTE,
        'meta_outputs': all_outputs,
        'meta_count': len(all_outputs),
    }
