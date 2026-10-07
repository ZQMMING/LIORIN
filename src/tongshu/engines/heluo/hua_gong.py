"""H6: 化工计算模块

职责：判断先天卦/后天卦是否得「天地生生化化之妙」。

**原典依据（2026-10-07 逐条核对，替换掉三处零命中的伪引）**：

  · L573 标题「**化工论**」——本模块出处。2026-10-07 首轮误判此节「检索 0 处」，
    实为**我的检索式写成「论化工」（词序相反）**所致，原著确有此节，已撤回该判断。
  · L576「化工者，天地生生化化之妙也。人得之为有生之理，士者得之则发科甲科名，
           常人得之则发生涯名举。传云，人生得化工，显位亦显名。」
  · L579 标题「化工相反图见前」＋ L585–594 四条化工相反（图见前，此处列其正文）。
  · L582「又有大象与小象化工虽相反，**却又有相生者，则吉。但忌克制，尤凶**。」
  · L597「凡人根基不得化工者，灾重也。……**有化工之气者，艰难获福**。」
  · L324「况夏至后生人，**离为正伯，即化工也**。化工入域，斯人必运帝王之筹策」
         ——「正伯」即坎震离兑四正卦，全书 6 处均此义。
  · L468「人生得元气富贵居高位，人生得化工荣显作名公。**但要入域**。」

  ⚠「逢化工诗」在原著检索 0 处，该项仍属误植，已删。

冻结规则：
  1. 四季对应化工卦（**简化近似**，见下）：
     - 冬（亥子丑月）→ 坎 ☵
     - 春（寅卯辰月）→ 震 ☳
     - 夏（巳午未月）→ 离 ☲
     - 秋（申酉戌月）→ 兑 ☱
     ⚠ 原典 L576 明言此口径是「前辈之论，拘于时气」，作者本人即持异议：
     「以予观之，春木夏火，秋金冬水，**气有浅深**。如十月立冬，水已司令，
     虽未及冬至，以为化工，岂不可乎？如正月生人，坎为得局化工也。而卦内无坎，
     却有震，岂必拘于坎而不以震木为化工乎？」
     ——即：化工无硬边界，随卦中实有之气而定。原典未给精确判定法，
     本映射只作**取象近似**，不作原典硬规则。

  2. 化工相反 = **四季对宫**，四组（L585–594 逐条）：
     坎↔离（主夏至后—秋分前）、震↔兑（主秋分后—冬至前）
     ⚠ 2026-10-07 首轮曾把此处误订正为「先天方位对宫」——原典逐条写的
     就是四季对宫，是**原表的震↔巽/兑↔艮错了**，不是注释错。首轮把对的
     注释改错去迁就错的表，本轮一并改回。

  3. 状态枚举：NORMAL / RESCUED / REVERSE / KEZHI / UNRESOLVED

  ⚠ **RESCUED 在本轴上不可达**（2026-10-07 实测，属可验事实）：
     按 L585–594 的四组，坎(水)↔离(火) 为水克火、震(木)↔兑(金) 为金克木，
     **四组两两互为克制，无一组相生**。故「正体 vs 化工相反卦」这一轴上
     只有 NORMAL / KEZHI / REVERSE / UNRESOLVED。
     L582「却又有相生者，则吉」说的是**大象（先天）与小象（流年）两个化工
     之间**相反时的关系（如本命冬得坎、流年秋得兑，兑金生坎水则为相生）。
     本模块只吃本命四卦与月支，**未接流年**，该轴未实现——
     RESCUED 分支保留为正确逻辑，但当前不可达，如实登记，不硬凑。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class HuaGongState(str, Enum):
    """化工状态。"""
    NORMAL = "NORMAL"       # 得位：卦中有当令化工卦，无反卦
    REVERSE = "REVERSE"     # 反位：只有反卦，无当令化工卦
    RESCUED = "RESCUED"     # 救应：虽有反卦，但化工卦与反卦**五行相生**（L582「则吉」）
    KEZHI = "KEZHI"         # 克制：虽有化工卦，但与反卦**五行相克**（L582「忌克制，尤凶」）
    UNRESOLVED = "UNRESOLVED"  # 无据：无法判定（含原典未载的「比和」一档）


#: 八卦五行
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金",
    "震": "木", "巽": "木",
    "坎": "水",
    "离": "火",
    "坤": "土", "艮": "土",
}

#: 五行相生：a 生 b
_WU_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
#: 五行相克：a 克 b
_WU_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _wu_relation(elem_a: str, elem_b: str) -> str:
    """两五行关系：'相生' / '克制' / '比和' / ''（未知）。

    判定口径取原典 L582「却又有相生者，则吉。但忌克制，尤凶」——
    双向皆算：a 生 b 或 b 生 a 都算相生（生我/我生皆为顺）。
    """
    if not elem_a or not elem_b:
        return ""
    if _WU_SHENG.get(elem_a) == elem_b or _WU_SHENG.get(elem_b) == elem_a:
        return "相生"
    if _WU_KE.get(elem_a) == elem_b or _WU_KE.get(elem_b) == elem_a:
        return "克制"
    if elem_a == elem_b:
        return "比和"
    return ""


# 四季 → 地支月 → 化工卦（**简化近似**，原典自己就反对此硬边界，见模块 docstring）
# 原典 L576 逐字：「前辈之论，拘于时气，如冬至后春分前，坎水用事，为化工之例，
# 其说是矣。以予观之，春木夏火，秋金冬水，**气有浅深**。如十月立冬，水已司令，
# 虽未及冬至，以为化工，岂不可乎？如正月生人，坎为得局化工也。而卦内无坎，
# 却有震，岂必拘于坎而不以震木为化工乎？若不以震为化工，则曰无化工矣。」
# ——故此处只作取象近似，不得当作原典硬规则引用。
SEASON_BRANCH_TO_HUAGONG: dict[str, str] = {
    "亥": "坎", "子": "坎", "丑": "坎",   # 冬
    "寅": "震", "卯": "震", "辰": "震",   # 春
    "巳": "离", "午": "离", "未": "离",   # 夏
    "申": "兑", "酉": "兑", "戌": "兑",   # 秋
}

# 化工相反（四季对宫）—— 原典 L585–594「化工相反图见前」逐条：
#   L585「坎卦反离，主夏至以后秋分前。」
#   L588「离卦反坎，主冬至以后春分前。」
#   L591「兑卦反震，主春分以后夏至前。」
#   L594「震卦反兑，主秋分以后冬至前。」
# ⚠ 这四组是**四季对宫**，不是先天方位对宫（乾↔坤、兑↔艮、离↔坎、震↔巽）。
#   2026-10-07 首轮误把注释订正为「先天对宫」、表却未动——等于把对的注改错
#   去迁就错的表。本轮表与注一并改回原典口径。
# ⚠ 乾/坤/艮/巽在化工相反图中**不出现**，故此表不收；
#   先天对宫另见 QIANXI_DUKONG（与本规则无关，不得混用）。
OPPOSITE_TRIGRAM: dict[str, str] = {
    "坎": "离",   # L585
    "离": "坎",   # L588
    "兑": "震",   # L591
    "震": "兑",   # L594
}

#: 先天方位对宫（六爻全变）。**与化工相反无关**，仅供先天方位判断。
#: 化工相反请用 OPPOSITE_TRIGRAM（L585–594）。
QIANXI_DUKONG: dict[str, str] = {
    "乾": "坤", "坤": "乾",
    "兑": "艮", "艮": "兑",
    "离": "坎", "坎": "离",
    "震": "巽", "巽": "震",
}


@dataclass(frozen=True)
class HuaGongResult:
    """化工计算结果。"""
    state: HuaGongState
    huagong_trigram: str          # 当令化工卦
    birth_month_branch: str       # 出生月支
    has_huagong: bool             # 先天/后天卦中是否有化工卦
    has_opposite: bool            # 先天/后天卦中是否有反卦
    wu_relation: str = ""         # 化工卦与反卦的五行关系：相生/克制/比和/空
    evidence: list[str] = field(default_factory=list)  # 可审计证据链


def compute_huagong(
    prenatal_upper: str,
    prenatal_lower: str,
    postnatal_upper: str,
    postnatal_lower: str,
    birth_month_branch: str,
) -> HuaGongResult:
    """
    计算化工状态。

    算法：
    1. 确定当令化工卦（出生月支 → 四季 → 卦）
    2. 检查先天卦上下卦是否有机气
    3. 检查后天卦上下卦是否有机气
    4. 检查是否有正反对（反卦）
    5. 判定状态

    原典原则：
      "根基不得化工者，灾重也"
      "有化工之气者，艰难获福"
      "大象与小象化工虽相反，却又有相生者，则吉"
    """
    evidence: list[str] = []

    # Step 1: 确定当令化工卦
    huagong_trigram = SEASON_BRANCH_TO_HUAGONG.get(birth_month_branch, "?")
    opposite_trigram = OPPOSITE_TRIGRAM.get(huagong_trigram, "")

    # Step 2: 检查卦中是否有化工卦 / 反卦
    all_trigrams = {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower}
    has_huagong = huagong_trigram in all_trigrams
    has_opposite = opposite_trigram in all_trigrams

    evidence.append(f"出生月支{birth_month_branch} → 当令化工卦={huagong_trigram}")
    evidence.append(f"卦中含化工卦: {has_huagong}（{all_trigrams}）")
    if has_opposite:
        evidence.append(f"卦中含反卦{opposite_trigram}（{huagong_trigram}↔{opposite_trigram}）")

    # Step 3: 判定状态
    # 原典 L597："凡人根基不得化工者，灾重也" / "有化工之气者，艰难获福"
    # 原典 L582："又有大象与小象化工虽相反，却又有相生者，则吉。但忌克制，尤凶。"
    #   —— 2026-10-07 修：旧实现命中「有化工卦+有反卦」就无条件判 RESCUED，
    #   evidence 只写「需五行相生救应」却从不计算；而下游把 RESCUED 当吉。
    #   坎(水)克离(火) 原典明说「尤凶」，却被判吉——此为有害误判，现按 L582 实算。
    if has_huagong and not has_opposite:
        state = HuaGongState.NORMAL
        evidence.append("得位：卦中含当令化工卦，无正反对")
    elif has_huagong and has_opposite:
        e_hg = TRIGRAM_ELEMENT.get(huagong_trigram, "")
        e_op = TRIGRAM_ELEMENT.get(opposite_trigram, "")
        rel = _wu_relation(e_hg, e_op)
        if rel == "相生":
            state = HuaGongState.RESCUED
            evidence.append(
                f"救应：化工卦{huagong_trigram}({e_hg})与反卦{opposite_trigram}({e_op})"
                f"**五行相生**（L582「有相生者则吉」）")
        elif rel == "克制":
            state = HuaGongState.KEZHI
            evidence.append(
                f"克制：化工卦{huagong_trigram}({e_hg})与反卦{opposite_trigram}({e_op})"
                f"**五行相克**（L582「但忌克制，尤凶」）——"
                f"非救应，原典此处为最凶一档，不得作吉断")
        else:
            # 比和（如震↔巽皆木）原典未载此档，不作硬断
            state = HuaGongState.UNRESOLVED
            evidence.append(
                f"比和：化工卦{huagong_trigram}({e_hg})与反卦{opposite_trigram}({e_op})"
                f"五行比和——原典只言「相生则吉、克制尤凶」，未载比和一档，"
                f"不作硬断")
    elif has_opposite and not has_huagong:
        state = HuaGongState.REVERSE
        evidence.append(f"反位：卦中含反卦{opposite_trigram}，无当令化工卦")
    else:
        state = HuaGongState.UNRESOLVED
        evidence.append("无据：卦中既无化工卦也无反卦")

    return HuaGongResult(
        state=state,
        huagong_trigram=huagong_trigram,
        birth_month_branch=birth_month_branch,
        has_huagong=has_huagong,
        has_opposite=has_opposite,
        wu_relation=_wu_relation(
            TRIGRAM_ELEMENT.get(huagong_trigram, ""),
            TRIGRAM_ELEMENT.get(opposite_trigram, "")),
        evidence=evidence,
    )
