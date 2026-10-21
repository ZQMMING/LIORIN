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

  3. 状态枚举：NORMAL / RESCUED / REVERSE / KEZHI / WEAK / UNRESOLVED

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
    WEAK = "WEAK"           # 浅薄：只得纳音级化工，L576「终是浅薄，福寿减半」
    UNRESOLVED = "UNRESOLVED"  # 无据：无法判定（含原典未载的「比和」一档）


#: ⚠ 2026-10-08 批次 G：五行生克此前在本模块与 hexagram_state 各存一份，
#:   内容相同。五行生克是全库最基本的五行关系，容不得两份各改各的——
#:   统一引用 hexagram_state，本模块不再自存。
from .hexagram_state import (ELEMENT_GENERATES as _WU_SHENG,  # noqa: E402
                             ELEMENT_OVERCOMES as _WU_KE)


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
#: 本轮拒算登记（新增于 2026-10-08）。
#: 坤艮十八日**判据不全**，不落码、不猜。
HUAGONG_REFUSED: tuple[tuple[str, str, str], ...] = (
    ("L570「坤艮卦主四季辰戌丑未月，除正节气十二日外，各旺十八日。」",
     "前半句（辰戌丑未月主坤艮）可落码且不冲突，但**「正节气十二日」是哪十二日，"
     "本卷未给**——只说「除……外」而未说从哪天起算、到哪天止。月长约三十日，"
     "十二日 + 十八日 = 三十，可见十二日与十八日互补，但互补只锁定了总量，"
     "没锁定在月内的位置。取错了就是整月偏移十八日，无从校验。",
     "须定案「正节气十二日」的起讫（是节气前六后六？是交节后十二日？还是别的）。"
     "定案前坤艮一律不落码，已落码的四正卦窗口不受影响。"),
)

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
HUAGONG_FAN_GUA: dict[str, str] = {
    "坎": "离",   # L585
    "离": "坎",   # L588
    "兑": "震",   # L591
    "震": "兑",   # L594
}

#: 三画卦 → 六爻（自下而上）。1=阳 0=阴。
#: 与 guajie.trigram_to_lines 同源，加守卫逐一对拍防漂移。
TRIGRAM_LINES: dict[str, tuple[int, int, int]] = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}

#: 三画卦 → 五行
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金",
    "震": "木", "巽": "木",
    "坎": "水",
    "离": "火",
    "坤": "土", "艮": "土",
}

#: 错卦（先天方位对宫，六爻全变）—— **单一来源 hexagram_state.QIANXI_DUKONG**。
#: ⚠ 与化工相反**不是一回事**，化工相反见 HUAGONG_FAN_GUA（L585–594）。
#:
#: 批次 G 之前的乱局：本表与「化工相反」表**都叫 HUAGONG_FAN_GUA**，
#: 而两者含义不同（本表八项先天对宫；化工相反四项四季对宫）。
#: 谁 `from … import HUAGONG_FAN_GUA` 拿错了就是**静默判错**——
#: 对乾/坤/艮/巽 取 .get() 直接返回 None。故一并消歧义，且错卦只留一份数据。
from .hexagram_state import QIANXI_DUKONG  # noqa: E402



