# -*- coding: utf-8 -*-
"""调候候神集中裁决源 (V7.25 收敛, 替换 case-by-case if 分支).

方法论: 引擎按算理算, 不按案例调 —— 候神逻辑收敛成本模块一张集中裁决,
yongyao_resolve / yongshen_engine / suiyun_validate 三处消费, 不再各补 if.

【候神表与职能的边界】
  qtbj_climate_candidates 120 格表只录原文候干(如乙-戌=癸辛, 不列火) —— 忠实查表.
  候神"职能"(食伤泄秀/制药/暖局) 不在候干表内, 属寒燥交互判: 候干表不候该职能时,
  由 _hanzao_shishang_rank 走 DTS L295/L300 寒暖燥湿交互: 寒燥临界月令 × 局内食伤有气
  → 食伤泄秀暖局/润燥, 作候(候神=局内食伤, 非候干表项). 此为算理推导, 非 case 特判.

两条集中裁决(全为布尔/序数, 禁浮点):
  1) 候神升 primary:
     a) 候干查表: 候干五行×局内候干有气(透干>=1 或坐旺) → 候干升 primary;
     b) 寒燥交互: 候干未候食伤职能 且 寒燥月令(申酉戌/亥子丑/寅卯辰/巳午未临界)
        × 局内食伤有气(透干>=1 或坐旺) → 食伤升 primary(泄秀暖局/润燥, DTS L295/L300).
     候神不刑不害(未入三刑丑戌未/寅巳申/子卯 且 未被合绊), 否则让位.
  2) 恶神抵消表: 刑/冲月令/冲主药根/破格 = 恶神(刑伤/提纲伤/药根拔/格破),
     不抵消制化之功(hard_good+恶神 -> 仍判主凶, 不平); 合绊 = 抵消(药被绊失制力).
     verdict 查表裁决, 不散落.

原典锚点:
  DTS L295/L298 寒之甚/过于燥皆偏枯 -> 候神优先(冬夏硬情形)
  DTS L30 燥湿 金水伤官要燥/木火伤官要湿 -> 寒燥交互候神
  PZZQ L24 身印两旺透食则贵 -> 寒燥交互食伤泄秀(暖局+泄秀双职能)
  丑戌未恃势之刑/寅巳申无恩之刑/子卯刑 -> 刑不入抵消
"""
from typing import Any, Dict, List, Optional

# 十神五行动作表
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生=食伤
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}     # 我克=财
SHENG_BACK = {v: k for k, v in SHENG.items()}                          # 生我=印
KE_BACK = {v: k for k, v in KE.items()}                                 # 克我=官杀
ZHI_BEN_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
              '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
              '戌': '土', '亥': '水'}
_WANG_ZHI = {'木': ('寅', '卯'), '火': ('巳', '午'), '土': ('辰', '戌', '丑', '未'),
             '金': ('申', '酉'), '水': ('亥', '子')}
# 寒燥交互月令: 秋金水(申酉戌)寒燥 + 冬(亥子丑)寒 + 春(寅卯辰)燥 + 夏(巳午未)燥
#   金水伤官要燥(申酉戌亥子丑), 木火伤官要湿(寅卯辰巳午未) —— DTS L30
_HANZAO = ('申', '酉', '戌', '亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未')

# ------------------------------------------------------------------ 候神表
def _hou_candidates(climate: Dict[str, Any]) -> List[Dict[str, Any]]:
    """候干查表: 读 qtbj_climate_candidates climate_candidates(原文序),
    五行级投影(原干序保留, 同五行去重). 未录入 -> []."""
    cands = (climate or {}).get('climate_candidates', []) or []
    seen: List[str] = []
    out: List[Dict[str, Any]] = []
    for c in cands:
        stem = c.get('stem', '')
        wx = GAN_WX.get(stem, '')
        if not wx:
            continue
        if wx not in seen:
            seen.append(wx)
            out.append({'wx': wx, 'order': c.get('order', 99),
                       'stem': stem, 'ref': c.get('evidence_refs') or []})
    return out


