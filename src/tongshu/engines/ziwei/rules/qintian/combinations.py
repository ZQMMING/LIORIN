# -*- coding: utf-8 -*-
"""
Qintian Combinations — 钦天门组合 detect 函数（Z44 蔡明宏主源版）

严格工程边界：
- 60 条 production detect 函数（grade 1×58 / 3×2，蔡明宏《悟我十八年》原文支持）
- detect 返回 QintianCombination-style dataclass
- 所有 detect 失败/缺失返回 None (fail-closed)
- Z44 主源切换：许铨仁/四余独步规则清除，主源=蔡明宏《悟我十八年》

规则清单（全部蔡明宏原文）：
  - QTN-CMB-001 来因宫 = 生年干所在宫位
  - QTN-CMB-002 生年四化=空间(体) / 自化=时间(用)
  - QTN-CMB-003 自化本义（引言·平衡原理/无为而自化/时空效应）
  - QTN-CMB-004 向心自化（箭头向内，物质的凝聚）
  - QTN-CMB-005 自化理象气数（四导读：理=平衡原理/象=时空出入/数=变化论/气=时间存有论）
  - QTN-CMB-006 串联自化（同向自化串联）
  - QTN-CMB-007 离心自化（箭头向外，物质的分散）
  - QTN-CMB-008 自化次序（生年忌再自化禄：由少到多之量）
  - QTN-CMB-009 自化理体论（生年四化=理体/自化=用/自化皆法象生年四化）
  - QTN-CMB-010 自化基本分类（单星/双星/串联/纯自化；来因宫自化另解）
  - QTN-CMB-011 自化五分类（生年有/无自化 × 飞宫遇/不遇）
  - QTN-CMB-012 出与入（自化面对生年四化的出入）
  - QTN-CMB-013 法象（自化之象对照生年四化宫位）
  - QTN-CMB-034 五行局论断（共用部分：陆斌兆《讲义》原文，grade=1）
  - QTN-CMB-035 五行局×身宫论断（南派陆斌兆体系延伸，grade=3；身宫落非六寄宫无论断）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from ..feixing_rule_graph import FlyingTransformFact, PalaceStemFact
from .qintian_shihua_readings import TEN_GAN_SIHUA_READINGS
from .features import (
    get_laiyin_palace, get_self_mutagen, get_xiangxin_mutagen, get_lixin_mutagen,
)

logger = logging.getLogger(__name__)


@dataclass
class QintianCombination:
    """钦天门单条组合 detect 结果"""
    rule_id: str
    detected: bool
    evidence_grade: int
    facts: Dict[str, Any] = field(default_factory=dict)
    semantic_summary: str = ""


# 斗数十二宫固定序（自命宫起 1-12）
# Z80-F（2026-10-14）：第 8 宫统一用「仆役」（= iztro/引擎盘面命名），
# 此前用书之「交友」，与 chart.palaces / flying_transforms 的「仆役」
# 不一致 → _palace_index("仆役") 返回 -1，凡涉及该宫的规则静默漏检
# （如空宫双忌 L2462、对宫互飞 L1216）。别名经 _palace_index 归一化兼容。
ZW_PALACES_ORDER = [
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
]

# 宫名别名：书之「交友宫」= iztro/引擎「仆役宫」（同一宫）
_PALACE_NAME_ALIAS = {"交友": "仆役"}


def _palace_index(name: str) -> int:
    """宫位序号（1-12）。兼容「交友」(书) / 「仆役」(iztro) 两种写法。"""
    name = _PALACE_NAME_ALIAS.get(name, name)
    try:
        return ZW_PALACES_ORDER.index(name) + 1
    except ValueError:
        return -1


def _triple_of(palace: str) -> List[str]:
    """以某宫立极的三合（书464行：命宫、财帛宫、官禄宫为之三合）
    以 A 为命 → A 的财帛 = A+4，A 的官禄 = A+8（顺数）。
    """
    i = _palace_index(palace)
    if i < 0:
        return []
    names = [palace]
    for off in (4, 8):
        idx = (i - 1 + off) % 12
        names.append(ZW_PALACES_ORDER[idx])
    return names


# ============================================================
# 60 条 production detect（grade 1×58 / 3×2）
# ============================================================

def detect_qtn_cmb_001_laiyin(chart) -> Optional[QintianCombination]:
    """QTN-CMB-001: 来因宫 = 生年干所在宫位（蔡明宏：太极即来因宫）"""
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    laiyin = get_laiyin_palace(chart.birth_year, palace_stems)
    if not laiyin:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-001",
        detected=True,
        evidence_grade=1,
        facts={
            "laiyin_palace": laiyin,
            "birth_year": chart.birth_year,
            "trigger_pattern": "来因宫 = 生年干所在宫位",
        },
        semantic_summary=(
            f"生年{chart.birth_year}年来因宫落{laiyin}，"
            f"此宫即命盘之「太极」，看四化之所用（蔡明宏《悟我十八年》）。"
        ),
    )


def detect_qtn_cmb_002_space_time(chart) -> Optional[QintianCombination]:
    """QTN-CMB-002: 生年四化=空间(体) / 自化=时间(用)

    蔡明宏：生年的象是空间性的（物的存在论）；自化的象是时间性的。
    两要素齐备（来因宫 + 至少1处自化）构成完整时空结构。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    laiyin = get_laiyin_palace(chart.birth_year, palace_stems)
    if not laiyin:
        return None

    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-002",
        detected=True,
        evidence_grade=1,
        facts={
            "laiyin_palace": laiyin,
            "self_mutagen_count": len(self_mutagens),
            "self_mutagens": [
                f"{ft.source_palace}/{ft.transformation}" for ft in self_mutagens
            ],
            "trigger_pattern": "来因宫 + 自化 双要素齐备（体+用）",
        },
        semantic_summary=(
            f"来因宫{laiyin}（体/空间）+ {len(self_mutagens)} 处自化（用/时间），"
            f"构成钦天完整时空结构（蔡明宏：生年四化体用合一）。"
        ),
    )


def detect_qtn_cmb_003_zihua_benyi(chart) -> Optional[QintianCombination]:
    """QTN-CMB-003: 自化本义（引言·平衡原理 / 无为而自化 / 时空效应）

    蔡明宏原文（自化篇·单元一 引言）：
    - 自化，是指一件事物现象本俱该有的平衡原理，就像五行，不能太过或不及一般。
      太过与不及就失去了它的平衡性，导致于出现了一件事物的吉或凶。
    - 它是应时间（不论大限或流年）而发生的，故它是无为的，自然而形成的，
      故曰：无为而自化。
    - 自化强调于时空效应法则，是一种事物变化的自然规律。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None
    n = len(self_mutagens)
    return QintianCombination(
        rule_id="QTN-CMB-003",
        detected=True,
        evidence_grade=1,
        facts={
            "self_count": n,
            "trigger_pattern": "本盘存在自化（自化=事物现象本俱的平衡原理）",
        },
        semantic_summary=(
            f"本盘有{n}处自化。自化，是指一件事物现象本俱该有的平衡原理，"
            f"如五行不能太过或不及，太过不及则失其平衡性，致吉凶生焉。"
            f"自化应时间而发，无为而自化；强调时空效应法则，是事物变化的自然规律"
            f"（蔡明宏《悟我十八年》自化篇·引言）。"
        ),
    )


def detect_qtn_cmb_004_xiangxin(chart) -> Optional[QintianCombination]:
    """QTN-CMB-004: 向心自化（箭头向内，物质的凝聚）"""
    xiangxin = get_xiangxin_mutagen(chart)
    if not xiangxin:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-004",
        detected=True,
        evidence_grade=1,
        facts={
            "xiangxin_count": len(xiangxin),
            "xiangxin_list": [
                f"{ft.source_palace}→{ft.target_palace}/{ft.transformation}"
                for ft in xiangxin
            ],
            "trigger_pattern": "至少 1 个向心自化（箭头向内）",
        },
        semantic_summary=(
            f"发现{len(xiangxin)}处向心自化，"
            f"主物质的凝聚（蔡明宏：箭头向内→向心力→物质的凝聚）。"
        ),
    )


def detect_qtn_cmb_005_lixiangqishu(chart) -> Optional[QintianCombination]:
    """QTN-CMB-005: 自化理象气数（四导读）

    蔡明宏原文（自化篇·单元二 导读）：
    - 就自化来说「理」——根本就是指宇宙万有现象的平衡原理。
      太极若引用在斗数上，所指的就是来因宫。
    - 就自化来说「象」——约而言之，就是现象有时空的出入。
    - 就自化来说「数」——现象存在的另一种变化论。
    - 就自化来说「气」——在表达时间上的种种不同物相的存有论。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-005",
        detected=True,
        evidence_grade=1,
        facts={
            "li": "宇宙万有现象的平衡原理（太极即来因宫）",
            "xiang": "现象有时空的出入",
            "shu": "现象存在的另一种变化论",
            "qi": "时间上种种不同物相的存有论",
            "trigger_pattern": "本盘存在自化 → 理象气数四要齐观",
        },
        semantic_summary=(
            f"本盘有自化，以理象气数四要观之："
            f"理=宇宙万有现象的平衡原理（太极即来因宫）；"
            f"象=现象有时空的出入；"
            f"数=现象存在的另一种变化论；"
            f"气=时间上种种不同物相的存有论（蔡明宏《悟我十八年》自化篇·导读）。"
        ),
    )


def detect_qtn_cmb_006_chuanlian(chart) -> Optional[QintianCombination]:
    """QTN-CMB-006: 串联自化

    蔡明宏：自化的游戏规则（3）串联与不串联；飞宫不遇生年四化但有自化者（并串联）。
    检测: 同一种四化的自化出现在 >=2 个不同宫位即串联。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None

    by_transform: dict = {}
    for ft in self_mutagens:
        by_transform.setdefault(ft.transformation, []).append(ft)

    chuanlian = []
    for transform, fts in by_transform.items():
        palaces = sorted({ft.source_palace for ft in fts})
        if len(palaces) >= 2:
            chuanlian.append({
                "transformation": transform,
                "palaces": palaces,
                "stars": sorted({ft.target_star for ft in fts}),
                "count": len(fts),
            })

    if not chuanlian:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-006",
        detected=True,
        evidence_grade=1,
        facts={
            "chuanlian_count": len(chuanlian),
            "chuanlian_list": chuanlian,
            "trigger_pattern": "同向自化（同四化）串联 >=2 宫",
        },
        semantic_summary=(
            f"发现{len(chuanlian)}组串联自化："
            + "、".join(f"{c['transformation']}@{'+'.join(c['palaces'])}" for c in chuanlian)
            + "（蔡明宏：串联与不串联）。"
        ),
    )


def detect_qtn_cmb_007_lixin(chart) -> Optional[QintianCombination]:
    """QTN-CMB-007: 离心自化（箭头向外，物质的分散）"""
    lixin = get_lixin_mutagen(chart)
    if not lixin:
        return None

    branch_dist: dict = {}
    palace_to_branch = {pf.palace_name: pf.branch for pf in chart.palace_stems}
    for ft in lixin:
        branch = palace_to_branch.get(ft.source_palace)
        if branch:
            branch_dist.setdefault(branch, 0)
            branch_dist[branch] += 1

    return QintianCombination(
        rule_id="QTN-CMB-007",
        detected=True,
        evidence_grade=1,
        facts={
            "lixin_count": len(lixin),
            "branch_distribution": branch_dist,
            "lixin_list": [
                f"{ft.source_palace}{ft.target_star}{ft.transformation}"
                for ft in lixin
            ],
            "trigger_pattern": "离心自化（箭头向外）",
        },
        semantic_summary=(
            f"发现{len(lixin)}处离心自化，"
            f"主物质的分散——把已有的事物现象变成没有或改变另一种模式（蔡明宏）。"
        ),
    )


def detect_qtn_cmb_008_zihua_cixu(chart) -> Optional[QintianCombination]:
    """QTN-CMB-008: 自化次序（生年忌再自化禄：由少到多之量）

    蔡明宏原文（自化篇·单元二 自化诠释 + 单元三 应用）：
    - 生年忌 再 自化禄：化忌主冬天，自化了禄，那好比今年冬天的植物，
      到明年秋天收成，这就是次序。
    - 生年忌在财，本是劳碌或上班的安定薪俸财。但因为化忌，再自化禄，
      代表会由少到多的「量」。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())

    # 生年四化所在宫
    sheng_nian_palaces = []
    for pf in chart.palace_stems:
        if any(s in pf.major_stars for s in birth_sihua):
            sheng_nian_palaces.append(pf.palace_name)
    if not sheng_nian_palaces:
        return None

    # 同宫生年四化 + 自化（次序现象）
    same_palace = [ft for ft in self_mutagens if ft.source_palace in sheng_nian_palaces]
    if not same_palace:
        return None

    order_notes = []
    for ft in same_palace:
        sn_idx = birth_sihua.index(ft.target_star) if ft.target_star in birth_sihua else None
        if sn_idx is not None:
            sheng_transform = ["禄", "权", "科", "忌"][sn_idx]
            order_notes.append(
                f"{ft.source_palace}生年{sheng_transform}再自化{ft.transformation}"
            )
    if not order_notes:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-008",
        detected=True,
        evidence_grade=1,
        facts={
            "order_phenomena": order_notes,
            "trigger_pattern": "生年四化所在宫同时有自化（生年X再自化Y = 次序）",
        },
        semantic_summary=(
            f"自化次序：{('；'.join(order_notes))}。"
            f"生年忌再自化禄，如今年冬天植物到明年秋天收成，是即次序；"
            f"生年忌在财再自化禄，本是劳碌或上班的安定薪俸财，化忌再自化禄，"
            f"代表会由少到多的量（蔡明宏《悟我十八年》自化篇）。"
        ),
    )


def detect_qtn_cmb_009_zihua_liti(chart) -> Optional[QintianCombination]:
    """QTN-CMB-009: 自化理体论（生年四化=理体 / 自化=用 / 自化皆法象生年四化）

    蔡明宏原文（自化篇·单元三 诠释(一) 自化在理上而言）：
    - 生年四化，就是「理」的本体存在论。
    - 生年又自化，就是自化的「用」，在「体」上发生了种种情况的变化。
    - 自化的「象」，都要「法象」到生年四化上去，再由宫位上判断现象的吉凶祸福。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    has_sheng_nian = any(
        any(s in pf.major_stars for s in birth_sihua) for pf in chart.palace_stems
    )
    if not has_sheng_nian:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-009",
        detected=True,
        evidence_grade=1,
        facts={
            "li_ti": "生年四化=理的本体存在论",
            "yong": "生年又自化=自化的用（在体上发生种种变化）",
            "faxiang_rule": "自化的象都要法象到生年四化上去，再由宫位判断吉凶",
            "trigger_pattern": "有生年四化 + 有自化 → 体用兼备",
        },
        semantic_summary=(
            f"自化理体论：生年四化是理的本体存在论（有物在先）；"
            f"生年又自化是自化的用，在体上发生种种情况的变化。"
            f"自化的象都要法象到生年四化上去，再由宫位上判断现象的吉凶祸福"
            f"（蔡明宏《悟我十八年》自化篇·理体论）。"
        ),
    )


def detect_qtn_cmb_010_zihua_fenlei(chart) -> Optional[QintianCombination]:
    """QTN-CMB-010: 自化基本分类（单星/双星/串联/纯自化；来因宫自化另解）

    蔡明宏原文（自化篇·单元三）：
    基本分类如下：
      第一、生年单星自化
      第二、生年双星自化
      第三、生年四化，自化又串联
      第四、无生年四化，但有自化——并串联
    注：来因宫自化者，请见来因宫专解。（不在此限）
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())

    # 生年四化星→宫
    sheng_nian_star_palaces = {}
    for pf in chart.palace_stems:
        for s in pf.major_stars:
            if s in birth_sihua:
                sheng_nian_star_palaces[s] = pf.palace_name

    laiyin = get_laiyin_palace(chart.birth_year, chart.palace_stems)

    # 按宫聚自化
    by_palace = {}
    for ft in self_mutagens:
        by_palace.setdefault(ft.source_palace, []).append(ft)

    single, double, pure, chuanlian, laiyin_self = [], [], [], [], []
    for palace, fts in by_palace.items():
        sheng_stars = {ft.target_star for ft in fts if ft.target_star in sheng_nian_star_palaces}
        if palace == laiyin:
            laiyin_self.append(f"{palace}（来因宫自化，另见来因宫专解）")
        elif len(sheng_stars) == 1:
            single.append(f"{palace}（{next(iter(sheng_stars))}生年单星自化）")
        elif len(sheng_stars) >= 2:
            double.append(f"{palace}（{'、'.join(sorted(sheng_stars))}生年双星自化）")
        else:
            pure.append(f"{palace}（无生年四化，纯自化）")

    # 串联：同transform跨>=2宫
    by_transform = {}
    for ft in self_mutagens:
        by_transform.setdefault(ft.transformation, set()).add(ft.source_palace)
    for t, palaces in by_transform.items():
        if len(palaces) >= 2:
            chuanlian.append(f"{t}化串联{'、'.join(sorted(palaces))}")

    parts = []
    if single:
        parts.append("生年单星自化：" + "；".join(single))
    if double:
        parts.append("生年双星自化：" + "；".join(double))
    if chuanlian:
        parts.append("自化又串联：" + "；".join(chuanlian))
    if pure:
        parts.append("无生年四化但有自化：" + "；".join(pure))
    if laiyin_self:
        parts.append("来因宫自化（另解）：" + "；".join(laiyin_self))

    return QintianCombination(
        rule_id="QTN-CMB-010",
        detected=True,
        evidence_grade=1,
        facts={
            "single": single, "double": double, "pure": pure,
            "chuanlian": chuanlian, "laiyin_self": laiyin_self,
            "trigger_pattern": "自化基本分类（单星/双星/串联/纯自化）",
        },
        semantic_summary=(
            "自化基本分类：" + ("；".join(parts) if parts else "（本盘自化归属待判）")
            + "（蔡明宏《悟我十八年》自化篇；来因宫自化者另见来因宫专解）"
        ),
    )


