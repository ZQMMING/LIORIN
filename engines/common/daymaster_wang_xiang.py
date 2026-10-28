# -*- coding: utf-8 -*-
"""PATCH-160-B V2 / D11 旺相休囚死状态派生器
只做日主五行相对月令本气五行的确定性五行生克映射, 不重排盘, 不改 L0.

原典授权(仅状态标签):
- YHZP-069-001 "各主旺相休囚死" -> 五态名目
- PZZQ-005-005 "旺相休囚年月日时亦有横盖之权, 不可执一论也"
  -> 五态是客观四时状态, 但不可单凭它判强弱

以月令本气五行當令為旺:
  同月令   = 旺
  月令生之 = 相 (M 生 D)
  生月令   = 休 (D 生 M)
  克月令   = 囚 (D 克 M)
  月令克之 = 死 (M 克 D)

禁: 旺相->身强 / 休囚死->身弱 / score / weight / threshold.
D1 in_season 是布尔(旺=非旺), 本派生器是其五态细化超集, 二者并存不冲突.
"""
from typing import Any, Dict
from spec.yinyang_system import SHENG, KE, SHENG_ME, KE_ME

WUXING = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 五行相生: SHENG[a] = a 所生

# 五行相克: KE[a] = a 所克

WANG = 'WANG'        # 旺(当令)
XIANG = 'XIANG'      # 相(令所生)
XIU = 'XIU'          # 休(生令)
QIU = 'QIU'          # 囚(克令)
SI = 'SI'            # 死(令所克)

_STATE_CN = {WANG: '旺', XIANG: '相', XIU: '休', QIU: '囚', SI: '死'}


def classify_wang_xiang(daymaster: str, month_qi_element: str) -> Dict[str, Any]:
    d = WUXING[daymaster]
    m = month_qi_element
    if d == m:
        state = WANG
    elif SHENG.get(m) == d:
        state = XIANG
    elif SHENG.get(d) == m:
        state = XIU
    elif KE.get(d) == m:
        state = QIU
    elif KE.get(m) == d:
        state = SI
    else:
        state = 'UNKNOWN'
    return {
        'daymaster': daymaster,
        'daymaster_element': d,
        'month_qi_element': m,
        'state': state,
        'state_cn': _STATE_CN.get(state, '未知'),
    }


def build_wang_xiang(facts: Dict[str, Any], daymaster: str) -> Dict[str, Any]:
    """输入 L0 build() facts(取 month_qi_element)."""
    mqe = facts.get('month_qi_element')
    core = classify_wang_xiang(daymaster, mqe)
    core.update({
        'generator': 'DaymasterWangXiangXiuQiu',
        'patch': 'PATCH-160-B-V2-D11',
        'judgment_status': 'WANG_XIANG_STATE_ONLY',
        'boundary_note': (
            '旺相休囚死仅为月令四时状态标签; 不相加不评分; '
            '旺相不等于身强, 休囚死不等于身弱(PZZQ 不可执一论)'
        ),
    })
    return core
