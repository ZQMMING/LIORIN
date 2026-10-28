# -*- coding: utf-8 -*-
"""PATCH-070 调候x岁运接口
流年/大运五行 -> 调候条件变化标记(warming/cooling/moistening/drying)
铁律: 只标climate_factor_change, 不直接断吉凶(吉凶属SMTH Rule Layer)
"""
import io, sys

ELEMENT_FACTOR = {
    "丙": "warming", "丁": "warming",
    "壬": "moistening", "癸": "moistening",
    "甲": "nourishing", "乙": "nourishing",
    "庚": "drying", "辛": "drying",
    "戊": "drying", "己": "drying",
}


def climate_luck_change(luck_stems):
    """
    luck_stems: 大运/流年天干列表
    return: 调候条件变化标记, 不断吉凶
    """
    factors = []
    for s in luck_stems:
        f = ELEMENT_FACTOR.get(s)
        if f:
            factors.append({"stem": s, "climate_factor": f})
    return {
        "state": "climate_condition_change",
        "namespace": "QTBJ.climate_luck",
        "factors": factors,
        "judgment": "ABSTAIN",
        "note": "只标调候条件变化, 吉凶属SMTH Rule Layer不直接断"
    }


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("=== PATCH-070 调候x岁运 ===")
    # GC-001 2024甲辰流年: 甲(比劫)+戊(财)
    r = climate_luck_change(["甲", "戊"])
    for k, v in r.items():
        print(f"  {k}: {v}")