def detect_qtn_cmb_011_wufenlei(chart) -> Optional[QintianCombination]:
    """QTN-CMB-011: 自化五分类

    蔡明宏原文：
    （一）生年四化，有自化者。（包括来因宫本身自己有自化者）
    （二）生年四化，没有自化者。
    （三）无生年四化，有自化者。
    （四）飞宫遇生年四化，又有自化者。
    （五）飞宫不遇生年四化，但有自化者。（并串联）
    """
    self_mutagens = get_self_mutagen(chart)
    # 生年四化（年干四化）落宫
    from ....ziwei_engine import GAN_SIHUA
    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())

    # 生年四化星所在宫（main stars 含该星）
    sheng_nian_palaces = []
    for pf in chart.palace_stems:
        if any(s in pf.major_stars for s in birth_sihua):
            sheng_nian_palaces.append(pf.palace_name)

    has_sheng_nian = len(sheng_nian_palaces) > 0
    has_self = len(self_mutagens) > 0

    # 飞宫 = 宫干四化（flying_transforms 中非生年干来源者）
    flying_transforms = [ft for ft in chart.flying_transforms]
    # 串联合并判定
    chuanlian = 0
    by_transform: dict = {}
    for ft in self_mutagens:
        by_transform.setdefault(ft.transformation, []).append(ft)
    for transform, fts in by_transform.items():
        if len({ft.source_palace for ft in fts}) >= 2:
            chuanlian += 1

    # 归类
    if has_sheng_nian and has_self:
        cat = "（一）生年四化有自化者（含来因宫自化）"
    elif has_sheng_nian and not has_self:
        cat = "（二）生年四化没有自化者"
    elif not has_sheng_nian and has_self:
        cat = "（三）无生年四化有自化者"
    else:
        cat = "（四）无生年四化且无自化者（盘面无自化）"

    note = f"，并串联{chuanlian}组" if chuanlian else ""

    return QintianCombination(
        rule_id="QTN-CMB-011",
        detected=True,
        evidence_grade=1,
        facts={
            "category": cat,
            "sheng_nian_palaces": sheng_nian_palaces,
            "sheng_nian_sihua": list(birth_sihua),
            "self_mutagen_count": len(self_mutagens),
            "chuanlian_count": chuanlian,
            "flying_transform_count": len(flying_transforms),
            "trigger_pattern": "自化五分类判定",
        },
        semantic_summary=(
            f"本盘归类：{cat}（蔡明宏自化五分类）{note}。"
        ),
    )


def detect_qtn_cmb_012_churu(chart) -> Optional[QintianCombination]:
    """QTN-CMB-012: 出与入

    蔡明宏原文：站在太阴化禄的流年（酉宫）去面对巨门的自化禄是'入'。
    站在巨门的自化禄去面对太阴的化禄是'出'。

    检测：生年四化宫 与 自化宫 的相对视角（入=生年四化面对自化；出=自化面对生年四化）。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None

    from ....ziwei_engine import GAN_SIHUA
    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())

    # 生年四化宫
    sheng_nian_palaces = []
    for pf in chart.palace_stems:
        if any(s in pf.major_stars for s in birth_sihua):
            sheng_nian_palaces.append(pf.palace_name)

    if not sheng_nian_palaces:
        return None

    # 与生年四化同宫的自化 = 入（生年四化面对自化）；异宫自化 = 出
    churu = []
    for ft in self_mutagens:
        if ft.source_palace in sheng_nian_palaces:
            churu.append(f"{ft.source_palace}{ft.transformation}（入）")
        else:
            churu.append(f"{ft.source_palace}{ft.transformation}（出）")

    return QintianCombination(
        rule_id="QTN-CMB-012",
        detected=True,
        evidence_grade=1,
        facts={
            "churu_list": churu,
            "sheng_nian_palaces": sheng_nian_palaces,
            "trigger_pattern": "自化相对生年四化的出入视角",
        },
        semantic_summary=(
            "出入判定（蔡明宏）：" + "；".join(churu[:8])
            + "（入=自化面对生年四化；出=自化背离生年四化）。"
        ),
    )


def detect_qtn_cmb_013_faxiang(chart) -> Optional[QintianCombination]:
    """QTN-CMB-013: 法象（自化之象对照生年四化宫位）

    蔡明宏原文：把自化的'象'（看是禄、权、科、忌的那一种），再去对照生年四化的宫位，
    然后依两宫位互动，就产生了现象与物相及吉或凶的征兆。
    """
    self_mutagens = get_self_mutagen(chart)
    if not self_mutagens:
        return None

    from ....ziwei_engine import GAN_SIHUA
    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())

    # 生年四化：星→宫 映射
    sheng_nian_map = {}  # star -> palace
    for pf in chart.palace_stems:
        for s in pf.major_stars:
            if s in birth_sihua:
                sheng_nian_map[s] = pf.palace_name

    # 法象：自化（象）→ 对照生年四化宫位
    faxiang = []
    for ft in self_mutagens:
        sn = sheng_nian_map.get(ft.target_star)
        if sn:
            faxiang.append({
                "self": f"{ft.source_palace}{ft.target_star}{ft.transformation}",
                "faxiang_to": sn,
            })

    return QintianCombination(
        rule_id="QTN-CMB-013",
        detected=True,
        evidence_grade=1,
        facts={
            "faxiang_list": faxiang,
            "self_mutagen_count": len(self_mutagens),
            "trigger_pattern": "自化之象法象到生年四化宫位",
        },
        semantic_summary=(
            f"法象判定（蔡明宏）：{len(faxiang)} 处自化法象到生年四化宫位"
            + ("：" + "；".join(f"{f['self']}→{f['faxiang_to']}" for f in faxiang[:6]) if faxiang else "（无同星生年四化可法象）")
            + "。"
        ),
    )


def detect_qtn_cmb_014_shengong(chart) -> Optional[QintianCombination]:
    """QTN-CMB-014: 北派身宫论断（命为体身为用，身宫=此生执念/果报落点）

    北派钦天二手整理（derived grade=3，未在《悟我十八年》原文检索到）：
    身宫六寄宫：子午=命 辰戌=财帛 寅申=官禄 卯酉=迁移 丑未=福德 巳亥=夫妻
    看身宫首看生年四化、宫内自化，次看三方四正，不可单以星曜断吉凶。
    """
    from ..shengong_wuxing_data import (
        get_qintian_shengong_total,
        get_qintian_shengong_assertion,
        SHENGONG_PALACE_DISPLAY,
    )

    soul_br = chart.body_earthly_branch  # 身宫地支（Z45fix：body 才是身宫）
    if not soul_br:
        return None
    shen_name = ""
    for _pn, _pd in chart.palaces.items():
        if _pd.get("branch") == soul_br:
            shen_name = _pn
            break
    if not shen_name:
        return None

    total = get_qintian_shengong_total()
    data = get_qintian_shengong_assertion(shen_name)
    if not data:
        # 身宫落非六寄宫（兄弟/子女/田宅/疾厄/仆役/父母）：只出总诀
        return QintianCombination(
            rule_id="QTN-CMB-014",
            detected=True,
            evidence_grade=3,
            facts={
                "shen_palace": shen_name,
                "shen_branch": soul_br,
                "total_assertion": total["text"],
                "has_palace_assertion": False,
                "trigger_pattern": "北派身宫论断（总诀）",
            },
            semantic_summary=(
                f"身宫落{shen_name}（非六寄宫），北派只出总诀：命为体身为用，"
                f"身宫=此生追求/执念/果报落点（北派二手整理 derived grade=3，未在《悟我十八年》原文检索到）。"
            ),
        )

    display = SHENGONG_PALACE_DISPLAY.get(shen_name, shen_name + "宫")
    return QintianCombination(
        rule_id="QTN-CMB-014",
        detected=True,
        evidence_grade=3,
        facts={
            "shen_palace": shen_name,
            "shen_branch": soul_br,
            "total_assertion": total["text"],
            "palace_assertion": data["text"],
            "palace_features": data["features"],
            "palace_display": display,
            "has_palace_assertion": True,
            "trigger_pattern": "北派身宫论断（六寄宫）",
        },
        semantic_summary=(
            f"北派身宫落{display}：{data['text'][:60]}..."
        ),
    )



def detect_qtn_cmb_015_sheng_nian_jieyi(chart) -> Optional[QintianCombination]:
    """QTN-CMB-015: 生年四化在十二宫之解义

    蔡明宏《紫微斗數飛星秘儀》「生年四化在十二宮之解義」：
    生年四化（依据出生年干）落于某宫，即以此宫之四化单象解义论断。
    全以单象而解（双象组合不在此卷范围）；生年四化本身无吉凶，只是「象」。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None

    # 生年四化：星→四化 映射（化禄/化权/化科/化忌）
    star_to_sihua = {
        birth_sihua[0]: "化禄",
        birth_sihua[1]: "化权",
        birth_sihua[2]: "化科",
        birth_sihua[3]: "化忌",
    }

    from .qintian_sheng_nian_data import get_sheng_nian_jieyi, PALACE_DISPLAY

    jieyi_list = []
    for pf in palace_stems:
        for star in pf.major_stars:
            sihua = star_to_sihua.get(star)
            if not sihua:
                continue
            palace_norm = pf.palace_name.rstrip('宫')
            text = get_sheng_nian_jieyi(palace_norm, sihua)
            if text is None:
                # 原书该宫无此四化条目（如疾厄无化忌），跳过而非报错
                continue
            jieyi_list.append({
                "palace": pf.palace_name,
                "palace_display": PALACE_DISPLAY.get(palace_norm, pf.palace_name),
                "star": star,
                "sihua": sihua,
                "jieyi": text,
            })

    if not jieyi_list:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-015",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "birth_sihua": list(birth_sihua),
            "jieyi_count": len(jieyi_list),
            "jieyi_list": jieyi_list,
            "trigger_pattern": "生年四化星落宫 → 十二宫单象解义",
        },
        semantic_summary=(
            f"生年{birth_stem}四化落宫解义（《飞星秘仪》单象解）："
            + ";".join(
                f"{j['palace']}{j['star']}{j['sihua']}={j['jieyi'][:18]}"
                for j in jieyi_list
            )
            + "。"
        ),
    )



def detect_qtn_cmb_016_liunian(chart) -> Optional[QintianCombination]:
    """QTN-CMB-016: 流年四化应用（以本命盘原始宫干为主，不以流年干）

    蔡明宏《飞星秘仪》流年四化应用：
    - 流年者即太岁也，每逢一年顺行一宫，四化运用不以小限为主。
    - 太岁使用分两种：(一)以本命盘原始宫干为主 (二)以流年干为主。
      唯飞星秘仪记载用本命盘之宫干为主。
    - 例：原命盘地支丑位为癸丑，则流年用「癸」一飞化，不以今年流年乙丑之「乙」为飞化。
      若用乙，则每个人今年均太阴化忌。
    - 若用流年干：四化为定象不可再转化，以忌冲为凶论；流年四化与大限对待，
      不与本命盘生年四化对待，不可三合而一使用。

    入参：chart.flow_year（流年年份），无则 fail-closed 返回 None。
    """
    flow_year = getattr(chart, 'flow_year', None)
    if not flow_year:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches_12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # 流年干（仅作对比说明用）与流年支
    flow_stem_nian = stems_10[(flow_year - 4) % 10]
    flow_branch = branches_12[(flow_year - 4) % 12]

    # 流年支所在宫（太岁位 = 流年命宫），取本命盘原始宫干
    flow_palace = None
    flow_stem_used = None
    for pf in palace_stems:
        if pf.branch == flow_branch:
            flow_palace = pf.palace_name
            flow_stem_used = pf.stem
            break
    if not flow_palace or not flow_stem_used:
        return None

    # 用本命盘原始宫干飞化（飞星秘仪主法）
    flow_sihua = GAN_SIHUA.get(flow_stem_used, ())
    if len(flow_sihua) < 4:
        return None

    # 若改用流年干（对比说明）
    nian_sihua = GAN_SIHUA.get(flow_stem_nian, ())

    # 四化落星宫位
    sihua_keys = ["化禄", "化权", "化科", "化忌"]
    sihua_palaces = []
    for pf in palace_stems:
        for star in pf.major_stars:
            for k, s in zip(sihua_keys, flow_sihua):
                if star == s:
                    sihua_palaces.append(f"{pf.palace_name}{star}{k}")

    diff_note = ""
    if nian_sihua and tuple(nian_sihua) != tuple(flow_sihua):
        diff_note = (
            "若改用流年干" + flow_stem_nian + "飞化则为：" + "".join(nian_sihua)
            + "（定象不可再转化，忌冲为凶）"
        )

    return QintianCombination(
        rule_id="QTN-CMB-016",
        detected=True,
        evidence_grade=1,
        facts={
            "flow_year": flow_year,
            "flow_branch": flow_branch,
            "flow_palace": flow_palace,
            "flow_stem_nian": flow_stem_nian,
            "flow_stem_used": flow_stem_used,
            "flow_sihua": list(flow_sihua),
            "sihua_palaces": sihua_palaces,
            "trigger_pattern": "流年四化以本命盘原始宫干为主（飞星秘仪）",
        },
        semantic_summary=(
            f"{flow_year}{flow_branch}年（{flow_stem_nian}干）：流年太岁位落{flow_palace}，"
            f"飞星秘仪以本命盘原始宫干{flow_stem_used}飞化（不用流年干{flow_stem_nian}）"
            + "，四化=" + "、".join(flow_sihua) + "。" + diff_note
        ),
    )



def detect_qtn_cmb_017_daixian(chart) -> Optional[QintianCombination]:
    """QTN-CMB-017: 大限四化应用（一律与本命息息相关，本命盘宫干为用）

    蔡明宏《飞星秘仪》大限四化应用：
    - 大限的應用，一律與本命息息相關。
    - 當任何宮位為飛化定點時，均與生年四化發生關係。
    - 例：用大限財帛言，則用命盤之「丙」干飛化；化祿照大限官祿，
      可是逢到生年忌，則構成祿忌，成為雙忌論。
    - 大限即以本命盤的宮干為大限之宮干（本命為天、大限為地、流年為人）。

    入参：chart.decadal_palace（大限命宫名，如"命宫"），无则 fail-closed 返回 None。
    """
    dec_palace = getattr(chart, 'decadal_palace', None)
    if not dec_palace:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    # 找大限命宫的本命盘原始宫干
    dec = None
    for pf in palace_stems:
        if pf.palace_name == dec_palace:
            dec = pf
            break
    if dec is None:
        return None
    dec_stem = dec.stem
    dec_sihua = GAN_SIHUA.get(dec_stem, ())
    if len(dec_sihua) < 4:
        return None

    # 大限三方（命财官，各隔四宫）：用宫序数组推算
    branches_12 = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    dec_idx = branches_12.index(dec.branch)
    tri_idx = [(dec_idx + 4 * k) % 12 for k in (0, 1, 2)]  # 命→财→官
    tri_branches = [branches_12[i] for i in tri_idx]

    tri_palaces = []
    for tb in tri_branches:
        for pf in palace_stems:
            if pf.branch == tb:
                tri_palaces.append({
                    "palace": pf.palace_name,
                    "branch": pf.branch,
                    "stem": pf.stem,
                })
                break

    # 生年四化（用生年干，非命宫宫干；对照碰撞用）
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_year = getattr(chart, 'birth_year', None)
    sheng_nian_sihua = ()
    if birth_year:
        sheng_stem = stems_10[(birth_year - 4) % 10]
        sheng_nian_sihua = GAN_SIHUA.get(sheng_stem, ())

    # 碰撞说明（书例：化禄照大限官禄，逢生年忌成双忌论）
    collision_notes = []
    sheng_nian_ji_palace = None
    if sheng_nian_sihua:
        ji_star = sheng_nian_sihua[3]  # 生年化忌星
        for pf in palace_stems:
            if ji_star in pf.major_stars:
                sheng_nian_ji_palace = pf.palace_name
                break
        if sheng_nian_ji_palace:
            lu_star = dec_sihua[0]  # 大限化禄星
            for pf2 in palace_stems:
                if lu_star in pf2.major_stars and pf2.palace_name == sheng_nian_ji_palace:
                    collision_notes.append(
                        f"大限化禄{lu_star}落{sheng_nian_ji_palace}宫，逢生年忌成双忌论"
                    )
                    break
            if ji_star in dec_sihua:
                collision_notes.append(
                    f"大限四化含生年忌星{ji_star}，飞化与生年四化对待"
                )

    return QintianCombination(
        rule_id="QTN-CMB-017",
        detected=True,
        evidence_grade=1,
        facts={
            "decadal_palace": dec_palace,
            "decadal_branch": dec.branch,
            "decadal_stem": dec_stem,
            "decadal_sihua": list(dec_sihua),
            "decadal_triangle": tri_palaces,
            "sheng_nian_ji_palace": sheng_nian_ji_palace if sheng_nian_sihua else None,
            "collision_notes": collision_notes,
            "trigger_pattern": "大限四化以本命盘宫干为用（飞星秘仪）",
        },
        semantic_summary=(
            f"大限命宫落{dec_palace}({dec.branch})，飞星秘仪以本命盘宫干{dec_stem}为用，"
            + "四化=" + "、".join(dec_sihua)
            + "；大限三合变迁：" + "、".join(f"{p['palace']}{p['branch']}({p['stem']})" for p in tri_palaces)
            + "。大限应用一律与本命息息相关，宫位为飞化定点时均与生年四化发生关系。"
        ),
    )




