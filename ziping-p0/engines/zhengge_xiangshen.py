# -*- coding: utf-8 -*-
"""正格族L2相神配对+L3成败救应"""
import sys
sys.path.insert(0, '.')
from spec.root_qi import STEM_WUXING, BENQI, BRANCH_CANGGAN


# 相神配对表（《子平真诠》顺用/逆用）
XIANGSHEN = {
    "官杀": {
        "顺用": ["财", "印"],  # 正官：财生官、印护官
        "逆用": ["食伤", "印"],  # 七杀：食伤制杀、印化杀
    },
    "财": {
        "顺用": ["食伤", "官杀"],  # 财格：食伤生财、官杀护财
        "逆用": [],
    },
    "食伤": {
        "顺用": ["财", "比劫"],  # 食神：财泄秀、比劫生食
        "逆用": ["印", "财"],  # 伤官：印制伤、财泄伤
    },
    "印": {
        "顺用": ["官杀", "比劫"],  # 印格：官杀生印、比劫护印
        "逆用": [],
    },
}

# 破格因素表
POGE = {
    "官杀": ["食伤"],  # 官杀格：食伤破格（伤官见官/食神制杀太过）
    "财": ["比劫"],  # 财格：比劫夺财
    "食伤": ["印"],  # 食伤格：枭神夺食
    "印": ["财"],  # 印格：财破印
}


def _tou_gan(stems, target_wx_set):
    """判某五行是否透干（跳过日干）"""
    for i, s in enumerate(stems):
        if i == 2: continue
        if STEM_WUXING.get(s) in target_wx_set:
            return True
    return False


def _you_gen(branches, target_wx):
    """判某五行是否有本气根"""
    for b in branches:
        if BENQI.get(b) == target_wx:
            return True
    return False


def l2_xiangshen(ge, day_wx, stems, branches):
    """
    L2相神配对

    返回：(相神, reason_tag)
    """
    # 确定顺用/逆用
    if ge == "官杀":
        # 七杀=逆用，正官=顺用（简化：都用两套候选）
        candidates = XIANGSHEN[ge]["顺用"] + XIANGSHEN[ge]["逆用"]
    else:
        candidates = XIANGSHEN[ge].get("顺用", [])

    # 十神→五行
    from spec.wuxing_of import WUXING_OF
    wx_map = WUXING_OF[day_wx]

    # 取最有力的相神（透干优先）
    for xs in candidates:
        xs_wx = wx_map.get(xs)
        if xs_wx and _tou_gan(stems, {xs_wx}):
            return (xs, f"{ge}格相神={xs}（透干）")

    # 透干的没有，取第一个候选
    if candidates:
        return (candidates[0], f"{ge}格相神={candidates[0]}（未透干）")

    return (None, f"{ge}格无相神")


def l3_chengbai(ge, day_wx, stems, branches):
    """
    L3成败救应

    返回：(破格因素列表, reason_tag)
    """
    from spec.wuxing_of import WUXING_OF
    wx_map = WUXING_OF[day_wx]

    poge_list = POGE.get(ge, [])
    poges = []

    for pg in poge_list:
        pg_wx = wx_map.get(pg)
        if pg_wx and _tou_gan(stems, {pg_wx}):
            poges.append(pg)

    if poges:
        return (poges, f"破格因素透干：{','.join(poges)}")
    else:
        return ([], "无破格因素透干")


def zhengge_grade(ge, xiangshen, poges, day_wx, stems, branches, month_branch):
    """
    正格族减项制分级

    返回：(grade, demote_count, reason_tag)
    """
    n = 0

    # 减项①：相神不透干
    if xiangshen:
        from spec.wuxing_of import WUXING_OF
        wx_map = WUXING_OF[day_wx]
        xs_wx = wx_map.get(xiangshen)
        if xs_wx and not _tou_gan(stems, {xs_wx}):
            n += 1

    # 减项②：相神无根
    if xiangshen:
        from spec.wuxing_of import WUXING_OF
        wx_map = WUXING_OF[day_wx]
        xs_wx = wx_map.get(xiangshen)
        if xs_wx and not _you_gen(branches, xs_wx):
            n += 1

    # 减项③：破格因素透干（无救应）
    n += len(poges)

    # 减项④：月令本气不透
    month_canggan = BRANCH_CANGGAN[month_branch]
    benqi = month_canggan[0]
    if benqi:
        benqi_tou = False
        for i, s in enumerate(stems):
            if i == 2: continue
            if s == benqi:
                benqi_tou = True
                break
        if not benqi_tou:
            n += 1

    # 分级
    if n == 0:
        grade = "CONFIRMED"
    elif n == 1:
        grade = "MID_1"
    elif n == 2:
        grade = "MID_2"
    else:
        grade = "REJECT"

    return (grade, n, f"减项{n}")