# ═══════════════════════════════════════════════════════════════════
# 四正卦化工窗口（原典 L558–L567，2026-10-08 落码）
# ═══════════════════════════════════════════════════════════════════
#
#   L558「坎卦自冬至十一月中以后至惊蛰终止。」
#   L561「震卦自春分二月中以后至芒种终止。」
#   L564「离卦自夏至五月中以后至白露终止。」
#   L567「兑卦自秋分八月中以后至大雪终止。」
#
# 四条起止**全是节气**，合起来正好把 jq 0–23 切成四等段：
#
#     坎 [冬至0, 惊蛰5]   震 [春分6, 芒种11]
#     离 [夏至12, 白露17] 兑 [秋分18, 大雪23]
#
# ══ 自校验：与 L585–L594「化工相反」表互证 ══
#   L585「坎卦反离，主**夏至以后秋分前**。」→ jq[12,18) = 离窗口
#   L588「离卦反坎，主**冬至以后春分前**。」→ jq[0,6)   = 坎窗口
#   L591「兑卦反震，主**春分以后夏至前**。」→ jq[6,12)  = 震窗口
#   L594「震卦反兑，主**秋分以后冬至前**。」→ jq[18,24) = 兑窗口
#
#   四条「反」窗口 = 四条「正」窗口各自**放宽到下一个节**，
#   一一对上、无一错位。这组互证是本表最硬的证据：不是我说它对，
#   是原典另一张独立的表在同一轴上说了同一件事。
#
# ⚠ 为什么不能压成月支表（2026-10-08 实测）：
#   窗口边界与月支边界不重合。卯月=[惊蛰,清明)，而震自**春分**起，
#   故卯月上半月属坎、下半月属震；午月、酉月同理被拦腰截断。
#   压成月支 → 这三个月各自劈成两半，再凭空多出三段「无窗口」。
#   那是映射丢精度造出来的洞，原典没有。
#: 节气名**不自造**：直接引 jiehhou.SOLAR_TERMS（全库单一来源，按 sxtwl
#: jqIndex 0–23 排，与 jiegua.JIE_GUA_TABLE 同序）。
#: 本轮初版在这里另抄了一份 24 字元组，属典型的「两份表各抄各的、
#: 索引错位无人发现」——同 jiehhou 自己在 SOLAR_TERMS 处记的旧账。
from .jiehhou import SOLAR_TERMS as _JQ_ORDER  # noqa: E402

#: (化工卦, 起始 jq, 终止 jq)，闭区间。原典出场次序。
HUAGONG_JIEQI_WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("坎", 0, 5), ("震", 6, 11), ("离", 12, 17), ("兑", 18, 23),
)

#: 化工相反窗口（L585–L594），(本卦, 相反卦, 起 jq, 止 jq 半开)。
#: 保留供守卫与 L558–L567 表互证，不另起判定口径。
HUAGONG_FAN_JIEQI: tuple[tuple[str, str, int, int], ...] = (
    ("坎", "离", 12, 18), ("离", "坎", 0, 6),
    ("兑", "震", 6, 12), ("震", "兑", 18, 24),
)


def huagong_by_jieqi(jq: int | None) -> str:
    """节气索引 → 当令化工卦。越界/未知一律返回空串，**不猜**。"""
    if jq is None or not (0 <= jq < len(_JQ_ORDER)):
        return ""
    for gua, lo, hi in HUAGONG_JIEQI_WINDOWS:
        if lo <= jq <= hi:
            return gua
    return ""


def huagong_by_jieqi_index(jq: int | None) -> tuple[str, str]:
    """节气索引 → ``(当令化工卦, 取法说明)``。**上游已有 jq 时走这里，零次计算**。

    canonical 的节候卦层（H11）本来就要算同一个 jq；化工再自己调一次 sxtwl
    属重复计算。故本函数与 :func:`huagong_by_birth_date` 分开：
    有 jq 直接用，没有才由出生日换算。
    """
    if jq is None or not (0 <= jq < len(_JQ_ORDER)):
        return "", "节气索引不可用（%r），不在 0–23 内" % (jq,)
    gua = huagong_by_jieqi(jq)
    if not gua:                                   # jq 0–23 已被四段完整切分，理论上不可达
        return "", "节气「%s」未落入 L558–L567 任何一个窗口（按原典即无化工卦）" % _JQ_ORDER[jq]
    return gua, "处「%s」→ 当令化工卦=%s" % (_JQ_ORDER[jq], gua)


def huagong_by_birth_date(date_str: str) -> tuple[str, str]:
    """出生日 → ``(当令化工卦, 取法说明)``。卦取不到时返回 ``("", 说明)``。

    节气换算**委托 jiehhou.get_current_jieqi_info** —— 全库已有两处节气实现
    （本函数原先用的 yue_ling_shu_ge.solar_jq_index、以及 jiehhou 那份带
    时间线缓存的），本模块不再当第三处。二者逐日对 sxtwl 原始表比对目前
    零误差，但两份实现并存必然漂移，故统一吃 jiehhou。

    取不到的情形都如实说明、不静默回落：没给日期 / 日期不合法 / 缺 sxtwl /
    真实计算异常。调用方据此回落近似表并把说明写进 evidence。
    """
    if not date_str:
        return "", "未给出生日，无法定节气窗口"
    try:
        from datetime import datetime as _dt
        bd = _dt.fromisoformat(date_str)
    except ValueError:
        return "", "出生日「%s」不是合法 ISO 日期，节气无法换算" % date_str
    except Exception as exc:                      # pragma: no cover
        return "", "出生日解析失败（%s: %s）" % (type(exc).__name__, exc)
    try:
        from .jiehhou import get_current_jieqi_info
    except Exception as exc:                      # pragma: no cover
        return "", "无法导入节气计算（%s）" % type(exc).__name__
    try:
        info = get_current_jieqi_info(bd.year, bd.month, bd.day)
    except Exception as exc:
        # jiehhou 有意让真实计算异常上抛（不吞成 None），此处如实转述，不降级。
        return "", "节气计算出错（%s: %s）" % (type(exc).__name__, exc)
    if info is None:
        return "", "无法由出生日「%s」定出所处节气（缺 sxtwl 或该日无可取节气）" % date_str
    gua, note = huagong_by_jieqi_index(info.jq_index)
    if not gua:
        return "", note
    return gua, "按原典 L558–L567 节气窗口：生日 %s %s" % (date_str, note)


