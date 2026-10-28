"""HL Engine - Phase 2 重构（8模块拆分）。

依据：SHUNTIAN §10 架构冻结 + Architecture Freeze V1.0 §2.3
旧版 hetu_luoshu.py（豹书/河图双背法草稿）已归档至 archive/heluo_legacy/，
生产代码统一使用 numbers.py 中的单一映射表（河图版，经原典核实）。
"""

from .canonical import HeluoCanonical, HeluoResult, heluo_calculate
from .exceptions import (
    ForbiddenRuleError,
    HeluoEngineError,
    HourOutOfRangeError,
    YuanTangResolutionError,
)
from .input import HeluoInput, Location, prepare_heluo_input
from .numbers import (
    get_hexagram_name,
    compute_tian_di_shu,
    number_to_trigram,
    STEM_VALUES,
    BRANCH_VALUES,
)
from .prenatal import PrenatalHexagram, determine_prenatal_hexagram
from .postnatal import PostnatalHexagram, compute_postnatal
from .yuan_tang import YuanTang, find_yuantang, resolve_yuantang
from .hexagram import HexagramStructure, analyze_hexagram, compute_ti_yong
from .temporal import Timeline, compute_timeline
from .hua_gong import compute_huagong, HuaGongResult, HuaGongState
from .yuanqi_tables import (
    DUI_GUA,
    GANZHI_GUA_GROUPS,
    GANZHI_TO_GUA,
    YUANQI_FAN_TABLE,
    YUANQI_GANZHI_TABLE_A,
    YUANQI_GANZHI_TABLE_B,
    ganzhi_element,
    ganzhi_guas,
    gua_of_ganzhi_table_a,
    gua_of_ganzhi_table_b,
    yuanqi_fan_ganzhi,
    yuanqi_fan_relation,
    yuanqi_fan_suffering,
    yuanqi_ganzhi_conflict,
)
from .jiehhou import (
    SOLAR_TERMS, JIEHOU_GUA, SeasonalHexagram, QiPhase,
    get_seasonal_hexagram, get_qi_phase, get_current_jieqi_info,
)
from .frozen_state import FrozenHeluoState, build_frozen_state

HeluoBirthInput = HeluoInput

__all__ = [
    "HeluoCanonical",
    "heluo_calculate",
    "HeluoInput",
    "Location",
    "prepare_heluo_input",
    "HeluoBirthInput",
    "HeluoResult",
    "PrenatalHexagram",
    "YuanTang",
    "PostnatalHexagram",
    "Timeline",
    "HexagramStructure",
    "analyze_hexagram",
    "compute_ti_yong",
    "compute_timeline",
    "number_to_trigram",
    "get_hexagram_name",
    "STEM_VALUES",
    "BRANCH_VALUES",
    "compute_huagong",
    "HuaGongResult",
    "HuaGongState",
    # 起例卷之上·元气干支两说 + 干支纳卦表（L471–L516 / L681–L693）
    "DUI_GUA",
    "GANZHI_GUA_GROUPS",
    "GANZHI_TO_GUA",
    "YUANQI_FAN_TABLE",
    "YUANQI_GANZHI_TABLE_A",
    "YUANQI_GANZHI_TABLE_B",
    "ganzhi_element",
    "ganzhi_guas",
    "gua_of_ganzhi_table_a",
    "gua_of_ganzhi_table_b",
    "yuanqi_fan_ganzhi",
    "yuanqi_fan_relation",
    "yuanqi_fan_suffering",
    "yuanqi_ganzhi_conflict",
    "SOLAR_TERMS",
    "JIEHOU_GUA",
    "SeasonalHexagram",
    "QiPhase",
    "get_seasonal_hexagram",
    "get_qi_phase",
    "get_current_jieqi_info",
    "FrozenHeluoState",
    "build_frozen_state",
]