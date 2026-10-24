"""P1.5: HEXAGRAM_STATE_ENGINE 卦象状态引擎

计算卦象的状态因子:
- 动静状态 (静/动/变/互)
- 旺衰状态 (得令/失令)
- 体用关系 (体卦/用卦)
- 机会因子
- 风险因子
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════════════════════════
TRIGRAM_NAMES = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}

ELEMENT_NAMES = {
    "木": 1, "火": 2, "土": 3, "金": 4, "水": 5
}

# 五行生克关系
ELEMENT_GENERATES = {
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
}

ELEMENT_OVERCOMES = {
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木"
}

# ⚠ 2026-10-08 批次 G：五行生克此前在本模块与 hua_gong._WU_SHENG/_WU_KE
#   各存一份（内容相同）。五行生克是全库最基本的五行关系，
#   容不得两份各改各的——已统一到此处。

# 错卦 = 先天方位对宫（六爻全变）。全库**单一来源**。
# ⚠ 2026-10-08 批次 G：错卦此前在 guajie / yuan_qi / hexagram / hua_gong
#   四处各存一份（内容相同），名字统一叫 OPPOSITE_TRIGRAM。
#   更糟的是另有一个**不同义**的表也叫 OPPOSITE_TRIGRAM——化工相反
#   （四季对宫，仅坎离震兑四项），对乾/坤/艮/巽 取 .get() 直接返回 None。
#   import 错了就是静默判错。故错卦统一名 QIANXI_DUKONG（单一来源），
#   化工相反另名 HUAGONG_FAN_GUA；改后无任何公开符号叫 OPPOSITE_TRIGRAM。
QIANXI_DUKONG = {
    "乾": "坤", "坤": "乾",
    "坎": "离", "离": "坎",
    "震": "巽", "巽": "震",
    "艮": "兑", "兑": "艮",
}


# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════
@dataclass
class HexagramState:
    """卦象状态定义。"""
    hexagram_id: str           # 如 "乾上乾下"
    state_type: str            # 静/动/变/互
    state_description: str
    opportunity_factor: float  # 0-1
    risk_factor: float         # 0-1
    element_bonus: dict        # 五行加成


@dataclass
class StateCalculationResult:
    """状态计算结果。"""
    hexagram: str
    state_type: str
    opportunity: float
    risk: float
    element_modifier: float
    net_factor: float
    interpretation: str


# ═══════════════════════════════════════════════════════════════════
# 核心算法
# ═══════════════════════════════════════════════════════════════════
def calculate_hexagram_state(
    hexagram: str,
    state_type: str = "静",
    element_state: Optional[dict] = None,
    month_branch: Optional[str] = None
) -> StateCalculationResult:
    """⛔ 已作废（2026-10-07）：整条链路建立在无原典依据的自拟分数上。

    本函数依次调用 :func:`get_base_factors`（静/动/变/互 因子）与
    :func:`calculate_element_modifier`（浮点权重），二者均已于本日作废，
    故本函数一并作废，避免"调用即抛"的中间态误导后人。

    ## 有据可依的替代

    - **静/动/变/互的机会风险** → :mod:`gui_ming_liu_ju` 的六项原典判据
      （起例卷之中 L630–L648：一卦名吉 / 二爻吉 / 三辞吉 / 四得时 /
      五有援 / 六顺时），返回判据名 + 原文依据 + 吉凶/不判。
    - **五行旺衰** → :func:`judge_element_state`，按起例卷之上 L102
      「当生者王，所生者相，生生者休，克生者囚，所克者死」判定名目。

    本模块目前**无生产调用方**，作废不影响线上输出；
    接线前必须改用上述有据实现，**不得**复活自拟分数。

    Raises:
        NotImplementedError: 恒抛出。
    """
    raise NotImplementedError(
        "calculate_hexagram_state 依赖的两个自拟分数函数已作废"
        "（get_base_factors / calculate_element_modifier），故一并作废。"
        "请改用 gui_ming_liu_ju.judge_liu_ju()（六项原典判据）"
        "与 judge_element_state()（原典 L102 王相休囚死）。"
    )


def get_base_factors(hexagram: str, state_type: str) -> Tuple[float, float]:
    """
    获取基础机会/风险因子。

    ⛔ **2026-10-07 起本函数禁止使用，返回 (nan, nan)。**

    ## 为什么作废

    本函数原返回「静=0.5/0.3、动=0.7/0.4、变=0.6/0.5、互=0.4/0.3」，
    2026-10-06 的注释已自承「**非查表所得，也非原典规定**」，
    2026-10-07 复核进一步确认：**这些数值在《河洛真数》全书中
    找不到任何出处**，且 `hexagram` 参数根本没被使用——不同卦返回同一组
    因子。它们不是「简化」，是**凭空捏造**。

    ## 原典的真实判据

    起例卷之中「贵命十体」L630–L648 给出的是**六项查表式判据**，
    不是打分：
        一卦名吉　二爻吉（元堂住二五爻）　三辞吉（有元吉亨利）
        四得时　五有援（元堂与应爻阴阳相反）　六顺时（天地二数与时偕行）
    已落成 ``gui_ming_liu_ju.py``（含逐条原文出处与不臆造守卫）。

    ## 迁移方式

    需要「机会/风险」时，请改用 :mod:`gui_ming_liu_ju` 的六项判据，
    它返回的是**原典判据名 + 原文依据 + 吉/凶/不判**，
    而不是自拟分数。若确需 0-1 数值，须先补上原典出处再实现。

    Raises:
        NotImplementedError: 恒抛出。**不得**静默回退到旧分数。
    """
    raise NotImplementedError(
        "get_base_factors 的静/动/变/互 因子无原典依据，已于 2026-10-07 作废。"
        "请改用 gui_ming_liu_ju.judge_liu_ju() 的六项原典判据"
        "（一卦名吉/二爻吉/三辞吉/四得时/五有援/六顺时，L630–L648）。"
    )


def get_base_factors_legacy() -> Tuple[float, float]:
    """⚠️ 已作废的自拟分数，仅供考古，**任何调用都是错的**。

    保留仅为让后人看清这组数字的来历；它们没有原典出处，
    且 `hexagram` 参数未被使用（不同卦返回同值）。
    """
    return _LEGACY_BASE_FACTORS["静"]


#: 已作废的自拟分数原样留档（仅供考古，禁止使用）
_LEGACY_BASE_FACTORS: dict[str, Tuple[float, float]] = {
    "静": (0.5, 0.3),
    "动": (0.7, 0.4),
    "变": (0.6, 0.5),
    "互": (0.4, 0.3),
}


def judge_element_state(element: str, month_branch: str) -> str:
    """按原典 L102 判定某五行在当月的「王相休囚死」。

    原典（起例卷之上 L102）逐字：

        「天以五行分隶四时，各有王相休囚之异。人生值之亦然。
          **当生者王，所生者相，生生者休，克生者囚，所克者死。**今列于后。」

    以**当令五行**（月支五行）为「我」，其余五行按与我的生克关系定名：
        王  = 当令者本身
        相  = 生我者（所生）
        休  = 我生者（生生）
        囚  = 克我者（克生）
        死  = 我克者（所克）

    :param element: 待判的五行（木/火/土/金/水）
    :param month_branch: 月支（子丑寅卯…）
    :returns: 王 / 相 / 休 / 囚 / 死；月支非法返回 "?"

    ⚠️ 本函数返回**原典判定的名目**，不返回浮点权重。
    2026-10-07 前本模块用的是一组自拟浮点权重
    （当令+0.15 / 相生+0.08 / 相克−0.10 / 被克−0.12 / 休囚−0.05），
    那些数字在原典中**无任何出处**，且注释「被克（被当令克）」与
    「休囚（被当令生）」方向互相矛盾（被当令生者按原典应为「休」，
    代码却记为负权重「被克」）。现按原文重写。
    """
    me = get_branch_element(month_branch)
    if me is None or element not in ("木", "火", "土", "金", "水"):
        return "?"
    if element == me:
        return "王"                                              # 当生者王
    if ELEMENT_GENERATES.get(element) == me:
        return "相"                                              # 所生者相
    if ELEMENT_GENERATES.get(me) == element:
        return "休"                                              # 生生者休
    if ELEMENT_OVERCOMES.get(element) == me:
        return "囚"                                              # 克生者囚
    if ELEMENT_OVERCOMES.get(me) == element:
        return "死"                                              # 所克者死
    return "?"


def calculate_element_modifier(
    element_state: Optional[dict],
    month_branch: Optional[str]
) -> float:
    """⛔ 已作废（2026-10-07）：返回的是无原典依据的自拟浮点权重。

    原实现对每个五行按下列**自拟**系数累加浮点数：

        当令 +0.15 / 相生 +0.08 / 相克 −0.10 / 被克 −0.12 / 休囚 −0.05

    问题有三：
      1. 这组数字在《河洛真数》全书中**找不到任何出处**；
      2. 注释「被克（被当令克）」与「休囚（被当令生）」方向自相矛盾
         ——被当令所生者按原典 L102 应为「休」，代码却记作负权重；
      3. 原典此处是**定性名目**（王/相/休/囚/死），本无浮点权重可言。

    ## 迁移方式

    改用 :func:`judge_element_state`，它按原典 L102 返回王相休囚死的**名目**，
    附带原文依据。若下游确需数值，须先为该数值补上原典出处。

    Raises:
        NotImplementedError: 恒抛出。**不得**静默回退到旧权重。
    """
    raise NotImplementedError(
        "calculate_element_modifier 的浮点权重（当令+0.15 等）无原典依据，"
        "已于 2026-10-07 作废，且原注释方向自相矛盾。"
        "请改用 judge_element_state() —— 按原典 L102「当生者王，所生者相，"
        "生生者休，克生者囚，所克者死」返回王相休囚死的名目。"
    )


def get_branch_element(branch: str) -> Optional[str]:
    """获取地支五行。"""
    BRANCH_ELEMENTS = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    return BRANCH_ELEMENTS.get(branch)


def generate_interpretation(
    hexagram: str,
    state_type: str,
    opportunity: float,
    risk: float,
    element_modifier: float
) -> str:
    """生成自然语言解释。"""
    parts = []
    
    if opportunity > 0.6:
        parts.append(" opportunities available")
    elif opportunity > 0.4:
        parts.append(" moderate opportunities")
    else:
        parts.append(" limited opportunities")
    
    if risk > 0.5:
        parts.append(" and notable risks")
    elif risk > 0.3:
        parts.append(" and some risks")
    
    if element_modifier > 0.1:
        parts.append(" with favorable elemental support")
    elif element_modifier < -0.1:
        parts.append(" with unfavorable elemental conditions")
    
    return f"{hexagram} ({state_type}){(''.join(parts)) if parts else ' neutral'}. "


if __name__ == "__main__":
    # ⚠ 2026-10-24：原此处是 `calculate_hexagram_state(...)` 的演示调用 ——
    #   而该函数**已作废**（恒抛 NotImplementedError），演示块只会抛异常，
    #   且会让人误以为「跑一下这个模块就能拿到状态分数」。
    #   现改为**只说明作废状态与有据替代路径**，不再调用无依据的分数函数。
    print(
        "本模块的 calculate_hexagram_state / get_base_factors / "
        "calculate_element_modifier 已于 2026-10-07 作废"
        "（自拟浮点分数无原典依据，恒抛 NotImplementedError）。\n"
        "有据替代路径：\n"
        "  · 静/动/变/互的机会风险 → gui_ming_liu_ju.judge_liu_ju()"
        "（起例卷之中 L630–L648 六项原典判据，给吉/凶/不判）\n"
        "  · 五行旺衰 → judge_element_state()（起例卷之上 L102）\n"
        "解读层接线见 heluo_engine/engines/heluo/interpretation_pipeline.py。"
    )