def _huagong_self_check() -> None:
    """导入即验：三件事必须同时成立，否则宁可导入失败也不要带着错表跑。"""
    # ① 四窗口必须把 jq 0–23 **完整**切分：无缝、不重叠、不少不重。
    covered: list[int] = []
    for _gua, lo, hi in HUAGONG_JIEQI_WINDOWS:
        covered.extend(range(lo, hi + 1))
    assert sorted(covered) == list(range(len(_JQ_ORDER))), \
        "L558–L567 四窗口未把 jq 0–23 切满：%d/%d" % (len(set(covered)), len(_JQ_ORDER))
    # ② 与 L585–L594「化工相反」表互证：每条「反」窗口须正好覆盖一个正窗口。
    for gua, fan, lo, hi in HUAGONG_FAN_JIEQI:
        inside = {g for g, a, b in HUAGONG_JIEQI_WINDOWS
                  if a >= lo and b < hi}
        assert inside == {fan}, (
            "L585–L594「%s反%s，主%s以后%s前」jq[%d,%d) 实际覆盖 %s，与本表对不上"
            % (gua, fan, _JQ_ORDER[lo], _JQ_ORDER[hi % len(_JQ_ORDER)],
               lo, hi, inside or "空"))
        assert HUAGONG_FAN_GUA.get(gua) == fan, \
            "HUAGONG_FAN_GUA 与 L585–L594 不一致：%s" % gua
    # ③ 每卦恰有一个窗口。
    names = [g for g, _lo, _hi in HUAGONG_JIEQI_WINDOWS]
    assert len(set(names)) == len(names), "有卦占了两个窗口"
    assert set(names) == set(HUAGONG_FAN_GUA), "窗口表与相反表覆盖的卦不一致"



#: ══ 接线记录：生产链已切到 L558–L567 节气窗口（2026-10-08 经用户批准）═══
#:
#: :func:`huagong_by_birth_date` 已实现、已导入自校验、已有守卫；
#: :func:`compute_huagong` 支持 ``jieqi_index`` 入参，
#: ``canonical._compute_huagong`` 已把它接上 —— 节候卦层（H11）算一次 jq，
#: 下传给化工复用，**同一份 sxtwl 结果不再算两遍**。
#:
#: 下方差异表是**当初为什么必须接线**的依据，不是遗留问题；
#: 保留在此是为了让后来人知道那张近似表与原典差在哪儿、别再拿它当依据。
#:
#:   月支   近似表   L558–L567 窗口        差异
#:   寅     震       坎                    **整月不符**
#:   卯     震       坎（上半月）/震（下半月） **跨窗口**
#:   辰     震       震                    一致
#:   巳     离       震                    **整月不符**
#:   午     离       震（上半月）/离（下半月） **跨窗口**
#:   未     离       离                    一致
#:   申     兑       离                    **整月不符**
#:   酉     兑       离（上半月）/兑（下半月） **跨窗口**
#:   戌     兑       兑                    一致
#:   亥     坎       兑                    **整月不符**
#:
#: 跨窗口的卯/午/酉 说明**月支粒度不够**（月支月跨两个节气），
#: 这是原典窗口的固有粒度，不是实现取巧。
#:
#: **翻过的两个 Golden（经用户显式批准，非静默改绿）**
#:
#:   1. tests/heluo/test_h2_frozen_state.py::TestFrozenStateGoldenCase::test_huagong
#:      纪晓岚 1724-05-22 处小满（jq=10）：旧期望「离(火)→WEAK」出自自造近似表，
#:      按 L561「震卦自春分二月中以后至芒种终止」应为「震(木)→KEZHI」
#:   2. tests/heluo/test_audit_batch_20261007.py::
#:      TestHuaGongLevelPervasive::test_weak_case_level_and_reduced_reach_frozen_state
#:      同一生日：WEAK/纳音/reduced=True → KEZHI/正体/reduced=False。
#:      旧用例顺带守的「reduced 必须透传」已拆出 test_reduced_false_is_propagated。
#:
#: ⚠ :data:`SEASON_BRANCH_TO_HUAGONG` 近似表**仍在**（无出生日且无 jieqi_index
#:   时的兜底），但生产链已不再走它。不得以它为依据，也不得把它「优化」回去。
HUAGONG_BRANCH_SWITCH: dict = {
    "状态": "已接线（2026-10-08，经用户显式批准）",
    "接线方式": "canonical 节候卦层算 jq 一次，下传 jieqi_index 给化工复用，零重复计算",
    "自造近似表的现状": "仅作无出生日/无 jq 时的兜底；生产链不走，不得为依据",
    "已翻转的 Golden": [
        "tests/heluo/test_h2_frozen_state.py::TestFrozenStateGoldenCase::test_huagong",
        "tests/heluo/test_audit_batch_20261007.py::"
        "TestHuaGongLevelPervasive::test_weak_case_level_and_reduced_reach_frozen_state",
    ],
    "不得回退": "把 jieqi_index 停传、或改回只用月支近似表",
}