def detect_qtn_cmb_018_zihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-018: 自化浅解（取意托乎随心而化乃名自化；自化反其意）

    蔡明宏《飞星秘仪》自化浅解：
    - 自化是易之「本易」。本易者，本义也。斗数上自化，有「不化」，亦有「有化」。
    - 秘仪有载：「取意托乎，随心而化，乃名自化」，为自化之解。
    - 自化定义：某宫宫干飞化之四化星恰在本宫（如夫妻宫干丙、天机化权在夫妻本宫 → 自化权）。
    - (B) 自化有反其「意」之作用：本为不好，也许因自化而好；本为不好，因自化而恶化；
      本是好的，因自化而更好；本是好的，因自化而变坏。
    - (F) 凡在四化中，不论四化如何飞化，或与生年四化碰撞产生的各种情况，
      若逢该宫自化时，其意则全变，不可拘泥于原本之意。
    - 书例：夫妻宫坐机梁、宫干丙，天机化权在夫妻本宫，谓之自化（夫妻有才干自立）；
      命宫坐戊天机化忌入夫妻，但化忌入夫妻及夫妻自化权，则其意完全变化，
      变成本身才华不及对方才干；女命多劳而荫夫。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    sihua_keys = ["化禄", "化权", "化科", "化忌"]
    zihua_list = []
    for pf in palace_stems:
        if not pf.stem or not pf.major_stars:
            continue
        sihua = GAN_SIHUA.get(pf.stem, ())
        if len(sihua) < 4:
            continue
        for k, star in zip(sihua_keys, sihua):
            if star in pf.major_stars:
                zihua_list.append({
                    "palace": pf.palace_name,
                    "branch": pf.branch,
                    "stem": pf.stem,
                    "sihua": k,
                    "star": star,
                })
    if not zihua_list:
        return None

    # 反意提示：逢自化其意全变，不可拘泥原本之意（书 F/B 条）
    # 若任一自化宫同时有他宫化忌入 → 其意完全变化（书例夫妻宫）
    reverse_notes = [
        f"{z['palace']}宫自化{z['sihua']}（{z['star']}），逢自化其意全变，不可拘泥原本之意"
        for z in zihua_list
    ]

    return QintianCombination(
        rule_id="QTN-CMB-018",
        detected=True,
        evidence_grade=1,
        facts={
            "zihua_list": zihua_list,
            "zihua_count": len(zihua_list),
            "reverse_notes": reverse_notes,
            "trigger_pattern": "自化浅解：取意托乎随心而化乃名自化（飞星秘仪）",
        },
        semantic_summary=(
            "自化浅解："
            + "、".join(f"{z['palace']}宫干{z['stem']}使{z['star']}{z['sihua']}在本宫" for z in zihua_list)
            + "。取意托乎随心而化乃名自化；自化有反其意之作用，逢自化其意全变，不可拘泥原本之意。"
        ),
    )



def detect_qtn_cmb_019_doujun(chart) -> Optional[QintianCombination]:
    """QTN-CMB-019: 生年斗君入十二宫解（十二宫以六宫论）

    蔡明宏《飞星秘仪》生年斗君入十二宫解：
    - 生年斗君落十二宫各有解义（言行/兄弟交友/夫妻官禄/子女田宅…）
    - 十二宫以六宫论：命宫100%|迁移70%、兄弟100%|交友70%、
      夫妻100%|官禄70%、子女100%|田宅70%、财帛100%|福德70%、疾厄100%|父母70%
    - 生年斗君在某宫，一生课题集中该宫与其对待宫
    入参：chart.doujun_palace（生年斗君所在宫名），无则 fail-closed 返回 None。
    """
    doujun = getattr(chart, 'doujun_palace', None)
    if not doujun:
        return None
    # 宫名归一：iztro 旧命名「仆役」= 钦天原文「交友」（同一宫）
    _NORM = {"仆役": "交友"}
    doujun = _NORM.get(doujun, doujun)
    from .qintian_doujun_data import get_doujun_jieyi, get_doujun_weight

    jieyi = get_doujun_jieyi(doujun)
    if not jieyi:
        return None
    weight = get_doujun_weight(doujun)

    return QintianCombination(
        rule_id="QTN-CMB-019",
        detected=True,
        evidence_grade=1,
        facts={
            "doujun_palace": doujun,
            "jieyi": jieyi,
            "weight_palace": weight["palace"] if weight else None,
            "weight_pct": weight["weight"] if weight else None,
            "trigger_pattern": "生年斗君入十二宫解（飞星秘仪）",
        },
        semantic_summary=(
            f"生年斗君在{doujun}宫：" + jieyi
            + (f"十二宫以六宫论：{doujun}宫为100%，{weight['palace']}宫为70%。" if weight else "")
        ),
    )


# ============================================================
# Detect All 函数
# ============================================================




def detect_qtn_cmb_020_yongshen(chart) -> Optional[QintianCombination]:
    """QTN-CMB-020: 用神法则（禄忌一组 / 权科一组；权科用神必须配合忌）

    蔡明宏原文（第五章 論命須知·四化圖 / 命例一）：
    - 用神：祿、忌一組 權、科一組 但，權、科用神，必須配合忌。
    - 凡是來因宮自化者，其命盤論命方式都要由「來因宮」做論命的緣起，
      並看來因宮的四化是什麼「象」，分出用神。用神的要領：就是祿～忌一組 權～科一組
    - 例：壬年生，來因宮自化在命宮，紫微權自化權，其用神就是權科組（優先次序）。
    - 權、科用神的媒介一定要有化忌。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    laiyin = get_laiyin_palace(chart.birth_year, palace_stems)
    if not laiyin:
        return None

    # 来因宫宫干四化
    laiyin_fact = next((p for p in palace_stems if p.palace_name == laiyin), None)
    if not laiyin_fact:
        return None
    laiyin_stem = laiyin_fact.stem
    sihua = GAN_SIHUA.get(laiyin_stem, ())
    if len(sihua) < 4:
        return None
    stars_in_palace = set(laiyin_fact.major_stars)
    lu, quan, ke, ji = sihua

    # 来因宫自化检测：宫干四化星恰在本宫主星
    self_mutagen_types = []
    if quan in stars_in_palace:
        self_mutagen_types.append("化权")
    if ke in stars_in_palace:
        self_mutagen_types.append("化科")
    if lu in stars_in_palace:
        self_mutagen_types.append("化禄")
    if ji in stars_in_palace:
        self_mutagen_types.append("化忌")
    if not self_mutagen_types:
        return None  # fail-closed：非来因宫自化盘，不硬推用神

    # 用神分组（优先次序：权科组）
    quan_ke_hit = any(t in self_mutagen_types for t in ("化权", "化科"))
    lu_ji_hit = any(t in self_mutagen_types for t in ("化禄", "化忌"))
    if quan_ke_hit:
        yongshen_group = "权科组"
    elif lu_ji_hit:
        yongshen_group = "禄忌组"
    else:
        return None

    # 权科用神必须配合忌：全盘是否有化忌（媒介）
    ji_palaces = sorted({
        ft.target_palace for ft in chart.flying_transforms
        if ft.transformation == "化忌"
    })
    has_ji = len(ji_palaces) > 0
    media_ok = (yongshen_group != "权科组") or has_ji  # 权科组才强制配忌

    note = ""
    if yongshen_group == "权科组":
        if has_ji:
            note = "，化忌媒介落" + "、".join(ji_palaces[:3]) + ("等" if len(ji_palaces) > 3 else "") + "，用神成立"
        else:
            note = "，但盘面无化忌可配，权科用神缺媒介（原著：權科用神必須配合忌）"

    return QintianCombination(
        rule_id="QTN-CMB-020",
        detected=True,
        evidence_grade=1,
        facts={
            "laiyin_palace": laiyin,
            "laiyin_stem": laiyin_stem,
            "laiyin_self_mutagen": self_mutagen_types,
            "yongshen_group": yongshen_group,
            "ji_media_palaces": ji_palaces,
            "media_ok": media_ok,
            "trigger_pattern": "来因宫自化 → 分出用神（权科优先）→ 权科必配忌",
        },
        semantic_summary=(
            "来因宫" + laiyin + "（" + laiyin_stem + "干）自化" + "、".join(self_mutagen_types) +
            "，其用神为" + yongshen_group + "（优先次序）" + note + "（蔡明宏《悟我十八年》第五章）。"
        ),
    )


def detect_qtn_cmb_021_yinyang_biaoli(chart) -> Optional[QintianCombination]:
    """QTN-CMB-021: 十二宫位阴阳表里（六阳六阴 / 一阴一阳相为表里 / 对宫同断）

    蔡明宏原文（第三章 細說十二宮位）：
    - 十二宮位，分六陽、六陰：阳=命/夫妻/财帛/迁移/事业/福德；阴=兄弟/子女/疾厄/交友/田宅/父母
    - 一陰一陽相為表裡（对宫六对：命↔迁移、兄弟↔交友、夫妻↔官禄、子女↔田宅、财帛↔福德、疾厄↔父母）
    - 命宮化忌入遷移，有驛馬在外之命或遷移化忌入命宮，解釋也是一樣（对宫同断）
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    # 对宫表（一阴一阳相为表里）
    # Z80-F: 「交友」→「仆役」以与盘面 ft.source/target_palace 一致（否则该对永不匹配）
    OPPOSITE_PAIRS = [
        ("命宫", "迁移"), ("兄弟", "仆役"), ("夫妻", "官禄"),
        ("子女", "田宅"), ("财帛", "福德"), ("疾厄", "父母"),
    ]
    YANG_PALACES = ["命宫", "夫妻", "财帛", "迁移", "官禄", "福德"]
    YIN_PALACES = ["兄弟", "子女", "疾厄", "仆役", "田宅", "父母"]

    # 检测对宫互飞（任一对宫 A→B 或 B→A 有化忌 → 对宫同断）
    hits = []
    for a, b in OPPOSITE_PAIRS:
        for ft in chart.flying_transforms:
            if ft.transformation == "化忌":
                if (ft.source_palace == a and ft.target_palace == b) or (
                        ft.source_palace == b and ft.target_palace == a):
                    hits.append({
                        "pair": a + "↔" + b,
                        "from": ft.source_palace,
                        "to": ft.target_palace,
                        "star": ft.target_star,
                        "transformation": ft.transformation,
                    })
    if not hits:
        return None  # fail-closed：无对宫互飞则不触发同断

    # 归类：命↔迁移互飞忌 → 驿马在外（书例）
    summaries = []
    for h in hits:
        if h["pair"] == "命宫↔迁移" and h["transformation"] == "化忌":
            summaries.append(h["from"] + "化忌入" + h["to"] + "，驿马在外之命（或反向同断）")
        else:
            summaries.append(h["from"] + "化忌入" + h["to"] + "，与" + h["pair"] + "同断（一阴一阳相为表里）")

    return QintianCombination(
        rule_id="QTN-CMB-021",
        detected=True,
        evidence_grade=1,
        facts={
            "yang_palaces": YANG_PALACES,
            "yin_palaces": YIN_PALACES,
            "opposite_pairs": [a + "↔" + b for a, b in OPPOSITE_PAIRS],
            "opposite_hits": hits,
            "trigger_pattern": "对宫互飞 → 对宫同断（六阳六阴表里）",
        },
        semantic_summary=(
            "十二宫分六阳六阴（阳：" + "、".join(YANG_PALACES) + "；阴：" + "、".join(YIN_PALACES) + "），"
            "一阴一阳相为表里共六对。本盘命中对宫同断：" + "；".join(summaries) + "（蔡明宏《悟我十八年》第三章）。"
        ),
    )




def detect_qtn_cmb_022_pingheng(chart) -> Optional[QintianCombination]:
    """QTN-CMB-022: 四化现象平衡原理（生年单象/双象 vs 自化，单对单、双对双）

    蔡明宏原文（第四章 自化应用篇·詮釋一 自化在「理」上而言）：
    - 生年四化，有單象與雙象之別，平衡其理，一定要單對單，雙對雙。
    - 把同類的歸類並兼看「宮位」，成現象的相對論。
    - 例：廉貞化祿在兄弟，又自化忌（單星自化）——把自化的化忌，去法生年忌。
    - 例：福德坐癸又自化科，但生年科、忌是雙象在官祿宮，所以把自化科法回生年科，
      一定還少一顆化忌，否則不會平衡。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    SIHUA_TRANS = ["化禄", "化权", "化科", "化忌"]

    # 每宫生年四化象（生年干四化星落该宫）
    sheng_nian_by_palace = {}
    for pf in palace_stems:
        hits = []
        for i, star in enumerate(birth_sihua):
            if star in pf.major_stars:
                hits.append({"transformation": SIHUA_TRANS[i], "star": star})
        if hits:
            sheng_nian_by_palace[pf.palace_name] = hits

    # 每宫自化象（本宫宫干四化星恰在本宫主星）
    zihua_by_palace = {}
    for ft in get_self_mutagen(chart):
        zihua_by_palace.setdefault(ft.source_palace, []).append(
            {"transformation": ft.transformation, "star": ft.target_star})

    # 平衡判定：仅对有自化的宫位论（无自化=五分类之"生年四化没有自化者"，不在此论）
    results = []
    for palace, sheng_nian_list in sheng_nian_by_palace.items():
        zihua_list = zihua_by_palace.get(palace, [])
        if not zihua_list:
            continue
        s_count = len(sheng_nian_list)
        z_count = len(zihua_list)
        if s_count == z_count:
            status = "平衡"
            note = "单对单" if s_count == 1 else "双对双"
        else:
            status = "不平衡"
            note = ("生年单象自化双象" if s_count == 1 else "生年双象自化单象")
        # 法象：自化中与生年同星之象（同类归类）
        sheng_nian_stars = {s["star"] for s in sheng_nian_list}
        faxiang = [
            z["transformation"] + "(" + z["star"] + ")"
            for z in zihua_list if z["star"] in sheng_nian_stars
        ]
        results.append({
            "palace": palace,
            "sheng_nian": [s["transformation"] + "(" + s["star"] + ")" for s in sheng_nian_list],
            "zihua": [z["transformation"] + "(" + z["star"] + ")" for z in zihua_list],
            "status": status,
            "rule": note,
            "faxiang": faxiang,
        })

    if not results:
        return None  # fail-closed：无同时具生年+自化的宫位

    balanced = [r for r in results if r["status"] == "平衡"]
    unbalanced = [r for r in results if r["status"] == "不平衡"]

    details = []
    for r in results:
        fx = "；法象：" + "、".join(r["faxiang"]) if r["faxiang"] else ""
        details.append(r["palace"] + "(" + "、".join(r["sheng_nian"]) + " vs " + "、".join(r["zihua"]) + ")=" + r["rule"] + fx)

    return QintianCombination(
        rule_id="QTN-CMB-022",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "balance_results": results,
            "balanced_count": len(balanced),
            "unbalanced_count": len(unbalanced),
            "trigger_pattern": "生年四化单象/双象 vs 自化象数 → 单对单/双对双",
        },
        semantic_summary=(
            "四化现象平衡原理（蔡明宏）：" + ("；".join(details) if details else "") +
            "。" + ("共" + str(len(results)) + "宫具生年+自化，"
                   + str(len(balanced)) + "宫平衡、" + str(len(unbalanced)) + "宫不平衡。")
        ),
    )




def detect_qtn_cmb_023_minggong_feihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-023: 命宫干飞化论贵格（三合入/照/冲）

    蔡明宏原文（《飞星秘仪》四化宫位变通浅释·命宫）：
    - 命宫代表一个人的命格高低，以命宫干四化显示命格的高低。
    - 禄、权、科落在本命三合，主贵格，并主自立更生。
    - 禄、权、科落在其余三宫（夫、迁、福），为之照，亦主贵，但须借他人之助，方易成功。
    - 化忌入本命三合，不失其格，唯其能力表现易犯小人干扰，阻碍多；
      化忌入其余三宫，谓之冲三合，则损贵中之格，易变初衷志向。
    - 化忌冲三合者，薪俸者为宜。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    ZHAO_PALACES = {"夫妻", "迁移", "福德"}  # 其余三宫（照）

    # 命宫
    ming = next((p for p in palace_stems if p.palace_name == "命宫"), None)
    if not ming or not ming.stem:
        return None
    sihua = GAN_SIHUA.get(ming.stem, ())
    if len(sihua) < 4:
        return None
    lu, quan, ke, ji = sihua

    # 命宫三合（书464行：命、财帛、官禄为之三合）
    sanhe_names = _triple_of("命宫")

    # 禄权科落宫
    hit_palaces = {}
    for star, trans in ((lu, "化禄"), (quan, "化权"), (ke, "化科")):
        for p in palace_stems:
            if star in p.major_stars:
                hit_palaces[trans] = p.palace_name

    # 化忌落宫
    ji_palace = None
    for p in palace_stems:
        if ji in p.major_stars:
            ji_palace = p.palace_name
            break

    # 归类
    ru_sanhe = [t for t, pal in hit_palaces.items() if pal in sanhe_names]
    zhao = [t for t, pal in hit_palaces.items() if pal in ZHAO_PALACES]
    guige_note = ""
    if ru_sanhe:
        guige_note = "禄权科入本命三合，主贵格，并主自立更生"
    elif zhao:
        guige_note = "禄权科照（夫迁福），亦主贵，但须借他人之助方易成功"

    ji_note = ""
    if ji_palace:
        if ji_palace in sanhe_names:
            ji_note = "化忌入本命三合，不失其格，唯能力表现易犯小人干扰"
        elif ji_palace in ZHAO_PALACES:
            ji_note = "化忌入其余三宫（冲三合），损贵中之格，易变初衷志向，薪俸者为宜"
        else:
            ji_note = "化忌落" + ji_palace + "（不入三合不冲三合）"

    return QintianCombination(
        rule_id="QTN-CMB-023",
        detected=True,
        evidence_grade=1,
        facts={
            "ming_stem": ming.stem,
            "sanhe_palaces": sanhe_names,
            "lu_quan_ke_palaces": hit_palaces,
            "ji_palace": ji_palace,
            "ru_sanhe": ru_sanhe,
            "zhao": zhao,
            "trigger_pattern": "命宫干四化 → 三合入/照/冲 → 贵格论",
        },
        semantic_summary=(
            "命宫干飞化论贵格（蔡明宏《飞星秘仪》）：" +
            (guige_note if guige_note else "禄权科不落三合亦不照夫迁福") +
            "；" + ji_note + "。"
        ),
    )


def detect_qtn_cmb_024_liuqin_ji(chart) -> Optional[QintianCombination]:
    """QTN-CMB-024: 六亲宫忌入忌冲（谁化忌冲谁缘薄，谁化忌入谁口角）

    蔡明宏原文（《飞星秘仪》四化宫位变通浅释）：
    - 六亲宫：命宫、兄弟、夫妻、子女、交友、父母，谓之六亲宫。
    - 凡六亲之宫位，谁化忌冲谁，均主缘薄。
      谁化忌入谁之宫位，虽不佳，但比冲吉，只可解口角意见多。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    ALIAS = {"仆役": "交友"}  # 北派仆役宫 = 书之交友宫
    def _norm(name):
        return ALIAS.get(name, name)
    LIUQIN = ["命宫", "兄弟", "夫妻", "子女", "交友", "父母"]
    # 对宫表（冲=入对宫）
    OPPOSITE = {
        "命宫": "迁移", "迁移": "命宫",
        "兄弟": "交友", "交友": "兄弟",
        "夫妻": "官禄", "官禄": "夫妻",
        "子女": "田宅", "田宅": "子女",
        "财帛": "福德", "福德": "财帛",
        "疾厄": "父母", "父母": "疾厄",
    }

    hits = []
    for p in palace_stems:
        if _norm(p.palace_name) not in LIUQIN or not p.stem:
            continue
        sihua = GAN_SIHUA.get(p.stem, ())
        if len(sihua) < 4:
            continue
        ji_star = sihua[3]
        target = None
        for q in palace_stems:
            if ji_star in q.major_stars:
                target = _norm(q.palace_name)
                break
        if not target or target not in LIUQIN:
            continue
        if OPPOSITE.get(target) == _norm(p.palace_name):
            # 化忌冲对方（A 忌入 B，B 是 A 对宫 → 冲）
            # 实际：A 化忌入 B 若 B 是 A 的对宫 → 为"冲"
            kind = "冲"
            text = _norm(p.palace_name) + "化忌冲" + target + "，主缘薄"
        else:
            kind = "入"
            text = _norm(p.palace_name) + "化忌入" + target + "，虽不佳但比冲吉，主口角意见多"
        hits.append({"from": _norm(p.palace_name), "to": target, "star": ji_star, "kind": kind, "text": text})

    if not hits:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-024",
        detected=True,
        evidence_grade=1,
        facts={
            "liuqin_hits": hits,
            "trigger_pattern": "六亲宫宫干化忌 → 入/冲另一六亲宫",
        },
        semantic_summary=(
            "六亲宫忌入忌冲（蔡明宏《飞星秘仪》）：" +
            "；".join(h["text"] for h in hits) + "。"
        ),
    )




