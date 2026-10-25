# -*- coding: utf-8 -*-
"""⚠️ DEPRECATED — 关系状态引擎残桩（Phase 5-D 草案）

**2026-10-22 裁定废弃**（证据：主仓 `D:\shuntian` 与本包 `src/` 内均**零生产
import**；本包唯一引用是 `tests/heluo/test_heluo_base_table_consistency.py` 拿它
比对两张五行生克表与 `guajie`/`hexagram_state` 是否一致；主仓
`pipeline_stages/compute_stage.py` 已把河洛结果断链（`heluo_result` 恒为 None），
无任何平台侧调用点）。

**已知缺陷（刻意保留并由守卫钉死，勿当可用实现）**：

1. `calculate_time_sync()` 里 ``any(y in ELEMENT_GEN for y in [year_a, year_b])``
   —— `ELEMENT_GEN` 的键是「木/火/土/金/水」，而 `year_a/year_b` 是**流年干支
   字符串**，故该分支**恒为假** → `time_sync` 实际只有「同步/异步」两值，
   「相生」分支不可达。
2. `calculate_hexagram_interaction()` 永不返回「冲突」→ 冲突判定是空分支。
3. `generate_relationship_state()` 的 ``evidence.sources`` **写死**
   ``['河洛理数', '周易', '《易经》']``，与实际计算无关 —— 属于**伪造出处**，
   河洛引擎的证据链不容许这种写法。
4. 本模块的「关系」判词（吉凶/建议）没有任何原典依据，属引擎自拟。

**为什么保留而不删**：本包 `tests/heluo/test_heluo_base_table_consistency.py`
仍需比对这里的 `ELEMENT_GEN` / `ELEMENT_KE` 与 `guajie.ELEMENT_GENERATES` /
`hexagram_state.ELEMENT_OVERCOMES` 是否逐字相等（防基础表副本漂移）。
保留文件 + 标废弃 + 钉死缺陷，比删除更安全：复活时会有告警，且不会出现
「两套口径并存」。

**生产代码请勿 import 本模块。** 关系/合盘类需求应另起模块并从
《河洛真数》《河洛理数》原典取依据，不得沿用本残桩的判词。
"""
from __future__ import annotations
import logging
import warnings
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict

warnings.warn(
    "heluo/relationship/engine.py is deprecated (Phase 5-D 残桩，2026-10-22 裁定废弃). "
    "生产代码请勿 import；如需关系/合盘判词，另起模块并从原典取依据。",
    DeprecationWarning,
    stacklevel=2,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 版本控制
ENGINE_VERSION = 'v1.0.0'

# ========== 数据模型 ==========

class ElementRelation(str, Enum):
    """五行关系类型。"""
    GEN = "gen"           # 相生
    KE = "ke"            # 相克
    TONG = "tong"        # 同类
    XIE = "xie"          # 泄耗
    HAO = "hao"          # 耗泄


class HexagramRelation(str, Enum):
    """卦象关系类型。"""
    SAME = "same"       # 同卦
    COMP = "comp"        # 互补
    CONFLICT = "conflict"  # 冲突
    SUPPORT = "support"   # 支持


class TimeSync(str, Enum):
    """时间同步类型。"""
    SYNC = "sync"         # 同步
    ASYNC = "async"       # 异步
    COMP = "comp"         # 互补
    CONFLICT = "conflict"  # 冲突


class StrengthLevel(str, Enum):
    """强度等级。"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


# ========== 输入数据模型 ==========

@dataclass
class PersonModel:
    """个人模型数据。"""
    user_id: str
    birth_info: Dict[str, str]
    heluo_model: Dict[str, str]
    daily_state: Dict[str, Any]
    
    @property
    def dominant_element(self) -> str:
        """获取主导五行元素。"""
        return self.heluo_model.get('dominant_element', '火')
    
    @property
    def benming_hexagram(self) -> str:
        """获取本命卦。"""
        return self.heluo_model.get('benming_hexagram', '')
    
    @property
    def yuan_tang(self) -> str:
        """获取元堂。"""
        return self.heluo_model.get('yuan_tang', '')
    
    @property
    def postnatal_hexagram(self) -> str:
        """获取后天卦。"""
        return self.heluo_model.get('postnatal_hexagram', '')
    
    @property
    def liu_nian(self) -> str:
        """获取流年。"""
        return self.daily_state.get('liu_nian', '')
    
    @property
    def liu_yue(self) -> str:
        """获取流月。"""
        return self.daily_state.get('liu_yue', '')
    
    @property
    def liu_ri(self) -> str:
        """获取流日。"""
        return self.daily_state.get('liu_ri', '')
    
    @property
    def element_balance(self) -> Dict[str, float]:
        """获取五行平衡。"""
        return self.daily_state.get('element_balance', {})


@dataclass
class RelationshipInput:
    """关系计算输入。"""
    person_a: PersonModel
    person_b: PersonModel
    relationship_type: str  # partner|family|business|friend
    target_date: date


# ========== D-1: 五行互动模型 ==========

# 五行相生关系
ELEMENT_GEN = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
}

# 五行相克关系
ELEMENT_KE = {
    '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
}


def calculate_element_interaction(
    person_a: PersonModel,
    person_b: PersonModel
) -> Dict[str, Any]:
    """
    计算五行互动。
    
    输出:
        - element_relation: 关系类型
        - dominant_element: 主导元素
        - interaction: 互动模式
    """
    elem_a = person_a.dominant_element
    elem_b = person_b.dominant_element
    
    # 同类判断
    if elem_a == elem_b:
        return {
            'element_relation': '同类',
            'dominant_element': elem_a,
            'interaction': '同类增强'
        }
    
    # 相生判断 (A生B)
    if ELEMENT_GEN.get(elem_a) == elem_b:
        return {
            'element_relation': '相生',
            'dominant_element': elem_a,
            'interaction': 'A生B - 支持'
        }
    
    # 相生判断 (B生A)
    if ELEMENT_GEN.get(elem_b) == elem_a:
        return {
            'element_relation': '相生',
            'dominant_element': elem_b,
            'interaction': 'B生A - 被支持'
        }
    
    # 相克判断 (A克B)
    if ELEMENT_KE.get(elem_a) == elem_b:
        return {
            'element_relation': '相克',
            'dominant_element': elem_a,
            'interaction': 'A克B - 制约'
        }
    
    # 相克判断 (B克A)
    if ELEMENT_KE.get(elem_b) == elem_a:
        return {
            'element_relation': '相克',
            'dominant_element': elem_b,
            'interaction': 'B克A - 被制约'
        }
    
    # 泄耗判断
    return {
        'element_relation': '平衡',
        'dominant_element': elem_a,
        'interaction': '中性平衡'
    }


# ========== D-2: 卦象互动模型 ==========

def calculate_hexagram_interaction(
    person_a: PersonModel,
    person_b: PersonModel
) -> Dict[str, Any]:
    """
    计算卦象互动。
    
    输出:
        - hexagram_relation: 关系类型
        - current_influence: 当前影响
        - interaction_mode: 互动模式
    """
    hex_a = person_a.benming_hexagram
    hex_b = person_b.benming_hexagram
    liu_ri = person_a.liu_ri  # 使用A的流日作为当前影响
    
    # 同卦判断
    if hex_a == hex_b:
        return {
            'hexagram_relation': '同卦',
            'current_influence': '共振增强',
            'interaction_mode': '共振'
        }
    
    # 互补卦判断 (乾↔坤, 坎↔离等)
    COMPACT_PAIRS = {
        '乾': '坤', '坤': '乾',
        '坎': '离', '离': '坎',
        '震': '兑', '兑': '震',
        '巽': '艮', '艮': '巽'
    }
    
    if COMPACT_PAIRS.get(hex_a) == hex_b:
        return {
            'hexagram_relation': '互补',
            'current_influence': '阴阳调和',
            'interaction_mode': '调和'
        }
    
    # 冲突判断 (简化版：根据卦序差)
    # 实际应使用完整的卦象冲突矩阵
    return {
        'hexagram_relation': '中性',
        'current_influence': '流日影响',
        'interaction_mode': '并行'
    }


# ========== D-3: 时间同步模型 ==========

def calculate_time_sync(
    person_a: PersonModel,
    person_b: PersonModel
) -> Dict[str, Any]:
    """
    计算时间同步。
    
    输出:
        - time_sync: 同步类型
        - current_phase: 当前阶段
        - cooperation_mode: 合作模式
    """
    # 流年对比
    year_a = person_a.liu_nian
    year_b = person_b.liu_nian
    
    # 流月对比
    month_a = person_a.liu_yue
    month_b = person_b.liu_yue
    
    # 流日对比
    day_a = person_a.liu_ri
    day_b = person_b.liu_ri
    
    # 流年同步判断
    if year_a == year_b:
        sync_type = '同步'
        phase = '协同期'
        mode = '协作'
    elif any(y in ELEMENT_GEN for y in [year_a, year_b]):
        sync_type = '相生'
        phase = '发展期'
        mode = '引导'
    else:
        sync_type = '异步'
        phase = '独立期'
        mode = '并行'
    
    return {
        'time_sync': sync_type,
        'current_phase': phase,
        'cooperation_mode': mode
    }


# ========== D-4: 统一输出协议 ==========

def generate_relationship_state(
    input_data: RelationshipInput
) -> Dict[str, Any]:
    """
    生成关系状态输出。
    
    整合五行、卦象、时间三个维度的计算结果。
    """
    # D-1: 五行互动
    element_result = calculate_element_interaction(
        input_data.person_a,
        input_data.person_b
    )
    
    # D-2: 卦象互动
    hexagram_result = calculate_hexagram_interaction(
        input_data.person_a,
        input_data.person_b
    )
    
    # D-3: 时间同步
    time_result = calculate_time_sync(
        input_data.person_a,
        input_data.person_b
    )
    
    # 计算综合强度
    strength = _calculate_overall_strength(
        element_result,
        hexagram_result,
        time_result
    )
    
    # 生成建议
    suggestion = _generate_suggestion(
        element_result,
        hexagram_result,
        time_result,
        input_data.relationship_type
    )
    
    return {
        'relationship_state': {
            'title': f"{element_result['element_relation']} {hexagram_result['hexagram_relation']}",
            'description': f"当前关系状态: {time_result['current_phase']}"
        },
        'interaction_pattern': {
            'strength': strength,
            'challenge': _identify_challenge(element_result, hexagram_result, time_result)
        },
        'time_context': {
            'current_phase': time_result['current_phase'],
            'recommended_period': _recommend_period(time_result, input_data.target_date)
        },
        'suggestion': {
            'action': suggestion['action'],
            'attention': suggestion['attention']
        },
        'evidence': {
            'rules': [
                f"EL-{element_result['element_relation']}",
                f"HG-{hexagram_result['hexagram_relation']}",
                f"TIME-{time_result['time_sync']}"
            ],
            'sources': ['河洛理数', '周易', '《易经》']
        },
        'metadata': {
            'calculation_version': ENGINE_VERSION,
            'relationship_type': input_data.relationship_type,
            'target_date': str(input_data.target_date)
        }
    }


def _calculate_overall_strength(
    element: Dict,
    hexagram: Dict,
    time: Dict
) -> str:
    """计算综合强度。"""
    score = 0
    
    # 五行权重
    if element['element_relation'] == '同类':
        score += 3
    elif element['element_relation'] == '相生':
        score += 2
    elif element['element_relation'] == '相克':
        score -= 1
    else:
        score += 1
    
    # 卦象权重
    if hexagram['hexagram_relation'] == '同卦':
        score += 3
    elif hexagram['hexagram_relation'] == '互补':
        score += 2
    elif hexagram['hexagram_relation'] == '冲突':
        score -= 1
    else:
        score += 1
    
    # 时间权重
    if time['time_sync'] == '同步':
        score += 3
    elif time['time_sync'] == '相生':
        score += 2
    else:
        score += 1
    
    # 映射到等级
    if score >= 7:
        return 'strong'
    elif score >= 4:
        return 'moderate'
    else:
        return 'weak'


def _identify_challenge(
    element: Dict,
    hexagram: Dict,
    time: Dict
) -> str:
    """识别主要挑战。"""
    challenges = []
    
    if element['element_relation'] == '相克':
        challenges.append(f"{element['dominant_element']}克制约")
    
    if hexagram['hexagram_relation'] == '冲突':
        challenges.append('卦象冲突')
    
    if time['time_sync'] == '异步':
        challenges.append('时间异步')
    
    return '、'.join(challenges) if challenges else '无显著挑战'


def _generate_suggestion(
    element: Dict,
    hexagram: Dict,
    time: Dict,
    rel_type: str
) -> Dict[str, str]:
    """生成建议。"""
    action = '保持现状'
    attention = '注意观察'
    
    if element['element_relation'] == '相克':
        action = '调和矛盾'
        attention = f"{element['dominant_element']}元素过强，需注意平衡"
    elif element['element_relation'] == '相生':
        action = '顺势而为'
        attention = '互动良好，可加深合作'
    
    if time['current_phase'] == '协同期':
        action = '主动推进'
        attention = '时间窗口良好'
    elif time['current_phase'] == '独立期':
        action = '各自发展'
        attention = '给予空间'
    
    return {'action': action, 'attention': attention}


def _recommend_period(time: Dict, target_date: date) -> str:
    """推荐时间周期。"""
    if time['current_phase'] in ['协同期', '发展期']:
        return f"当前至{target_date + timedelta(days=30)}为有利窗口"
    else:
        return '建议观察后续变化'


from datetime import timedelta