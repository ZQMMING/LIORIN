# -*- coding: utf-8 -*-
"""P160 相神静态配对候选 · 第四刀（只读枚举, 不判成相/破相/有情/成格）

原典:
  PZZQ-007-004 論相神緊要:
    「月令既得用神, 則別位亦必有相, 若君之有相, 輔我用神者是也。
     如官逢財生, 則官為用、財為相; 財旺生官, 則財為用、官為相;
     煞逢食制, 則煞為用、食為相。」
  PZZQ-005-007 論用神(順逆用護制):
    財喜食以相生、生官以護財; 官喜透財以相生、生印以護官;
    印喜官煞以相生、劫財以護印; 食喜生財以護食;
    煞喜食以制伏; 傷喜佩印以制伏、生財以化傷;
    刃喜煞以制伏; 月劫喜透官以制伏、利用財以化劫。

只做: 格神(用神)確定後, 按原典靜態配對枚舉「誰有資格當相」+ 該十神在盤中存在性。
硬禁(EFFECT, 原典雖有但本刀不授權):
  - 不判「相神無破/有傷」→ 不判成格/敗格;
  - 不判有情無情/有力無力(格局高低);
  - 不判身強弱(食格「身旺以相生」不納入);
  - 不選唯一相神, 多候選並列;
  - 不接 production_entry。
"""
from typing import Any, Dict, List
from engines.common.yongshen_geju import build_yongshen_geju

_EVIDENCE = ['PZZQ-007-004', 'PZZQ-005-007']

# 格神(十神) -> 相神角色候選十神列表
# 依 PZZQ-005-007 順逆用護制 + PZZQ-007-004 明舉三式
_XIANG_ROLES: Dict[str, List[str]] = {
    # 順用(善): 順其性而生護
    '正财': ['食神', '伤官', '正官'],          # 財逢食生 / 財旺生官
    '偏财': ['食神', '伤官', '正官'],
    '正官': ['正财', '偏财', '正印', '偏印'],    # 官逢財生 / 官逢印護
    '正印': ['正官', '七杀', '劫财', '比肩'],    # 印逢官煞生 / 劫財護印
    '偏印': ['正官', '七杀', '劫财', '比肩'],
    '食神': ['正财', '偏财'],                  # 食逢財生(身旺以相生涉強弱, 不錄)
    # 逆用(不善): 制伏/化泄
    '七杀': ['食神'],                          # 煞逢食制
    '伤官': ['正印', '偏印', '正财', '偏财'],    # 傷官佩印 / 傷官生財
    '比肩': ['正官', '七杀', '正财', '偏财'],    # 月劫透官制 / 用財化劫
    '劫财': ['正官', '七杀', '正财', '偏财'],
    '阳刃': ['七杀', '正官'],                  # 刃喜煞制(陽刃以七殺為主, 官亦制刃)
}


def _collect_ten_gods(facts: Dict[str, Any]) -> Dict[str, Dict[str, bool]]:
    """聚合盤中十神存在性: stem_present=天干有, root_present=地支藏干有。"""
    agg: Dict[str, Dict[str, bool]] = {}
    for m in facts.get('ten_god_members', []):
        tg = m.get('ten_god')
        if not tg:
            continue
        slot = agg.setdefault(tg, {'stem_present': False, 'root_present': False})
        if m.get('type') == 'stem':
            slot['stem_present'] = True
        else:
            slot['root_present'] = True
    return agg


def build_xiang_shen_candidates(facts: Dict[str, Any]) -> Dict[str, Any]:
    """只枚舉相神角色候選, 不判成相/破相/有情/成格。"""
    geshen = build_yongshen_geju(facts)
    tg_presence = _collect_ten_gods(facts)

    candidates: List[Dict[str, Any]] = []
    for gs in geshen.get('ge_shen_candidates', []):
        # 相神配对只处理月令格局候选(本气/透干), 不处理非月令透干候选
        _src = gs.get('candidate_source', '')
        if _src and _src not in ('BENQI', 'TRANSPARENT_STEM'):
            continue
        gs_tg = gs.get('ten_god')
        gs_id = gs.get('candidate_id')
        roles = _XIANG_ROLES.get(gs_tg, [])
        for role_tg in roles:
            pres = tg_presence.get(role_tg, {'stem_present': False, 'root_present': False})
            candidates.append({
                'candidate_id': 'XIANG-%s-%s' % (gs_id, role_tg),
                'ge_shen': gs_tg,
                'ge_shen_candidate_id': gs_id,
                'xiang_role': role_tg,
                'stem_present': bool(pres['stem_present']),
                'root_present': bool(pres['root_present']),
                'present_in_chart': bool(pres['stem_present'] or pres['root_present']),
                'evidence_refs': list(_EVIDENCE),
                'status': 'CANDIDATE',
            })

    return {
        'module': 'XIANG_SHEN_CANDIDATES',
        'patch': 'P160-XIANG-4',
        'namespace': 'PZZQ.use_god',
        'namespace_type': 'pattern',
        'xiang_shen_candidates': candidates,
        'candidate_count': len(candidates),
        'judgment_status': 'XIANG_ROLE_CANDIDATE_ONLY',
        'boundary_note': (
            '僅枚舉「格神→誰有資格當相」的原典靜態配對 + 該十神盤中存在性; '
            '多候選並列不選唯一; 不判相神無破/有傷, 不判成格/敗格; '
            '不判有情無情/有力無力(格局高低); 不判身強弱; 相神≠已成相; 不接 production_entry'
        ),
        'evidence_refs': list(_EVIDENCE),
    }