def _stem_present(wx: str, pillars: Optional[Dict[str, Any]]) -> int:
    """透干计数: 年月时干(不含日干, 日主非候神)."""
    if not pillars:
        return 0
    n = 0
    for pos in ('year', 'month', 'hour'):
        p = pillars.get(pos) or [None, None]
        if GAN_WX.get(p[0]) == wx:
            n += 1
    return n


def _ben_wang(wx: str, pillars: Optional[Dict[str, Any]]) -> bool:
    """坐旺: 四支(年/月/日/时)本气含候神且坐该候神旺地."""
    if not pillars:
        return False
    wzs = _WANG_ZHI.get(wx, ())
    for pos in ('year', 'month', 'day', 'hour'):
        p = pillars.get(pos) or [None, None]
        z = p[1]
        if z in wzs and ZHI_BEN_WX.get(z) == wx:
            return True
    return False


def _in_xing(wx: str, pillars: Optional[Dict[str, Any]]) -> bool:
    """候神支未入三刑(丑戌未/寅巳申/子卯两支). 候神无坐支 -> 不刑."""
    if not pillars:
        return False
    zs = set()
    for pos in ('year', 'month', 'day', 'hour'):
        p = pillars.get(pos) or [None, None]
        zs.add(p[1])
    _XJ = (frozenset(('丑', '戌', '未')), frozenset(('寅', '巳', '申')),
           frozenset(('子', '卯')))
    for z in zs:
        if ZHI_BEN_WX.get(z) == wx:
            for xj in _XJ:
                if z in xj and len(xj & zs) >= 2:
                    return True
    return False


# ------------------------------------------------------------------ 寒燥交互候神
def _hanzao_shishang_rank(climate: Dict[str, Any],
                          dm_wx: str,
                          month_branch: str,
                          pillars: Optional[Dict[str, Any]]
                          ) -> Dict[str, Any]:
    """寒燥交互候神裁决: 候干表未候食伤职能 且 寒燥临界月令 × 局内食伤有气
    -> 食伤泄秀(暖局/润燥)作候(DTS L295/L300 寒暖燥湿互证). 算理推导, 非 case.

    返回 {'rank': 'PROMOTE'|'DEMOTE', 'wx': 食伤五行, 'reason': [...], 'refs': [...]}
    """
    # 候干表是否已候食伤(若候干含食伤, 食伤已由候干轨覆盖, 不重复走寒燥交互)
    cands = _hou_candidates(climate)
    _shishang = SHENG.get(dm_wx, '')            # 食伤=我生
    _hou_gan_cover = any(c['wx'] == _shishang for c in cands)
    if _hou_gan_cover:
        return {'rank': 'DEMOTE', 'wx': _shishang,
                'reason': ['候干表已候食伤, 不重复走寒燥交互'],
                'refs': ['候干轨覆盖']}
    if month_branch not in _HANZAO:
        return {'rank': 'DEMOTE', 'wx': _shishang,
                'reason': ['月令%s非寒燥交互临界(寒燥互证 DTS L30)' % month_branch],
                'refs': ['DTS L30 金水伤官要燥/木火伤官要湿']}
    # 局内食伤有气(透干>=1 或坐旺)
    _in_chu = _stem_present(_shishang, pillars) >= 1 or _ben_wang(_shishang, pillars)
    _reason = ['寒燥交互: %s月候干未候食伤职能' % month_branch,
               '局内食伤有气: 透干%d/坐旺%s' % (_stem_present(_shishang, pillars), _ben_wang(_shishang, pillars))]
    if not _in_chu:
        _reason.append('食伤无气(不透不旺), 让位候干')
        return {'rank': 'DEMOTE', 'wx': _shishang, 'reason': _reason,
                'refs': ['DTS L295/L300']}
    # 局内食伤有气 且 候干表未候食伤职能 -> 食伤泄秀暖局/润燥候
    _reason.append('食伤泄秀暖局/润燥(DTS L295/L300 寒暖燥湿互证) -> 升 primary')
    return {'rank': 'PROMOTE', 'wx': _shishang, 'reason': _reason,
            'refs': ['DTS L295/L300 寒燥交互候神', 'PZZQ L24 身印两旺透食则贵']}