def detect_qtn_cmb_025_tianzhai_feihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-025: 田宅宫飞化论断（住宅环境/祖产财源/驿马/置产）

    蔡明宏原文（《飞星秘仪》四化宫位变通浅释·田宅宫）：
    - 田宅宫：称之为不动产宫，包括祖业在内，亦名家运宫、财库宫、环境宫。
    - 田宅宫飞化之四化在田宅三合，可见住宅附近之环境，有物相应。
    - 田宅宫飞化之四化在本命三合，可见祖产有无及财源应用，包括照命三合。
    - 田宅宫飞化之四化，在迁移、子女，代表驿马。
    - 命、财、官飞化入田宅，可见有无增置不动产。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    ZHAO_PALACES = {"夫妻", "迁移", "福德"}

    def _triple_names(palace):
        return _triple_of(palace)

    # 田宅宫
    tianzhai = next((p for p in palace_stems if p.palace_name == "田宅"), None)
    if not tianzhai or not tianzhai.stem:
        return None
    sihua = GAN_SIHUA.get(tianzhai.stem, ())
    if len(sihua) < 4:
        return None

    # 田宅干四化落宫
    tianzhai_sihua_palaces = []
    for star in sihua:
        for p in palace_stems:
            if star in p.major_stars and p.palace_name not in tianzhai_sihua_palaces:
                tianzhai_sihua_palaces.append(p.palace_name)

    tianzhai_triple = _triple_names("田宅")
    ming_triple = _triple_names("命宫")

    notes = []
    if tianzhai_sihua_palaces:
        in_tt = [x for x in tianzhai_sihua_palaces if x in tianzhai_triple]
        in_mt = [x for x in tianzhai_sihua_palaces if x in ming_triple or x in ZHAO_PALACES]
        in_yi = [x for x in tianzhai_sihua_palaces if x in ("迁移", "子女")]
        if in_tt:
            notes.append("田宅飞化入田宅三合（" + "、".join(in_tt) + "），住宅附近之环境有物相应")
        if in_mt:
            notes.append("田宅飞化入本命三合（" + "、".join(in_mt) + "），可见祖产有无及财源应用")
        if in_yi:
            notes.append("田宅飞化入迁移/子女（" + "、".join(in_yi) + "），代表驿马")

    # 命、财、官飞化入田宅（置产）
    zhi_chan = []
    for palace in ("命宫", "财帛", "官禄"):
        p = next((x for x in palace_stems if x.palace_name == palace), None)
        if not p or not p.stem:
            continue
        ps = GAN_SIHUA.get(p.stem, ())
        if len(ps) < 4:
            continue
        for star in ps:
            for q in palace_stems:
                if q.palace_name == "田宅" and star in q.major_stars:
                    zhi_chan.append(palace)
                    break

    if zhi_chan:
        notes.append("命、财、官飞化入田宅（" + "、".join(zhi_chan) + "），可见有增置不动产之象")

    if not notes:
        return None  # fail-closed：田宅飞化无命中落点

    return QintianCombination(
        rule_id="QTN-CMB-025",
        detected=True,
        evidence_grade=1,
        facts={
            "tianzhai_stem": tianzhai.stem,
            "tianzhai_sihua_palaces": tianzhai_sihua_palaces,
            "tianzhai_triple": tianzhai_triple,
            "ming_triple": ming_triple,
            "zhi_chan_from": zhi_chan,
            "trigger_pattern": "田宅干四化落点 → 三合/本命三合/迁移子女/命财官入田宅",
        },
        semantic_summary=(
            "田宅宫飞化论断（蔡明宏《飞星秘仪》）：" + "；".join(notes) + "。"
        ),
    )




def detect_qtn_cmb_026_sanjihua_yinyang(chart) -> Optional[QintianCombination]:
    """QTN-CMB-026: 六阳宫主贵六阴宫主富（生年三吉化落宫贵富取向）

    蔡明宏原文（《飞星秘仪》四化宫位变通浅释·命宫）：
    - 六陽宮主貴，六陰宮主富。
    - 三吉化於六陰者，要成就的基本條件，是「人和」；得有人和者，財利亦隨之而來。
    - 生年祿權科分別在六陰位，表示此人會有錢（有無錢要有時運）……以財富為主，偏向財利之格。
      也因有此之格，將來大限週旋，時運來臨，則財多勝貴之質。（vr-d.com 原书 PDF 补证）
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    YANG_PALACES = {"命宫", "夫妻", "财帛", "迁移", "官禄", "福德"}
    YIN_PALACES = {"兄弟", "子女", "疾厄", "仆役", "田宅", "父母"}

    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    sihua = GAN_SIHUA.get(birth_stem, ())
    if len(sihua) < 4:
        return None
    lu, quan, ke = sihua[0], sihua[1], sihua[2]

    yang_hits, yin_hits = [], []
    for p in palace_stems:
        for star, trans in ((lu, "化禄"), (quan, "化权"), (ke, "化科")):
            if star in p.major_stars:
                if p.palace_name in YANG_PALACES:
                    yang_hits.append(p.palace_name + trans)
                elif p.palace_name in YIN_PALACES:
                    yin_hits.append(p.palace_name + trans)

    if not yang_hits and not yin_hits:
        return None

    if len(yang_hits) >= len(yin_hits):
        orient = "贵格取向（六阳宫主贵）"
    else:
        orient = "富格取向（六阴宫主富）"

    # PDF 补证：三吉化全落六阴 → 以财富为主偏向财利之格，时运来财多胜贵
    notes = []
    if yin_hits and not yang_hits:
        notes.append("生年禄权科分别落六阴位，主有钱，以财富为主偏向财利之格，时运来临则财多胜贵之质")
    if yin_hits:
        notes.append("三吉化於六陰者，要成就的基本條件是「人和」，得有人和者財利亦隨之而來，是人蔭其成而非本身之獨成")

    if notes:
        orient = orient + "；" + "；".join(notes)

    return QintianCombination(
        rule_id="QTN-CMB-026",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "yang_hits": yang_hits,
            "yin_hits": yin_hits,
            "orient": orient,
            "trigger_pattern": "生年三吉化落六阳/六阴 → 贵/富取向",
        },
        semantic_summary=(
            "六阳宫主贵、六阴宫主富（蔡明宏《飞星秘仪》）：生年三吉化落六阳（"
            + "、".join(yang_hits) + "）六阴（" + "、".join(yin_hits) + "），"
            + orient + "。"
        ),
    )


def detect_qtn_cmb_027_laiyin_guige(chart) -> Optional[QintianCombination]:
    """QTN-CMB-027: 来因宫定贵格自立/借力（三方见禄权科 + 来因宫财帛/兄弟）

    蔡明宏原文（《飞星秘仪》四化活盘应用）：
    - 某甲之命盘三方有禄、权、科——主贵。
    - 某甲生年干若与财帛同宫，则其人之贵靠自己，不需借他人之助，代表可自立独谋之格。
    - 某乙生年干若与兄弟同宫，则其人之贵非靠自己，而需借朋友或兄弟之协，方可助其贵，
      否则生年四化在三方见，亦无用於济事，便成一种假象。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    laiyin = get_laiyin_palace(chart.birth_year, palace_stems)
    if not laiyin:
        return None

    birth_stem_idx = (chart.birth_year - 4) % 10
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[birth_stem_idx]
    sihua = GAN_SIHUA.get(birth_stem, ())
    if len(sihua) < 4:
        return None

    # 三方 = 命、财帛、官禄（书464行）
    sanfang = _triple_of("命宫")
    lu, quan, ke = sihua[0], sihua[1], sihua[2]

    # 生年三吉化落三方？
    sanfang_hits = []
    for p in palace_stems:
        if p.palace_name not in sanfang:
            continue
        for star, trans in ((lu, "化禄"), (quan, "化权"), (ke, "化科")):
            if star in p.major_stars:
                sanfang_hits.append(p.palace_name + trans)

    if not sanfang_hits:
        return None  # 三方无禄权科 → 不构成贵格前提

    if laiyin == "财帛":
        note = "来因宫在财帛：贵靠自己，不需借他人之助，可自立独谋之格"
    elif laiyin == "兄弟":
        note = "来因宫在兄弟：贵非靠自己，需借朋友或兄弟之协方可助其贵，否则三方见亦成假象"
    else:
        note = "来因宫在" + laiyin + "（非财帛/兄弟），贵格依三方禄权科而显"

    return QintianCombination(
        rule_id="QTN-CMB-027",
        detected=True,
        evidence_grade=1,
        facts={
            "laiyin_palace": laiyin,
            "sanfang_hits": sanfang_hits,
            "trigger_pattern": "三方见禄权科 + 来因宫财帛/兄弟 → 自立/借力",
        },
        semantic_summary=(
            "来因宫定贵格（蔡明宏《飞星秘仪》四化活盘应用）：三方见禄权科（"
            + "、".join(sanfang_hits) + "）主贵；" + note + "。"
        ),
    )




def detect_qtn_cmb_028_shihua_shallow(chart) -> Optional[QintianCombination]:
    """QTN-CMB-028: 十干化曜浅释（生年四化逐星论断）

    蔡明宏原文（《飞星秘仪》十干化曜浅释 73-77页）：
    十干各化星论断数据表 TEN_GAN_SIHUA_READINGS。
    辛干文曲科原书第61页命例原文完整（巨门禄/太阳权/文曲科/文昌忌）；第126页十干四化表辛行OCR缺阳字，61页命例补全。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None

    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    readings = TEN_GAN_SIHUA_READINGS.get(birth_stem, {})
    if not readings:
        return None

    sihua = GAN_SIHUA.get(birth_stem, ())
    if len(sihua) < 4:
        return None
    trans_map = [("禄", sihua[0]), ("权", sihua[1]), ("科", sihua[2]), ("忌", sihua[3])]

    notes = []
    star_palaces = {}
    for p in palace_stems:
        for star in p.major_stars:
            star_palaces.setdefault(star, []).append(p.palace_name)

    missing = []
    for trans, star in trans_map:
        entry = readings.get(trans)
        if entry is None:
            missing.append(trans)
            continue
        read_star, read_text = entry
        places = star_palaces.get(star, [])
        notes.append(
            birth_stem + "干" + read_star + "化" + trans
            + ("入" + "、".join(places) if places else "（未落主星宫）")
            + "：" + read_text
        )

    if not notes:
        return None

    extra = "；辛干文曲科以第61页命例原文为据" if "科" in missing else ""
    return QintianCombination(
        rule_id="QTN-CMB-028",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "readings": {t: (s, txt) for t, (s, txt) in
                        [(tr, readings[tr]) for tr in ("禄", "权", "科", "忌") if readings.get(tr)]},
            "missing_trans": missing,
            "trigger_pattern": "生年干四化逐星论断（十干化曜浅释）",
        },
        semantic_summary="十干化曜浅释（蔡明宏《飞星秘仪》）：" + "；".join(notes[:4]) + extra,
    )




def detect_qtn_cmb_029_daxian_liuqin_chong(chart) -> Optional[QintianCombination]:
    """QTN-CMB-029: 大限六亲宫忌冲本命六亲（缘薄/对待不佳）

    蔡明宏原文（《飞星秘仪》基本活盘观念 70页）：
    - 大限六親宮化忌不宜沖本命之某六親宮，是主某六親對某六親緣份薄或對待不佳。
    - 例：大限兄弟宮化忌沖本命父母宮，代表此大限兄弟與父母間，對待不會良佳，口角難免。
    - 理則：即「用」不可沖「體」，若祿、權、科者照體則為佳論。

    入参：chart.decadal_palace（大限命宫名），无则 fail-closed。
    """
    dec_palace = getattr(chart, 'decadal_palace', None)
    if not dec_palace:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    # 大限十二宫：以 dec_palace 为命宫顺排
    i = _palace_index(dec_palace)
    if i < 0:
        return None
    dec_palaces = [ZW_PALACES_ORDER[(i - 1 + k) % 12] for k in range(12)]
    # Z80-F: 六亲宫名统一为盘面口径「仆役」（原「交友」与 dec_palaces 不一致致漏检）
    dec_liuqin = [p for p in dec_palaces[:7] if p in ("命宫", "兄弟", "夫妻", "子女", "仆役", "父母")]

    # 本命六亲对宫表（命↔迁移 非六亲；六亲内部对宫：兄弟↔仆役、疾厄↔父母）
    OPP = {"兄弟": "仆役", "仆役": "兄弟", "疾厄": "父母", "父母": "疾厄"}

    hits = []
    for p in palace_stems:
        if p.palace_name not in dec_liuqin or not p.stem:
            continue
        sihua = GAN_SIHUA.get(p.stem, ())
        if len(sihua) < 4:
            continue
        ji_star = sihua[3]
        for q in palace_stems:
            if ji_star not in q.major_stars:
                continue
            opp = OPP.get(q.palace_name)
            if opp and opp in ("命宫", "兄弟", "夫妻", "子女", "仆役", "父母"):
                hits.append({
                    "from": "大限" + p.palace_name,
                    "to": "本命" + opp,
                    "star": ji_star,
                })
            break

    if not hits:
        return None

    notes = [h["from"] + "化忌冲" + h["to"] + "，主该六亲对该六亲缘份薄或对待不佳，口角难免" for h in hits]
    return QintianCombination(
        rule_id="QTN-CMB-029",
        detected=True,
        evidence_grade=1,
        facts={
            "decadal_palace": dec_palace,
            "hits": hits,
            "trigger_pattern": "大限六亲宫化忌冲本命六亲宫 → 缘薄对待不佳",
        },
        semantic_summary="大限六亲宫忌冲（蔡明宏《飞星秘仪》）：" + "；".join(notes) + "。理则：用不可冲体，若禄权科照体则为佳论。",
    )


def detect_qtn_cmb_030_mingge_zihua_sun(chart) -> Optional[QintianCombination]:
    """QTN-CMB-030: 命格自化损格（三方见禄权科 + 所落宫自化 → 贵达不显）

    蔡明宏原文（《飞星秘仪》命例解·命格解 72页）：
    - 用生年四化，三方見祿、權、科、主貴，唯其所落祿、權、科之宮位，均有「自化」，
      則貴中有損其格，便成貴達不顯。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    sihua = GAN_SIHUA.get(birth_stem, ())
    if len(sihua) < 4:
        return None

    sanfang = _triple_of("命宫")
    # 生年禄权科落三方
    hits = []
    for p in palace_stems:
        if p.palace_name not in sanfang or not p.stem:
            continue
        for star, trans in ((sihua[0], "化禄"), (sihua[1], "化权"), (sihua[2], "化科")):
            if star in p.major_stars:
                # 该宫是否自化：宫干四化任一星落本宫
                p_sihua = GAN_SIHUA.get(p.stem, ())
                self_mut = any(s in p.major_stars for s in p_sihua) if len(p_sihua) >= 4 else False
                hits.append({
                    "palace": p.palace_name,
                    "trans": trans,
                    "star": star,
                    "self_mutagen": self_mut,
                })

    if not hits:
        return None

    sun = [h for h in hits if h["self_mutagen"]]
    if not sun:
        return None  # 三方见禄权科但无自化 → 贵格无损，不触发

    notes = ["三方见禄权科主贵，唯" + h["palace"] + h["trans"] + "（" + h["star"] + "）有自化，贵中有损其格，贵达不显" for h in sun]
    return QintianCombination(
        rule_id="QTN-CMB-030",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "hits": hits,
            "self_mutagen_palaces": [h["palace"] + h["trans"] for h in sun],
            "trigger_pattern": "三方见禄权科 + 所落宫自化 → 贵中有损贵达不显",
        },
        semantic_summary="命格自化损格（蔡明宏《飞星秘仪》命格解）：" + "；".join(notes) + "。",
    )