_huagong_self_check()


def _lines_to_trigram(chunk: tuple[int, ...] | list[int]) -> str:
    rev = {(1, 1, 1): "乾", (1, 1, 0): "兑", (1, 0, 1): "离", (1, 0, 0): "震",
           (0, 1, 1): "巽", (0, 1, 0): "坎", (0, 0, 1): "艮", (0, 0, 0): "坤"}
    return rev.get(tuple(chunk), "")


def compute_mutual_trigram(upper: str, lower: str) -> tuple[str, str]:
    """由卦的上下三画卦求互体，返回 ``(上互, 下互)``。

    取法与 guajie.compute_huti 完全一致：下互＝二三四爻（lines[1:4]），
    上互＝三四五爻（lines[2:5]）。原典 L104 例（渐卦）：
    「九五六四九三互离，六四九三六二互坎，合之为未济」✓

    ⚠ 本函数与 guajie.compute_huti 是**两份等价实现**（hua_gong 不 import guajie
    以免循环依赖），由 tests/heluo/test_h6_hua_gong.py 逐卦对拍防漂移。
    """
    lo = TRIGRAM_LINES.get(lower, ())
    up = TRIGRAM_LINES.get(upper, ())
    if not lo or not up:
        return "", ""
    lines = list(lo) + list(up)          # 六爻，自下而上
    return (_lines_to_trigram(lines[2:5]),
            _lines_to_trigram(lines[1:4]))


#: 纳音层可成立的五行——化工只取四正（水木火金），土不硬套
HUAGONG_ELEMENTS = frozenset({"水", "木", "火", "金"})


@dataclass(frozen=True)
class HuaGongResult:
    """化工计算结果。"""
    state: HuaGongState
    huagong_trigram: str          # 当令化工卦
    birth_month_branch: str       # 出生月支
    has_huagong: bool             # 先天/后天卦中是否有化工卦
    has_opposite: bool            # 先天/后天卦中是否有反卦
    wu_relation: str = ""         # 化工卦与反卦的五行关系：相生/克制/比和/空
    level: str = "正体"           # 得化工之层：正体 / 互体 / 纳音 / 无（L576 三级）
    reduced: bool = False         # 末级减半（L576「终是浅薄，福寿减半」）
    evidence: list[str] = field(default_factory=list)  # 可审计证据链


