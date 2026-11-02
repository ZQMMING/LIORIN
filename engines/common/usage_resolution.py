"""Source-scoped usage summary, without voting or inventing a unique yongshen.

This is ENGINEERING_STRUCTURE: it classifies disagreement in already calculated
outputs. A candidate is not proof of efficacy; this view does not validate rules.
"""
from copy import deepcopy

SOURCE_NAMES = {'ZPZQ': 'PZZQ', 'QTBJ': 'QTBJ', 'SFTK': 'SFTK', 'DTS': 'DTS'}


def summarize_usage(tracks_result, medicine):
    legacy = deepcopy(medicine.get('xiji_xian') or {})
    legacy_ji = set(legacy.get('ji_wx') or [])
    legacy_xi = list(legacy.get('xi_wx') or [])
    sources = {}
    conditional = {}
    for track_id, track in (tracks_result.get('tracks') or {}).items():
        source = SOURCE_NAMES.get(track_id, track_id)
        ranked = track.get('rank_status') != 'UNDETERMINED'
        candidates = deepcopy(track.get('candidates') or [])
        sources[source] = {'activated': track.get('activated', False),
                           'candidates': candidates,
                           'rank_status': track.get('rank_status', 'CANDIDATE_ORDER'),
                           'scope': track.get('track_name'),
                           'evidence_grade': track.get('evidence_grade'),
                           'status': 'COMPUTED_CANDIDATES_NOT_VALIDATED'}
        if not track.get('activated') or not ranked:
            continue
        for c in candidates:
            wx = c.get('element')
            if wx in legacy_ji:
                conditional.setdefault(wx, []).append({
                    'source': source, 'stem': c.get('stem_element'),
                    'role': 'SOURCE_CANDIDATE_VS_LEGACY_TABOO',
                    'evidence': c.get('evidence'), 'boundary': c.get('boundary')})
    # These books are present in the foundation; do not pretend they execute an
    # independent medicine track in this four-track implementation.
    for source in ('YHZP', 'SMTH'):
        sources[source] = {'status': 'NO_INDEPENDENT_USAGE_TRACK', 'candidates': []}
    conditional_wx = [wx for wx in '木火土金水' if wx in conditional]
    return {'status': 'PROVISIONAL', 'method': 'ENGINEERING_STRUCTURE_NO_VOTING',
            'sources': sources,
            'summary': {
                'xi_wx': [wx for wx in '木火土金水' if wx in legacy_xi and wx not in conditional],
                'ji_wx': [wx for wx in legacy.get('ji_wx', []) if wx not in conditional],
                'conditional_wx': conditional_wx,
                'xian_wx': [wx for wx in legacy.get('xian_wx', []) if wx not in conditional],
                'classification_scope': '候选与原喜忌的条件归类，非效用已验证'},
            'conditional_evidence': conditional,
            'legacy_element_view': legacy,
            'primary_scope': '各轨分别取用，不合成唯一第一用神',
            'transit_scope': '原岁运裁决为病药规则结果，不代表六书综合裁决'}