def _qtn_gongwei_feihua_sanhe(chart, palace_name: str, rule_id: str, title: str,
                              summary_head: str) -> Optional[QintianCombination]:
    """通用：某宫干飞化入/照/冲本命三合（命财官）论断

    原文（《飞星秘仪》四化宫位变通浅释）：
    财帛：禄权科入本命三合是自立谋生，贵中之财；照三合赚钱能力大于入三合；
          化忌宜入本命三合为吉，不宜冲三合为凶，以上班薪俸为宜。
    官禄：禄权科入三合是自立谋生、事业顺利；照三合亦主自立谋生、多方面发展；
          化忌宜入三合为吉稳定（薪俸并不代表升迁），不宜冲三合为凶、不稳定变动多。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    gong = next((p for p in palace_stems if p.palace_name == palace_name), None)
    if not gong or not gong.stem:
        return None
    sihua = GAN_SIHUA.get(gong.stem, ())
    if len(sihua) < 4:
        return None

    sanfang = _triple_of("命宫")  # 本命三合 = 命财官
    zhao_palaces = {"夫妻", "迁移", "福德"}
    lu, quan, ke, ji = sihua

    # 各化落宫
    def _place(star):
        for p in palace_stems:
            if star in p.major_stars:
                return p.palace_name
        return None

    lu_p, quan_p, ke_p, ji_p = _place(lu), _place(quan), _place(ke), _place(ji)

    lqk_in = [x for x in (lu_p, quan_p, ke_p) if x in sanfang]
    lqk_zhao = [x for x in (lu_p, quan_p, ke_p) if x in zhao_palaces]
    ji_in = ji_p in sanfang
    ji_chong = ji_p in zhao_palaces

    notes = []
    if lqk_in:
        notes.append("禄权科入本命三合（" + "、".join(lqk_in) + "）" + summary_head[0])
    if lqk_zhao:
        notes.append("禄权科照本命三合（" + "、".join(lqk_zhao) + "）" + summary_head[1])
    if ji_in:
        notes.append("化忌（" + (ji_p or "?") + "）入本命三合为吉" + summary_head[2])
    if ji_chong:
        notes.append("化忌（" + (ji_p or "?") + "）冲本命三合为凶" + summary_head[3])

    if not notes:
        return None

    return QintianCombination(
        rule_id=rule_id,
        detected=True,
        evidence_grade=1,
        facts={
            "palace": palace_name,
            "palace_stem": gong.stem,
            "sanfang": sanfang,
            "lqk_in": lqk_in,
            "lqk_zhao": lqk_zhao,
            "ji_in": ji_in,
            "ji_chong": ji_chong,
            "trigger_pattern": palace_name + "宫干飞化入/照/冲本命三合",
        },
        semantic_summary=title + "（蔡明宏《飞星秘仪》）：" + "；".join(notes) + "。",
    )


def detect_qtn_cmb_032_caibo_feihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-032: 财帛宫飞化论断（入/照/冲本命三合）"""
    return _qtn_gongwei_feihua_sanhe(
        chart, "财帛", "QTN-CMB-032", "财帛宫飞化论断",
        ["是自立谋生，贵中之财", "亦是自立谋生，照三合之赚钱能力大于入三合",
         "，以上班薪俸为宜", "，不宜冲三合，以上班薪俸为宜"],
    )


def detect_qtn_cmb_033_guanlu_feihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-033: 官禄宫飞化论断（入/照/冲本命三合）"""
    return _qtn_gongwei_feihua_sanhe(
        chart, "官禄", "QTN-CMB-033", "官禄宫飞化论断",
        ["是自立谋生、事业顺利", "亦主自立谋生、事业顺利并多方面发展，唯照三合之发展大于入三合",
         "，稳定，但薪俸者并不代表升迁", "，冲者不稳定性变动多"],
    )




def detect_qtn_cmb_034_wuxing_ju(chart) -> Optional[QintianCombination]:
    """QTN-CMB-034: 五行局论断（南/北派共用部分）

    陆斌兆《紫微斗数讲义：星曜性质》王亭之注解（复旦大学出版社）原文：
    水二局/木三局/金四局/土五局/火六局，各局根气与心性论断（grade=1）。
    """
    wuj = getattr(chart, 'fiveElementsClass', '')
    if not wuj:
        return None
    from ..shengong_wuxing_data import get_wuxing_ju_assertion
    data = get_wuxing_ju_assertion(wuj)
    if not data:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-034",
        detected=True,
        evidence_grade=data.get("grade", 1),
        facts={
            "wuxing_ju": wuj,
            "text": data["text"],
            "features": data["features"],
            "source": data.get("source", ""),
            "trigger_pattern": "五行局论断（共用部分）",
        },
        semantic_summary=(
            f"{wuj}：{data['text']}特点：{data['features']}"
            f"（{data.get('source', '')}）"
        ),
    )


def detect_qtn_cmb_035_wuxing_shengong(chart) -> Optional[QintianCombination]:
    """QTN-CMB-035: 五行局×身宫论断（南派陆斌兆体系延伸，grade=3）

    身宫落六寄宫（命/财帛/官禄/迁移/福德/夫妻）才有组合论断；
    落非六寄宫无论断（fail-closed，用户铁律：身宫落非六寄宫无论断）。
    """
    wuj = getattr(chart, 'fiveElementsClass', '')
    shen_br = getattr(chart, 'body_earthly_branch', '')
    if not wuj or not shen_br:
        return None
    # 身宫名
    shen_name = ""
    for _pn, _pd in chart.palaces.items():
        if _pd.get("branch") == shen_br:
            shen_name = _pn
            break
    if not shen_name:
        return None
    from ..shengong_wuxing_data import get_shengong_wuxing_assertion, SHENGONG_PALACE_DISPLAY
    data = get_shengong_wuxing_assertion(wuj, shen_name)
    if not data:
        # 身宫落非六寄宫：无论断（用户铁律）
        return None
    display = SHENGONG_PALACE_DISPLAY.get(shen_name, shen_name + "宫")
    return QintianCombination(
        rule_id="QTN-CMB-035",
        detected=True,
        evidence_grade=3,
        facts={
            "wuxing_ju": wuj,
            "shen_palace": shen_name,
            "shen_branch": shen_br,
            "palace_display": display,
            "text": data["text"],
            "features": data["features"],
            "source": "陆斌兆体系延伸（derived_commentary，grade=3）",
            "trigger_pattern": "五行局×身宫寄宫组合论断",
        },
        semantic_summary=(
            f"{wuj}·身落{display}：{data['text']}特点：{data['features']}"
            f"（陆斌兆体系延伸 derived，grade=3）"
        ),
    )


def detect_qtn_cmb_031_sihua_xiangyi(chart) -> Optional[QintianCombination]:
    """QTN-CMB-031: 四化象义（季节/天地人物/分组）——解析层数据

    蔡明宏原文（《悟我十八年》第四章·关注你生命的眼神，421-424页）：
    - 化科：春天是万物萌生，百花盛开的季节。
    - 化权：夏天是水果丰盛，水中弄潮的季节。
    - 化禄：秋天是谷穗飘香，五谷丰收的季节。
    - 化忌：冬天是银装素裹，合家团聚的季节。
    - 四化相应天地人物：禄=天、权=地、科=人、忌=物。
    - 化科、化权一组（木、火一家）；化禄、化忌一组（金、水同航）。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA

    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    sihua = GAN_SIHUA.get(birth_stem, ())
    if len(sihua) < 4:
        return None

    XIANGYI = {
        "禄": ("秋天，谷穗飘香，五谷丰收", "天", "金水同航（与忌一组）"),
        "权": ("夏天，水果丰盛，水中弄潮", "地", "木火一家（与科一组）"),
        "科": ("春天，万物萌生，百花盛开", "人", "木火一家（与权一组）"),
        "忌": ("冬天，银装素裹，合家团聚", "物", "金水同航（与禄一组）"),
    }
    trans_map = [("禄", sihua[0]), ("权", sihua[1]), ("科", sihua[2]), ("忌", sihua[3])]

    notes = []
    star_palaces = {}
    for p in palace_stems:
        for star in p.major_stars:
            star_palaces.setdefault(star, []).append(p.palace_name)

    for trans, star in trans_map:
        season, tiandi, group = XIANGYI[trans]
        places = star_palaces.get(star, [])
        notes.append(
            birth_stem + "干" + star + "化" + trans
            + ("入" + "、".join(places) if places else "（未落主星宫）")
            + "：" + season + "；象" + tiandi + "；" + group
        )

    return QintianCombination(
        rule_id="QTN-CMB-031",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "xiangyi": XIANGYI,
            "trigger_pattern": "生年四化季节/天地人物/分组象义（解析层）",
        },
        semantic_summary="四化象义（蔡明宏《悟我十八年》）：" + "；".join(notes),
    )


def detect_qtn_cmb_036_caibo_ji_yazhi(chart) -> Optional[QintianCombination]:
    """QTN-CMB-036: 财帛宫坐生年化忌（财格压制）

    蔡明宏《紫微斗數飛星秘儀》原文：
    「財帛宮化忌顯示不吉之象，則祿、權、科，同時顯示不吉利解，化忌凶時，三吉化亦凶，
    化忌為吉時，三吉化亦吉。」（财帛宫四化应用·化忌论断）
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    ji_star = birth_sihua[3]
    for pf in palace_stems:
        if pf.palace_name != "财帛":
            continue
        if ji_star in pf.major_stars:
            return QintianCombination(
                rule_id="QTN-CMB-036",
                detected=True,
                evidence_grade=1,
                facts={
                    "birth_stem": birth_stem,
                    "ji_star": ji_star,
                    "caibo_palace_branch": pf.branch,
                    "trigger_pattern": "财帛宫坐生年化忌星",
                },
                semantic_summary=(
                    f"财帛宫坐生年{birth_stem}化忌（{ji_star}）：财帛宫化忌显示不吉之象，"
                    f"则禄、权、科同时显示不吉利解，化忌凶时三吉化亦凶，化忌为吉时三吉化亦吉。"
                    f"（蔡明宏《飞星秘仪》财帛宫化忌论断）"
                ),
            )
    return None


def detect_qtn_cmb_037_caibo_luqunkuo(chart) -> Optional[QintianCombination]:
    """QTN-CMB-037: 财帛宫坐生年禄权科（财格显象）

    蔡明宏《紫微斗數飛星秘儀》原文：
    「財帛：化祿：能自立謀生。自創業賺錢。忙碌。不善理財。化權：善於用錢創業。
    不存死錢利於週轉活用。」
    「（四）化科在財帛宮，代表以上班宜，且安定不善變動。並更主此人貴人相助良多。」
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    star_to_sihua = {
        birth_sihua[0]: "化禄",
        birth_sihua[1]: "化权",
        birth_sihua[2]: "化科",
    }
    for pf in palace_stems:
        if pf.palace_name != "财帛":
            continue
        for star in pf.major_stars:
            sihua = star_to_sihua.get(star)
            if not sihua:
                continue
            text = {
                "化禄": "能自立谋生、自创业赚钱；忙碌，不善理财",
                "化权": "善于用钱创业、不存死钱利于周转活用",
                "化科": "以上班为宜、安定不善变动，贵人相助良多",
            }[sihua]
            return QintianCombination(
                rule_id="QTN-CMB-037",
                detected=True,
                evidence_grade=1,
                facts={
                    "birth_stem": birth_stem,
                    "star": star,
                    "sihua": sihua,
                    "caibo_palace_branch": pf.branch,
                    "trigger_pattern": "财帛宫坐生年禄/权/科",
                },
                semantic_summary=(
                    f"财帛宫坐生年{birth_stem}{sihua}（{star}）：{text}。"
                    f"（蔡明宏《飞星秘仪》财帛宫四化论断）"
                ),
            )
    return None


def detect_qtn_cmb_038_hunqi_xiongxing(chart) -> Optional[QintianCombination]:
    """QTN-CMB-038: 夫妻宫坐凶星（婚姻凶象）

    蔡明宏《紫微斗數飛星秘儀》原文：
    - 破军：「破軍星在夫妻宮、子女宮，容易有失的一面，即意味著留不住，耗損現象。」
    - 巨门：「巨門星入六親宮，代表排斥性較強，象徵遺棄星……在夫妻宮宜晚婚為佳。」
    - 空劫：「地空星與地劫星在夫妻宮……使婚姻難以成局。」
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    notes = []
    for pf in palace_stems:
        if pf.palace_name != "夫妻":
            continue
        if "破军" in pf.major_stars:
            notes.append("破军：容易有失的一面，即留不住、耗损现象")
        if "巨门" in pf.major_stars:
            notes.append("巨门：六亲缘薄之遗弃星，宜晚婚为佳")
        if "地空" in pf.minor_stars or "地劫" in pf.minor_stars:
            notes.append("地空地劫：感情难以成局，对方思想悲观")
        if "天梁" in pf.major_stars:
            notes.append("天梁：宜改老大之作风，防婚姻与感情问题")
        if not notes:
            return None
        return QintianCombination(
            rule_id="QTN-CMB-038",
            detected=True,
            evidence_grade=1,
            facts={
                "marriage_palace_branch": pf.branch,
                "notes": notes,
                "trigger_pattern": "夫妻宫坐破军/巨门/空劫",
            },
            semantic_summary=(
                "夫妻宫坐凶星（婚姻凶象）：" + "；".join(notes) + "。"
                "（蔡明宏《飞星秘仪》星曜论）"
            ),
        )
    return None


def detect_qtn_cmb_039_sheng_nian_ji_hunqi(chart) -> Optional[QintianCombination]:
    """QTN-CMB-039: 生年化忌坐夫妻宫（婚姻波折）

    蔡明宏《紫微斗數飛星秘儀》原文：
    「化忌在夫妻：忌星在六親宮，代表虧欠，即虧欠，則主此人必有太太或先生，
    不必為婚姻之事煩惱。唯不宜太早婚，婚前會有波折。」
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    ji_star = birth_sihua[3]
    for pf in palace_stems:
        if pf.palace_name != "夫妻":
            continue
        if ji_star in pf.major_stars:
            return QintianCombination(
                rule_id="QTN-CMB-039",
                detected=True,
                evidence_grade=1,
                facts={
                    "birth_stem": birth_stem,
                    "ji_star": ji_star,
                    "marriage_palace_branch": pf.branch,
                    "trigger_pattern": "生年化忌坐夫妻宫",
                },
                semantic_summary=(
                    f"生年{birth_stem}化忌（{ji_star}）坐夫妻宫：忌星在六亲宫代表亏欠，"
                    f"主此人必有太太或先生，不必为婚姻之事烦恼；唯不宜太早婚，婚前会有波折。"
                    f"（蔡明宏《飞星秘仪》生年四化在十二宫·夫妻宫）"
                ),
            )
    return None


