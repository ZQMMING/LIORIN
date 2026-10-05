# -*- coding: utf-8 -*-
"""L3 severity 序数层 severity.py —— 病机程度 0-4 序数

方法论: 禁浮点/乘除加权; 分层判定(规则优先级), 命中即返回, 不叠加。

severity 不是「打分」, 是「结构序数派生」—— 由病五行在命局中的客观离散事实
(当令/成党/透干/本根) 按优先级逐层定档:

    S4  病五行当令(旺/相) 且 combo>=6          「当令成党, 病势极重」
    S3  病五行当令 或 combo>=6                 「当令或成党」
    S2  病五行 combo>=4 或 透干>=2 或 本根>=2  「成势」
    S1  病五行有透干 或 有本根                 「有气」
    S0  无以上任何结构                         「无病势」

每档挂切片依据(原文程度词):
    S4  PZZQ「杀重身轻」/ DTS「土重金埋」 —— 重/多为当令成党之病
    S3  PZZQ「财多身弱」/ SFTK「财多身弱, 俱喜木为医药」
    S2  PZZQ「比肩成党」/ YHZP「枭神夺食」
    S1  SFTK「八字中原有所害之神」
    S0  —
口径声明: 档位阈值(当令/combo>=6/>=4/透干>=2)为工程整数档, 非原典明文;
         程度词映射见各档依据, 后续切片刻词校准可替换。
"""
from typing import Any, Dict, List

# 月令序数(与 wuxing_power ling_state 同构: 旺/相/休/囚/死)
_LING_STRONG = ("旺", "相")

# 切片依据(程度词映射, 逐档可追溯)
_BASIS = {
    4: ["PZZQ「杀重身轻」杀当令成党; DTS「土重金埋」土重为病", "病五行当令(旺/相)且combo>=6"],
    3: ["PZZQ「财多身弱」财多/杀重为病; SFTK-008-001「杀重身轻/财多身弱」", "病五行当令(旺/相)或combo>=6"],
    2: ["PZZQ「比肩成党」/ YHZP「枭神夺食」成党为病", "病五行combo>=4 或透干>=2 或本根>=2"],
    1: ["SFTK-008-001「八字中原有所害之神」有气即病", "病五行有透干或本根"],
    0: ["无病势", "无透干/无本根/无成党/不克身"],
}


def derive_severity(bing_wx: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """由病五行 + 全 facts 派生 0-4 序数。

    返回:
      {"level": 0-4, "basis": [依据...], "facts": {"dang_ling":bool,"combo":int,"stem_n":int,"ben_n":int}}
    病五行缺失 -> level=0 + basis 标注缺失(不臆断)。
    """
    wp = ((facts.get("wuxing_power") or {}).get("wuxing_power") or {})
    p = wp.get(bing_wx) or {}
    ling = p.get("ling_state") or ""
    combo = p.get("combo") or 0
    stem_n = p.get("stem_n") or 0
    ben_n = p.get("ben_n") or 0

    dang_ling = ling in _LING_STRONG
    d = {"dang_ling": dang_ling, "combo": combo, "stem_n": stem_n, "ben_n": ben_n}

    if dang_ling and combo >= 6:
        level = 4
    elif dang_ling or combo >= 6:
        level = 3
    elif combo >= 4 or stem_n >= 2 or ben_n >= 2:
        level = 2
    elif stem_n >= 1 or ben_n >= 1:
        level = 1
    else:
        level = 0

    return {
        "level": level,
        "basis": _BASIS[level],
        "facts": d,
    }


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    # 冒烟: 土当令combo6 -> 4; 土combo3透1 -> 1; 无 -> 0
    for wx, p in [
        ("土", {"ling_state": "旺", "combo": 6, "stem_n": 1, "ben_n": 2}),
        ("水", {"ling_state": "死", "combo": 3, "stem_n": 1, "ben_n": 0}),
        ("金", {"ling_state": "休", "combo": 1, "stem_n": 0, "ben_n": 0}),
    ]:
        r = derive_severity(wx, {"wuxing_power": {"wuxing_power": {wx: p}}})
        print("  %s -> level=%d facts=%s" % (wx, r["level"], r["facts"]))
