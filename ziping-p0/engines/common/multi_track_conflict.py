# -*- coding: utf-8 -*-
"""多轨冲突标注层 v0.1.
按 Authority Matrix v0.1 要求: 多轨输出冲突保留, 不强行统一.
统一处理多轨输出的冲突识别和标注.
不裁决, 只标注冲突类型和涉及轨道.
"""
from typing import Dict, List, Any, Optional, Set


# 冲突类型枚举
CONFLICT_TYPES = {
    'GEJU_VS_DIAOHOU': '格局vs调候',
    'GEJU_VS_BINGYAO': '格局vs病药',
    'GEJU_VS_TIYONG': '格局vs体用',
    'DIAOHOU_VS_BINGYAO': '调候vs病药',
    'DIAOHOU_VS_TIYONG': '调候vs体用',
    'BINGYAO_VS_TIYONG': '病药vs体用',
    'MULTI_TRACK': '多轨冲突',
    'NO_CONFLICT': '无冲突',
}


def _get_track_first_element(track_output: Dict[str, Any]) -> Optional[str]:
    """获取轨道的首选候选元素."""
    candidates = track_output.get('candidates', [])
    if not candidates:
        return None
    # 按priority排序, 取第一个
    sorted_candidates = sorted(candidates, key=lambda x: x.get('priority', 999))
    return sorted_candidates[0].get('element')


def _get_track_elements(track_output: Dict[str, Any]) -> Set[str]:
    """获取轨道的所有候选元素."""
    candidates = track_output.get('candidates', [])
    return {c.get('element', '') for c in candidates if c.get('element')}


def detect_conflict(tracks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """检测多轨输出的冲突.
    输入: tracks = {track_id: track_output}
    输出: 冲突信息(不裁决, 只标注)
    """
    # 只看激活的轨道
    activated_tracks = {
        tid: tout for tid, tout in tracks.items()
        if tout.get('activated', False) and tout.get('candidates')
    }

    if len(activated_tracks) < 2:
        return {
            'has_conflict': False,
            'conflict_type': CONFLICT_TYPES['NO_CONFLICT'],
            'tracks_involved': [],
            'resolution': '单轨或无候选, 无冲突',
            'display_note': '',
        }

    # 获取各轨道的首选候选元素
    first_elements = {}
    for tid, tout in activated_tracks.items():
        elem = _get_track_first_element(tout)
        if elem:
            first_elements[tid] = elem

    if len(first_elements) < 2:
        return {
            'has_conflict': False,
            'conflict_type': CONFLICT_TYPES['NO_CONFLICT'],
            'tracks_involved': [],
            'resolution': '有效候选不足, 无冲突',
            'display_note': '',
        }

    # 检查是否所有轨道的首选候选都相同
    unique_elements = set(first_elements.values())
    if len(unique_elements) == 1:
        return {
            'has_conflict': False,
            'conflict_type': CONFLICT_TYPES['NO_CONFLICT'],
            'tracks_involved': list(first_elements.keys()),
            'resolution': '多轨首选候选一致, 无冲突',
            'display_note': f'所有轨道首选候选均为 {list(unique_elements)[0]}',
        }

    # 存在冲突, 确定冲突类型
    track_ids = list(first_elements.keys())
    conflict_type = _determine_conflict_type(track_ids)

    # 构建展示说明
    display_parts = []
    for tid in track_ids:
        track_name = activated_tracks[tid].get('track_name', tid)
        elem = first_elements[tid]
        display_parts.append(f'若按{track_name}则用{elem}')
    display_note = '；'.join(display_parts) + '，请结合命局整体判断'

    return {
        'has_conflict': True,
        'conflict_type': conflict_type,
        'tracks_involved': track_ids,
        'track_elements': first_elements,
        'resolution': '保留多解, 不裁决',
        'display_note': display_note,
        'authority_matrix_note': 'Authority Matrix v0.1: 冲突保留不强行统一. '
                                  '按命理元分Primary/Secondary/Alternate, 不跨经典统一优先级.',
    }


def _determine_conflict_type(track_ids: List[str]) -> str:
    """根据涉及的轨道组合确定冲突类型."""
    track_set = set(track_ids)

    # 两轨冲突
    if len(track_set) == 2:
        if 'ZPZQ' in track_set and 'QTBJ' in track_set:
            return CONFLICT_TYPES['GEJU_VS_DIAOHOU']
        if 'ZPZQ' in track_set and 'SFTK' in track_set:
            return CONFLICT_TYPES['GEJU_VS_BINGYAO']
        if 'ZPZQ' in track_set and 'DTS' in track_set:
            return CONFLICT_TYPES['GEJU_VS_TIYONG']
        if 'QTBJ' in track_set and 'SFTK' in track_set:
            return CONFLICT_TYPES['DIAOHOU_VS_BINGYAO']
        if 'QTBJ' in track_set and 'DTS' in track_set:
            return CONFLICT_TYPES['DIAOHOU_VS_TIYONG']
        if 'SFTK' in track_set and 'DTS' in track_set:
            return CONFLICT_TYPES['BINGYAO_VS_TIYONG']

    # 多轨冲突
    return CONFLICT_TYPES['MULTI_TRACK']


def build_multi_track_output(
    meta_id: str,
    tracks: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """构建多轨输出(含冲突标注).
    输入: meta_id(命理元ID), tracks(各轨道输出)
    输出: 多轨输出+冲突标注
    """
    conflict = detect_conflict(tracks)

    # 构建候选集并集(用于命中率@K评估)
    all_candidates = []
    for tid, tout in tracks.items():
        if tout.get('activated', False):
            for c in tout.get('candidates', []):
                all_candidates.append({
                    'element': c.get('element'),
                    'track_id': tid,
                    'track_name': tout.get('track_name', tid),
                    'priority': c.get('priority'),
                    'evidence': c.get('evidence', ''),
                    'boundary': c.get('boundary', ''),
                })

    return {
        'meta_id': meta_id,
        'tracks': tracks,
        'conflict': conflict,
        'all_candidates': all_candidates,
        'candidate_elements': list({c['element'] for c in all_candidates if c.get('element')}),
        'authority_matrix_version': 'v0.1',
        'boundary_note': '多轨输出, 冲突保留不裁决. '
                         '不输出单一的最终答案. '
                         '命中率@K = 标准答案在候选集中的比例. '
                         'Authority Matrix v0.1: 按命理元分Primary/Secondary/Alternate.',
    }


def hit_at_k(candidate_elements: List[str], standard_answer: str) -> bool:
    """计算命中率@K: 标准答案是否在候选集中."""
    return standard_answer in candidate_elements
