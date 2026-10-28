# -*- coding: utf-8 -*-
"""正格族L1取格"""
import sys
sys.path.insert(0, '.')
from spec.root_qi import STEM_WUXING, BRANCH_CANGGAN


# 十神表
SHISHEN = {
    "木": {"木": "比劫", "火": "食伤", "土": "财", "金": "官杀", "水": "印"},
    "火": {"火": "比劫", "土": "食伤", "金": "财", "水": "官杀", "木": "印"},
    "土": {"土": "比劫", "金": "食伤", "水": "财", "木": "官杀", "火": "印"},
    "金": {"金": "比劫", "水": "食伤", "木": "财", "火": "官杀", "土": "印"},
    "水": {"水": "比劫", "木": "食伤", "火": "财", "土": "官杀", "金": "印"},
}


def _get_shishen(day_wx, target_wx):
    """根据日主五行和目标五行，返回十神类别"""
    return SHISHEN[day_wx].get(target_wx, "未知")


def l1_quge(stems, branches, day_stem):
    """
    L1取格——六条优先级链

    返回：(格名, reason_tag)
    """
    day_wx = STEM_WUXING[day_stem]
    month_branch = branches[1]

    month_canggan = BRANCH_CANGGAN[month_branch]
    month_benqi = month_canggan[0]

    # 1. 月令本气透干 → 取本气为格（最高优先级）
    if month_benqi:
        for i, s in enumerate(stems):
            if i == 2: continue
            if s == month_benqi:
                benqi_wx = STEM_WUXING[month_benqi]
                shishen = _get_shishen(day_wx, benqi_wx)
                if shishen != "比劫":
                    return (shishen, f"月令{month_branch}本气{month_benqi}透干取格")

    # 2. 月令本气不透，但本气是比劫 → 看时支（跳过本气）
    # 3. 月令本气不透，本气非比劫 → 优先取本气为格（本气>中气/余气透干）
    if month_benqi:
        benqi_wx = STEM_WUXING[month_benqi]
        shishen_benqi = _get_shishen(day_wx, benqi_wx)
        if shishen_benqi != "比劫":
            return (shishen_benqi, f"月令{month_branch}本气{month_benqi}不透取格（本气优先）")

    # 3. 月令本气是比劫 → 看时支藏干透干
    hour_branch = branches[3]
    hour_canggan = BRANCH_CANGGAN[hour_branch]
    for cg in hour_canggan:
        if not cg: continue
        cg_wx = STEM_WUXING[cg]
        for i, s in enumerate(stems):
            if i == 2: continue
            if s == cg:
                shishen = _get_shishen(day_wx, cg_wx)
                if shishen != "比劫":
                    return (shishen, f"时支{hour_branch}藏{cg}透干取格")

    # 4. 时支也不透 → 无格，按败格论
    return (None, "无格可取——月令时支均不透")