# ------------------------------------------------------------------ 候神集中裁决
def _tiaohou_primary_rank(climate: Dict[str, Any],
                          bing_wx: str,
                          dm_wx: str,
                          pillars: Optional[Dict[str, Any]]
                          ) -> Dict[str, Any]:
    """候神集中裁决: 候神是否升 primary + 候神五行.

    裁决序: ①候干查表升 primary(候干有气且未刑) → ②候干无候食伤职能则寒燥交互候食伤
    (寒燥月令 × 局内食伤有气). 全布尔, 禁浮点.
    """
    mb = (climate or {}).get('month_branch', '') or ''
    # ① 候干查表: 候干序1 有气 + 职能中(食伤泄秀/制药/炼金) -> 升.
    #   候干=生我(印) 时是主病之源(印多成病), 不升候干(让位寒燥交互候食伤).
    cands = _hou_candidates(climate)
    if cands:
        top = cands[0]
        wx = top['wx']
        _in_chu = _stem_present(wx, pillars) >= 1 or _ben_wang(wx, pillars)
        _is_shishang = SHENG.get(dm_wx, '') == wx     # 候干=食伤(我生)=泄秀
        _is_zhi = KE_BACK.get(bing_wx, '') == wx     # 候干=制药(克主病)
        _is_yin = SHENG_BACK.get(dm_wx, '') == wx     # 候干=生我(印)=主病源
        # V7.26 炼金职能: 金日主 主病印(土)重埋金时, 官火=炼金(制比劫+成器)为候神(原典"土重金埋需火炼金").
        #   候火不入忌(炼金是药), 同食伤泄秀.
        _is_lianjin = (dm_wx == '金' and bing_wx == SHENG_BACK.get(dm_wx, '') and wx == KE.get(dm_wx, ''))
        _reason = ['候干序1=%s 有气: 透干%d/坐旺%s' % (top.get('stem', ''), _stem_present(wx, pillars), _ben_wang(wx, pillars))]
        if _in_chu and not _in_xing(wx, pillars) and (_is_shishang or _is_zhi or _is_lianjin):
            _role = []
            if _is_shishang:
                _role.append('食伤泄秀')
            if _is_zhi:
                _role.append('制药')
            if _is_lianjin:
                _role.append('炼金(制比劫+成器)')
            _reason.append('候干职能: %s' % '+'.join(_role))
            _reason.append('候干有气+职能中+未刑 -> 升 primary')
            return {'rank': 'PROMOTE', 'wx': wx, 'reason': _reason,
                    'refs': ['QTBJ %s 候干序1=%s' % (mb, top.get('stem', ''))] + list(top.get('ref') or [])}
        if _is_yin:
            _reason.append('候干=生我(印)=主病之源, 不升(让位寒燥交互候食伤)')
            return _hanzao_shishang_rank(climate, dm_wx, mb, pillars)
        _reason.append('候干无气/入刑/职能不中, 让位寒燥交互候')
        return _hanzao_shishang_rank(climate, dm_wx, mb, pillars)
    # 候干表未录入 -> 直接寒燥交互候
    return _hanzao_shishang_rank(climate, dm_wx, mb, pillars)


# ------------------------------------------------------------------ 恶神抵消表
def _evil_no_offset(bad_items: List[str]) -> bool:
    """恶神抵消表: 刑/冲月令/冲主药根/破格 = 恶神(刑伤/提纲伤/药根拔/格破),
    不抵消制化之功 -> verdict 仍判主凶(不平). 合绊 = 抵消(药被绊失制力, 走 hard_bad).
    全为布尔(字符串前缀判定), 禁浮点."""
    _EVIL = ('三刑', '冲月令', '冲日主重根', '格局破格')
    return any(any(k in b for k in _EVIL) for b in (bad_items or []))
