"""V2.2.2 FINAL 附录 L 枚举注册 + §M 状态模型枚举。

值域治理，不负责证明业务语义（附录 L-1）。
"""

from enum import Enum


class EngineID(str, Enum):
    """六部经典引擎 ID（V2.2.2 §1）。"""
    YUHAI_ZIPING = "YUHAI_ZIPING"
    ZIPIN_ZHENQUAN = "ZIPIN_ZHENQUAN"
    DI_TIAN_SUI = "DI_TIAN_SUI"
    QIONGTONG_BAOJIAN = "QIONGTONG_BAOJIAN"
    SANMING_TONGHUI = "SANMING_TONGHUI"
    SHENFENG_TONGKAO = "SHENFENG_TONGKAO"


class EngineStatus(str, Enum):
    """§71 Engine Final Status。

    RULE_NOT_APPLICABLE 不是 Engine Final Status，属于 RuleMatchState。
    """
    PASS = "PASS"
    UNKNOWN = "UNKNOWN"
    CLASSICAL_DIVERGENCE = "CLASSICAL_DIVERGENCE"
    FAIL = "FAIL"
    FAIL_CLOSED = "FAIL_CLOSED"


class RuleMatchState(str, Enum):
    """§36 L-7 Internal Rule Match State。"""
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    RULE_NOT_APPLICABLE = "RULE_NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class TextLayer(str, Enum):
    """附录 D Source Text Layer。"""
    ORIGINAL = "ORIGINAL"
    ANNOTATION = "ANNOTATION"
    LATER_COMMENTARY = "LATER_COMMENTARY"
    UNVERIFIED = "UNVERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class EvidenceGrade(str, Enum):
    """§78 Evidence Grade：证据质量描述，不是概率。"""
    A = "A"  # ORIGINAL
    B = "B"  # ANNOTATION
    C = "C"  # LATER_COMMENTARY
    D = "D"  # UNVERIFIED / NEEDS_REVIEW


class RuleStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FROZEN = "FROZEN"


class SourceStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FROZEN = "FROZEN"


class Operator(str, Enum):
    """§46 Rule Preconditions 白名单（禁止嵌套/比较符）。"""
    EQUALS = "equals"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class RuleOperator(str, Enum):
    """§45 Rule 顶层 operator。"""
    EMIT = "emit"
    REQUIRE = "require"
    SUPPRESS = "suppress"


class RuleType(str, Enum):
    DEFINITION = "definition"
    RESOLUTION = "resolution"
    ACTIVATION = "activation"
    EFFECTIVENESS = "effectiveness"
    DIAGNOSIS = "diagnosis"
    MEDICINE = "medicine"


# ---------- 附录 L 各引擎枚举 ----------

class PZZQFormationState(str, Enum):
    FORMED = "FORMED"
    NOT_FORMED = "NOT_FORMED"
    UNKNOWN = "UNKNOWN"


class PZZQDestructionState(str, Enum):
    DESTROYED = "DESTROYED"
    NOT_DESTROYED = "NOT_DESTROYED"
    UNKNOWN = "UNKNOWN"


class PZZQRescueState(str, Enum):
    RESCUED = "RESCUED"
    NOT_RESCUED = "NOT_RESCUED"
    UNKNOWN = "UNKNOWN"


class PZZQStructureState(str, Enum):
    VALID = "VALID"
    BROKEN = "BROKEN"
    VALID_WITH_DEFECT = "VALID_WITH_DEFECT"
    BROKEN_WITH_RESCUE = "BROKEN_WITH_RESCUE"
    UNKNOWN = "UNKNOWN"


class PZZQChengbaiState(str, Enum):
    CHENG = "CHENG"
    BAI = "BAI"
    CHENG_ZHONG_DAI_JI = "CHENG_ZHONG_DAI_JI"
    BAI_ZHONG_YOU_CHENG = "BAI_ZHONG_YOU_CHENG"
    UNKNOWN = "UNKNOWN"


class DTSQiType(str, Enum):
    BEN_QI = "本气"
    ZHONG_QI = "中气"
    YU_QI = "余气"


class DTSSupportState(str, Enum):
    """生扶/支持强度（V2.22-PATCH-001 §7：至少 NONE/WEAK/NORMAL/STRONG/EXCESSIVE/UNDETERMINED）。

    注：EXCESSIVE=生扶过旺（生多为克，母慈灭子类）；UNDETERMINED=无法确定。
    从格专用 dts_cong_support_state（NONE/HAS_SUPPORT/UNKNOWN）语义为「有无生扶」，
    属 F-3 裁决独立枚举，不并入本强度枚举。
    """
    NONE = "NONE"
    WEAK = "WEAK"
    NORMAL = "NORMAL"
    STRONG = "STRONG"
    EXCESSIVE = "EXCESSIVE"
    UNDETERMINED = "UNDETERMINED"


class DTSStrengthState(str, Enum):
    """§G-6：旺 ≠ 强；不得使用 score/percentage/probability。"""
    STRONG = "STRONG"
    SLIGHTLY_STRONG = "SLIGHTLY_STRONG"
    NEUTRAL = "NEUTRAL"
    SLIGHTLY_WEAK = "SLIGHTLY_WEAK"
    WEAK = "WEAK"
    UNDETERMINED = "UNDETERMINED"


class DTSEffectState(str, Enum):
    """效力状态（V2.22-PATCH-001 §8：必须含 CONDITIONAL/UNDETERMINED）。

    CONDITIONAL=效力成立但有条件依赖（如伤官配印需身弱方有效）；
    UNDETERMINED=证据/规则不足以确定效力。
    """
    EFFECTIVE = "effective"
    PARTIALLY_EFFECTIVE = "partially_effective"
    INEFFECTIVE = "ineffective"
    BLOCKED = "blocked"
    CONDITIONAL = "conditional"
    UNDETERMINED = "undetermined"


class QTBJRequirementType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    AVOID = "AVOID"


class SMTHCombinationType(str, Enum):
    LIU_HE = "六合"
    SAN_HE = "三合"
    SAN_HUI = "三会"
    BAN_HE = "半合"
    GONG_HE = "拱合"
    AN_HE = "暗合"


class SMTHCompleteness(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class SMTHActivationStatus(str, Enum):
    ACTIVE = "active"
    CONDITIONAL = "conditional"
    INACTIVE = "inactive"


class SFTKDiseaseType(str, Enum):
    DIAO = "雕"
    KU = "枯"
    WANG = "旺"
    RUO = "弱"


class SFTKMedicineType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    THROUGH_CHANNEL = "through_channel"
    PROTECTIVE = "protective"


class SFTKDongjingState(str, Enum):
    DONG = "动"
    JING = "静"
    DONGJING_XIANGJIAN = "动静相兼"


class SFTKGaitouState(str, Enum):
    GAITOU = "盖头"
    BEI_GAI = "被盖"
    WU_GAITOU = "无盖头"


# ---------- 附录 L-7 通用 ----------

class Scope(str, Enum):
    NATAL = "natal"
    DECADE = "decade"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    SHENSHA = "shensha"
    PALACE = "palace"