def detect_qtn_cmb_040_sisha_sunge(chart) -> Optional[QintianCombination]:
    """QTN-CMB-040: 贵格见四煞（格高受折）

    蔡明宏《紫微斗數飛星秘儀》原文：
    「紫微化科：名聲遠揚，貴人提拔，地位高升，若見四煞星，升遷受挫，破財招損，
    尊星化科較重面子。」
    「左輔星與右弼星三合會巨門星、天機星、七殺星、四煞星等，主命格較低。」
    条件：命宫三方（命/财帛/官禄）见生年禄权科（贵格基础）且同方见四煞 → 贵格受折。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    three_ji = set(birth_sihua[:3])  # 禄权科之星
    si_sha = {"火星", "铃星", "擎羊", "陀罗"}
    sanhe = {"命宫", "财帛", "官禄"}
    has_ji, has_sha, sha_palaces = False, False, []
    for pf in palace_stems:
        if pf.palace_name not in sanhe:
            continue
        if set(pf.major_stars) & three_ji:
            has_ji = True
        sha = set(pf.minor_stars) & si_sha
        if sha:
            has_sha = True
            sha_palaces.append(f"{pf.palace_name}({','.join(sorted(sha))})")
    if not (has_ji and has_sha):
        return None
    return QintianCombination(
        rule_id="QTN-CMB-040",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "sha_palaces": sha_palaces,
            "trigger_pattern": "命宫三方见禄权科 + 四煞（贵格折扣）",
        },
        semantic_summary=(
            f"本命三合见生年禄权科主贵，唯三合见四煞（{'、'.join(sha_palaces)}）："
            f"紫微化科若见四煞星，升迁受挫、破财招损；左辅右弼三合会四煞等，主命格较低。"
            f"贵中有折，贵达不显。"
            f"（蔡明宏《飞星秘仪》四煞损贵论）"
        ),
    )


def detect_qtn_cmb_041_zaisha_xueguang(chart) -> Optional[QintianCombination]:
    """QTN-CMB-041: 灾煞星血光论断（命/疾厄/迁移）

    蔡明宏《紫微斗數飛星秘儀》原文：
    - 擎羊（羊刃）：「化氣為刑傷、凶厄之神，主災殺，易見血光，個性好強、激烈。」
    - 破军：「破軍星也是血光星，對本身而言，多外傷。」
    - 太阴：「又稱為血光之星，與開刀有關。」
    - 天机化忌：「代表死亡星，四肢易有外傷，或機械、車禍之事發生。」
    - 廉贞化忌：「在遷移宮化忌與羊刃同宮多凶險。遇廉貞、七殺大小二限重逢，小心車禍。」
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    target = {"命宫", "疾厄", "迁移"}
    notes = []
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    ji_star = birth_sihua[3] if len(birth_sihua) >= 4 else None
    for pf in palace_stems:
        if pf.palace_name not in target:
            continue
        if "擎羊" in pf.minor_stars:
            notes.append(f"{pf.palace_name}坐擎羊（羊刃）：主灾杀，易见血光，个性激烈")
        if "破军" in pf.major_stars:
            notes.append(f"{pf.palace_name}坐破军：血光星，多外伤")
        if "太阴" in pf.major_stars:
            notes.append(f"{pf.palace_name}坐太阴：血光之星，与开刀有关")
        if ji_star == "天机" and "天机" in pf.major_stars:
            notes.append(f"{pf.palace_name}坐天机化忌：死亡星，四肢易有外伤，或机械、车祸之事发生")
        if pf.palace_name == "迁移" and ji_star == "廉贞" and "廉贞" in pf.major_stars:
            notes.append("迁移坐廉贞化忌：与羊刃同宫多凶险，遇廉贞七杀大小二限重逢小心车祸")
    if not notes:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-041",
        detected=True,
        evidence_grade=1,
        facts={
            "notes": notes,
            "trigger_pattern": "命/疾厄/迁移宫坐擎羊/破军/太阴",
        },
        semantic_summary=(
            "灾煞星血光论断：" + "；".join(notes) + "。"
            "（蔡明宏《飞星秘仪》星曜凶性论）"
        ),
    )


def detect_qtn_cmb_042_konggong_shuangji(chart) -> Optional[QintianCombination]:
    """QTN-CMB-042: 空宫双忌论（四化宫位变通·四象法）

    蔡明宏《飞星秘仪》四化宫位变通浅释（一）（OCR校对版第33页）：
    「(二)四象法：宫位无主星，不借对宫之星为用，以本无主星之宫位的
    宫干为四化飞化要诀，以象其宫位之吉凶。……命宫在申无主星，对宫寅
    有太阳、巨门同宫，若命宫干为甲，则太阳化忌在对宫，便成双忌论，
    力量加倍。因命宫无主星之故。……凡无主星之宫位皆同。」

    规则：某宫空（无主星）→ 以该宫宫干飞化四化，若忌星落对宫主星 →
    双忌论（该化力量加倍）。原文以忌为证；禄权科双化论原文未直接给例，
    铁律 fail-closed 不硬建（待原文补证）。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    notes = []
    for pf in palace_stems:
        if pf.major_stars:
            continue  # 非空宫
        pidx = _palace_index(pf.palace_name)
        if pidx < 1:
            continue
        opp_name = ZW_PALACES_ORDER[(pidx - 1 + 6) % 12]
        opp = next((q for q in palace_stems if q.palace_name == opp_name), None)
        if not opp or not opp.major_stars:
            continue
        sihua = GAN_SIHUA.get(pf.stem, ())
        if len(sihua) < 4:
            continue
        ji_star = sihua[3]
        if ji_star in opp.major_stars:
            notes.append(
                f"{pf.palace_name}无主星（空宫），宫干{pf.stem}化忌星{ji_star}在对宫"
                f"{opp_name}（{ji_star}坐{opp_name}）→ 双忌论，力量加倍"
            )
    if not notes:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-042",
        detected=True,
        evidence_grade=1,
        facts={
            "notes": notes,
            "trigger_pattern": "空宫宫干飞化忌星落对宫主星（四象法）",
        },
        semantic_summary=(
            "空宫双忌论：" + "；".join(notes) + "。"
            "（蔡明宏《飞星秘仪》四化宫位变通浅释一，OCR第33页）"
        ),
    )

def detect_all_production(chart) -> List[QintianCombination]:
    """运行所有 production detect 函数"""
    results = []
    for detect_fn in PRODUCTION_DETECTORS:
        try:
            r = detect_fn(chart)
            if r is not None:
                results.append(r)
        except Exception:
            # fail-closed: 错误不传播, 该规则静默失败。
            # Z80-F（2026-10-14）：补日志 —— 此前纯 pass 无任何痕迹，
            # 检测器报错会导致命中数静默减少而无从排查。
            logger.warning(
                "qintian detector failed: %s", getattr(detect_fn, "__name__", detect_fn),
                exc_info=True,
            )
    return results


def detect_all_draft(chart) -> List[QintianCombination]:
    """运行所有 DRAFT detect (应全返回 None)"""
    results = []
    for detect_fn in DRAFT_DETECTORS:
        try:
            r = detect_fn(chart)
            if r is not None:
                results.append(r)
        except Exception:
            logger.debug(
                "qintian draft detector failed: %s",
                getattr(detect_fn, "__name__", detect_fn), exc_info=True,
            )
    return results


def detect_qtn_cmb_043_huaji_ming_you_huaji(chart) -> Optional[QintianCombination]:
    """QTN-CMB-043: 化忌在命又化忌（难贵显·格局中上层以下）

    蔡明宏《飞星秘仪》四化宫位变通·命宫论断（OCR校对版第55页）：
    「（四）化忌在命，又化忌，難貴顯，格局難在中上層面，縱任有財，層面不變。」

    规则：生年化忌星坐命宫（条件1）+ 命宫又自化忌（条件2，命宫干化忌星
    恰在本宫主星）→ 难贵显，格局难在中上层，纵任有财层面不变。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    from .features import get_self_mutagen

    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    ji_star = birth_sihua[3]

    ming = next((p for p in palace_stems if p.palace_name == "命宫"), None)
    if not ming or not ming.major_stars:
        return None

    # 条件1：生年化忌星坐命宫
    if ji_star not in ming.major_stars:
        return None

    # 条件2：命宫又自化忌（命宫干化忌星在本宫主星）
    self_muts = get_self_mutagen(chart)
    has_self_ji = any(
        f.source_palace == "命宫" and f.transformation == "化忌"
        for f in self_muts
    )
    if not has_self_ji:
        return None

    return QintianCombination(
        rule_id="QTN-CMB-043",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "ji_star": ji_star,
            "ming_stem": ming.stem,
            "trigger_pattern": "生年化忌坐命宫 + 命宫自化忌 → 难贵显",
        },
        semantic_summary=(
            f"化忌在命又化忌：生年化忌星{ji_star}坐命宫，命宫干{ming.stem}又自化忌"
            f"（{ji_star}）→ 难贵显，格局难在中上层，纵任有财，层面不变。"
            "（蔡明宏《飞星秘仪》四化宫位变通·命宫论断，OCR第55页）"
        ),
    )



def detect_qtn_cmb_044_shuangxiang_lun(chart) -> Optional[QintianCombination]:
    """QTN-CMB-044: 双象论（生年四化两星同宫，六种双象组合论断）

    蔡明宏《紫微斗數飛星秘儀》「四化应用入门篇」原文（vr-d.com 原著 PDF）：
    - 四化雖名四象，亦分單象與雙象之排列組合，合十干歸四象，演四象步十干，
      單、雙相對法兩儀……沒有固定誰吉誰凶，因它是象，象是假象。
    - 祿忌：祿不可解忌，以雙忌論，主凶。
    - 祿權：財利、發達、吉祥、名利雙收（利大於名）。
    - 祿科：名揚、才幹、獲利、長壽、名利雙收（名大於利）。
    - 權科：名利得，以專技才藝為主，不可自愎太過。
    - 權忌：以技能或薪俸為主，先忌後權，倍加辛勞。
    - 科忌：以學術或手藝為主，先忌後得助。勿太自信反敗。

    规则：生年四化（禄权科忌）四星中任两星落同一宫 → 双象论按组合论断。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    lu, quan, ke, ji = birth_sihua

    SHUANGXIANG = {
        frozenset((lu, ji)): ("祿忌", "祿不可解忌，以雙忌論，主凶"),
        frozenset((lu, quan)): ("祿權", "財利、發達、吉祥、名利雙收（利大於名）"),
        frozenset((lu, ke)): ("祿科", "名揚、才幹、獲利、長壽、名利雙收（名大於利）"),
        frozenset((quan, ke)): ("權科", "名利得，以專技才藝為主，不可自愎太過"),
        frozenset((quan, ji)): ("權忌", "以技能或薪俸為主，先忌後權，倍加辛勞"),
        frozenset((ke, ji)): ("科忌", "以學術或手藝為主，先忌後得助。勿太自信反敗"),
    }

    star_palace = {}
    for pf in palace_stems:
        for st in pf.major_stars:
            if st in (lu, quan, ke, ji):
                star_palace.setdefault(st, pf)

    found = []
    for st1, st2 in [(lu, quan), (lu, ke), (lu, ji), (quan, ke), (quan, ji), (ke, ji)]:
        p1 = star_palace.get(st1)
        p2 = star_palace.get(st2)
        if p1 and p2 and p1.palace_name == p2.palace_name:
            key = frozenset((st1, st2))
            if key in SHUANGXIANG:
                found.append((p1.palace_name, st1, st2, SHUANGXIANG[key]))
    if not found:
        return None
    # 取第一组（同宫双象）
    palace_name, st1, st2, (name, verdict) = found[0]
    return QintianCombination(
        rule_id="QTN-CMB-044",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "palace": palace_name,
            "star1": st1,
            "star2": st2,
            "double_type": name,
            "trigger_pattern": "生年四化两星同宫成双象",
        },
        semantic_summary=(
            f"双象论：生年{birth_stem}化星{st1}与{st2}同落{palace_name}宫，成「{name}」双象——"
            f"{verdict}。（蔡明宏《飞星秘仪》四化应用入门篇，vr-d.com 原著 PDF）"
        ),
    )


def detect_qtn_cmb_045_minggan_double(chart) -> Optional[QintianCombination]:
    """QTN-CMB-045: 命宫宫干=生年干（四化双倍函义·为臣不为君格）

    蔡明宏《紫微斗數飛星秘儀》「命格解」原文（vr-d.com 原著 PDF）：
    - 命宮宮干爲甲，與生年甲同樣的四化，顯示雙倍之函義，故吉凶成敗，有強烈分明之別。
    - 忌星坐命，上班爲宜，又宮干坐甲，太陽又化忌，可謂爲臣不爲君之格，
      若強而爲君格，終究必敗，宜幕後之使者。

    规则：命宫宫干与生年干相同 → 四化双倍；若命宫又坐生年化忌 → 为臣不为君格。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    ming = next((p for p in palace_stems if p.palace_name == "命宫"), None)
    if not ming or not ming.stem or ming.stem != birth_stem:
        return None
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    ji_star = birth_sihua[3] if len(birth_sihua) >= 4 else None
    extra = ""
    if ji_star and ji_star in ming.major_stars:
        extra = ("且命宫坐生年化忌星%s，可謂「為臣不為君」之格，若強而為君格終究必敗，宜幕後之使者。" % ji_star)
    return QintianCombination(
        rule_id="QTN-CMB-045",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "ming_stem": ming.stem,
            "ming_has_sheng_nian_ji": bool(ji_star and ji_star in ming.major_stars),
            "trigger_pattern": "命宫宫干=生年干 → 四化双倍",
        },
        semantic_summary=(
            f"命宫宫干{birth_stem}与生年干相同：四化显示双倍函义，吉凶成败强烈分明。"
            f"{extra}（蔡明宏《飞星秘仪》命格解，vr-d.com 原著 PDF）"
        ),
    )


