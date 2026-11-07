# -*- coding: utf-8 -*-
"""一格两面合并裁决层

A+B俱足→化气型(争合降MID) / A独足→专旺型 / B独足→CANDIDATE / 皆空→REJECT
"""
from typing import Tuple, Optional
from engines.axis_xiuqi import XiuqiResult
from engines.axis_fude import FudeResult

def merge(x: XiuqiResult, f: FudeResult, key: str) -> Tuple[Optional[str], str, str, int]:
    """
    返回 (pattern_claimed, pattern_type, confidence, score)
    """
    a_ok = f.a1_day and f.a2_ju and f.a3_po
    b_ok = (x.b1a or x.b1b) and x.b2

    if a_ok and b_ok:
        # F5：化无所化（仅乙庚化金）——日主五行=化神五行时，优先专旺型
        # 理由：化气之义在弃其本性而从他神，日主即化神时化无所化，仍属一行成象
        from engines.axis_xiuqi import HUA_SHEN, HE, WUXING
        g = HE.get(x.day_stem, "")
        pair = "".join(sorted([x.day_stem, g]))
        hx = HUA_SHEN.get(pair, "")
        day_wx = WUXING.get(x.day_stem, "")
        if day_wx == hx and hx == "金":
            # 乙庚化金，日主即金，化无所化→优先专旺型
            if f.score >= 3 and not f.cai_po:
                conf = "CONFIRMED"
            else:
                conf = "MID"
            return (f.pattern_root, "专旺型", conf, f.score)
        ge = f.pattern_root.split("·")[1] if f.pattern_root else x.pattern_root.split("·")[1]
        conf = "MID" if x.b1b else "CONFIRMED"
        total = x.score + f.score + (1 if x.b3 else 0)
        return (f"一行成象·{ge}", "化气型", conf, total)

    if a_ok:
        if f.score >= 3 and not f.cai_po:
            conf = "CONFIRMED"
        else:
            conf = "MID"
        return (f.pattern_root, "专旺型", conf, f.score)

    if b_ok:
        # G8硬闸：财透两位/根深 → 转格REJECT
        if not x.b7:
            return (None, None, "REJECT", 0)  # TODO: rebase to 正格族 once available
        # B独足 → 化气型
        # 档位规则（选项A：b3为升档键，b5为硬权重）：
        #  b5=True + 无其他减项 → CONFIRMED
        #  b5=False + b3=True（逢龙代局）→ MID
        #  b5=False + b3=False → REJECT
        if x.b1b or x.b8 or not x.b6:
            # 有减项，最高MID
            conf = "MID"
        else:
            if x.b5:
                conf = "CONFIRMED"
            elif x.b3:
                conf = "MID"  # 逢龙代局，次等之贵
            else:
                return (None, None, "REJECT", 0)  # 局不全+不见龙，不化
        return (x.pattern_root, "化气型", conf, x.score)

    return (None, None, "REJECT", 0)
