"""Z80: ZiWei Temporal Ontology——时间层 Fact 层。

只做"怎么算出来"，不做"算出来怎么解释"。
来源：《紫微斗数全书》卷二安星诀。

模块：
- BIG_LIMIT: 大限安法
- SMALL_LIMIT: 小限安法
- CHILD_LIMIT: 童限安法
- DOU_JUN: 斗君安法
- TAISUI: 太岁（流年地支宫位）
- FLOW_LU_YANG_TUO: 流禄/流羊/流陀
- LIUNIAN_SANSHA: 流年三杀（奏书/将军/直符）

Z80-H 接线（2026-10-15）：本模块资产已接入生产 —— 落点 classical_detail.temporal_facts + ziwei_engine._compute_doujun（build_answer 顶层键 classical_detail，独立通道，
  不并入 12 宫位维/体用层）。
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md（Z80-H 收口）
"""
from __future__ import annotations

BRANCH_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 流年天干 -> 禄存/擎羊/陀罗 所在地支（以流年干五虎遁）
# 禄存：甲禄寅乙禄卯丙戊禄巳丁己禄午庚禄申辛禄酉壬禄亥癸禄子
# 擎羊=禄存前一位，陀罗=禄存后一位
FLOW_STAR_BY_YEAR_GAN = {
    "甲": {"lu": "寅", "yang": "卯", "tuo": "丑"},
    "乙": {"lu": "卯", "yang": "辰", "tuo": "寅"},
    "丙": {"lu": "巳", "yang": "午", "tuo": "辰"},
    "丁": {"lu": "午", "yang": "未", "tuo": "巳"},
    "戊": {"lu": "巳", "yang": "午", "tuo": "辰"},
    "己": {"lu": "午", "yang": "未", "tuo": "巳"},
    "庚": {"lu": "申", "yang": "酉", "tuo": "未"},
    "辛": {"lu": "酉", "yang": "戌", "tuo": "申"},
    "壬": {"lu": "亥", "yang": "子", "tuo": "戌"},
    "癸": {"lu": "子", "yang": "丑", "tuo": "亥"},
}


def small_limit_start_branch(year_branch: str) -> str:
    """小限起宫：
    寅午戌人起辰宫，申子辰人自戌宫，巳酉丑人起未宫，亥卯未人起丑宫。
    """
    group = {
        "辰": ["寅", "午", "戌"],
        "戌": ["申", "子", "辰"],
        "未": ["巳", "酉", "丑"],
        "丑": ["亥", "卯", "未"],
    }
    for start, branches in group.items():
        if year_branch in branches:
            return start
    raise ValueError(f"unknown year_branch: {year_branch}")


def small_limit_branch(birth_year_branch: str, gender: str, age: int) -> str:
    """小限宫位：男顺女逆，从起宫起1岁，顺/逆数到age。"""
    start = small_limit_start_branch(birth_year_branch)
    i = BRANCH_ORDER.index(start)
    if gender == "男":
        return BRANCH_ORDER[(i + age - 1) % 12]
    else:
        return BRANCH_ORDER[(i - (age - 1)) % 12]


def doujun_branch(taisui_branch: str, birth_month: int, birth_hour_idx: int) -> str:
    """斗君安法：
    于流年太岁宫起正月，逆数至生月，再生月宫起子时，顺数至生时。
    birth_month: 农历月 1-12
    birth_hour_idx: 子时=0, 丑时=1, ..., 亥时=11
    """
    # 太岁宫起正月，逆数至生月
    i = BRANCH_ORDER.index(taisui_branch)
    month_palace = BRANCH_ORDER[(i - (birth_month - 1)) % 12]
    # 生月宫起子时，顺数至生时
    j = BRANCH_ORDER.index(month_palace)
    return BRANCH_ORDER[(j + birth_hour_idx) % 12]


def flow_star_positions(year_gan: str) -> dict:
    """流禄/流羊/流陀 以流年天干为准。"""
    return FLOW_STAR_BY_YEAR_GAN[year_gan]


def taisui_branch(year: int) -> str:
    """太岁宫 = 流年地支。"""
    # 1984甲子年，地支=子
    offset = (year - 1984) % 12
    return BRANCH_ORDER[offset]