def detect_qtn_cmb_046_ming_ji_baishou(chart) -> Optional[QintianCombination]:
    """QTN-CMB-046: 命宫坐生年忌+三合不见三吉化（白手起家·贵达难显）

    蔡明宏《紫微斗數飛星秘儀》「命格解」原文（vr-d.com 原著 PDF）：
    - 命宮三合不見生年祿、權、科，而命宮自坐生年忌，主白手起家。
      貴達難顯，以上班或技術為生計。

    规则：命宫坐生年化忌星 + 命宫三合（命财官）内不见生年禄权科
    → 白手起家，贵达难显，以班职或技术为生计。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    lu, quan, ke, ji = birth_sihua
    ming = next((p for p in palace_stems if p.palace_name == "命宫"), None)
    if not ming or not ming.major_stars:
        return None
    # 条件1：命宫坐生年化忌星
    if ji not in ming.major_stars:
        return None
    # 条件2：命宫三合（命财官）不见禄权科
    sanfang = _triple_of("命宫")
    sanfang_names = set(sanfang)
    sanfang_palaces = [p for p in palace_stems if p.palace_name in sanfang_names]
    three_ji_stars = {lu, quan, ke}
    has_three = any(
        st in p.major_stars for p in sanfang_palaces for st in three_ji_stars
    )
    if has_three:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-046",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "ji_star": ji,
            "ming_branch": ming.branch,
            "trigger_pattern": "命宫坐生年忌 + 三合不见禄权科 → 白手起家",
        },
        semantic_summary=(
            f"命宫坐生年{birth_stem}化忌（{ji}），命宫三合（命财官）不见生年禄权科"
            f"→ 主白手起家，贵达难显，以上班或技术为生计。"
            "（蔡明宏《飞星秘仪》命格解，vr-d.com 原著 PDF）"
        ),
    )



def detect_qtn_cmb_047_jiehun_xian(chart) -> Optional[QintianCombination]:
    """QTN-CMB-047: 结婚限（夫妻宫坐生年三吉化 → 第三大限为结婚限）

    蔡明宏《紫微斗數飛星秘儀》「命例解」原文（vr-d.com 原著 PDF）：
    - 夫妻宮坐壬干……已象徵在此大限會結婚，不論順行或逆行者，均於第三個大限爲結婚限。

    规则：命盘夫妻宫坐生年禄/权/科任一 → 第三大限为结婚限（应期层）。
    """
    palace_stems = getattr(chart, 'palace_stems', None)
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    lu, quan, ke = birth_sihua[0], birth_sihua[1], birth_sihua[2]
    three_ji = {lu, quan, ke}
    hun = next((p for p in palace_stems if p.palace_name == "夫妻"), None)
    if not hun or not hun.major_stars:
        return None
    hit_stars = [st for st in hun.major_stars if st in three_ji]
    if not hit_stars:
        return None
    # 第三大限宫位：阳男阴女顺行 / 阴男阳女逆行（从命宫起第3个大限）
    dec_palace = getattr(chart, 'decadal_palace', None) or "命宫"
    order = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役", "官禄", "田宅", "福德", "父母"]
    aliases = {"交友": "仆役"}
    birth_stem_yin = birth_stem in ("甲", "丙", "戊", "庚", "壬")
    gender = getattr(chart, 'gender', 'male')
    male = gender in ("male", "男")
    forward = (birth_stem_yin and male) or (not birth_stem_yin and not male)
    try:
        i0 = order.index(aliases.get(dec_palace, dec_palace))
    except ValueError:
        i0 = 0
    step = 1 if forward else -1
    third_idx = (i0 + 2 * step) % 12
    third_palace = order[third_idx]
    return QintianCombination(
        rule_id="QTN-CMB-047",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "hun_stars": hit_stars,
            "third_decadal_palace": third_palace,
            "direction": "顺行" if forward else "逆行",
            "trigger_pattern": "夫妻宫坐生年三吉化 → 第三大限结婚限",
        },
        semantic_summary=(
            f"结婚限：夫妻宫坐生年{birth_stem}三吉化（{'、'.join(hit_stars)}）"
            f"→ 不论顺行逆行，均于第三大限（{third_palace}宫）为结婚限。"
            "（蔡明宏《飞星秘仪》命例解，vr-d.com 原著 PDF）"
        ),
    )



def _tianxing_palace(chart):
    """返回天刑所在宫名（无则 None）。"""
    for pf in chart.palace_stems:
        if "天刑" in pf.minor_stars:
            return pf.palace_name
    return None


def _tianyao_palace(chart):
    """返回天姚所在宫名（无则 None）。"""
    for pf in chart.palace_stems:
        if "天姚" in pf.minor_stars:
            return pf.palace_name
    return None


def detect_qtn_cmb_048_tianxing_huaji_guanfei(chart) -> Optional[QintianCombination]:
    """QTN-CMB-048: 天刑逢生年化忌 → 官非牢狱之灾

    蔡明宏《飞星秘仪》星性解原文：
    「天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。」
    """
    tx = _tianxing_palace(chart)
    if not tx:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_stem, ())
    if len(birth_sihua) < 4:
        return None
    ji_star = birth_sihua[3]
    pf = next((x for x in chart.palace_stems if x.palace_name == tx), None)
    if not pf:
        return None
    all_stars = set(pf.major_stars) | set(pf.minor_stars)
    if ji_star not in all_stars:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-048",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": birth_stem,
            "ji_star": ji_star,
            "palace": tx,
            "trigger_pattern": "天刑 + 生年化忌同宫 → 官非牢狱",
        },
        semantic_summary=(
            f"官非牢狱格：天刑在{tx}宫，与生年{birth_stem}化忌（{ji_star}）同宫"
            "——「天刑星代表官非與牢獄之災，尤其逢化忌時，要注意」"
            "（蔡明宏《飞星秘仪》星性解）"
        ),
    )


def detect_qtn_cmb_049_tianxing_hun(rely) -> Optional[QintianCombination]:
    """QTN-CMB-049: 天刑入夫妻宫 → 易离婚、宜晚婚

    蔡明宏《飞星秘仪》星性解原文：
    「天刑星不宜入夫妻宮，容易有離婚現象，晚婚佳。」
    """
    tx = _tianxing_palace(rely)
    if tx != "夫妻":
        return None
    return QintianCombination(
        rule_id="QTN-CMB-049",
        detected=True,
        evidence_grade=1,
        facts={
            "palace": tx,
            "trigger_pattern": "天刑入夫妻宫 → 易离婚晚婚",
        },
        semantic_summary=(
            "婚姻刑克：天刑入夫妻宫——「天刑星不宜入夫妻宮，容易有離婚現象，晚婚佳」"
            "（蔡明宏《飞星秘仪》星性解）"
        ),
    )


def detect_qtn_cmb_050_tianyao_taohua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-050: 天姚入夫妻宫 → 夫妻多艳遇（桃花）

    蔡明宏《飞星秘仪》星性解原文：
    「天姚星在夫妻宮，夫妻雙方都有人緣，多艷遇。」
    """
    ty = _tianyao_palace(chart)
    if ty != "夫妻":
        return None
    return QintianCombination(
        rule_id="QTN-CMB-050",
        detected=True,
        evidence_grade=1,
        facts={
            "palace": ty,
            "trigger_pattern": "天姚入夫妻宫 → 多艳遇",
        },
        semantic_summary=(
            "桃花格：天姚入夫妻宫——「天姚星在夫妻宮，夫妻雙方都有人緣，多艷遇」"
            "（蔡明宏《飞星秘仪》星性解）"
        ),
    )


def detect_qtn_cmb_051_wuqu_huaji_tianxing(chart) -> Optional[QintianCombination]:
    """QTN-CMB-051: 武曲化忌与天刑同宫 → 官非刑罚

    蔡明宏《飞星秘仪》十干化曜·己干原文：
    「武曲化忌：財星化忌，主財不利，周轉不靈，倒債多，與天刑同宮化忌，因官非刑罰。」
    """
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    if birth_stem != "己":
        return None
    tx = _tianxing_palace(chart)
    if not tx:
        return None
    pf = next((x for x in chart.palace_stems if x.palace_name == tx), None)
    if not pf:
        return None
    all_stars = set(pf.major_stars) | set(pf.minor_stars)
    if "武曲" not in all_stars:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-051",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": "己",
            "palace": tx,
            "trigger_pattern": "己干武曲化忌 + 天刑同宫 → 官非刑罚",
        },
        semantic_summary=(
            f"官非刑罚格：己干武曲化忌与天刑同宫（{tx}）——"
            "「武曲化忌……與天刑同宮化忌，因官非刑罰，宜節省守財」"
            "（蔡明宏《飞星秘仪》十干化曜）"
        ),
    )


def detect_qtn_cmb_052_taiyang_huaji_tianxing(chart) -> Optional[QintianCombination]:
    """QTN-CMB-052: 太阳化忌与天刑同宫 → 牢狱之灾

    蔡明宏《飞星秘仪》十干化曜·庚干原文：
    「太陽化忌：不利男性、父、夫、子、眼目有疾……與天刑星逢化忌，注意牢獄之災。」
    """
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    birth_stem = stems_10[(chart.birth_year - 4) % 10]
    if birth_stem != "庚":
        return None
    tx = _tianxing_palace(chart)
    if not tx:
        return None
    pf = next((x for x in chart.palace_stems if x.palace_name == tx), None)
    if not pf:
        return None
    all_stars = set(pf.major_stars) | set(pf.minor_stars)
    if "太阳" not in all_stars:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-052",
        detected=True,
        evidence_grade=1,
        facts={
            "birth_stem": "庚",
            "palace": tx,
            "trigger_pattern": "庚干太阳化忌 + 天刑同宫 → 牢狱之灾",
        },
        semantic_summary=(
            f"牢狱格：庚干太阳化忌与天刑同宫（{tx}）——"
            "「太陽化忌……與天刑星逢化忌，注意牢獄之災」"
            "（蔡明宏《飞星秘仪》十干化曜）"
        ),
    )





def detect_qtn_cmb_058_xin_gan_sihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-058: 辛干四化（巨门禄/太阳权/文曲科/文昌忌）——钦天原文例

    《飞星秘仪》子女宫解（辛干例）：
    - 子女宮宮干坐「辛」巨門化祿與文昌化忌，同宮在財帛，雖言雙忌，必有
      子女（不論男女），因忌入財帛，與命三合。唯雙忌，主不多產時宜多加
      注意母體健康。
    - 太陽化權入命宮，有子女，唯將來子女均獨立，即自立更生格，個性比較剛強。
    - 文曲化科入夫妻，代表子女會喜接近母親，得父母之寵……更也代表子女會孝順。

    规则（数据层+原文论断）：生年干=辛时，输出辛干四化定位：
    - 巨门禄+文昌忌同宫 → 双忌结构（原文例语境：必有子女/产育注意）
    - 太阳权入命宫 → 子女独立刚强
    - 文曲科入夫妻 → 子女近母孝顺
    （仅输出原文可核验结构，不做额外推测。）
    """
    from ....ziwei_engine import GAN_SIHUA
    stems = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    g = stems[(chart.birth_year - 4) % 10]
    if g != "辛":
        return None
    sihua = GAN_SIHUA.get(g, ())
    if len(sihua) < 4:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    star_palace = {}
    for pn, pd in chart.palaces.items():
        for grp in ("major","minor","adj"):
            for st in pd.get(grp, []):
                star_palace[st] = pn
    lu, quan, ke, ji = sihua
    lu_pn = star_palace.get(lu, '')
    quan_pn = star_palace.get(quan, '')
    ke_pn = star_palace.get(ke, '')
    ji_pn = star_palace.get(ji, '')
    facts = {
        "gan": "辛",
        "lu": lu, "lu_palace": lu_pn,
        "quan": quan, "quan_palace": quan_pn,
        "ke": ke, "ke_palace": ke_pn,
        "ji": ji, "ji_palace": ji_pn,
        "lu_ji_same_palace": bool(lu_pn and lu_pn == ji_pn),
        "quan_in_ming": quan_pn == "命宫",
        "ke_in_fuqi": ke_pn == "夫妻",
    }
    notes = []
    if lu_pn and lu_pn == ji_pn:
        notes.append(f"{lu}禄与{ji}忌同宫（{lu_pn}）——原文例：双忌结构，产育/母体健康注意")
    if quan_pn == "命宫":
        notes.append("太阳化权入命宫——原文例：子女独立、自立更生格")
    if ke_pn == "夫妻":
        notes.append("文曲化科入夫妻——原文例：子女喜近母亲、孝顺")
    return QintianCombination(
        rule_id="QTN-CMB-058",
        detected=True,
        evidence_grade=1,
        semantic_summary=(
            f"辛干四化：{lu}禄@{lu_pn or '？'}、{quan}权@{quan_pn or '？'}、"
            f"{ke}科@{ke_pn or '？'}、{ji}忌@{ji_pn or '？'}" + (f"；{'；'.join(notes)}" if notes else '')
        ),
        facts=facts,
    )

def _qintian_flow_doujun_branch(chart):
    """钦天斗君地支：本命盘寅位宫，地支恒为寅。

    蔡明宏《飞星秘仪》流月四化应用：「斗君之位一定在原命盤寅位之宮位，
    例原命盤寅位為子女宮，則每年流年君必是流年之子女位」「邵子曰易統寅
    而生人，故月令之始，與寅宮再建正月何別」。

    十二宫名与地支的对应在盘面上固定（palace_stems 恒以寅位宫开头）：
    本命盘寅位宫名 = palace_stems[0].palace_name；斗君即此宫，其地支
    恒为寅（「用寅为正月始」与「用斗君」在钦天定义下等价）。

    注：与《紫微斗数全书》安斗君诀（流年太岁宫起正月逆至生月、生月宫
    起子顺数至生时——流年斗君随太岁变）属三合体系用法；北派钦天流月
    应用依蔡明宏原文取本命盘寅位宫，两者不混用。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    return '寅'


def detect_qtn_cmb_054_liuyue_sihua(chart) -> Optional[QintianCombination]:
    """QTN-CMB-054: 流月四化应用（钦天斗君起正月，本命盘宫干飞化）

    《飞星秘仪》流月四化应用原文：
    - 流月即指流年十二個月的吉凶，法流年而行。
    - 用：其用有二種。（一）斗君 （二）用寅為正月始。
    - 若流年之宮干用原始宮干者，流月一律用「斗君」。原因：斗君之位
      一定在原命盤寅位之宮位，例原命盤寅位為子女宮，則每年流年君必是
      流年之子女位，邵子曰：「易統寅而生人」，故月令之始，與寅宮再建
      正月何別？
    - 流月四化飛曜天干：一律用本命盤天干，不可另取用。

    实现（本引擎 016 流年用本命盘原始宫干 → 流月走斗君路线）：
    - 斗君宫 = 本命盘寅位宫名在流年盘定位（生年斗君=寅位=「寅为正月始」）
    - 流月宫 = 斗君宫地支顺行 (flow_month-1) 位
    - 流月四化 = 流月宫的本命盘宫干四化（数据层输出）
    入参：chart.flow_month（1-12），无则 fail-closed 返回 None。
    """
    flow_month = getattr(chart, 'flow_month', 0)
    if not flow_month or flow_month < 1 or flow_month > 12:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    BR = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    br2pn = {p.branch: p.palace_name for p in palace_stems}
    stem_by_pn = {p.palace_name: p.stem for p in palace_stems}
    dj_br = _qintian_flow_doujun_branch(chart)
    if not dj_br:
        return None
    mb = BR[(BR.index(dj_br) + (flow_month - 1)) % 12]
    mp = br2pn[mb]
    g = stem_by_pn.get(mp, '')
    if not g:
        return None
    sihua = GAN_SIHUA.get(g, ())
    if len(sihua) < 4:
        return None
    lu_q, quan_q, ke_q, ji_q = sihua
    star_palace = {}
    for p in palace_stems:
        for s in (list(p.major_stars) + list(p.minor_stars)):
            star_palace[s] = p.palace_name
    def _home(s):
        return star_palace.get(s, "?")
    return QintianCombination(
        rule_id="QTN-CMB-054",
        detected=True,
        evidence_grade=1,
        facts={
            "flow_month": flow_month,
            "doujun_palace": br2pn[dj_br],
            "month_palace": mp,
            "month_branch": mb,
            "month_stem": g,
            "liuyue_sihua": {"lu": sihua[0], "quan": sihua[1], "ke": sihua[2], "ji": sihua[3]},
        },
        semantic_summary=(
            f"流月四化（钦天斗君法，{flow_month}月）：斗君居本命{br2pn[dj_br]}（{dj_br}位），"
            f"流月宫={mp}（{mb}），流月干={g}，飞化为 "
            f"化禄{lu_q}({_home(lu_q)})、化权{quan_q}({_home(quan_q)})、"
            f"化科{ke_q}({_home(ke_q)})、化忌{ji_q}({_home(ji_q)})。"
        ),
    )


def detect_qtn_cmb_055_liuyue_ji_tianxing(chart) -> Optional[QintianCombination]:
    """QTN-CMB-055: 流月化忌入天刑宫 → 该月官非牢狱（应期到月）

    依据组合：
    - 《飞星秘仪》星性解：「天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。」
    - 《飞星秘仪》流月四化应用：「流月用斗君……流月四化飛曜天干一律用本命盤天干」
    规则：流月宫本命盘宫干四化，化忌星落在天刑所在宫
      → 该流月官非牢狱结构成立。
    入参：chart.flow_month（1-12），无则 fail-closed 返回 None。
    """
    flow_month = getattr(chart, 'flow_month', 0)
    if not flow_month or flow_month < 1 or flow_month > 12:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    BR = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    br2pn = {p.branch: p.palace_name for p in palace_stems}
    stem_by_pn = {p.palace_name: p.stem for p in palace_stems}
    dj_br = _qintian_flow_doujun_branch(chart)
    if not dj_br:
        return None
    mb = BR[(BR.index(dj_br) + (flow_month - 1)) % 12]
    mp = br2pn[mb]
    g = stem_by_pn.get(mp, '')
    if not g:
        return None
    sihua = GAN_SIHUA.get(g, ())
    if len(sihua) < 4:
        return None
    ji_star = sihua[3]
    tx = next((p for p in palace_stems if "天刑" in p.minor_stars), None)
    if not tx:
        return None
    tx_stars = set(tx.major_stars) | set(tx.minor_stars)
    if ji_star not in tx_stars:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-055",
        detected=True,
        evidence_grade=1,
        facts={
            "flow_month": flow_month,
            "month_palace": mp,
            "month_stem": g,
            "ji_star": ji_star,
            "tianxing_palace": tx.palace_name,
        },
        semantic_summary=(
            f"流月官非结构（{flow_month}月）：流月{mp}宫（{mb}）{g}干化忌{ji_star}，"
            f"而{ji_star}落天刑所在之{tx.palace_name}宫——"
            f"《飞星秘仪》「天刑星代表官非與牢獄之災，尤其逢化忌時要注意」，"
            f"该流月防官非诉讼、刑责是非。（应期到月，吉否仍参看生年/大限对待）"
        ),
    )


def detect_qtn_cmb_056_sanjihua_liuyin(chart) -> Optional[QintianCombination]:
    """QTN-CMB-056: 三吉化于六阴宫 → 成就条件在「人和」

    《飞星秘仪》三吉化于六阴（PDF书85-86页原文，OCR空表格为命盘图非文字残缺）：
    - 祿、權、科全在六陰位，非自立格，若要有成，必須要有人於背後輔佐，輔相，才有自立可言
    - 三吉化於六陰者，要成就的基本條件，是「人和」，若失人和，就註定
      失敗的命運步伐。得有人和者，財利亦隨之而來，是人蔭其成，而非
      本身之獨成。
    六阴：地支阴支 巳未酉亥丑卯（六阳=子寅辰午申戌）。
    规则：生年干四化中禄/权/科（三吉化）至少一化落六阴宫
      → 三吉化于六阴结构成立（定性：成败系于人和，人和判断留待
      解析层/用户输入，引擎不做自动判定）。
    """
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    # 生年干
    stems = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    g = stems[(chart.birth_year - 4) % 10]
    sihua = GAN_SIHUA.get(g, ())
    if len(sihua) < 4:
        return None
    LIUYIN = {"巳","未","酉","亥","丑","卯"}
    star_palace = {}
    for pn, pd in chart.palaces.items():
        for grp in ("major","minor","adj"):
            for st in pd.get(grp, []):
                star_palace[st] = pn
    branch_by_pn = {p.palace_name: p.branch for p in palace_stems}
    hits = []
    for idx, name in ((0,"禄"),(1,"权"),(2,"科")):
        st = sihua[idx]
        pn = star_palace.get(st)
        if pn and branch_by_pn.get(pn) in LIUYIN:
            hits.append({"hua": name, "star": st, "palace": pn, "branch": branch_by_pn[pn]})
    if not hits:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-056",
        detected=True,
        evidence_grade=1,
        semantic_summary=f"三吉化于六阴：{g}干 {'、'.join(h['hua'] + h['star'] + '入' + h['palace'] for h in hits)}，成就系于人和（《飞星秘仪》）。",
        facts={
            "gan": g,
            "liuyin_hits": hits,
            "verbatim": "三吉化於六陰者，要成就的基本條件，是「人和」，若失人和，就註定失敗的命運步伐。得有人和者，財利亦隨之而來，是人蔭其成，而非本身之獨成。",
        },
    )