def compute_huagong(
    prenatal_upper: str,
    prenatal_lower: str,
    postnatal_upper: str,
    postnatal_lower: str,
    birth_month_branch: str,
    year_gan: str = "",
    year_zhi: str = "",
    birth_date: str = "",
    jieqi_index: int | None = None,
) -> HuaGongResult:
    """
    计算化工状态。

    算法（L576 三级回退）：
      1. 确定当令化工卦（优先级自上而下）：
         jieqi_index 入参 → **复用上游已算的节气**，零次计算（生产走这条）
         无 jieqi_index 但有出生日 → 委托 jiehhou 换算节气，再查原典窗口
         两者皆无 → 回落月支近似表 :data:`SEASON_BRANCH_TO_HUAGONG`（兜底，非原典口径）
      2. **正体**：先天/后天卦的上下卦中是否有该化工卦
      3. **互体**：正体不得而互体得之
      4. **纳音**：正互俱无则取纳甲纳音，**终是浅薄，福寿减半**
      5. 判定状态（正常 / 化工相反 → 按 L582 分相生·克制）

    原典原则（L576 / L582 / L597）：
      「故正不逢而互体得之。若正互俱无，则取纳甲纳音，终是浅薄，福寿减半。」
      「又有大象与小象化工虽相反，却又有相生者，则吉。但忌克制，尤凶。」
      「凡人根基不得化工者，灾重也。……有化工之气者，艰难获福。」
    """
    evidence: list[str] = []

    # Step 1: 确定当令化工卦（两条取法，evidence 必须写明走了哪条）
    # ⚠ 2026-10-08：兜底披露曾挂在 `if not _jq_note` 下——可 _jq_note 恰恰是
    #   **取不到节气窗口时才有值**，于是走兜底反而不写「兜底」二字，
    #   披露逻辑整个反了（守卫 test_disclosed_in_evidence_when_falling_back 逮到）。
    #   现改为按**实际走了哪条**分支，与 _jq_note 有无无关。
    if jieqi_index is not None:
        # 上游（H11 节候卦）已算过同一个 jq，直接复用，**不再调第二次 sxtwl**。
        huagong_trigram, _jq_note = huagong_by_jieqi_index(jieqi_index)
        _jq_note = ("复用节候卦层已算的节气索引（jieqi_index=%d），未重复计算；"
                    "按原典 L558–L567 节气窗口：%s" % (jieqi_index, _jq_note))
    else:
        huagong_trigram, _jq_note = huagong_by_birth_date(birth_date)
    if huagong_trigram:
        _huagong_basis = "节气窗口（原典 L558–L567）——" + _jq_note
    else:
        huagong_trigram = SEASON_BRANCH_TO_HUAGONG.get(birth_month_branch, "?")
        _huagong_basis = ("月支近似表（**兜底**）——" + _jq_note
                          + "；该近似与 L558–L567 节气窗口在 寅/巳/申/亥 整月不符，"
                            "卯/午/酉 跨窗口，结论仅供参考")
    opposite_trigram = HUAGONG_FAN_GUA.get(huagong_trigram, "")

    # Step 2: L576 三级回退 —— 正体 → 互体 → 纳音
    zhengti = {prenatal_upper, prenatal_lower, postnatal_upper, postnatal_lower}
    pre_mut = compute_mutual_trigram(prenatal_upper, prenatal_lower)
    post_mut = compute_mutual_trigram(postnatal_upper, postnatal_lower)
    huti = set(pre_mut) | set(post_mut)
    huti.discard("")

    # L576 第三级「纳甲纳音」：须有年干支方能取到纳音。
    # ⚠ 2026-10-07 审计修：旧实现把「未传年干支」与「取纳音抛异常」一律静默置空，
    #   随后 evidence 照写「正体、互体、纳音三层俱不得化工」——把**根本没跑的检查**
    #   写成**已检查且未通过**。现改为逐层登记，本级未参与则如实说明。
    nayin_elem = ""
    nayin_checked = False
    nayin_note = "未启用（本级缺年干支输入，未参与判定）"
    if year_gan and year_zhi:
        try:
            from .guajie import get_nayin_element  # 延迟导入：避免循环依赖
            nayin_elem = get_nayin_element(year_gan, year_zhi)
            nayin_checked = True
            nayin_note = ("已查：「%s%s」纳音属%s"
                          % (year_gan, year_zhi, nayin_elem or "未知（不在六十甲子纳音表内）"))
        except Exception as exc:
            nayin_note = ("查询失败（%s: %s），本级不可判"
                          % (type(exc).__name__, exc))

    hg_elem = TRIGRAM_ELEMENT.get(huagong_trigram, "")
    level, reduced, pool = "无", False, zhengti
    if huagong_trigram in zhengti:
        level, pool = "正体", zhengti
        evidence.append(f"一级 正体得化工卦{huagong_trigram}（{sorted(zhengti)}）")
    elif huagong_trigram in huti:
        level, pool = "互体", huti
        evidence.append(f"二级 互体得化工卦{huagong_trigram}"
                        f"（先天互{pre_mut}／后天互{post_mut}）"
                        f"——L576「故正不逢而互体得之」")
    elif nayin_elem and nayin_elem == hg_elem and hg_elem in HUAGONG_ELEMENTS:
        # pool 记当令化工卦本身：纳音层**确实得了化工**（只是浅薄减半），
        # 若 pool 置空会让 has_huagong=False、state 落到「无据」，
        # 与 evidence「取纳甲纳音…与化工卦同气」自相矛盾。
        level, reduced, pool = "纳音", True, {huagong_trigram}
        evidence.append(f"三级 正互俱无，取纳甲纳音「{year_gan}{year_zhi}」"
                        f"得{nayin_elem}，与化工卦{huagong_trigram}同气"
                        f"——L576「终是浅薄，福寿减半」")
    else:
        if nayin_checked:
            evidence.append("正体、互体俱不得化工；三级纳音%s，与当令化工卦%s(%s)不同气"
                            "——L576「若不以震为化工，则曰无化工矣」"
                            % (nayin_note, huagong_trigram, hg_elem or "无"))
        else:
            evidence.append("正体、互体俱不得化工；三级纳音%s，"
                            "故本盘**只作二级否定**，不得称「三层俱不得」"
                            "——L576「若不以震为化工，则曰无化工矣」" % nayin_note)

    # 「卦中所有三画卦」= 正体 ∪ 互体。
    # 互体亦由本卦六爻化出（L576「故正不逢而互体得之」），其三画卦同属本卦之体；
    # 化工相反（L579/L585–594）判的是**卦与卦**的对应，故按全卦体求，不限于化工所在层。
    # 2026-10-07 审计指出旧版 evidence 会打印当层集合、下一行却宣称全集里的反卦，
    # 审计链自相矛盾；现改为——判定按全集，**打印也按全集并逐卦标层**。
    all_trigrams = zhengti | huti

    def _where(t: str) -> str:
        parts = []
        if t in zhengti:
            parts.append("正体")
        if t in huti:
            parts.append("互体")
        return "、".join(parts) or "未见"

    has_huagong = huagong_trigram in pool
    has_opposite = opposite_trigram in all_trigrams

    evidence.append(f"出生月支{birth_month_branch} → 当令化工卦={huagong_trigram}（{hg_elem}）")
    evidence.append(f"当令化工卦取法：{_huagong_basis}")
    evidence.append(f"化工所得之层: {level}"
                    + ("，**福寿减半**" if reduced else ""))
    evidence.append(f"卦中三画卦全集: {sorted(all_trigrams)}"
                    f"（正体{sorted(zhengti)}／互体{sorted(huti)}）；"
                    f"化工取自「{level}」层")
    evidence.append(f"卦中含化工卦: {has_huagong}（见于{_where(huagong_trigram)}）")
    if has_opposite:
        evidence.append(f"卦中含反卦{opposite_trigram}"
                        f"（{huagong_trigram}↔{opposite_trigram}，见于{_where(opposite_trigram)}）")

    # Step 3: 判定状态
    # 原典 L597："凡人根基不得化工者，灾重也" / "有化工之气者，艰难获福"
    # 原典 L582："又有大象与小象化工虽相反，却又有相生者，则吉。但忌克制，尤凶。"
    #   —— 2026-10-07 修：旧实现命中「有化工卦+有反卦」就无条件判 RESCUED，
    #   evidence 只写「需五行相生救应」却从不计算；而下游把 RESCUED 当吉。
    #   坎(水)克离(火) 原典明说「尤凶」，却被判吉——此为有害误判，现按 L582 实算。
    if reduced:
        # L576：「若正互俱无，则取纳甲纳音，终是浅薄，福寿减半。」
        # 减半的化工**不得**报 NORMAL（得位·有机气）——那是高报。
        # 既非吉（无正逢互得之实），亦非凶（到底还是得了化工）→ NEUTRAL。
        state = HuaGongState.WEAK
        evidence.append("浅薄：仅得纳音级化工，按 L576「终是浅薄，福寿减半」"
                        "——不作得位论")
    elif has_huagong and not has_opposite:
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
        level=level,
        reduced=reduced,
        evidence=evidence,
    )
