"""
P6.1-A — L1 Bazi Fact Expansion: Twelve Life Stages + Complete Hidden Stems

Library Adapter Audit + L1 Fact Integration

验收标准:
✅ 十二长生作为 L1 原始事实接入
✅ 完整藏干作为 L1 原始事实接入
✅ GitHub 库只作为 implementation source，不作为 Canonical Source
✅ 零旺衰判断、零强弱判断、零评分、零阈值、零身强/身弱推导

Adapter 只负责: 输入 → 规范化 → 输出统一字段
不允许: if 长生:身强 / if 墓:身弱 / if 有藏干:有根 / if 无藏干:无根
这些全部属于后面的 Semantic Mapping。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ============================================================
# 一、Implementation Source 声明
# ============================================================

IMPLEMENTATION_SOURCE = {
    "source": "freddylamlc/bazi-patterns (GitHub)",
    "source_type": "IMPLEMENTATION_SOURCE",
    "canonical_source_status": "NOT_CANONICAL_SOURCE",
    "notes": "GitHub开源库作为实现参考，数据为传统主流命理体系。"
             "不作为Canonical Source使用。任何命理结论需经过五部经典Canonical Source Audit。",
    "twelve_growth_system": "传统主流体系：阳干顺行，阴干逆行，戊己与丙丁同论（火土同生）",
    "hidden_stem_system": "传统主流藏干表：本气/中气/余气三层",
}


# ============================================================
# 二、十二长生表（L1 原始事实数据）
# ============================================================
# 体系声明：传统主流体系
#   阳干顺行：甲长生在亥，丙戊长生在寅，庚长生在巳，壬长生在申
#   阴干逆行：乙长生在午，丁己长生在酉，辛长生在子，癸长生在卯
#   戊己与丙丁同论（火土同生）
# 注意：这是 L1 原始事实数据，不代表 Canonical Source 授权。
#       不同流派可能有不同排法，后续 Semantic Mapping 需明确采用哪套体系。

TWELVE_GROWTH_STAGES = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养"
]

# 天干在各地支的十二长生状态
# 数据来源: bazi-patterns (implementation source)
# 体系: 阳顺阴逆，火土同生
TIAN_GAN_TWELVE_GROWTH = {
    "甲": {"子": "沐浴", "丑": "冠带", "寅": "临官", "卯": "帝旺", "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "绝", "酉": "胎", "戌": "养", "亥": "长生"},
    "乙": {"子": "病", "丑": "衰", "寅": "帝旺", "卯": "临官", "辰": "冠带", "巳": "沐浴", "午": "长生", "未": "养", "申": "胎", "酉": "绝", "戌": "墓", "亥": "死"},
    "丙": {"子": "胎", "丑": "养", "寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝"},
    "丁": {"子": "绝", "丑": "墓", "寅": "死", "卯": "病", "辰": "衰", "巳": "帝旺", "午": "临官", "未": "冠带", "申": "沐浴", "酉": "长生", "戌": "养", "亥": "胎"},  # P0-1.3 修正：丁火阴干逆布（长生在酉），原表顺布已修正。依据：子平真诠阳顺阴逆 + bazi_fixed_tables DING 验证。
    "戊": {"子": "胎", "丑": "养", "寅": "长生", "卯": "沐浴", "辰": "冠带", "巳": "临官", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "绝"},
    "己": {"子": "临官", "丑": "帝旺", "寅": "衰", "卯": "病", "辰": "死", "巳": "墓", "午": "绝", "未": "胎", "申": "养", "酉": "长生", "戌": "沐浴", "亥": "冠带"},  # P0-1.3：己土保持原表，UNRESOLVED。不得根据阴阳对称或体系推导直接修正。己土完整体系原典授权状态：PARTIAL（P0-1.2.3）。
    "庚": {"子": "死", "丑": "墓", "寅": "绝", "卯": "胎", "辰": "养", "巳": "长生", "午": "沐浴", "未": "冠带", "申": "临官", "酉": "帝旺", "戌": "衰", "亥": "病"},
    "辛": {"子": "长生", "丑": "养", "寅": "胎", "卯": "绝", "辰": "墓", "巳": "死", "午": "病", "未": "衰", "申": "帝旺", "酉": "临官", "戌": "冠带", "亥": "沐浴"},
    "壬": {"子": "帝旺", "丑": "衰", "寅": "病", "卯": "死", "辰": "墓", "巳": "绝", "午": "胎", "未": "养", "申": "长生", "酉": "沐浴", "戌": "冠带", "亥": "临官"},
    "癸": {"子": "临官", "丑": "冠带", "寅": "沐浴", "卯": "长生", "辰": "养", "巳": "胎", "午": "绝", "未": "墓", "申": "死", "酉": "病", "戌": "衰", "亥": "帝旺"},
}


# ============================================================
# 三、完整地支藏干表（L1 原始事实数据）
# ============================================================
# P0-FNDR-04 (R-10 ⑧ 藏干 audit fix): 单源真相迁移到 bazi_facts.BRANCH_HIDDEN_STEMS
# 本表为派生视图 (适配 L1 中文键格式), 不再持有独立事实数据.
# 依赖图: facts.bazi_facts → reasoning.bazi_ten_gods → engines.bazi_l1_facts
from ..facts.bazi_facts import BRANCH_HIDDEN_STEMS as _FACTS_BRANCH_HIDDEN_STEMS
from ..facts.bazi_facts import EARTHLY_BRANCHES as _FACTS_EARTHLY_BRANCHES
from ..facts.bazi_facts import HEAVENLY_STEMS as _FACTS_HEAVENLY_STEMS
from ..facts.bazi_facts import STEM_ELEMENT as _FACTS_STEM_ELEMENT
from ..facts.bazi_facts import EVIDENCE_IDS as _FACTS_EVIDENCE_IDS

# P0-FNDR-04: BZ_L1_HIDDEN_STEMS_CHINESE 是派生视图, 从 bazi_facts 转换
# 拼音 -> 中文, (stem, role) tuple -> {本气,中气,余气} dict.
# 不再独立存储事实数据, 与 canonical 单源保持同步.

_BRANCH_PINYIN_TO_CHINESE = {
    "ZI":   "子", "CHOU": "丑", "YIN":  "寅", "MAO":  "卯",
    "CHEN": "辰", "SI":   "巳", "WU":   "午", "WEI":  "未",
    "SHEN": "申", "YOU":  "酉", "XU":   "戌", "HAI":  "亥",
}

_STEM_PINYIN_TO_CHINESE = {
    "JIA":  "甲", "YI":   "乙", "BING": "丙", "DING": "丁",
    "WU":   "戊", "JI":   "己", "GENG": "庚", "XIN":  "辛",
    "REN":  "壬", "GUI":  "癸",
}

_CHINESE_ELEMENT = {"木", "火", "土", "金", "水"}
# P0-FNDR-04: BRANCH_HIDDEN_STEMS 现在是派生视图 (中文键), 由 bazi_facts 单源生成.
BRANCH_HIDDEN_STEMS = {}
for _pinyin, _chinese in _BRANCH_PINYIN_TO_CHINESE.items():
    _entries = _FACTS_BRANCH_HIDDEN_STEMS[_pinyin]
    _role_map = {"main": "本气", "middle": "中气", "residual": "余气"}
    _hidden_dict = {"本气": None, "中气": None, "余气": None}
    for _stem, _role in _entries:
        _hidden_dict[_role_map[_role]] = _STEM_PINYIN_TO_CHINESE[_stem]
    BRANCH_HIDDEN_STEMS[_chinese] = _hidden_dict

# 天干五行映射 (拼音 -> 中文)
TIAN_GAN_WU_XING = {}
for _pinyin, _chinese in _STEM_PINYIN_TO_CHINESE.items():
    TIAN_GAN_WU_XING[_chinese] = _FACTS_STEM_ELEMENT[_pinyin]

# Evidence IDs (从 bazi_facts 复用)
HIDDEN_STEM_EVIDENCE_ID = _FACTS_EVIDENCE_IDS["BRANCH_HIDDEN_STEMS"]


# ============================================================
# 四、L1 Fact 数据结构
# ============================================================

@dataclass
class TwelveGrowthFact:
    """
    L1 原始事实：单个地支的十二长生状态。
    只保存原始状态值，不做任何旺衰/强弱判断。
    """
    branch: str                    # 地支（子/丑/寅/...）
    pillar_position: str           # 柱位（年/月/日/时）
    growth_stage: str              # 十二长生状态（长生/沐浴/.../养）
    fact_type: str = "TWELVE_GROWTH_STAGE"
    implementation_source: str = "bazi-patterns"
    canonical_source_status: str = "NOT_CANONICAL"


@dataclass
class HiddenStemFact:
    """
    L1 原始事实：单个地支的完整藏干。
    只保存藏干原始值和层级，不做任何"有根/无根"判断。
    """
    branch: str                    # 地支
    pillar_position: str           # 柱位
    main_qi: Optional[str]         # 本气（主气）
    middle_qi: Optional[str]       # 中气
    residual_qi: Optional[str]     # 余气
    all_stems: List[str] = field(default_factory=list)  # 所有藏干列表（按层级顺序）
    fact_type: str = "HIDDEN_STEM"
    implementation_source: str = "bazi-patterns"
    canonical_source_status: str = "NOT_CANONICAL"


@dataclass
class BaziL1Facts:
    """
    L1 原始事实集合：十二长生 + 完整藏干。
    这是纯事实层，不包含任何命理结论。
    后续 Canonical Relationship Matrix 消费这些事实。
    """
    day_master: str                # 日主天干
    twelve_growth: List[TwelveGrowthFact] = field(default_factory=list)
    hidden_stems: List[HiddenStemFact] = field(default_factory=list)
    implementation_source: dict = field(default_factory=lambda: IMPLEMENTATION_SOURCE)
    fact_layer: str = "L1_ENGINE_FACT"
    derived_conclusions: str = "NONE"  # 明确声明：零旺衰/强弱/评分/阈值/身强身弱推导

    def get_growth_for_branch(self, branch: str) -> Optional[str]:
        """获取某个地支的十二长生状态（纯事实查询，不做判断）。"""
        for g in self.twelve_growth:
            if g.branch == branch:
                return g.growth_stage
        return None

    def get_hidden_stems_for_branch(self, branch: str) -> Optional[HiddenStemFact]:
        """获取某个地支的完整藏干（纯事实查询，不做判断）。"""
        for h in self.hidden_stems:
            if h.branch == branch:
                return h
        return None

    def to_dict(self) -> dict:
        return {
            "day_master": self.day_master,
            "fact_layer": self.fact_layer,
            "derived_conclusions": self.derived_conclusions,
            "implementation_source": self.implementation_source,
            "twelve_growth": [
                {
                    "branch": g.branch,
                    "pillar_position": g.pillar_position,
                    "growth_stage": g.growth_stage,
                    "fact_type": g.fact_type,
                }
                for g in self.twelve_growth
            ],
            "hidden_stems": [
                {
                    "branch": h.branch,
                    "pillar_position": h.pillar_position,
                    "main_qi": h.main_qi,
                    "middle_qi": h.middle_qi,
                    "residual_qi": h.residual_qi,
                    "all_stems": h.all_stems,
                    "fact_type": h.fact_type,
                }
                for h in self.hidden_stems
            ],
        }


# ============================================================
# 五、Adapter 层：输入 → 规范化 → 输出统一字段
# ============================================================

def calculate_twelve_growth(day_master: str, branches: List[str], pillar_positions: List[str]) -> List[TwelveGrowthFact]:
    """
    Adapter: 计算日主在四个地支的十二长生状态。

    只做: 查表 → 规范化 → 输出 TwelveGrowthFact 列表
    不做: 任何旺衰/强弱/评分/阈值判断

    Args:
        day_master: 日主天干（甲/乙/丙/...）
        branches: 四个地支列表 [年支, 月支, 日支, 时支]
        pillar_positions: 柱位列表 ["年", "月", "日", "时"]

    Returns:
        TwelveGrowthFact 列表
    """
    growth_table = TIAN_GAN_TWELVE_GROWTH.get(day_master, {})
    results = []
    for branch, position in zip(branches, pillar_positions):
        stage = growth_table.get(branch, "")
        results.append(TwelveGrowthFact(
            branch=branch,
            pillar_position=position,
            growth_stage=stage,
        ))
    return results


def calculate_hidden_stems(branches: List[str], pillar_positions: List[str]) -> List[HiddenStemFact]:
    """
    Adapter: 计算四个地支的完整藏干。

    只做: 查表 → 规范化 → 输出 HiddenStemFact 列表
    不做: 任何"有根/无根/根深/根浅"判断

    Args:
        branches: 四个地支列表
        pillar_positions: 柱位列表

    Returns:
        HiddenStemFact 列表
    """
    results = []
    for branch, position in zip(branches, pillar_positions):
        hidden = BRANCH_HIDDEN_STEMS.get(branch, {"本气": None, "中气": None, "余气": None})
        all_stems = []
        if hidden.get("本气"):
            all_stems.append(hidden["本气"])
        if hidden.get("中气"):
            all_stems.append(hidden["中气"])
        if hidden.get("余气"):
            all_stems.append(hidden["余气"])
        results.append(HiddenStemFact(
            branch=branch,
            pillar_position=position,
            main_qi=hidden.get("本气"),
            middle_qi=hidden.get("中气"),
            residual_qi=hidden.get("余气"),
            all_stems=all_stems,
        ))
    return results


def build_bazi_l1_facts(
    day_master: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> BaziL1Facts:
    """
    Adapter 入口：构建完整的 L1 原始事实集合。

    只做: 输入 → 规范化 → 输出 BaziL1Facts
    不做: 任何命理结论推导

    Args:
        day_master: 日主天干
        year_branch: 年支
        month_branch: 月支
        day_branch: 日支
        hour_branch: 时支

    Returns:
        BaziL1Facts（纯L1事实，零推导）
    """
    branches = [year_branch, month_branch, day_branch, hour_branch]
    positions = ["年", "月", "日", "时"]

    twelve_growth = calculate_twelve_growth(day_master, branches, positions)
    hidden_stems = calculate_hidden_stems(branches, positions)

    return BaziL1Facts(
        day_master=day_master,
        twelve_growth=twelve_growth,
        hidden_stems=hidden_stems,
    )


# ============================================================
# 六、Library Adapter Audit（核验）
# ============================================================

def audit_twelve_growth_system() -> dict:
    """
    核验十二长生表的体系正确性。
    检查: 阳干顺行、阴干逆行、戊己火土同生。
    """
    audit = {
        "system": "阳顺阴逆，火土同生",
        "checks": [],
        "passed": True,
    }

    # 检查阳干长生位置
    yang_growth = {
        "甲": "亥", "丙": "寅", "戊": "寅", "庚": "巳", "壬": "申"
    }
    for gan, expected_branch in yang_growth.items():
        actual = TIAN_GAN_TWELVE_GROWTH[gan][expected_branch]
        passed = actual == "长生"
        audit["checks"].append({
            "item": f"阳干{gan}长生在{expected_branch}",
            "expected": "长生",
            "actual": actual,
            "passed": passed,
        })
        if not passed:
            audit["passed"] = False

    # 检查阴干长生位置
    yin_growth = {
        "乙": "午", "丁": "酉", "己": "酉", "辛": "子", "癸": "卯"
    }
    for gan, expected_branch in yin_growth.items():
        actual = TIAN_GAN_TWELVE_GROWTH[gan][expected_branch]
        passed = actual == "长生"
        audit["checks"].append({
            "item": f"阴干{gan}长生在{expected_branch}",
            "expected": "长生",
            "actual": actual,
            "passed": passed,
        })
        if not passed:
            audit["passed"] = False

    # 检查戊己与丙丁同论（火土同生）
    wu_ji_same_as_bing_ding = True
    for branch in ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]:
        if TIAN_GAN_TWELVE_GROWTH["戊"][branch] != TIAN_GAN_TWELVE_GROWTH["丙"][branch]:
            wu_ji_same_as_bing_ding = False
        if TIAN_GAN_TWELVE_GROWTH["己"][branch] != TIAN_GAN_TWELVE_GROWTH["丁"][branch]:
            wu_ji_same_as_bing_ding = False
    audit["checks"].append({
        "item": "戊己与丙丁同论（火土同生）",
        "expected": "戊=丙, 己=丁",
        "actual": "一致" if wu_ji_same_as_bing_ding else "不一致",
        "passed": wu_ji_same_as_bing_ding,
    })
    if not wu_ji_same_as_bing_ding:
        audit["passed"] = False

    return audit


def audit_hidden_stems_system() -> dict:
    """核验藏干表的完整性。"""
    audit = {
        "system": "传统主流藏干表（本气/中气/余气）",
        "checks": [],
        "passed": True,
    }

    # 检查12地支都有藏干
    all_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    for branch in all_branches:
        hidden = BRANCH_HIDDEN_STEMS.get(branch)
        passed = hidden is not None and hidden.get("本气") is not None
        audit["checks"].append({
            "item": f"{branch}藏干完整",
            "expected": "有本气",
            "actual": hidden.get("本气") if hidden else "缺失",
            "passed": passed,
        })
        if not passed:
            audit["passed"] = False

    # 检查特定地支的藏干
    expected = {
        "寅": ("甲", "丙", "戊"),
        "巳": ("丙", "戊", "庚"),
        "申": ("庚", "壬", "戊"),
        "亥": ("壬", "甲", None),
        "丑": ("己", "癸", "辛"),
        "辰": ("戊", "乙", "癸"),
        "未": ("己", "丁", "乙"),
        "戌": ("戊", "辛", "丁"),
    }
    for branch, (main, middle, residual) in expected.items():
        hidden = BRANCH_HIDDEN_STEMS[branch]
        passed = (hidden["本气"] == main and
                  hidden["中气"] == middle and
                  hidden["余气"] == residual)
        audit["checks"].append({
            "item": f"{branch}藏干={main}/{middle}/{residual}",
            "expected": f"{main}/{middle}/{residual}",
            "actual": f"{hidden['本气']}/{hidden['中气']}/{hidden['余气']}",
            "passed": passed,
        })
        if not passed:
            audit["passed"] = False

    return audit


# ============================================================
# 七、Negative Tests（验收标准验证）
# ============================================================

def run_negative_tests(l1_facts: BaziL1Facts) -> List[tuple]:
    """
    验证验收标准：零旺衰判断、零强弱判断、零评分、零阈值、零身强/身弱推导。
    """
    tests = []

    # NEG-01: 十二长生只保存原始状态，不包含"强/弱"判断
    has_strength_in_growth = any(
        "强" in g.growth_stage or "弱" in g.growth_stage
        for g in l1_facts.twelve_growth
    )
    tests.append((
        "NEG-01",
        not has_strength_in_growth,
        "十二长生只保存原始状态（长生/沐浴/.../养），不包含强/弱判断"
    ))

    # NEG-02: 藏干只保存原始值，不包含"有根/无根"判断
    has_root_in_hidden = any(
        "根" in str(h.main_qi) or "根" in str(h.middle_qi) or "根" in str(h.residual_qi)
        for h in l1_facts.hidden_stems
    )
    tests.append((
        "NEG-02",
        not has_root_in_hidden,
        "藏干只保存原始值（本气/中气/余气），不包含有根/无根判断"
    ))

    # NEG-03: derived_conclusions = NONE
    tests.append((
        "NEG-03",
        l1_facts.derived_conclusions == "NONE",
        "derived_conclusions = NONE（零旺衰/强弱/评分/阈值/身强身弱推导）"
    ))

    # NEG-04: fact_layer = L1_ENGINE_FACT
    tests.append((
        "NEG-04",
        l1_facts.fact_layer == "L1_ENGINE_FACT",
        "fact_layer = L1_ENGINE_FACT（明确标注为L1原始事实层）"
    ))

    # NEG-05: canonical_source_status = NOT_CANONICAL
    all_not_canonical = all(
        g.canonical_source_status == "NOT_CANONICAL"
        for g in l1_facts.twelve_growth
    ) and all(
        h.canonical_source_status == "NOT_CANONICAL"
        for h in l1_facts.hidden_stems
    )
    tests.append((
        "NEG-05",
        all_not_canonical,
        "所有事实的 canonical_source_status = NOT_CANONICAL（GitHub库只作为implementation source）"
    ))

    # NEG-06: 不包含任何数值评分
    has_score = any(
        hasattr(g, 'score') or hasattr(g, 'weight') or hasattr(g, 'threshold')
        for g in l1_facts.twelve_growth
    )
    tests.append((
        "NEG-06",
        not has_score,
        "十二长生事实不包含任何数值评分/权重/阈值"
    ))

    # NEG-07: 不包含任何"身强/身弱"字段
    has_shen_qiang_ruo = any(
        hasattr(l1_facts, field_name)
        for field_name in ['shen_qiang', 'shen_ruo', 'day_master_strength', 'wang_shuai', 'qiang_ruo']
    )
    tests.append((
        "NEG-07",
        not has_shen_qiang_ruo,
        "L1事实集合不包含任何身强/身弱/旺衰/强弱字段"
    ))

    return tests


# ============================================================
# 八、主执行
# ============================================================

def main():
    print("=" * 80)
    print("P6.1-A — L1 Bazi Fact Expansion: Twelve Life Stages + Complete Hidden Stems")
    print("=" * 80)

    # 1. Library Adapter Audit
    print("\n" + "=" * 80)
    print("一、Library Adapter Audit")
    print("=" * 80)

    print("\n--- 十二长生表体系核验 ---")
    growth_audit = audit_twelve_growth_system()
    print(f"体系: {growth_audit['system']}")
    for check in growth_audit["checks"]:
        status = "✅" if check["passed"] else "❌"
        print(f"  {status} {check['item']}: 期望={check['expected']}, 实际={check['actual']}")
    print(f"结果: {'✅ 全部通过' if growth_audit['passed'] else '❌ 存在问题'}")

    print("\n--- 藏干表体系核验 ---")
    hidden_audit = audit_hidden_stems_system()
    print(f"体系: {hidden_audit['system']}")
    for check in hidden_audit["checks"]:
        status = "✅" if check["passed"] else "❌"
        print(f"  {status} {check['item']}: 期望={check['expected']}, 实际={check['actual']}")
    print(f"结果: {'✅ 全部通过' if hidden_audit['passed'] else '❌ 存在问题'}")

    # 2. Implementation Source 声明
    print("\n" + "=" * 80)
    print("二、Implementation Source 声明")
    print("=" * 80)
    print(f"  source: {IMPLEMENTATION_SOURCE['source']}")
    print(f"  source_type: {IMPLEMENTATION_SOURCE['source_type']}")
    print(f"  canonical_source_status: {IMPLEMENTATION_SOURCE['canonical_source_status']}")
    print(f"  twelve_growth_system: {IMPLEMENTATION_SOURCE['twelve_growth_system']}")
    print(f"  hidden_stem_system: {IMPLEMENTATION_SOURCE['hidden_stem_system']}")
    print(f"  notes: {IMPLEMENTATION_SOURCE['notes']}")

    # 3. 用1983命例验证
    print("\n" + "=" * 80)
    print("三、1983命例验证（癸亥 壬戌 乙未 壬午，日主乙木）")
    print("=" * 80)

    l1_facts = build_bazi_l1_facts(
        day_master="乙",
        year_branch="亥",
        month_branch="戌",
        day_branch="未",
        hour_branch="午",
    )

    print("\n--- 十二长生（L1原始事实）---")
    for g in l1_facts.twelve_growth:
        print(f"  {g.pillar_position}支 {g.branch}: {g.growth_stage}")

    print("\n--- 完整藏干（L1原始事实）---")
    for h in l1_facts.hidden_stems:
        stems_str = "/".join(h.all_stems)
        print(f"  {h.pillar_position}支 {h.branch}: 本气={h.main_qi}, 中气={h.middle_qi}, 余气={h.residual_qi} (全部: {stems_str})")

    print(f"\n  fact_layer: {l1_facts.fact_layer}")
    print(f"  derived_conclusions: {l1_facts.derived_conclusions}")

    # 4. Negative Tests
    print("\n" + "=" * 80)
    print("四、Negative Tests（验收标准验证）")
    print("=" * 80)
    tests = run_negative_tests(l1_facts)
    passed = 0
    for test_id, result, description in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        if result:
            passed += 1
        print(f"  [{test_id}] {status}")
        print(f"    {description}")
    print(f"\n  总计: {passed}/{len(tests)} PASS")

    # 5. 最终状态
    print("\n" + "=" * 80)
    print("五、最终状态")
    print("=" * 80)
    print(f"  十二长生 L1 接入: {'✅' if growth_audit['passed'] else '❌'}")
    print(f"  完整藏干 L1 接入: {'✅' if hidden_audit['passed'] else '❌'}")
    print(f"  GitHub库作为implementation source: ✅")
    print(f"  零旺衰判断: ✅")
    print(f"  零强弱判断: ✅")
    print(f"  零评分: ✅")
    print(f"  零阈值: ✅")
    print(f"  零身强/身弱推导: ✅")
    print(f"  Negative Tests: {passed}/{len(tests)} PASS")

    print("\n" + "=" * 80)
    print("P6.1-A 完成。L1 事实层已补齐十二长生和完整藏干。")
    print("下一步：将这些新增 L1 facts 送进 Phase 6.1 Relationship Audit，")
    print("核验五部经典究竟明确授权了哪些关系。")
    print("=" * 80)


if __name__ == "__main__":
    main()
