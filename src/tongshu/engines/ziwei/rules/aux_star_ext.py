"""Z79: 辅煞杂曜补遗——《紫微斗数全书》诸星问答论+安星诀。

Z77b已录16条命宫断语。本文件补：
- 天伤天使（限运断语）
- 天哭天虚（命宫+限运）
- 红鸾天喜（断语）

原典无"辅煞杂曜×12宫"逐宫断语——记录NOT_ESTABLISHED。

Z80-G 审核标注（2026-10-14）：本模块在 src/ 内**零引用**（仅测试/文档提及）。
  处置建议：证据资产 —— 天伤天使/哭虚/鸾喜补遗，QTN-047~055 部分覆盖
  依据：docs/audit/ZIWEI_ENGINE_FULL_AUDIT_20261014.md
"""
from __future__ import annotations

SRC = "紫微斗数全书·诸星问答论"

# 天伤天使
TIANSHANG_TIANSHI = [
    {"star": "天伤", "palace": "限运", "verbatim": "天伤乃上天虚耗之神。太岁二限逢之不问得地否？只要吉多为福其祸稍轻，如无吉，值巨门、羊陀、火铃、忌、天机，其年必主官灾，丧亡破败。", "source": SRC, "status": "VERIFIED"},
    {"star": "天使", "palace": "限运", "verbatim": "天使乃上天传使之神。太岁二限逢之不问得地否？只要吉多为福其祸稍轻，如无吉，值巨门、羊陀、火铃、忌、天机，其年必主官灾，丧亡破败。", "source": SRC, "status": "VERIFIED"},
]

# 天哭天虚
TIANKU_TIANXU = [
    {"star": "天哭", "palace": "命宫", "verbatim": "哭虚为恶曜，临命最非常。加临父母内，破荡卖田庄。若教身命陷，穷独带刑伤。丑卯申宫吉，遇禄名显扬。二限若逢之，哀哀哭断肠。", "source": SRC, "status": "VERIFIED"},
    {"star": "天虚", "palace": "命宫", "verbatim": "哭虚为恶曜，临命最非常。加临父母内，破荡卖田庄。若教身命陷，穷独带刑伤。丑卯申宫吉，遇禄名显扬。二限若逢之，哀哀哭断肠。", "source": SRC, "status": "VERIFIED"},
]

# 红鸾天喜
HONGLUAN_TIANXI = [
    {"star": "红鸾", "palace": "命宫/限运", "verbatim": "年少婚姻喜事奇，老人必主丧其妻，三十年前为吉曜，五十年后不相宜。", "source": "紫微斗数全书·安红鸾天喜诀第四十一", "status": "VERIFIED"},
    {"star": "天喜", "palace": "命宫/限运", "verbatim": "对宫天喜不差移。年少婚姻喜事奇，老人必主丧其妻，三十年前为吉曜，五十年后不相宜。", "source": "紫微斗数全书·安红鸾天喜诀第四十一", "status": "VERIFIED"},
]

# NOT_ESTABLISHED：原典无逐宫12宫断语
NOT_ESTABLISHED_12PALACE = {
    "note": "原典诸星问答论中，辅曜/煞曜/杂曜主要为命宫/身宫/限运断语，无逐宫12宫断语体系。",
    "stars_checked": ["左辅","右弼","文昌","文曲","天魁","天钺","禄存","天马","擎羊","陀罗","火星","铃星","地空","地劫","天刑","天姚"],
    "status": "NOT_ESTABLISHED",
}

ALL_AUX_EXT = TIANSHANG_TIANSHI + TIANKU_TIANXU + HONGLUAN_TIANXI


def count_verified() -> int:
    return sum(1 for x in ALL_AUX_EXT if x["status"] == "VERIFIED")