def detect_qtn_cmb_057_liunian_liuyue(chart) -> Optional[QintianCombination]:
    """QTN-CMB-057: 流年+流月四化组合（天地人三盘数据层）

    《飞星秘仪》四化总结概要：
    - 本命為天──生年四化與大限錯綜，斷大限吉凶。
      大限為地──大限介於本命與流年之間為機紐。
      流年為人──生年四化與流年錯綜，斷流年吉凶。
    - 大限為天 流年為地 流月為人──亦三合而一。四化之飛曜天干，
      一律用本命盤天干。不可另取用。

    实现（纯数据层，不断言吉凶事件）：
    - flow_year（流年太岁宫原始宫干四化）+ flow_month（斗君流月四化）
      同时指定时，输出两层四化 + 化忌落宫交集（供解析层判读）。
    入参：chart.flow_year + chart.flow_month，缺一 fail-closed。
    """
    flow_year = getattr(chart, 'flow_year', 0)
    flow_month = getattr(chart, 'flow_month', 0)
    if not flow_year or not flow_month:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    stems_10 = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    branches_12 = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    flow_branch = branches_12[(flow_year - 4) % 12]
    br2pn = {p.branch: p.palace_name for p in palace_stems}
    stem_by_pn = {p.palace_name: p.stem for p in palace_stems}
    star_palace = {}
    for pn, pd in chart.palaces.items():
        for grp in ("major","minor","adj"):
            for st in pd.get(grp, []):
                star_palace[st] = pn

    # 流年层：太岁宫原始宫干四化
    flow_palace = br2pn.get(flow_branch, '')
    flow_stem = stem_by_pn.get(flow_palace, '')
    if not flow_palace or not flow_stem:
        return None
    fy_sihua = GAN_SIHUA.get(flow_stem, ())
    if len(fy_sihua) < 4:
        return None

    # 流月层：钦天流年斗君起正月顺行
    dj_br = _qintian_flow_doujun_branch(chart)
    mb = branches_12[(branches_12.index(dj_br) + (flow_month - 1)) % 12] if dj_br else ''
    mp = br2pn.get(mb, '')
    mg = stem_by_pn.get(mp, '')
    if not mp or not mg:
        return None
    fm_sihua = GAN_SIHUA.get(mg, ())
    if len(fm_sihua) < 4:
        return None

    fy_ji_star = fy_sihua[3]
    fm_ji_star = fm_sihua[3]
    fy_ji_palace = star_palace.get(fy_ji_star, '')
    fm_ji_palace = star_palace.get(fm_ji_star, '')
    return QintianCombination(
        rule_id="QTN-CMB-057",
        detected=True,
        evidence_grade=1,
        semantic_summary=(
            f"流年{flow_year}{flow_branch}年四化（{flow_stem}干，{flow_palace}宫）："
            f"{fy_sihua[0]}禄、{fy_sihua[1]}权、{fy_sihua[2]}科、{fy_sihua[3]}忌@{fy_ji_palace}；"
            f"流月{flow_month}月（{mg}干，{mp}宫）："
            f"{fm_sihua[0]}禄、{fm_sihua[1]}权、{fm_sihua[2]}科、{fm_sihua[3]}忌@{fm_ji_palace}。"
        ),
        facts={
            "flow_year": flow_year,
            "flow_branch": flow_branch,
            "flow_palace": flow_palace,
            "flow_stem": flow_stem,
            "flow_sihua": list(fy_sihua),
            "flow_ji_palace": fy_ji_palace,
            "flow_month": flow_month,
            "month_palace": mp,
            "month_stem": mg,
            "month_sihua": list(fm_sihua),
            "month_ji_palace": fm_ji_palace,
            "double_ji_same_palace": bool(fy_ji_palace and fy_ji_palace == fm_ji_palace),
        },
    )

def detect_qtn_cmb_053_daxian_ji_tianxing(chart) -> Optional[QintianCombination]:
    """QTN-CMB-053: 大限化忌入天刑宫 → 该大限官非牢狱（应期层，第一大限）

    依据组合：
    - 《飞星秘仪》星性解：「天刑星代表官非與牢獄之災，尤其逢化忌時，要注意。」
    - 《飞星秘仪》大限四化应用：「大限即以本命盤的宮干為大限之宮干」
      （本命为天、大限为地，大限四化用本命盘宫干飞化）。
    - 第一大限（decadal_palace）用其本命宫干飞化，化忌星落天刑所在宫
      → 大限层官非牢狱结构成立。
    """
    dec_palace = getattr(chart, 'decadal_palace', None)
    if not dec_palace:
        return None
    from ....ziwei_engine import GAN_SIHUA
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    dec = next((p for p in palace_stems if p.palace_name == dec_palace), None)
    if not dec or not dec.stem:
        return None
    dec_sihua = GAN_SIHUA.get(dec.stem, ())
    if len(dec_sihua) < 4:
        return None
    ji_star = dec_sihua[3]
    tx = next((p for p in palace_stems if "天刑" in p.minor_stars), None)
    if not tx:
        return None
    all_stars = set(tx.major_stars) | set(tx.minor_stars)
    if ji_star not in all_stars:
        return None
    return QintianCombination(
        rule_id="QTN-CMB-053",
        detected=True,
        evidence_grade=1,
        facts={
            "decadal_palace": dec_palace,
            "decadal_stem": dec.stem,
            "ji_star": ji_star,
            "tianxing_palace": tx.palace_name,
            "trigger_pattern": "大限化忌入天刑宫 → 大限官非牢狱",
        },
        semantic_summary=(
            f"大限官非格：大限命宫{dec_palace}（本命{dec.stem}干）化忌（{ji_star}）"
            f"入天刑所在{tx.palace_name}宫——此大限防官非牢狱之灾"
            "（蔡明宏《飞星秘仪》星性解 + 大限四化应用）"
        ),
    )


def detect_qtn_cmb_059_daxian_liunian_shuangji(chart) -> Optional[QintianCombination]:
    """QTN-CMB-059: 大限忌 + 流年忌 双忌叠加（应期到年）

    多源一致论断：
    - 中州派《紫微斗数深造讲义·化曜》："推断流年，通常只需视大限及流年
      两组化曜。当生年四化被冲会之时，然后始须注意，不冲起则作用甚小。"
    - 《紫微斗数精成》第14章："推算流年运，应由大限盘的天干四化情况并
      结合本命盘之象来推断，三环相扣。"
    - 通行法：流年化忌落入大限化忌所在宫（或对冲），称「双忌叠加」，
      该年该宫代表事项需高度留意，单忌有转圜、双忌需提前止损。

    实现（结构判定，不下"大凶"硬断语，只陈述叠加事实+标准提示）：
    - 大限忌 = decadal_palace 本命盘宫干四化之忌星落宫
    - 流年忌 = flow_year 太岁位宫（本命原始宫干）四化之忌星落宫
    - 二者同宫或对冲 → 双忌叠加成立。
    入参：chart.flow_year（须 > birth_year，否则与本命同年 trivial，fail-closed）。
    """
    flow_year = getattr(chart, 'flow_year', 0)
    birth_year = getattr(chart, 'birth_year', 0)
    dec_palace = getattr(chart, 'decadal_palace', None)
    if not flow_year or not birth_year or flow_year <= birth_year or not dec_palace:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    branches_12 = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    stems_10 = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    br2pn = {p.branch: p.palace_name for p in palace_stems}
    stem_by_pn = {p.palace_name: p.stem for p in palace_stems}
    pn2br = {p.palace_name: p.branch for p in palace_stems}
    star_palace = {}
    for pn, pd in chart.palaces.items():
        for grp in ("major", "minor", "adj"):
            for st in pd.get(grp, []):
                star_palace[st] = pn

    # 大限忌
    dec_stem = stem_by_pn.get(dec_palace, '')
    dec_sihua = GAN_SIHUA.get(dec_stem, ())
    if len(dec_sihua) < 4:
        return None
    dec_ji_star = dec_sihua[3]
    dec_ji_palace = star_palace.get(dec_ji_star, '')

    # 流年忌（太岁位宫原始宫干）
    flow_branch = branches_12[(flow_year - 4) % 12]
    flow_palace = br2pn.get(flow_branch, '')
    flow_stem = stem_by_pn.get(flow_palace, '')
    flow_sihua = GAN_SIHUA.get(flow_stem, ())
    if not flow_palace or not flow_stem or len(flow_sihua) < 4:
        return None
    fy_ji_star = flow_sihua[3]
    fy_ji_palace = star_palace.get(fy_ji_star, '')

    if not dec_ji_palace or not fy_ji_palace:
        return None
    same = (dec_ji_palace == fy_ji_palace)
    opposite = False
    if not same:
        dbr = pn2br.get(dec_ji_palace, '')
        fbr = pn2br.get(fy_ji_palace, '')
        if dbr and fbr:
            opposite = abs(branches_12.index(dbr) - branches_12.index(fbr)) == 6
    if not (same or opposite):
        return None
    rel = "同宫叠加" if same else "对冲冲会"
    return QintianCombination(
        rule_id="QTN-CMB-059",
        detected=True,
        evidence_grade=1,
        facts={
            "flow_year": flow_year,
            "decadal_palace": dec_palace,
            "decadal_ji_star": dec_ji_star,
            "decadal_ji_palace": dec_ji_palace,
            "flow_ji_star": fy_ji_star,
            "flow_ji_palace": fy_ji_palace,
            "relation": rel,
            "trigger_pattern": "大限忌+流年忌同宫/对冲 → 双忌叠加",
        },
        semantic_summary=(
            f"双忌叠加应期（{flow_year}年）：大限{dec_palace}（{dec_stem}干）化忌"
            f"（{dec_ji_star}@{dec_ji_palace}），流年{flow_year}{flow_branch}（{flow_stem}干）化忌"
            f"（{fy_ji_star}@{fy_ji_palace}）——二者{rel}。"
            f"中州派法：此年该宫代表事项需高度留意，单忌有转圜、双忌需提前止损。"
        ),
    )


def detect_qtn_cmb_060_sanji_tonggong(chart) -> Optional[QintianCombination]:
    """QTN-CMB-060: 生年忌 + 大限忌 + 流年忌 三忌同宫（高风险年）

    通行法：本命、大限、流年三层忌落同一宫位，称「三忌同宫/三忌叠加」，
    那一年该宫代表事项需优先留意，事件概率大幅提升（多源一致）。
    实现（结构判定，不断吉凶事件）：三层忌星落宫全等 → 三忌同宫成立。
    入参：chart.flow_year（须 > birth_year）。
    """
    flow_year = getattr(chart, 'flow_year', 0)
    birth_year = getattr(chart, 'birth_year', 0)
    dec_palace = getattr(chart, 'decadal_palace', None)
    if not flow_year or not birth_year or flow_year <= birth_year or not dec_palace:
        return None
    palace_stems = chart.palace_stems
    if not palace_stems:
        return None
    from ....ziwei_engine import GAN_SIHUA
    branches_12 = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    stems_10 = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    br2pn = {p.branch: p.palace_name for p in palace_stems}
    stem_by_pn = {p.palace_name: p.stem for p in palace_stems}
    star_palace = {}
    for pn, pd in chart.palaces.items():
        for grp in ("major", "minor", "adj"):
            for st in pd.get(grp, []):
                star_palace[st] = pn

    # 生年忌
    birth_gan = stems_10[(birth_year - 4) % 10]
    birth_sihua = GAN_SIHUA.get(birth_gan, ())
    if len(birth_sihua) < 4:
        return None
    birth_ji_star = birth_sihua[3]
    birth_ji_palace = star_palace.get(birth_ji_star, '')

    # 大限忌
    dec_stem = stem_by_pn.get(dec_palace, '')
    dec_sihua = GAN_SIHUA.get(dec_stem, ())
    if len(dec_sihua) < 4:
        return None
    dec_ji_star = dec_sihua[3]
    dec_ji_palace = star_palace.get(dec_ji_star, '')

    # 流年忌
    flow_branch = branches_12[(flow_year - 4) % 12]
    flow_palace = br2pn.get(flow_branch, '')
    flow_stem = stem_by_pn.get(flow_palace, '')
    flow_sihua = GAN_SIHUA.get(flow_stem, ())
    if not flow_palace or not flow_stem or len(flow_sihua) < 4:
        return None
    fy_ji_star = flow_sihua[3]
    fy_ji_palace = star_palace.get(fy_ji_star, '')

    if not (birth_ji_palace and dec_ji_palace and fy_ji_palace):
        return None
    if not (birth_ji_palace == dec_ji_palace == fy_ji_palace):
        return None
    return QintianCombination(
        rule_id="QTN-CMB-060",
        detected=True,
        evidence_grade=1,
        facts={
            "flow_year": flow_year,
            "birth_ji_star": birth_ji_star,
            "decadal_ji_star": dec_ji_star,
            "flow_ji_star": fy_ji_star,
            "ji_palace": birth_ji_palace,
            "trigger_pattern": "生年忌+大限忌+流年忌三忌同宫 → 高风险年",
        },
        semantic_summary=(
            f"三忌同宫（{flow_year}年）：生年忌（{birth_ji_star}）、大限忌（{dec_ji_star}）、"
            f"流年忌（{fy_ji_star}）三层化忌同落{birth_ji_palace}宫。"
            f"此年{birth_ji_palace}宫代表事项为全年风险焦点，需优先留意（三忌叠加，事件概率大幅提升）。"
        ),
    )


PRODUCTION_DETECTORS = [
    detect_qtn_cmb_001_laiyin,
    detect_qtn_cmb_002_space_time,
    detect_qtn_cmb_003_zihua_benyi,
    detect_qtn_cmb_004_xiangxin,
    detect_qtn_cmb_005_lixiangqishu,
    detect_qtn_cmb_006_chuanlian,
    detect_qtn_cmb_007_lixin,
    detect_qtn_cmb_008_zihua_cixu,
    detect_qtn_cmb_009_zihua_liti,
    detect_qtn_cmb_010_zihua_fenlei,
    detect_qtn_cmb_011_wufenlei,
    detect_qtn_cmb_012_churu,
    detect_qtn_cmb_013_faxiang,
    detect_qtn_cmb_014_shengong,
    detect_qtn_cmb_015_sheng_nian_jieyi,
    detect_qtn_cmb_016_liunian,
    detect_qtn_cmb_017_daixian,
    detect_qtn_cmb_018_zihua,
    detect_qtn_cmb_019_doujun,
    detect_qtn_cmb_020_yongshen,
    detect_qtn_cmb_021_yinyang_biaoli,
    detect_qtn_cmb_022_pingheng,
    detect_qtn_cmb_023_minggong_feihua,
    detect_qtn_cmb_024_liuqin_ji,
    detect_qtn_cmb_025_tianzhai_feihua,
    detect_qtn_cmb_026_sanjihua_yinyang,
    detect_qtn_cmb_027_laiyin_guige,
    detect_qtn_cmb_028_shihua_shallow,
    detect_qtn_cmb_029_daxian_liuqin_chong,
    detect_qtn_cmb_030_mingge_zihua_sun,
    detect_qtn_cmb_034_wuxing_ju,
    detect_qtn_cmb_035_wuxing_shengong,
    detect_qtn_cmb_031_sihua_xiangyi,
    detect_qtn_cmb_032_caibo_feihua,
    detect_qtn_cmb_033_guanlu_feihua,
    detect_qtn_cmb_036_caibo_ji_yazhi,
    detect_qtn_cmb_037_caibo_luqunkuo,
    detect_qtn_cmb_038_hunqi_xiongxing,
    detect_qtn_cmb_039_sheng_nian_ji_hunqi,
    detect_qtn_cmb_040_sisha_sunge,
    detect_qtn_cmb_041_zaisha_xueguang,
    detect_qtn_cmb_042_konggong_shuangji,
    detect_qtn_cmb_043_huaji_ming_you_huaji,
    detect_qtn_cmb_044_shuangxiang_lun,
    detect_qtn_cmb_045_minggan_double,
    detect_qtn_cmb_046_ming_ji_baishou,
    detect_qtn_cmb_047_jiehun_xian,
    detect_qtn_cmb_048_tianxing_huaji_guanfei,
    detect_qtn_cmb_049_tianxing_hun,
    detect_qtn_cmb_050_tianyao_taohua,
    detect_qtn_cmb_051_wuqu_huaji_tianxing,
    detect_qtn_cmb_052_taiyang_huaji_tianxing,
    detect_qtn_cmb_053_daxian_ji_tianxing,
    detect_qtn_cmb_054_liuyue_sihua,
    detect_qtn_cmb_055_liuyue_ji_tianxing,
    detect_qtn_cmb_056_sanjihua_liuyin,
    detect_qtn_cmb_057_liunian_liuyue,
    detect_qtn_cmb_058_xin_gan_sihua,
    detect_qtn_cmb_059_daxian_liunian_shuangji,
    detect_qtn_cmb_060_sanji_tonggong,
]

DRAFT_DETECTORS: List = []
